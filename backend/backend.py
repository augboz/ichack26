from concurrent.futures import ThreadPoolExecutor
import time
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import os


# Set this to False when deploying to production
TEST_MODE = True

# Object detection model setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL = "ssd"

if MODEL == "ssd":
    CONFIG = os.path.join(SCRIPT_DIR, "ssd_mobilenet_v2_coco_2018_03_29.pbtxt")
    WEIGHTS = os.path.join(SCRIPT_DIR, "ssd_mobilenet_v2_coco_2018_03_29.pb")
    INPUT_SIZE = (300, 300)
else:
    CONFIG = os.path.join(SCRIPT_DIR, "faster_rcnn_inception_v2_coco_2018_01_28.pbtxt")
    WEIGHTS = os.path.join(SCRIPT_DIR, "faster_rcnn_inception_v2_coco_2018_01_28.pb")
    INPUT_SIZE = (800, 600)

CONFIDENCE_THRESHOLD = 0.3

# Load detection model (only if model files exist)
detection_net = None
try:
    if os.path.exists(WEIGHTS) and os.path.exists(CONFIG):
        detection_net = cv2.dnn.readNetFromTensorflow(WEIGHTS, CONFIG)
        print("Object detection model loaded successfully")
    else:
        print(f"Warning: Model files not found. Detection will not work.")
        print(f"CONFIG: {CONFIG}")
        print(f"WEIGHTS: {WEIGHTS}")
except Exception as e:
    print(f"Error loading detection model: {e}")


def is_person(class_id):
    """Check if class_id represents a person (COCO dataset: class 1 is person)."""
    return class_id == 1


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
        p1x, p1y = p2x, p2y

    return inside


