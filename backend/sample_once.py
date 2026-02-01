"""
Single Sample Run Script

Processes all active cameras once and logs occupancy status to the database.
This is useful for testing or manual sampling.

Usage:
    python sample_once.py
"""

import cv2
import numpy as np
import os
from typing import Optional, Dict, List, Tuple

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'occupancy_db',
    'user': 'root',
    'password': 'yazool921'
}

# Detection model configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL = "ssd"

if MODEL == "ssd":
    CONFIG = os.path.join(SCRIPT_DIR, "ssd_mobilenet_v2_coco_2018_03_29.pbtxt")
    WEIGHTS = os.path.join(SCRIPT_DIR, "ssd_mobilenet_v2_coco_2018_03_29.pb")
    INPUT_SIZE = (300, 300)
else:
    CONFIG = os.path.join(SCRIPT_DIR, "faster_rcnn_inception_v2_coco_2018_03_29.pbtxt")
    WEIGHTS = os.path.join(SCRIPT_DIR, "faster_rcnn_inception_v2_coco_2018_03_29.pb")
    INPUT_SIZE = (800, 600)

CONFIDENCE_THRESHOLD = 0.3
TEST_MODE = True  # Set to False to use camera streams instead of test images


def load_detection_model():
    """Load the object detection model."""
    if not os.path.exists(WEIGHTS) or not os.path.exists(CONFIG):
        print(f"ERROR: Model files not found!")
        print(f"CONFIG: {CONFIG}")
        print(f"WEIGHTS: {WEIGHTS}")
        return None

    try:
        net = cv2.dnn.readNetFromTensorflow(WEIGHTS, CONFIG)
        print("✓ Detection model loaded successfully")
        return net
    except Exception as e:
        print(f"ERROR loading detection model: {e}")
        return None


def is_occupancy_indicator(class_id):
    """Check if class_id represents an occupancy indicator (person, laptop, phone)."""
    return class_id in [0, 63, 67]  # 0=person, 63=laptop, 67=cell phone


def point_in_polygon(point: Tuple[int, int], polygon: List[Tuple[int, int]]) -> bool:
    """Check if a point is inside a polygon using ray casting algorithm."""
    x, y = point
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
                    elif p1x == p2x:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def detect_persons(image: np.ndarray, detection_net) -> List[Tuple[int, int, int, int]]:
    """Detect persons/laptops/phones in an image."""
    if detection_net is None:
        return []

    h, w = image.shape[:2]
    blob = cv2.dnn.blobFromImage(image, size=INPUT_SIZE, swapRB=True, crop=False)
    detection_net.setInput(blob)
    detections = detection_net.forward()

    boxes = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence < CONFIDENCE_THRESHOLD:
            continue

        class_id = int(detections[0, 0, i, 1])
        if not is_occupancy_indicator(class_id):
            continue

        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])

        if not np.all(np.isfinite(box)):
            continue

        (x1, y1, x2, y2) = box.astype(int)

        if x1 < 0 or y1 < 0 or x2 > w or y2 > h or x2 <= x1 or y2 <= y1:
            continue

        boxes.append((x1, y1, x2, y2))

    return boxes


def get_desk_occupancy(image: np.ndarray, desk_rectangles: Dict, detection_net) -> List[Tuple[int, bool]]:
    """
    Determine which desks are occupied in the image.

    Returns:
        List of (desk_id, is_occupied) tuples
    """
    if image is None or not desk_rectangles:
        return []

    # Detect all occupancy indicators
    boxes = detect_persons(image, detection_net)

    # Calculate midpoints
    midpoints = []
    for x1, y1, x2, y2 in boxes:
        midpoint = ((x1 + x2) // 2, (y1 + y2) // 2)
        midpoints.append(midpoint)

    # Check each desk
    results = []
    for desk_id, vertices in desk_rectangles.items():
        is_occupied = any(point_in_polygon(mp, vertices) for mp in midpoints)
        results.append((desk_id, is_occupied))

    return results


def get_active_cameras(db):
    """Get all active camera IDs from database."""
    cur = db.conn.cursor()
    try:
        cur.execute("SELECT camera_id FROM Camera WHERE is_active = TRUE ORDER BY camera_id")
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()


def get_desk_rectangles(db, camera_id):
    """Get desk rectangles for a camera."""
    desks = db.get_desks_for_camera(camera_id)

    rectangles = {}
    for desk in desks:
        vertices = [
            (desk['bottom_left_x'], desk['bottom_left_y']),
            (desk['bottom_right_x'], desk['bottom_right_y']),
            (desk['top_right_x'], desk['top_right_y']),
            (desk['top_left_x'], desk['top_left_y'])
        ]
        rectangles[desk['desk_id']] = vertices

    return rectangles


def get_image(camera_id):
    """Get image from camera (file in TEST_MODE, stream in production)."""
    if TEST_MODE:
        filename = f"test_camera_{camera_id}.jpg"
        if not os.path.exists(filename):
            print(f"  Warning: Test image not found: {filename}")
            return None

        image = cv2.imread(filename)
        if image is None:
            print(f"  Error: Failed to load image: {filename}")
            return None

        return image
    else:
        # Production mode - get stream URL and capture from camera
        print("  Production mode not implemented in this script")
        return None


def main():
    print("\n" + "="*60)
    print("SINGLE SAMPLE RUN")
    print("="*60)
    print(f"Mode: {'TEST (using image files)' if TEST_MODE else 'PRODUCTION (using camera streams)'}")
    print()

    # Load detection model
    detection_net = load_detection_model()
    if detection_net is None:
        print("ERROR: Cannot proceed without detection model")
        return

    # Connect to database
    try:
        from db_interface import OccupancyDatabase
        db = OccupancyDatabase(**DB_CONFIG)
        print("✓ Connected to database")
    except Exception as e:
        print(f"ERROR: Cannot connect to database: {e}")
        return

    try:
        # Get all active cameras
        cameras = get_active_cameras(db)
        print(f"✓ Found {len(cameras)} active cameras: {cameras}")
        print()

        if not cameras:
            print("No active cameras found in database")
            return

        # Process each camera
        total_desks_processed = 0
        total_occupied = 0

        for camera_id in cameras:
            print(f"Processing camera {camera_id}...")

            # Get image
            image = get_image(camera_id)
            if image is None:
                print(f"  Skipping camera {camera_id} (no image)")
                continue

            print(f"  Image loaded: {image.shape[1]}x{image.shape[0]}")

            # Get desk rectangles
            desk_rectangles = get_desk_rectangles(db, camera_id)
            print(f"  Found {len(desk_rectangles)} desks")

            if not desk_rectangles:
                continue

            # Detect occupancy
            occupancy_results = get_desk_occupancy(image, desk_rectangles, detection_net)

            # Log to database
            for desk_id, is_occupied in occupancy_results:
                try:
                    db.add_log(desk_id, is_occupied)
                    status = "OCCUPIED" if is_occupied else "EMPTY"
                    print(f"  Desk {desk_id}: {status}")

                    total_desks_processed += 1
                    if is_occupied:
                        total_occupied += 1

                except Exception as e:
                    print(f"  Error logging desk {desk_id}: {e}")

            print()

        # Summary
        print("="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Cameras processed: {len(cameras)}")
        print(f"Desks processed: {total_desks_processed}")
        print(f"Occupied: {total_occupied}")
        print(f"Empty: {total_desks_processed - total_occupied}")
        print(f"Occupancy rate: {(total_occupied / total_desks_processed * 100):.1f}%" if total_desks_processed > 0 else "N/A")
        print()

    finally:
        db.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
