from concurrent.futures import ThreadPoolExecutor
import time
import cv2
import numpy as np
from pathlib import Path
from typing import Optional


# Set this to False when deploying to production
TEST_MODE = True


# Takes an image file and a list of table ID -> rectangle mappings.
# rectangles are defined by their four vertices.
def get_table_occupations(img, t_id_rect_map):
    return None
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
            password=""  # Update with actual password
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
        Dictionary mapping table_id to list of 4 vertices [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
        Returns None if error occurs
    """
    try:
        from db_interface import OccupancyDatabase

        db = OccupancyDatabase(
            host="localhost",
            database="occupancy_db",
            user="root",
            password=""  # Update with actual password
        )

        try:
            tables = db.get_tables_for_camera(camera_id)

            if not tables:
                print(f"Warning: No tables found for camera {camera_id}")
                return {}

            # Build table_id -> rectangle mapping
            tid_rect_map = {}
            for table in tables:
                table_id = table['table_id']

                # Extract the 4 vertices in order: bottom-left, bottom-right, top-right, top-left
                vertices = [
                    (table['bottom_left_x'], table['bottom_left_y']),
                    (table['bottom_right_x'], table['bottom_right_y']),
                    (table['top_right_x'], table['top_right_y']),
                    (table['top_left_x'], table['top_left_y'])
                ]

                tid_rect_map[table_id] = vertices

            return tid_rect_map

        finally:
            db.close()

    except Exception as e:
        print(f"Error retrieving table rectangles for camera {camera_id}: {e}")
        return None

# update table samples, and potentially update sql database if a change in the system is detected.
def update_table_samples(tid_occ_list):
    return None

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
            password=""  # Update with actual password
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
    tableid_rect_map = get_trect_map(camera)
    tid_occ_list = get_table_occupations(image, tableid_rect_map)
    update_table_samples(tid_occ_list)

while True:
    cameras = get_camera_ids()
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_camera, cameras)
    time.sleep(1)

# respond to front end get requests
# research how to receive and respond to get requests
# 1. GET request returns a list of space IDs
# 2. GET Request that receives a space ID and returns a list of table IDs along with occupations statuses