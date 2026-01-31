-- Insert test data for test_camera_1.jpg

-- 1. Create a test space
INSERT INTO Space (name, building, total_capacity)
VALUES ('Test Library', 'Test Building', 10);

-- Get the space_id (will be 1 if this is the first space)
SET @space_id = LAST_INSERT_ID();

-- 2. Create a camera entry for test_camera_1.jpg
-- Assuming image dimensions - adjust if needed
INSERT INTO Camera (space_id, name, stream_url, resolution_x, resolution_y, is_active)
VALUES (@space_id, 'Test Camera 1', NULL, 1920, 1080, TRUE);

-- Get the camera_id
SET @camera_id = LAST_INSERT_ID();

-- 3. Create table entry with the provided vertices
-- Vertices provided: (162, 112), (283, 1144), (1046, 1169), (1078, 66)
-- Mapping based on y-coordinates:
--   Top-left: (162, 112) - lowest y on left
--   Bottom-left: (283, 1144) - highest y on left
--   Bottom-right: (1046, 1169) - highest y on right
--   Top-right: (1078, 66) - lowest y on right

INSERT INTO Tables (
    camera_id,
    space_id,
    name,
    capacity,
    bottom_left_x, bottom_left_y,
    bottom_right_x, bottom_right_y,
    top_right_x, top_right_y,
    top_left_x, top_left_y,
    is_active
)
VALUES (
    @camera_id,
    @space_id,
    'Table 1',
    4,
    283, 1144,    -- bottom_left
    1046, 1169,   -- bottom_right
    1078, 66,     -- top_right
    162, 112,     -- top_left
    TRUE
);

-- Verify the data was inserted
SELECT 'Inserted Space:' as Info;
SELECT * FROM Space WHERE space_id = @space_id;

SELECT 'Inserted Camera:' as Info;
SELECT * FROM Camera WHERE camera_id = @camera_id;

SELECT 'Inserted Table:' as Info;
SELECT * FROM Tables WHERE camera_id = @camera_id;
