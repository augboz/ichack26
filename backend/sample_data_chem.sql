-- ============================================================================
-- Imperial Chemistry Building - Setup Script
-- ============================================================================
-- Sets up building, spaces, cameras, and desks for Imperial Chemistry
-- ============================================================================

USE occupancy_db;

-- ============================================================================
-- Insert Building
-- ============================================================================
-- Imperial Chemistry at 51° 29′ 55″ N, 0° 10′ 42.82″ W
-- Converting to decimal: 51.498611, -0.178561
INSERT INTO Building (name, map_latitude, map_longitude, address) VALUES
('Imperial Chemistry', 51.49861111, -0.17856111, 'South Kensington Campus, London SW7 2AZ');

SET @building_id = LAST_INSERT_ID();

-- ============================================================================
-- Insert Spaces
-- ============================================================================
-- Floor 4: 3x2 grid (3 columns, 2 rows) = 6 desks, 1 camera
INSERT INTO Space (building_id, name, total_capacity, grid_width, grid_height) VALUES
(@building_id, 'Floor 4', 6, 3, 2);

SET @space_floor4_id = LAST_INSERT_ID();

-- Floor 5: 2x2 per camera, 2 cameras = 4x2 grid (4 columns, 2 rows) = 8 desks
INSERT INTO Space (building_id, name, total_capacity, grid_width, grid_height) VALUES
(@building_id, 'Floor 5', 8, 4, 2);

SET @space_floor5_id = LAST_INSERT_ID();

-- Floor 6: 1x2 per camera, 3 cameras = 3x2 grid (3 columns, 2 rows) = 6 desks
INSERT INTO Space (building_id, name, total_capacity, grid_width, grid_height) VALUES
(@building_id, 'Floor 6', 6, 3, 2);

SET @space_floor6_id = LAST_INSERT_ID();

-- ============================================================================
-- Insert Cameras
-- ============================================================================
-- Floor 4: 1 camera covering 3x2 grid
INSERT INTO Camera (space_id, name, stream_url, resolution_x, resolution_y, is_active) VALUES
(@space_floor4_id, 'Floor4-Cam1', 'rtsp://camera.imperial.ac.uk/floor4/cam1', 1920, 1080, TRUE);

SET @camera_f4_c1 = LAST_INSERT_ID();

-- Floor 5: 2 cameras, each covering 2x2 grid
INSERT INTO Camera (space_id, name, stream_url, resolution_x, resolution_y, is_active) VALUES
(@space_floor5_id, 'Floor5-Cam1', 'rtsp://camera.imperial.ac.uk/floor5/cam1', 1920, 1080, TRUE),
(@space_floor5_id, 'Floor5-Cam2', 'rtsp://camera.imperial.ac.uk/floor5/cam2', 1920, 1080, TRUE);

SET @camera_f5_c1 = LAST_INSERT_ID() - 1;
SET @camera_f5_c2 = LAST_INSERT_ID();

-- Floor 6: 3 cameras, each covering 1x2 grid
INSERT INTO Camera (space_id, name, stream_url, resolution_x, resolution_y, is_active) VALUES
(@space_floor6_id, 'Floor6-Cam1', 'rtsp://camera.imperial.ac.uk/floor6/cam1', 1920, 1080, TRUE),
(@space_floor6_id, 'Floor6-Cam2', 'rtsp://camera.imperial.ac.uk/floor6/cam2', 1920, 1080, TRUE),
(@space_floor6_id, 'Floor6-Cam3', 'rtsp://camera.imperial.ac.uk/floor6/cam3', 1920, 1080, TRUE);

SET @camera_f6_c1 = LAST_INSERT_ID() - 2;
SET @camera_f6_c2 = LAST_INSERT_ID() - 1;
SET @camera_f6_c3 = LAST_INSERT_ID();

-- ============================================================================
-- Insert Desks - Floor 4 (3x2 grid, 1 camera)
-- ============================================================================
-- Camera 1 covers entire 3x2 grid
-- Pixel coordinates are example bounding boxes in 1920x1080 space

-- Row 0
INSERT INTO Desks (camera_id, space_id, name, capacity, zone, 
                   bottom_left_x, bottom_left_y, bottom_right_x, bottom_right_y,
                   top_left_x, top_left_y, top_right_x, top_right_y,
                   grid_x, grid_y) VALUES
(@camera_f4_c1, @space_floor4_id, 'F4-D1', 1, 'North Row',
 100, 700, 400, 700, 100, 500, 400, 500, 0, 0),
(@camera_f4_c1, @space_floor4_id, 'F4-D2', 1, 'North Row',
 450, 700, 750, 700, 450, 500, 750, 500, 1, 0),
(@camera_f4_c1, @space_floor4_id, 'F4-D3', 1, 'North Row',
 800, 700, 1100, 700, 800, 500, 1100, 500, 2, 0);

-- Row 1
INSERT INTO Desks (camera_id, space_id, name, capacity, zone,
                   bottom_left_x, bottom_left_y, bottom_right_x, bottom_right_y,
                   top_left_x, top_left_y, top_right_x, top_right_y,
                   grid_x, grid_y) VALUES
(@camera_f4_c1, @space_floor4_id, 'F4-D4', 1, 'South Row',
 100, 1000, 400, 1000, 100, 800, 400, 800, 0, 1),
(@camera_f4_c1, @space_floor4_id, 'F4-D5', 1, 'South Row',
 450, 1000, 750, 1000, 450, 800, 750, 800, 1, 1),
(@camera_f4_c1, @space_floor4_id, 'F4-D6', 1, 'South Row',
 800, 1000, 1100, 1000, 800, 800, 1100, 800, 2, 1);

