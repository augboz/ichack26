"""
Setup script to add test camera and desk to database
"""
import cv2
import numpy as np
from db_interface import OccupancyDatabase

# Configuration
IMAGE_PATH = "test_camera_1.jpg"
VERTICES = [(162, 112), (283, 1144), (1046, 1169), (1078, 66)]

def main():
    # 1. Read image and get dimensions
    img = cv2.imread(IMAGE_PATH)
    if img is None:
        print(f"Error: Could not load image {IMAGE_PATH}")
        return

    height, width = img.shape[:2]
    print(f"Image dimensions: {width}x{height}")

    # 2. Visualize the polygon on the image
    img_vis = img.copy()
    pts = np.array(VERTICES, np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.polylines(img_vis, [pts], True, (0, 255, 0), 3)

    # Draw vertex numbers
    for i, (x, y) in enumerate(VERTICES):
        cv2.circle(img_vis, (x, y), 5, (0, 0, 255), -1)
        cv2.putText(img_vis, str(i), (x+10, y+10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    # Save visualization
    cv2.imwrite("test_camera_1_annotated.jpg", img_vis)
    print("Saved annotated image to test_camera_1_annotated.jpg")

    # 3. Map vertices to desk coordinates
    # Vertices: [(162, 112), (283, 1144), (1046, 1169), (1078, 66)]
    # Based on y-coordinates:
    #   (162, 112) and (1078, 66) are top (low y)
    #   (283, 1144) and (1046, 1169) are bottom (high y)
    # Based on x-coordinates:
    #   (162, 112) and (283, 1144) are left (low x)
    #   (1078, 66) and (1046, 1169) are right (high x)

    desk_coords = {
        'top_left': (162, 112),
        'top_right': (1078, 66),
        'bottom_left': (283, 1144),
        'bottom_right': (1046, 1169)
    }

    print(f"\nDesk coordinates:")
    for corner, coords in desk_coords.items():
        print(f"  {corner}: {coords}")

    # 4. Insert into database
    db = OccupancyDatabase()

    try:
        # Insert space
        cur = db.conn.cursor()
        cur.execute("""
            INSERT INTO Space (name, building, total_capacity)
            VALUES (%s, %s, %s)
        """, ('Test Library', 'Test Building', 10))
        db.conn.commit()
        space_id = cur.lastrowid
        print(f"\nCreated space with ID: {space_id}")

        # Insert camera
        cur.execute("""
            INSERT INTO Camera (space_id, name, stream_url, resolution_x, resolution_y, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (space_id, 'Test Camera 1', None, width, height, True))
        db.conn.commit()
        camera_id = cur.lastrowid
        print(f"Created camera with ID: {camera_id}")

        # Insert desk
        cur.execute("""
            INSERT INTO Desks (
                camera_id, space_id, name, capacity,
                bottom_left_x, bottom_left_y,
                bottom_right_x, bottom_right_y,
                top_right_x, top_right_y,
                top_left_x, top_left_y,
                is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            camera_id, space_id, 'Desk 1', 1,
            desk_coords['bottom_left'][0], desk_coords['bottom_left'][1],
            desk_coords['bottom_right'][0], desk_coords['bottom_right'][1],
            desk_coords['top_right'][0], desk_coords['top_right'][1],
            desk_coords['top_left'][0], desk_coords['top_left'][1],
            True
        ))
        db.conn.commit()
        desk_id = cur.lastrowid
        print(f"Created desk with ID: {desk_id}")

        cur.close()

        print("\nSetup complete!")
        print(f"  Space ID: {space_id}")
        print(f"  Camera ID: {camera_id}")
        print(f"  Desk ID: {desk_id}")
        print(f"\nYou can now run: python backend.py")

    except Exception as e:
        print(f"Error inserting data: {e}")
        db.conn.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
