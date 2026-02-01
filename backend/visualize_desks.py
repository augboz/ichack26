"""
Visualize desk polygons on test image to diagnose polygon issues
"""
import cv2
import numpy as np
from db_interface import OccupancyDatabase

# Load test image
img = cv2.imread('test_camera_1.jpg')
if img is None:
    print("Error: Could not load test_camera_1.jpg")
    exit(1)

# Connect to database and get desk polygons for camera 1
db = OccupancyDatabase(
    host="localhost",
    database="occupancy_db",
    user="root",
    password="yazool921"
)

try:
    desks = db.get_desks_for_camera(1)

    if not desks:
        print("No desks found for camera 1")
        exit(1)

    # Draw each desk polygon
    colors = [(0, 255, 0), (0, 0, 255), (255, 0, 0), (255, 255, 0)]

    for i, desk in enumerate(desks):
        desk_id = desk['desk_id']

        # Get vertices
        vertices = [
            (desk['bottom_left_x'], desk['bottom_left_y']),
            (desk['bottom_right_x'], desk['bottom_right_y']),
            (desk['top_right_x'], desk['top_right_y']),
            (desk['top_left_x'], desk['top_left_y'])
        ]

        color = colors[i % len(colors)]

        # Draw polygon
        pts = np.array(vertices, np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(img, [pts], True, color, 3)

        # Draw vertices with labels
        for j, (x, y) in enumerate(vertices):
            cv2.circle(img, (x, y), 8, color, -1)
            labels = ['BL', 'BR', 'TR', 'TL']
            cv2.putText(img, f"D{desk_id}-{labels[j]}", (x+15, y+15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Print coordinates
        print(f"\nDesk {desk_id}:")
        print(f"  Bottom-left:  {vertices[0]}")
        print(f"  Bottom-right: {vertices[1]}")
        print(f"  Top-right:    {vertices[2]}")
        print(f"  Top-left:     {vertices[3]}")

        # Check for inverted coordinates
        bl_x, br_x = vertices[0][0], vertices[1][0]
        if bl_x > br_x:
            print(f"  ⚠️  WARNING: Bottom-left X ({bl_x}) > Bottom-right X ({br_x}) - INVERTED!")

    # Save annotated image
    cv2.imwrite('desk_polygons_visualization.jpg', img)
    print(f"\n✓ Saved visualization to: desk_polygons_visualization.jpg")

finally:
    db.close()