-- ============================================================================
-- Insert Desks - Floor 5 (4x2 grid, 2 cameras each covering 2x2)
-- ============================================================================
-- Camera 1 covers columns 0-1, Camera 2 covers columns 2-3

-- Camera 1 - Row 0
INSERT INTO Desks (camera_id, space_id, name, capacity, zone,
                   bottom_left_x, bottom_left_y, bottom_right_x, bottom_right_y,
                   top_left_x, top_left_y, top_right_x, top_right_y,
                   grid_x, grid_y) VALUES
(@camera_f5_c1, @space_floor5_id, 'F5-D1', 1, 'West Wing',
 100, 700, 500, 700, 100, 400, 500, 400, 0, 0),
(@camera_f5_c1, @space_floor5_id, 'F5-D2', 1, 'West Wing',
 600, 700, 1000, 700, 600, 400, 1000, 400, 1, 0);

-- Camera 1 - Row 1
INSERT INTO Desks (camera_id, space_id, name, capacity, zone,
                   bottom_left_x, bottom_left_y, bottom_right_x, bottom_right_y,
                   top_left_x, top_left_y, top_right_x, top_right_y,
                   grid_x, grid_y) VALUES
(@camera_f5_c1, @space_floor5_id, 'F5-D3', 1, 'West Wing',
 100, 1000, 500, 1000, 100, 800, 500, 800, 0, 1),
(@camera_f5_c1, @space_floor5_id, 'F5-D4', 1, 'West Wing',
 600, 1000, 1000, 1000, 600, 800, 1000, 800, 1, 1);

-- Camera 2 - Row 0
INSERT INTO Desks (camera_id, space_id, name, capacity, zone,
                   bottom_left_x, bottom_left_y, bottom_right_x, bottom_right_y,
                   top_left_x, top_left_y, top_right_x, top_right_y,
                   grid_x, grid_y) VALUES
(@camera_f5_c2, @space_floor5_id, 'F5-D5', 1, 'East Wing',
 100, 700, 500, 700, 100, 400, 500, 400, 2, 0),
(@camera_f5_c2, @space_floor5_id, 'F5-D6', 1, 'East Wing',
 600, 700, 1000, 700, 600, 400, 1000, 400, 3, 0);

-- Camera 2 - Row 1
INSERT INTO Desks (camera_id, space_id, name, capacity, zone,
                   bottom_left_x, bottom_left_y, bottom_right_x, bottom_right_y,
                   top_left_x, top_left_y, top_right_x, top_right_y,
                   grid_x, grid_y) VALUES
(@camera_f5_c2, @space_floor5_id, 'F5-D7', 1, 'East Wing',
 100, 1000, 500, 1000, 100, 800, 500, 800, 2, 1),
(@camera_f5_c2, @space_floor5_id, 'F5-D8', 1, 'East Wing',
 600, 1000, 1000, 1000, 600, 800, 1000, 800, 3, 1);

-- ============================================================================
-- Insert Desks - Floor 6 (3x2 grid, 3 cameras each covering 1x2)
-- ============================================================================
-- Camera 1 covers column 0, Camera 2 covers column 1, Camera 3 covers column 2

-- Camera 1 - Column 0
INSERT INTO Desks (camera_id, space_id, name, capacity, zone,
                   bottom_left_x, bottom_left_y, bottom_right_x, bottom_right_y,
                   top_left_x, top_left_y, top_right_x, top_right_y,
                   grid_x, grid_y) VALUES
(@camera_f6_c1, @space_floor6_id, 'F6-D1', 1, 'Quiet Zone',
 200, 700, 700, 700, 200, 400, 700, 400, 0, 0),
(@camera_f6_c1, @space_floor6_id, 'F6-D2', 1, 'Quiet Zone',
 200, 1000, 700, 1000, 200, 800, 700, 800, 0, 1);

-- Camera 2 - Column 1
INSERT INTO Desks (camera_id, space_id, name, capacity, zone,
                   bottom_left_x, bottom_left_y, bottom_right_x, bottom_right_y,
                   top_left_x, top_left_y, top_right_x, top_right_y,
                   grid_x, grid_y) VALUES
(@camera_f6_c2, @space_floor6_id, 'F6-D3', 1, 'Main Area',
 200, 700, 700, 700, 200, 400, 700, 400, 1, 0),
(@camera_f6_c2, @space_floor6_id, 'F6-D4', 1, 'Main Area',
 200, 1000, 700, 1000, 200, 800, 700, 800, 1, 1);

-- Camera 3 - Column 2
INSERT INTO Desks (camera_id, space_id, name, capacity, zone,
                   bottom_left_x, bottom_left_y, bottom_right_x, bottom_right_y,
                   top_left_x, top_left_y, top_right_x, top_right_y,
                   grid_x, grid_y) VALUES
(@camera_f6_c3, @space_floor6_id, 'F6-D5', 1, 'Window Seats',
 200, 700, 700, 700, 200, 400, 700, 400, 2, 0),
(@camera_f6_c3, @space_floor6_id, 'F6-D6', 1, 'Window Seats',
 200, 1000, 700, 1000, 200, 800, 700, 800, 2, 1);

-- ============================================================================
-- Verification Queries
-- ============================================================================
-- Uncomment to verify the setup:

-- SELECT * FROM Building WHERE name = 'Imperial Chemistry';
-- SELECT * FROM Space WHERE building_id = @building_id;
-- SELECT * FROM Camera WHERE space_id IN (@space_floor4_id, @space_floor5_id, @space_floor6_id);
-- SELECT space_id, COUNT(*) as desk_count FROM Desks 
--   WHERE space_id IN (@space_floor4_id, @space_floor5_id, @space_floor6_id) 
--   GROUP BY space_id;