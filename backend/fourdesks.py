import cv2
import numpy as np
import os

# Model options:
#   SSD MobileNet V2 (fast, less accurate):
#     CONFIG  = "ssd_mobilenet_v2_coco_2018_03_29.pbtxt"
#     WEIGHTS = "ssd_mobilenet_v2_coco_2018_03_29.pb"
#     INPUT_SIZE = (300, 300)
#
#   Faster R-CNN Inception V2 (slower, more accurate):
#     CONFIG  = "faster_rcnn_inception_v2_coco_2018_01_28.pbtxt"
#     WEIGHTS = "faster_rcnn_inception_v2_coco_2018_01_28.pb"
#     INPUT_SIZE = (800, 600)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Choose model: "ssd" or "fasterrcnn"
MODEL = "fasterrcnn"

if MODEL == "ssd":
    CONFIG  = os.path.join(SCRIPT_DIR, "ssd_mobilenet_v2_coco_2018_03_29.pbtxt")
    WEIGHTS = os.path.join(SCRIPT_DIR, "ssd_mobilenet_v2_coco_2018_03_29.pb")
    INPUT_SIZE = (300, 300)
else:  # fasterrcnn
    CONFIG  = os.path.join(SCRIPT_DIR, "faster_rcnn_inception_v2_coco_2018_01_28.pbtxt")
    WEIGHTS = os.path.join(SCRIPT_DIR, "faster_rcnn_inception_v2_coco_2018_01_28.pb")
    INPUT_SIZE = (800, 600)

CONFIDENCE_THRESHOLD = 0.5

# COCO class labels (90 classes)
CLASSES = [
    "background", "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "unused", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse",
    "sheep", "table", "elephant", "bear", "zebra", "giraffe", "unused", "backpack", "umbrella", "unused",
    "unused", "handbag", "desk", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
    "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "unused", "wine glass", "cup", "fork", "knife",
    "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza",
    "donut", "cake", "chair", "couch", "potted plant", "bed", "unused", "dining table", "unused", "unused",
    "toilet", "unused", "drink", "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave", "oven",
    "toaster", "bag", "refrigerator", "unused", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
    "toothbrush"
]
COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3)).astype(int)

net = cv2.dnn.readNetFromTensorflow(WEIGHTS, CONFIG)

# Store baseline detections (boxes that should be ignored)
# Format: dict of desk_id -> list of (class_id, x1, y1, x2, y2)
baseline_detections = {}

# Current image/video dimensions (set dynamically)
IMG_WIDTH = None
IMG_HEIGHT = None

# Cached ROIs (recomputed when dimensions change)
DESK_ROIS = {}
TABLE_ROIS = {}

TABLE_MARGIN_OUTER = 0.2