def box_intersects_polygon(box: Tuple[int, int, int, int], polygon: List[Tuple[int, int]]) -> bool:
    """Check if a bounding box intersects with a polygon (table boundary)."""
    x1, y1, x2, y2 = box

    # Check if any corner of the box is inside the polygon
    corners = [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]
    for corner in corners:
        if point_in_polygon(corner, polygon):
            return True

    # Check if center of box is in polygon
    center = ((x1 + x2) // 2, (y1 + y2) // 2)
    if point_in_polygon(center, polygon):
        return True

    return False


def detect_persons_in_image(image: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """
    Detect persons in an image using the loaded model.

    Returns:
        List of bounding boxes (x1, y1, x2, y2) for detected persons
    """
    if detection_net is None:
        print("Warning: Detection model not loaded")
        return []

    h, w = image.shape[:2]

    blob = cv2.dnn.blobFromImage(image, size=INPUT_SIZE, swapRB=True, crop=False)
    detection_net.setInput(blob)
    detections = detection_net.forward()

    person_boxes = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence < CONFIDENCE_THRESHOLD:
            continue

        class_id = int(detections[0, 0, i, 1])
        if not is_person(class_id):
            continue

        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        (x1, y1, x2, y2) = box.astype(int)
        person_boxes.append((x1, y1, x2, y2))

    return person_boxes


def get_table_occupations(img: Optional[np.ndarray], t_id_rect_map: Optional[Dict]) -> Optional[List[Tuple[int, bool]]]:
    """
    Takes an image and a dict of table ID -> rectangle mappings.
    Rectangles are defined by their four vertices.

    Args:
        img: Image as numpy array (BGR format)
        t_id_rect_map: Dictionary mapping desk_id to list of 4 vertices [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]

    Returns:
        List of tuples (desk_id, is_occupied) or None if error
    """
    if img is None:
        print("Warning: No image provided to get_table_occupations")
        return None

    if t_id_rect_map is None or len(t_id_rect_map) == 0:
        print("Warning: No table rectangles provided to get_table_occupations")
        return []

    # Detect all persons in the image
    person_boxes = detect_persons_in_image(img)

    # Check each table for occupancy
    tid_occ_list = []
    for desk_id, vertices in t_id_rect_map.items():
        is_occupied = False

        # Check if any detected person intersects with this table's polygon
        for person_box in person_boxes:
            if box_intersects_polygon(person_box, vertices):
                is_occupied = True
                break

        tid_occ_list.append((desk_id, is_occupied))

    return tid_occ_list
# Gets an image from the desired camera.

# Set this to False when deploying to production
TEST_MODE = True


def get_image_from_file(camera_id: int, filename: str) -> Optional[np.ndarray]:

    try:
        filepath = Path(filename)
        if not filepath.exists():
            print(f"Warning: Test image file not found for camera {camera_id}: {filename}")
            return None
            
        image = cv2.imread(str(filepath))
        if image is None:
            print(f"Error: Failed to load image for camera {camera_id}: {filename}")
            return None
            
        return image
        
    except Exception as e:
        print(f"Error loading test image for camera {camera_id}: {e}")
        return None


def get_image_from_stream(camera_id: int, stream_url: str) -> Optional[np.ndarray]:
    """
    Capture a frame from a camera stream (RTSP, HTTP, etc.).
    
    Args:
        camera_id: Camera identifier
        stream_url: URL of the camera stream (e.g., rtsp://camera_ip/stream)
        
    Returns:
        Image as numpy array (BGR format) or None if failed
    """
    cap = None
    try:
        # Open video stream
        cap = cv2.VideoCapture(stream_url)
        
        if not cap.isOpened():
            print(f"Error: Cannot open stream for camera {camera_id}: {stream_url}")
            return None
        
        # Set timeout and buffer properties for real-time streaming
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer to get latest frame
        
        # Read frame
        ret, frame = cap.read()
        
        if not ret or frame is None:
            print(f"Error: Failed to read frame from camera {camera_id}")
            return None
        
        return frame
        
    except Exception as e:
        print(f"Error capturing frame from camera {camera_id}: {e}")
        return None
        
    finally:
        if cap is not None:
            cap.release()


def get_stream_url_from_db(camera_id: int) -> Optional[str]:
    """
    Query the database to get the stream URL for a camera.
    
    Args:
        camera_id: Camera identifier
        
    Returns:
        Stream URL string or None if not found
    """
    try:
        from db_interface import OccupancyDatabase
        
        db = OccupancyDatabase(
            host="localhost",
            database="occupancy_db",
            user="root",
            password="yazool921"  # Update with actual password
        )
        
        try:
            with db.conn.cursor() as cur:
                cur.execute(
                    "SELECT stream_url FROM Camera WHERE camera_id = %s AND is_active = TRUE",
                    (camera_id,)
                )
                result = cur.fetchone()
                
                if result is None:
                    print(f"Warning: No active camera found with ID {camera_id}")
                    return None
                    
                stream_url = result[0]
                if not stream_url:
                    print(f"Warning: Camera {camera_id} has no stream URL configured")
                    return None
                    
                return stream_url
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error retrieving stream URL for camera {camera_id}: {e}")
        return None


def get_image(camera_id):
    """
    Get an image from the specified camera.
    In TEST_MODE, loads from file. In production, captures from stream.
    
    Args:
        camera_id: Camera identifier
        
    Returns:
        Image as numpy array (BGR format) or None if failed
    """
    if TEST_MODE:
        return get_image_from_file(camera_id, f"test_camera_{camera_id}.jpg")
    else:
        stream_url = get_stream_url_from_db(camera_id)
        if stream_url is None:
            return None
        return get_image_from_stream(camera_id, stream_url)

# SQL script that queries the database for vertices and returns the list of vertices.
def get_trect_map(camera_id):
    """
    Get table ID to rectangle mapping for a given camera.

    Args:
        camera_id: Camera identifier

    Returns:
        Dictionary mapping desk_id to list of 4 vertices [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
        Returns None if error occurs
    """
    try:
        from db_interface import OccupancyDatabase

        db = OccupancyDatabase(
            host="localhost",
            database="occupancy_db",
            user="root",
            password="yazool921"  # Update with actual password
        )

        try:
            tables = db.get_desks_for_camera(camera_id)

            if not tables:
                print(f"Warning: No tables found for camera {camera_id}")
                return {}

            # Build desk_id -> rectangle mapping
            tid_rect_map = {}
            for table in tables:
                desk_id = table['desk_id']

                # Extract the 4 vertices in order: bottom-left, bottom-right, top-right, top-left
                vertices = [
                    (table['bottom_left_x'], table['bottom_left_y']),
                    (table['bottom_right_x'], table['bottom_right_y']),
                    (table['top_right_x'], table['top_right_y']),
                    (table['top_left_x'], table['top_left_y'])
                ]

                tid_rect_map[desk_id] = vertices

            return tid_rect_map

        finally:
            db.close()

    except Exception as e:
        print(f"Error retrieving table rectangles for camera {camera_id}: {e}")
        return None

# Cache to track previous state of each table to avoid redundant logging
# Format: {desk_id: is_occupied}
previous_desk_states = {}


def get_last_desk_states():
    """
    Initialize the previous states cache by querying the most recent log for each table.
    Called once at startup.
    """
    global previous_desk_states

    try:
        from db_interface import OccupancyDatabase

        db = OccupancyDatabase(
            host="localhost",
            database="occupancy_db",
            user="root",
            password="yazool921"  # Update with actual password
        )

        try:
            cur = db.conn.cursor(dictionary=True)
            try:
                # Get the most recent log for each table
                cur.execute("""
                    SELECT t1.desk_id, t1.is_occupied
                    FROM Table_Occupancy_Logs t1
                    INNER JOIN (
                        SELECT desk_id, MAX(timestamp) as max_timestamp
                        FROM Table_Occupancy_Logs
                        GROUP BY desk_id
                    ) t2 ON t1.desk_id = t2.desk_id AND t1.timestamp = t2.max_timestamp
                """)

                results = cur.fetchall()

                for row in results:
                    previous_desk_states[row['desk_id']] = row['is_occupied']

                print(f"Initialized previous states for {len(previous_desk_states)} tables")

            finally:
                cur.close()
        finally:
            db.close()

    except Exception as e:
        print(f"Error initializing previous table states: {e}")


# update table samples, and potentially update sql database if a change in the system is detected.
def update_desk_samples(tid_occ_list):
    """
    Update the database with table occupancy samples.
    Only logs when the occupancy state changes from the previous state.

    Args:
        tid_occ_list: List of tuples (desk_id, is_occupied)
    """
    global previous_desk_states

    if tid_occ_list is None:
        print("Warning: No occupancy data to update")
        return

    try:
        from db_interface import OccupancyDatabase

        db = OccupancyDatabase(
            host="localhost",
            database="occupancy_db",
            user="root",
            password="yazool921"  # Update with actual password
        )

        try:
            changes_logged = 0

            # Add logs only for tables where the state changed
            for desk_id, is_occupied in tid_occ_list:
                # Check if this is a new table or if the state changed
                previous_state = previous_desk_states.get(desk_id)

                if previous_state is None or previous_state != is_occupied:
                    # State changed or new table - log it
                    try:
                        db.add_log(desk_id, is_occupied)
                        previous_desk_states[desk_id] = is_occupied
                        changes_logged += 1
                        print(f"Table {desk_id} changed: {previous_state} -> {is_occupied}")
                    except Exception as e:
                        print(f"Error adding log for table {desk_id}: {e}")

            if changes_logged > 0:
                print(f"Logged {changes_logged} state changes out of {len(tid_occ_list)} tables")
            # No message if no changes to avoid spam

        finally:
            db.close()

    except Exception as e:
        print(f"Error updating table samples: {e}")

# get camera ids.
def get_camera_ids():
    """
    Get all active camera IDs from the database.

    Returns:
        List of camera IDs, or empty list if none found or error occurs
    """
    try:
        from db_interface import OccupancyDatabase

        db = OccupancyDatabase(
            host="localhost",
            database="occupancy_db",
            user="root",
            password="yazool921"  # Update with actual password
        )

        try:
            with db.conn.cursor() as cur:
                cur.execute(
                    "SELECT camera_id FROM Camera WHERE is_active = TRUE ORDER BY camera_id"
                )
                results = cur.fetchall()

                # Extract camera_ids from tuples
                camera_ids = [row[0] for row in results]

                if not camera_ids:
                    print("Warning: No active cameras found in database")

                return camera_ids

        finally:
            db.close()

    except Exception as e:
        print(f"Error retrieving camera IDs: {e}")
        return []


def process_camera(camera):
    image = get_image(camera)
    deskid_rect_map = get_trect_map(camera)
    tid_occ_list = get_table_occupations(image, deskid_rect_map)
    update_desk_samples(tid_occ_list)


if __name__ == "__main__":
    print("Initializing backend...")

    # Initialize previous states from database
    get_last_desk_states()

    print("Starting camera processing loop...")

    while True:
        cameras = get_camera_ids()
        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(process_camera, cameras)
        time.sleep(1)

# respond to front end get requests
# research how to receive and respond to get requests
# 1. GET request returns a list of space IDs
# 2. GET Request that receives a space ID and returns a list of table IDs along with occupations statuses