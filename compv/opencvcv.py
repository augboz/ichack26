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
MODEL = "ssd"

if MODEL == "ssd":
    CONFIG  = os.path.join(SCRIPT_DIR, "ssd_mobilenet_v2_coco_2018_03_29.pbtxt")
    WEIGHTS = os.path.join(SCRIPT_DIR, "ssd_mobilenet_v2_coco_2018_03_29.pb")
    INPUT_SIZE = (300, 300)
else:  # fasterrcnn
    CONFIG  = os.path.join(SCRIPT_DIR, "faster_rcnn_inception_v2_coco_2018_01_28.pbtxt")
    WEIGHTS = os.path.join(SCRIPT_DIR, "faster_rcnn_inception_v2_coco_2018_01_28.pb")
    INPUT_SIZE = (800, 600)

CONFIDENCE_THRESHOLD = 0.3

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
# Format: list of (class_id, x1, y1, x2, y2)
baseline_detections = []


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


def overlaps_baseline(class_id, box, threshold=0.5):

    for (base_class, x1, y1, x2, y2) in baseline_detections:
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


def set_baseline(images, roi=None):
    global baseline_detections
    
    # Handle single image or list of images
    if not isinstance(images, list):
        images = [images]
    
    baseline_detections = []
    
    for i, image in enumerate(images):
        if image is None:
            continue
        detections = get_detections(image, roi)
        new_baselines = [(class_id, x1, y1, x2, y2) for (class_id, _, x1, y1, x2, y2) in detections]
        baseline_detections.extend(new_baselines)
        print(f"Baseline image {i+1}: {len(new_baselines)} detection(s)")
    
    persons = sum(1 for (cid, *_) in baseline_detections if is_person(cid))
    objects = len(baseline_detections) - persons
    print(f"Total baseline: {persons} person(s), {objects} object(s) to ignore")
    return baseline_detections


def detect(image, roi=None, use_baseline=True):
    detections = get_detections(image, roi)
    
    for (class_id, confidence, x1, y1, x2, y2) in detections:
        # Skip if this detection overlaps with baseline of same category
        if use_baseline and overlaps_baseline(class_id, (x1, y1, x2, y2)):
            continue
        
        # Simplify to person vs object
        if is_person(class_id):
            label = "person"
            color = (0, 255, 0)  # Green for person
        else:
            label = "object"
            color = (0, 0, 255)  # Red for objects

        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(image, f"{label} {confidence:.2f}", (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    return image


def check_occupancy(image, roi=None, use_baseline=True):
    
    detections = get_detections(image, roi)
    
    persons = []
    objects = []
    
    for (class_id, confidence, x1, y1, x2, y2) in detections:
        if use_baseline and overlaps_baseline(class_id, (x1, y1, x2, y2)):
            continue
        
        if is_person(class_id):
            persons.append((confidence, x1, y1, x2, y2))
        else:
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


def is_desk_empty(image, roi=None, use_baseline=True):
    is_occupied, _, _, _ = check_occupancy(image, roi, use_baseline)
    return not is_occupied


def is_desk_occupied(image, roi=None, use_baseline=True):
    is_occupied, _, _, _ = check_occupancy(image, roi, use_baseline)
    return is_occupied


def detect_video(input_path, output_path, baseline_imgs=None, roi=None, skip_frames=0, scale=0.5):
    if baseline_imgs is not None:
        set_baseline(baseline_imgs, roi)
    
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
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_count = 0
    processed = 0
    
    print(f"Processing: {total_frames} frames @ {fps:.1f} FPS")
    print(f"Input: {orig_width}x{orig_height} -> Output: {width}x{height} (scale={scale})")
    print(f"Model: {MODEL}, skip_frames={skip_frames}")
    
    last_result = None
    last_status = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Resize frame for compression
        frame = cv2.resize(frame, (width, height))
        
        frame_count += 1
        
        if skip_frames == 0 or frame_count % (skip_frames + 1) == 1:
            # Check occupancy
            is_occupied, has_person, has_object, details = check_occupancy(
                frame.copy(), roi, use_baseline=baseline_imgs is not None
            )
            
            # Draw detections
            result = detect(frame.copy(), roi, use_baseline=baseline_imgs is not None)
            
            # Add status overlay
            if is_occupied:
                status = "OCCUPIED"
                if has_person and has_object:
                    status += " (person + objects)"
                elif has_person:
                    status += " (person)"
                else:
                    status += " (objects only)"
                status_color = (0, 0, 255)  # Red
            else:
                status = "EMPTY"
                status_color = (0, 255, 0)  # Green
            
            cv2.putText(result, status, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, status_color, 2)
            
            last_result = result
            last_status = (is_occupied, has_person, has_object)
            processed += 1
            
            # Print status changes
            if last_status != (is_occupied, has_person, has_object):
                print(f"  Frame {frame_count}: {status}")
        else:
            # Reuse last detection overlay on current frame
            result = frame if last_result is None else last_result
        
        out.write(result)
        
        if frame_count % 100 == 0:
            print(f"  {frame_count}/{total_frames} ({100*frame_count/total_frames:.1f}%)")
    
    cap.release()
    out.release()
    print(f"Done! {processed} frames processed -> {output_path}")


if __name__ == "__main__":
    import sys
    
    # Two baseline images: with chair and without chair
    BASELINE_WITH_CHAIR = os.path.join(SCRIPT_DIR, "images/desk.png")
    BASELINE_WITHOUT_CHAIR = os.path.join(SCRIPT_DIR, "images/deskonly.png")
    
    if len(sys.argv) > 1:
        INPUT = sys.argv[1]
    else:
        INPUT = os.path.join(SCRIPT_DIR, "videos/checker.mp4")
    
    video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
    ext = os.path.splitext(INPUT)[1].lower()
    
    # Load both baseline images
    baseline_imgs = []
    for path in [BASELINE_WITH_CHAIR, BASELINE_WITHOUT_CHAIR]:
        img = cv2.imread(path)
        if img is not None:
            print(f"Loaded baseline: {path}")
            baseline_imgs.append(img)
        else:
            print(f"Warning: Could not load {path}")
    
    if ext in video_exts:
        OUTPUT = os.path.splitext(INPUT)[0] + "_detected.mp4"
        detect_video(INPUT, OUTPUT, baseline_imgs if baseline_imgs else None, skip_frames=3, scale=0.5)
    else:
        OUTPUT = os.path.splitext(INPUT)[0] + "_detected.png"
        if baseline_imgs:
            set_baseline(baseline_imgs)
        image = cv2.imread(INPUT)
        if image is None:
            print(f"Error: Could not read {INPUT}")
        else:
            result = detect(image)
            cv2.imwrite(OUTPUT, result)