def update_dimensions(width, height):
    """Update ROIs based on actual image/video dimensions."""
    global IMG_WIDTH, IMG_HEIGHT, DESK_ROIS, TABLE_ROIS
    
    if IMG_WIDTH == width and IMG_HEIGHT == height:
        return  # No change needed
    
    IMG_WIDTH = width
    IMG_HEIGHT = height
    
    # Define the 4 desk ROIs as (x1, y1, x2, y2) - equal quadrants
    DESK_ROIS = {
        1: (0, 0, IMG_WIDTH // 2, IMG_HEIGHT // 2),                          # Top-left
        2: (IMG_WIDTH // 2, 0, IMG_WIDTH, IMG_HEIGHT // 2),                  # Top-right
        3: (0, IMG_HEIGHT // 2, IMG_WIDTH // 2, IMG_HEIGHT),                 # Bottom-left
        4: (IMG_WIDTH // 2, IMG_HEIGHT // 2, IMG_WIDTH, IMG_HEIGHT)          # Bottom-right
    }
    
    # Compute table ROIs
    TABLE_ROIS = {did: get_table_roi(did) for did in DESK_ROIS}
    print(f"ROIs updated for {width}x{height}")


def get_table_roi(desk_id):
    x1, y1, x2, y2 = DESK_ROIS[desk_id]
    w = x2 - x1
    h = y2 - y1
    
    # Left column (1, 3): crop left edge (outer), keep right aligned (inner)
    # Right column (2, 4): crop right edge (outer), keep left aligned (inner)
    if desk_id in [1, 3]:
        tx1 = x1 + int(w * TABLE_MARGIN_OUTER)  # Crop left (outer edge)
        tx2 = x2  # Keep right edge aligned (inner)
    else:
        tx1 = x1  # Keep left edge aligned (inner)
        tx2 = x2 - int(w * TABLE_MARGIN_OUTER)  # Crop right (outer edge)
    
    if desk_id in [1, 2]:
        # Top row desks: crop top 30%, table at bottom
        ty1 = y1 + int(h * 0.3)  # Skip top 30%
        ty2 = y2
    else:
        # Bottom row desks: use full height (object could be anywhere)
        ty1 = y1
        ty2 = y2
    
    return (tx1, ty1, tx2, ty2)


def iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0


def is_person(class_id):
    return class_id == 0 or class_id == 1


def overlaps_baseline(desk_id, class_id, box, threshold=0.5):
    if desk_id not in baseline_detections:
        return False
    
    for (base_class, x1, y1, x2, y2) in baseline_detections[desk_id]:
        # Only compare same category (person-to-person, object-to-object)
        if is_person(class_id) != is_person(base_class):
            continue
        if iou(box, (x1, y1, x2, y2)) > threshold:
            return True
    return False


def get_detections(image, roi=None):
    h, w = image.shape[:2]
    
    if roi is not None:
        rx1, ry1, rx2, ry2 = roi
        rx1, ry1 = max(0, rx1), max(0, ry1)
        rx2, ry2 = min(w, rx2), min(h, ry2)
        cropped = image[ry1:ry2, rx1:rx2]
        crop_h, crop_w = cropped.shape[:2]
    else:
        cropped = image
        crop_h, crop_w = h, w
        rx1, ry1 = 0, 0

    # Pre-resize to model input size for efficiency (optional)
    # This reduces memory usage and speeds up inference for large images
    target_w, target_h = INPUT_SIZE
    if crop_w > target_w * 1.5 or crop_h > target_h * 1.5:
        # Resize while maintaining aspect ratio
        scale_factor = min(target_w / crop_w, target_h / crop_h)
        new_w = int(crop_w * scale_factor)
        new_h = int(crop_h * scale_factor)
        resized = cv2.resize(cropped, (new_w, new_h))
        blob = cv2.dnn.blobFromImage(resized, size=INPUT_SIZE, swapRB=True, crop=False)
    else:
        blob = cv2.dnn.blobFromImage(cropped, size=INPUT_SIZE, swapRB=True, crop=False)
    
    net.setInput(blob)
    detections = net.forward()

    results = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence < CONFIDENCE_THRESHOLD:
            continue

        class_id = int(detections[0, 0, i, 1])
        box = detections[0, 0, i, 3:7] * np.array([crop_w, crop_h, crop_w, crop_h])
        (x1, y1, x2, y2) = box.astype(int)
        
        x1, x2 = x1 + rx1, x2 + rx1
        y1, y2 = y1 + ry1, y2 + ry1
        
        results.append((class_id, confidence, x1, y1, x2, y2))
    
    return results


def set_baseline(images, desk_id=None):
    global baseline_detections
    
    # Handle single image or list of images
    if not isinstance(images, list):
        images = [images]
    
    # Resize baseline images to match current dimensions
    resized_images = []
    for image in images:
        if image is None:
            continue
        h, w = image.shape[:2]
        if w != IMG_WIDTH or h != IMG_HEIGHT:
            image = cv2.resize(image, (IMG_WIDTH, IMG_HEIGHT))
        resized_images.append(image)
    images = resized_images
    
    if desk_id is not None:
        # Set baseline for specific desk
        roi = DESK_ROIS.get(desk_id)
        baseline_detections[desk_id] = []
        
        for i, image in enumerate(images):
            if image is None:
                continue
            detections = get_detections(image, roi)
            new_baselines = [(class_id, x1, y1, x2, y2) for (class_id, _, x1, y1, x2, y2) in detections]
            baseline_detections[desk_id].extend(new_baselines)
        
        persons = sum(1 for (cid, *_) in baseline_detections[desk_id] if is_person(cid))
        objects = len(baseline_detections[desk_id]) - persons
        print(f"Desk {desk_id} baseline: {persons} person(s), {objects} object(s)")
    else:
        # Set baseline for all desks
        for did, roi in DESK_ROIS.items():
            baseline_detections[did] = []
            
            for image in images:
                if image is None:
                    continue
                detections = get_detections(image, roi)
                new_baselines = [(class_id, x1, y1, x2, y2) for (class_id, _, x1, y1, x2, y2) in detections]
                baseline_detections[did].extend(new_baselines)
            
            persons = sum(1 for (cid, *_) in baseline_detections[did] if is_person(cid))
            objects = len(baseline_detections[did]) - persons
            print(f"Desk {did} baseline: {persons} person(s), {objects} object(s)")
    
    return baseline_detections


def detect(image, desk_id=None, use_baseline=True):

    if desk_id is not None:
        # Single desk detection
        desk_roi = DESK_ROIS.get(desk_id)
        table_roi = TABLE_ROIS.get(desk_id)
        
        # Detect persons in full desk area
        desk_detections = get_detections(image, desk_roi)
        for (class_id, confidence, x1, y1, x2, y2) in desk_detections:
            if use_baseline and overlaps_baseline(desk_id, class_id, (x1, y1, x2, y2)):
                continue
            if is_person(class_id):
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(image, f"person {confidence:.2f}", (x1, y1 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Detect objects in table-only area
        table_detections = get_detections(image, table_roi)
        for (class_id, confidence, x1, y1, x2, y2) in table_detections:
            if use_baseline and overlaps_baseline(desk_id, class_id, (x1, y1, x2, y2)):
                continue
            if not is_person(class_id):
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(image, f"object {confidence:.2f}", (x1, y1 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    else:
        # All desks detection
        for did in DESK_ROIS:
            desk_roi = DESK_ROIS[did]
            table_roi = TABLE_ROIS[did]
            
            # Draw desk boundary (cyan)
            rx1, ry1, rx2, ry2 = desk_roi
            cv2.rectangle(image, (rx1, ry1), (rx2, ry2), (255, 255, 0), 2)
            cv2.putText(image, f"Desk {did}", (rx1 + 10, ry1 + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)
            
            # Draw table boundary (magenta)
            tx1, ty1, tx2, ty2 = table_roi
            cv2.rectangle(image, (tx1, ty1), (tx2, ty2), (255, 0, 255), 2)
            
            # Detect persons in full desk area
            desk_detections = get_detections(image, desk_roi)
            for (class_id, confidence, x1, y1, x2, y2) in desk_detections:
                if use_baseline and overlaps_baseline(did, class_id, (x1, y1, x2, y2)):
                    continue
                if is_person(class_id):
                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(image, f"person {confidence:.2f}", (x1, y1 - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Detect objects in table-only area
            table_detections = get_detections(image, table_roi)
            for (class_id, confidence, x1, y1, x2, y2) in table_detections:
                if use_baseline and overlaps_baseline(did, class_id, (x1, y1, x2, y2)):
                    continue
                if not is_person(class_id):
                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(image, f"object {confidence:.2f}", (x1, y1 - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    return image


def check_occupancy(image, desk_id=None, use_baseline=True):
    if desk_id is not None:
        # Check full desk area for persons
        desk_roi = DESK_ROIS.get(desk_id)
        desk_detections = get_detections(image, desk_roi)
        
        persons = []
        for (class_id, confidence, x1, y1, x2, y2) in desk_detections:
            if use_baseline and overlaps_baseline(desk_id, class_id, (x1, y1, x2, y2)):
                continue
            if is_person(class_id):
                persons.append((confidence, x1, y1, x2, y2))
        
        # Check table-only area for objects (smaller ROI)
        table_roi = TABLE_ROIS.get(desk_id)
        table_detections = get_detections(image, table_roi)
        
        objects = []
        for (class_id, confidence, x1, y1, x2, y2) in table_detections:
            if use_baseline and overlaps_baseline(desk_id, class_id, (x1, y1, x2, y2)):
                continue
            if not is_person(class_id):
                objects.append((confidence, x1, y1, x2, y2))
        
        has_person = len(persons) > 0
        has_object = len(objects) > 0
        is_occupied = has_person or has_object
        
        details = {
            "person_count": len(persons),
            "object_count": len(objects),
            "persons": persons,
            "objects": objects
        }
        
        return is_occupied, has_person, has_object, details
    else:
        # All desks
        results = {}
        for did in DESK_ROIS:
            results[did] = check_occupancy(image, did, use_baseline)
        return results


def check_all_desks(image, use_baseline=True):
    results = check_occupancy(image, desk_id=None, use_baseline=use_baseline)
    return {did: result[0] for did, result in results.items()}


def is_desk_empty(image, desk_id, use_baseline=True):
    is_occupied, _, _, _ = check_occupancy(image, desk_id, use_baseline)
    return not is_occupied


def is_desk_occupied(image, desk_id, use_baseline=True):
    is_occupied, _, _, _ = check_occupancy(image, desk_id, use_baseline)
    return is_occupied


def detect_video(input_path, output_path, baseline_imgs=None, skip_frames=0, scale=1.0):
    cap = cv2.VideoCapture(input_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video {input_path}")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Compressed dimensions
    width = int(orig_width * scale)
    height = int(orig_height * scale)
    
    # Update ROIs for video dimensions (after scaling)
    update_dimensions(width, height)
    
    if baseline_imgs is not None:
        set_baseline(baseline_imgs)  # Sets baseline for all desks
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_count = 0
    processed = 0
    
    print(f"Processing: {total_frames} frames @ {fps:.1f} FPS")
    print(f"Input: {orig_width}x{orig_height} -> Output: {width}x{height} (scale={scale})")
    print(f"Model: {MODEL}, skip_frames={skip_frames}")
    
    last_result = None
    last_statuses = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Resize frame for compression
        if scale != 1.0:
            frame = cv2.resize(frame, (width, height))
        
        frame_count += 1
        
        if skip_frames == 0 or frame_count % (skip_frames + 1) == 1:
            # Check occupancy for all desks
            all_occupancy = check_occupancy(frame.copy(), desk_id=None, use_baseline=baseline_imgs is not None)
            
            # Draw detections for all desks
            result = detect(frame.copy(), desk_id=None, use_baseline=baseline_imgs is not None)
            
            # Add status overlay for each desk
            y_offset = 30
            for did in sorted(DESK_ROIS.keys()):
                is_occupied, has_person, has_object, _ = all_occupancy[did]
                
                if is_occupied:
                    status = f"Desk {did}: OCCUPIED"
                    if has_person:
                        status += " (person)"
                    elif has_object:
                        status += " (objects)"
                    status_color = (0, 0, 255)  # Red
                else:
                    status = f"Desk {did}: EMPTY"
                    status_color = (0, 255, 0)  # Green
                
                cv2.putText(result, status, (10, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
                y_offset += 25
            
            last_result = result
            last_statuses = {did: all_occupancy[did][0] for did in DESK_ROIS}
            processed += 1
        else:
            result = frame if last_result is None else last_result
        
        out.write(result)
        
        if frame_count % 100 == 0:
            print(f"  {frame_count}/{total_frames} ({100*frame_count/total_frames:.1f}%)")
    
    cap.release()
    out.release()
    print(f"Done! {processed} frames processed -> {output_path}")


if __name__ == "__main__":
    import sys
    
    # Default input: 4-desk grid image
    if len(sys.argv) > 1:
        INPUT = sys.argv[1]
    else:
        INPUT = os.path.join(SCRIPT_DIR, "fourdesks.jpg")
    
    # Baseline image (empty desks reference)
    BASELINE_PATH = os.path.join(SCRIPT_DIR, "images_4grid/tables_reference.jpg")
    
    video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
    ext = os.path.splitext(INPUT)[1].lower()
    
    # Load baseline if it exists
    baseline_imgs = None
    if os.path.exists(BASELINE_PATH):
        baseline_img = cv2.imread(BASELINE_PATH)
        if baseline_img is not None:
            print(f"Loaded baseline: {BASELINE_PATH}")
            # Resize baseline to match video if needed (handled in set_baseline)
            baseline_imgs = [baseline_img]
    
    if ext in video_exts:
        OUTPUT = os.path.splitext(INPUT)[0] + "_detected.mp4"
        detect_video(INPUT, OUTPUT, baseline_imgs, skip_frames=30, scale=1)
    else:
        OUTPUT = os.path.splitext(INPUT)[0] + "_detected.jpg"
        
        # Image scale factor (1.0 = full res, 0.5 = half, etc.)
        IMAGE_SCALE = 0.4
        
        image = cv2.imread(INPUT)
        if image is None:
            print(f"Error: Could not read {INPUT}")
        else:
            # Downsample image
            if IMAGE_SCALE != 1.0:
                h, w = image.shape[:2]
                new_w, new_h = int(w * IMAGE_SCALE), int(h * IMAGE_SCALE)
                image = cv2.resize(image, (new_w, new_h))
                print(f"Scaled: {w}x{h} -> {new_w}x{new_h}")
            
            # Update ROIs for image dimensions
            h, w = image.shape[:2]
            update_dimensions(w, h)
            
            # Set baseline for all 4 desks (after dimensions are set)
            if baseline_imgs:
                set_baseline(baseline_imgs)
            
            # Check occupancy for all desks
            print("\n=== Desk Occupancy ===")
            occupancy = check_all_desks(image, use_baseline=baseline_imgs is not None)
            for desk_id in sorted(occupancy.keys()):
                status = "OCCUPIED" if occupancy[desk_id] else "EMPTY"
                print(f"  Desk {desk_id}: {status}")
            
            # Draw detections on all desks
            result = detect(image, desk_id=None, use_baseline=baseline_imgs is not None)
            cv2.imwrite(OUTPUT, result)
            print(f"\nSaved: {OUTPUT}")