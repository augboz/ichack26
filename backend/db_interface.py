"""
Simple database interface for Study Space Occupancy Tracking System
"""

import mysql.connector
from typing import List, Dict, Optional


class OccupancyDatabase:
    """Simple database interface for occupancy tracking."""

    def __init__(self, host="localhost", database="occupancy_db",
                 user="root", password="yazool921"):
        """Initialize database connection."""
        self.conn = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    # ========================================================================
    # BASIC OPERATIONS
    # ========================================================================
    
    def get_all_spaces(self) -> List[Dict]:
        """Get all spaces."""
        cur = self.conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM Space ORDER BY space_id")
            return cur.fetchall()
        finally:
            cur.close()

    def get_cameras_for_space(self, space_id: int) -> List[Dict]:
        """Get all cameras for a space."""
        cur = self.conn.cursor(dictionary=True)
        try:
            cur.execute(
                "SELECT * FROM Camera WHERE space_id = %s ORDER BY camera_id",
                (space_id,)
            )
            return cur.fetchall()
        finally:
            cur.close()

    def get_desks_for_camera(self, camera_id: int) -> List[Dict]:
        """Get all desks for a camera."""
        cur = self.conn.cursor(dictionary=True)
        try:
            cur.execute(
                'SELECT * FROM Desks WHERE camera_id = %s ORDER BY desk_id',
                (camera_id,)
            )
            return cur.fetchall()
        finally:
            cur.close()
    
    def add_desk(self, camera_id: int, space_id: int, name: str,
                 bottom_left_x: int, bottom_left_y: int,
                 bottom_right_x: int, bottom_right_y: int,
                 top_left_x: int, top_left_y: int,
                 top_right_x: int, top_right_y: int,
                 grid_x: int, grid_y: int,
                 capacity: int = 1, zone: str = None) -> int:
        """Add a new desk. Returns the new desk_id."""
        cur = self.conn.cursor()
        try:
            cur.execute("""
                INSERT INTO Desks (
                    camera_id, space_id, name, capacity, zone,
                    bottom_left_x, bottom_left_y,
                    bottom_right_x, bottom_right_y,
                    top_left_x, top_left_y,
                    top_right_x, top_right_y,
                    grid_x, grid_y
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (camera_id, space_id, name, capacity, zone,
                  bottom_left_x, bottom_left_y,
                  bottom_right_x, bottom_right_y,
                  top_left_x, top_left_y,
                  top_right_x, top_right_y,
                  grid_x, grid_y))
            self.conn.commit()
            return cur.lastrowid
        finally:
            cur.close()

    def add_log(self, desk_id: int, is_occupied: bool) -> int:
        """Add occupancy log. Returns the new log_id."""
        cur = self.conn.cursor()
        try:
            cur.execute("""
                INSERT INTO Desk_Occupancy_Logs (desk_id, is_occupied)
                VALUES (%s, %s)
            """, (desk_id, is_occupied))
            self.conn.commit()
            return cur.lastrowid
        finally:
            cur.close()


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Connect
    db = OccupancyDatabase(
        host="localhost",
        database="occupancy_db",
        user="root",
        password="your_password"
    )

    # Use it
    spaces = db.get_all_spaces()
    cameras = db.get_cameras_for_space(space_id=1)
    desks = db.get_desks_for_camera(camera_id=1)

    # Add a log
    db.add_log(desk_id=1, is_occupied=True)

    # Close when done
    db.close()