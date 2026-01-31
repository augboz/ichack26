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
    """Calculate Intersection over Union between two boxes."""
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
    """Check if class_id represents a person."""
    return class_id == 0 or class_id == 1


def overlaps_baseline(class_id, box, threshold=0.5):
    """
    Check if a detection overlaps with baseline.
    Only compares against same category (person vs person, object vs object).
    """
    for (base_class, x1, y1, x2, y2) in baseline_detections:
        # Only compare same category (person-to-person, object-to-object)
        if is_person(class_id) != is_person(base_class):
            continue
        if iou(box, (x1, y1, x2, y2)) > threshold:
            return True
    return False


def get_detections(image, roi=None):
    """
    Get raw detections from image (without drawing).
    
    Returns list of (class_id, confidence, x1, y1, x2, y2)
    """
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


def set_baseline(image, roi=None):
    """
    Set the baseline image. All detections in this image will be ignored in future detections.
    """
    global baseline_detections
    detections = get_detections(image, roi)
    baseline_detections = [(class_id, x1, y1, x2, y2) for (class_id, _, x1, y1, x2, y2) in detections]
    
    persons = sum(1 for (cid, *_) in baseline_detections if is_person(cid))
    objects = len(baseline_detections) - persons
    print(f"Baseline set: {persons} person(s), {objects} object(s) to ignore")
    return baseline_detections


def detect(image, roi=None, use_baseline=True):
    """
    Detect objects in image.
    
    Args:
        image: Input image (BGR)
        roi: Optional region of interest as (x1, y1, x2, y2) tuple.
             If provided, only searches within this area.
        use_baseline: If True, filter out detections that overlap with baseline.
    """
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


if __name__ == "__main__":
    BASELINE = os.path.join(SCRIPT_DIR, "images/desk.png")
    INPUT  = os.path.join(SCRIPT_DIR, "images/clyde.png")
    OUTPUT = os.path.join(SCRIPT_DIR, "images/output.png")

    # Set baseline (objects to ignore)
    baseline_img = cv2.imread(BASELINE)
    if baseline_img is not None:
        set_baseline(baseline_img)
    else:
        print(f"Warning: Could not load baseline {BASELINE}")

    # Detect new objects (filtering out baseline)
    image = cv2.imread(INPUT)
    result = detect(image)
    cv2.imwrite(OUTPUT, result)
    print(f"Saved to {OUTPUT}")