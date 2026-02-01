"""
Occupancy Detection Backend using YOLOv11

INSTALLATION:
    pip install ultralytics opencv-python numpy

FIRST RUN:
    The YOLOv11 model will be automatically downloaded on first run.
    Requires internet connection for initial download (~6MB for yolo11n.pt).

MODEL OPTIONS:
    - yolo11n.pt (fastest, recommended for real-time)
    - yolo11s.pt (small)
    - yolo11m.pt (medium)
    - yolo11l.pt (large)
    - yolo11x.pt (most accurate, slowest)
"""

from concurrent.futures import ThreadPoolExecutor
import time
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import os
import fourdesks


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
    CONFIG = os.path.join(SCRIPT_DIR, "faster_rcnn_inception_v2_coco_2018_03_29.pbtxt")
    WEIGHTS = os.path.join(SCRIPT_DIR, "faster_rcnn_inception_v2_coco_2018_03_29.pb")
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


def is_occupancy_indicator(class_id):
    """
    Check if class_id represents an occupancy indicator.

    COCO dataset classes:
    - 0: person
    - 63: laptop
    - 67: cell phone (includes tablets/iPads)
    """
    return class_id in [0, 63, 67]


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
                        # Horizontal line case
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
        if not is_occupancy_indicator(class_id):
            continue

        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])

        # Check for invalid values (NaN or infinity) before casting
        if not np.all(np.isfinite(box)):
            continue

        (x1, y1, x2, y2) = box.astype(int)

        # Validate box coordinates are within image bounds
        if x1 < 0 or y1 < 0 or x2 > w or y2 > h:
            continue
        if x2 <= x1 or y2 <= y1:
            continue

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

    # Calculate midpoint for each detected person
    person_midpoints = []
    for x1, y1, x2, y2 in person_boxes:
        # Validate bounding box coordinates
        if x2 <= x1 or y2 <= y1:
            continue  # Skip invalid boxes

        # Calculate midpoint safely (using integer division)
        midpoint_x = (x1 + x2) // 2
        midpoint_y = (y1 + y2) // 2

        # Ensure midpoint is within image bounds
        if midpoint_x < 0 or midpoint_y < 0:
            continue

        person_midpoints.append((midpoint_x, midpoint_y))

    # Check each desk for occupancy
    tid_occ_list = []
    for desk_id, vertices in t_id_rect_map.items():
        is_occupied = False

        # Check if any person's midpoint falls within this desk's polygon
        for midpoint in person_midpoints:
            if point_in_polygon(midpoint, vertices):
                is_occupied = True
                break

        tid_occ_list.append((desk_id, is_occupied))

    return tid_occ_list


# Gets an image from the desired camera.
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

# ============================================================================
# BUFFERING SYSTEM FOR TEMPORAL SMOOTHING
# ============================================================================

# Configuration
SAMPLES_PER_WINDOW = 2      # Number of samples to collect before making a decision
OCCUPANCY_THRESHOLD = 0.5    # If >= 50% of samples are occupied, classify as occupied

# Sample buffer: {desk_id: [list of boolean samples]}
desk_sample_buffer = {}

# Timestamp when current buffering window started
buffer_window_start = None

# Cache of last committed states to detect changes
# Format: {desk_id: is_occupied}
last_committed_states = {}


