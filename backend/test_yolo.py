"""
Unit test for YOLO detection on test_camera_1.jpg
Shows what YOLO is detecting with bounding boxes
"""

from ultralytics import YOLO
import cv2

# Load model
model = YOLO('yolo11n.pt')

# Load test image
image = cv2.imread('test_camera_1.jpg')

# Run detection once
results = model(image, conf=0.45, verbose=False)

# Draw detections and save
annotated = image.copy()
for result in results:
    boxes = result.boxes
    for box in boxes:
        # Get coordinates
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        # Get class and confidence
        class_id = int(box.cls[0])
        conf = float(box.conf[0])

        # Draw box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Add label
        label = f"Class {class_id}: {conf:.2f}"
        cv2.putText(annotated, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        print(f"Detected: Class {class_id}, Confidence {conf:.2f}, Box: ({x1},{y1}) to ({x2},{y2})")

# Save annotated image
cv2.imwrite('test_camera_1_detections.jpg', annotated)
print(f"\nAnnotated image saved to: test_camera_1_detections.jpg")
