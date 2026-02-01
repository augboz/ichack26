"""Debug script to test fourdesks detection"""
import cv2
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Test 1: Check if fourdesks.jpg exists
fourdesks_path = os.path.join(SCRIPT_DIR, "fourdesks.jpg")
print(f"1. Checking fourdesks.jpg path: {fourdesks_path}")
print(f"   Exists: {os.path.exists(fourdesks_path)}")

# Test 2: Try to load the image
image = cv2.imread(fourdesks_path)
if image is None:
    print("2. ERROR: Failed to load fourdesks.jpg")
else:
    h, w = image.shape[:2]
    print(f"2. Image loaded successfully: {w}x{h}")

# Test 3: Import and test fourdesks module
print("\n3. Testing fourdesks module...")
try:
    import fourdesks
    print("   Module imported successfully")

    # Update dimensions
    fourdesks.update_dimensions(w, h)
    print(f"   Dimensions updated: {w}x{h}")
    print(f"   DESK_ROIS: {fourdesks.DESK_ROIS}")

    # Test detection
    print("\n4. Testing detection...")
    occupancy = fourdesks.check_all_desks(image, use_baseline=False)
    print(f"   Occupancy results: {occupancy}")

    # Get detailed results
    print("\n5. Detailed per-desk results:")
    for desk_id in [1, 2, 3, 4]:
        is_occupied, has_person, has_object, details = fourdesks.check_occupancy(image, desk_id, use_baseline=False)
        print(f"   Desk {desk_id}: occupied={is_occupied}, person={has_person}, object={has_object}")
        print(f"            persons={details['person_count']}, objects={details['object_count']}")

except Exception as e:
    import traceback
    print(f"   ERROR: {e}")
    traceback.print_exc()

# Test 4: Check database mapping for camera > 6
print("\n6. Testing database mapping for cameras > 6...")
try:
    from db_interface import OccupancyDatabase

    db = OccupancyDatabase(
        host="localhost",
        database="occupancy_db",
        user="root",
        password="yazool921"
    )

    # Get all cameras
    cur = db.conn.cursor(dictionary=True)
    cur.execute("SELECT camera_id FROM Camera WHERE camera_id > 6 AND is_active = TRUE")
    cameras = cur.fetchall()
    print(f"   Cameras with ID > 6: {[c['camera_id'] for c in cameras]}")

    # For each camera > 6, get desk mapping
    for cam in cameras:
        camera_id = cam['camera_id']
        cur.execute("""
            SELECT desk_id, grid_x, grid_y, name
            FROM Desks
            WHERE camera_id = %s AND is_active = TRUE
            ORDER BY grid_y, grid_x
        """, (camera_id,))
        desks = cur.fetchall()
        print(f"   Camera {camera_id} desks: {[(d['desk_id'], d['name'], d['grid_x'], d['grid_y']) for d in desks]}")

    cur.close()
    db.close()

except Exception as e:
    import traceback
    print(f"   ERROR: {e}")
    traceback.print_exc()