def get_last_desk_states():
    """
    Initialize the last committed states cache by querying the most recent log for each desk.
    Called once at startup.
    """
    global last_committed_states
    try:
        from db_interface import OccupancyDatabase

        print("  Connecting to database...", flush=True)
        db = OccupancyDatabase(
            host="localhost",
            database="occupancy_db",
            user="root",
            password="yazool921"  # Update with actual password
        )
        print("  Database connection established", flush=True)

        try:
            cur = db.conn.cursor(dictionary=True)
            try:
                print("  Querying last desk states...", flush=True)
                # Get the most recent log for each desk
                cur.execute("""
                    SELECT t1.desk_id, t1.is_occupied
                    FROM Desk_Occupancy_Logs t1
                    INNER JOIN (
                        SELECT desk_id, MAX(timestamp) as max_timestamp
                        FROM Desk_Occupancy_Logs
                        GROUP BY desk_id
                    ) t2 ON t1.desk_id = t2.desk_id AND t1.timestamp = t2.max_timestamp
                """)

                results = cur.fetchall()

                for row in results:
                    last_committed_states[row['desk_id']] = row['is_occupied']

                if len(last_committed_states) == 0:
                    print("  No previous desk states found (first run or empty logs)")
                else:
                    print(f"  Loaded state for {len(last_committed_states)} desks")

            finally:
                cur.close()
        finally:
            db.close()

    except Exception as e:
        print(f"  ERROR initializing last committed states: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise  # Re-raise to stop execution if DB is not available


def add_sample_to_buffer(tid_occ_list):
    """
    Add detection samples to the buffer for temporal smoothing.
    Does NOT write to database - just buffers the samples.

    Args:
        tid_occ_list: List of tuples (desk_id, is_occupied)
    """
    global desk_sample_buffer

    if tid_occ_list is None:
        return

    for desk_id, is_occupied in tid_occ_list:
        if desk_id not in desk_sample_buffer:
            desk_sample_buffer[desk_id] = []

        desk_sample_buffer[desk_id].append(is_occupied)


def flush_buffer_to_database():
    """
    Process the buffered samples and write all results to database.
    Clears the buffer after processing.
    """
    global desk_sample_buffer

    if not desk_sample_buffer:
        return

    try:
        from db_interface import OccupancyDatabase

        db = OccupancyDatabase(
            host="localhost",
            database="occupancy_db",
            user="root",
            password="yazool921"
        )

        try:
            for desk_id, samples in desk_sample_buffer.items():
                if not samples:
                    continue

                # Calculate occupancy based on threshold
                occupied_count = sum(1 for s in samples if s)
                total_count = len(samples)
                occupancy_ratio = occupied_count / total_count
                is_occupied = occupancy_ratio >= OCCUPANCY_THRESHOLD

                # Always write to database
                try:
                    db.add_log(desk_id, is_occupied)
                    state_str = "OCCUPIED" if is_occupied else "EMPTY"
                    print(f"Desk {desk_id}: {state_str} ({occupied_count}/{total_count})", flush=True)
                except Exception as e:
                    print(f"Error logging desk {desk_id}: {e}")

        finally:
            db.close()

    except Exception as e:
        print(f"Error flushing buffer to database: {e}")

    finally:
        desk_sample_buffer.clear()

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


def get_fourdesks_desk_mapping(camera_id):
    """
    Get mapping from fourdesks local desk IDs (1-4) to actual database desk IDs.

    fourdesks uses quadrant-based detection:
      - Desk 1: top-left (grid 0,0)
      - Desk 2: top-right (grid 1,0)
      - Desk 3: bottom-left (grid 0,1)
      - Desk 4: bottom-right (grid 1,1)

    Returns:
        Dict mapping fourdesks local ID -> database desk_id
    """
    try:
        from db_interface import OccupancyDatabase

        db = OccupancyDatabase(
            host="localhost",
            database="occupancy_db",
            user="root",
            password="yazool921"
        )

        try:
            cur = db.conn.cursor(dictionary=True)
            try:
                cur.execute("""
                    SELECT desk_id, grid_x, grid_y
                    FROM Desks
                    WHERE camera_id = %s AND is_active = TRUE
                    ORDER BY grid_y, grid_x
                """, (camera_id,))

                results = cur.fetchall()

                # Map grid position to fourdesks local ID
                # (0,0)->1, (1,0)->2, (0,1)->3, (1,1)->4
                grid_to_local = {
                    (0, 0): 1,
                    (1, 0): 2,
                    (0, 1): 3,
                    (1, 1): 4
                }

                local_to_desk_id = {}
                for row in results:
                    grid_pos = (row['grid_x'], row['grid_y'])
                    if grid_pos in grid_to_local:
                        local_id = grid_to_local[grid_pos]
                        local_to_desk_id[local_id] = row['desk_id']

                return local_to_desk_id

            finally:
                cur.close()
        finally:
            db.close()

    except Exception as e:
        print(f"Error getting fourdesks desk mapping for camera {camera_id}: {e}")
        return {}


def process_camera(camera):
    """Process a single camera: detect persons and buffer the results."""

    if camera > 6:
        # Use fourdesks.py with fourdesks.jpg for cameras with ID > 6
        try:
            INPUT = os.path.join(SCRIPT_DIR, "fourdesks.jpg")
            image = cv2.imread(INPUT)
            if image is None:
                print(f"Error: Could not read {INPUT}")
                return

            IMAGE_SCALE = 0.4
            h, w = image.shape[:2]
            new_w, new_h = int(w * IMAGE_SCALE), int(h * IMAGE_SCALE)
            image = cv2.resize(image, (new_w, new_h))

            h, w = image.shape[:2]
            fourdesks.update_dimensions(w, h)

            BASELINE_PATH = os.path.join(SCRIPT_DIR, "images_4grid/tables_reference.jpg")
            baseline_imgs = None
            if os.path.exists(BASELINE_PATH):
                baseline_img = cv2.imread(BASELINE_PATH)
                if baseline_img is not None:
                    baseline_imgs = [baseline_img]
                    fourdesks.set_baseline(baseline_imgs)

            occupancy = fourdesks.check_all_desks(image, use_baseline=baseline_imgs is not None)

            # Print desk occupancy status
            occupied = [d for d, occ in occupancy.items() if occ]
            empty = [d for d, occ in occupancy.items() if not occ]
            print(f"Occupied: {occupied}  Empty: {empty}", flush=True)

            local_to_desk_id = get_fourdesks_desk_mapping(camera)
            print(f"Desk mapping for camera {camera}: {local_to_desk_id}", flush=True)

            if local_to_desk_id:
                tid_occ_list = []
                for local_id, is_occupied in occupancy.items():
                    if local_id in local_to_desk_id:
                        actual_desk_id = local_to_desk_id[local_id]
                        tid_occ_list.append((actual_desk_id, is_occupied))
                print(f"Buffering: {tid_occ_list}", flush=True)
                add_sample_to_buffer(tid_occ_list)
            else:
                print(f"WARNING: No desk mapping found for camera {camera}!", flush=True)

        except Exception as e:
            print(f"Error processing fourdesks camera {camera}: {e}")
            import traceback
            traceback.print_exc()
    else:
        # Use standard polygon-based detection for cameras with ID <= 6
        image = get_image(camera)
        deskid_rect_map = get_trect_map(camera)
        tid_occ_list = get_table_occupations(image, deskid_rect_map)
        add_sample_to_buffer(tid_occ_list)


if __name__ == "__main__":
    try:
        print("\n" + "="*60, flush=True)
        print("OCCUPANCY DETECTION BACKEND", flush=True)
        print("="*60, flush=True)

        # Check if detection model loaded
        if detection_net is None:
            print("\nWARNING: Detection model not loaded!", flush=True)
            print("Make sure model files exist in backend directory", flush=True)
            print(f"  CONFIG: {CONFIG}", flush=True)
            print(f"  WEIGHTS: {WEIGHTS}", flush=True)
            exit(1)

        print("Detection model loaded successfully\n", flush=True)

        # Initialize last committed states from database
        print("Initializing database connection...", flush=True)
        get_last_desk_states()
        print("Database initialized successfully", flush=True)

        # Initialize buffer window start time
        buffer_window_start = time.time()

        print(f"\nCONFIGURATION:", flush=True)
        print(f"  Detection model: SSD MobileNet v2")
        print(f"  Samples per window: {SAMPLES_PER_WINDOW}")
        print(f"  Sampling rate: 1Hz (1 sample/sec)")
        print(f"  Flush interval: ~{SAMPLES_PER_WINDOW}s")
        print(f"  Occupancy threshold: {OCCUPANCY_THRESHOLD * 100}%")
        print(f"  Confidence threshold: {CONFIDENCE_THRESHOLD * 100}%")
        print("\nSTARTING DETECTION LOOP...\n", flush=True)

        sample_count = 0

        while True:
            try:
                # Process all cameras and buffer samples
                cameras = get_camera_ids()
                if not cameras:
                    print("Warning: No cameras found, waiting...", flush=True)
                    time.sleep(5.0)
                    continue

                # Separate regular cameras from fourdesks cameras
                # fourdesks has global state - must process sequentially
                regular_cameras = [c for c in cameras if c <= 6]
                fourdesks_cameras = [c for c in cameras if c > 6]

                # Process regular cameras in parallel (thread-safe SSD model)
                if regular_cameras:
                    with ThreadPoolExecutor(max_workers=5) as executor:
                        executor.map(process_camera, regular_cameras)

                # Process fourdesks cameras sequentially (global state not thread-safe)
                for camera in fourdesks_cameras:
                    process_camera(camera)

                sample_count += 1

                # Check if it's time to flush the buffer (based on sample count)
                if sample_count >= SAMPLES_PER_WINDOW:
                    elapsed = time.time() - buffer_window_start

                    # Flush buffer to database
                    flush_buffer_to_database()

                    print(f"[{time.strftime('%H:%M:%S')}] Flushed after {elapsed:.1f}s")

                    # Reset window
                    buffer_window_start = time.time()
                    sample_count = 0

                time.sleep(1.0)  # 1 sample per second

            except KeyboardInterrupt:
                print("\n\nShutting down gracefully...", flush=True)
                break
            except Exception as e:
                print(f"\nError in main loop: {e}", flush=True)
                import traceback
                traceback.print_exc()
                print("Continuing after error...\n", flush=True)
                time.sleep(1.0)

    except KeyboardInterrupt:
        print("\n\nShutdown requested by user", flush=True)
    except Exception as e:
        print(f"\n\nFATAL ERROR during initialization: {e}", flush=True)
        import traceback
        traceback.print_exc()
        print("\nProgram exiting due to fatal error", flush=True)
        exit(1)

# respond to front end get requests
# research how to receive and respond to get requests
# 1. GET request returns a list of space IDs
# 2. GET Request that receives a space ID and returns a list of table IDs along with occupations statuses