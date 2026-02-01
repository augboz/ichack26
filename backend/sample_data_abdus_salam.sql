-- ============================================================================
-- Sample Data: Abdus Salam Library
-- ============================================================================
-- 5 floors, each with 1 camera and 4 desks in a 2x2 grid
-- Coordinates: 51°29′54″N 0°10′42″W
-- ============================================================================

USE occupancy_db;

-- 1. Create Building
INSERT INTO Building (name, map_latitude, map_longitude, address)
VALUES (
    'Abdus Salam Library',
    51.498333,  -- 51°29′54″N
    -0.178333,  -- 0°10′42″W
    'Imperial College London, South Kensington Campus, London SW7 2AZ'
);

SET @building_id = LAST_INSERT_ID();

-- ============================================================================
-- FLOOR 1
-- ============================================================================

INSERT INTO Space (name, building_id, total_capacity, grid_width, grid_height)
VALUES ('Floor 1', @building_id, 4, 2, 2);
SET @space_id_1 = LAST_INSERT_ID();

INSERT INTO Camera (space_id, name, stream_url, resolution_x, resolution_y, is_active)
VALUES (@space_id_1, 'Floor 1 Camera', NULL, 1920, 1080, TRUE);
SET @camera_id_1 = LAST_INSERT_ID();

-- Desk 1 (Top-Left: grid 0,0)
INSERT INTO Desks (
    camera_id, space_id, name, capacity, zone,
    bottom_left_x, bottom_left_y, bottom_right_x, bottom_right_y,
    top_left_x, top_left_y, top_right_x, top_right_y,
    grid_x, grid_y, is_active
) VALUES (
    @camera_id_1, @space_id_1, 'F1-D1', 1, 'Floor 1 Study Area',
    1, 670, 500, 670, 20, 1062, 500, 1062,
    0, 0, TRUE
);

-- Desk 2 (Top-Right: grid 1,0)
INSERT INTO Desks (
    camera_id, space_id, name, capacity, zone,
    bottom_left_x, bottom_left_y, bottom_right_x, bottom_right_y,
    top_left_x, top_left_y, top_right_x, top_right_y,
    grid_x, grid_y, is_active
) VALUES (
    @camera_id_1, @space_id_1, 'F1-D2', 1, 'Floor 1 Study Area',
    10, 600, 500, 600, 10, 10, 500, 10,
    1, 0, TRUE
);

-- Desk 3 (Bottom-Left: grid 0,1)
INSERT INTO Desks (
    camera_id, space_id, name, capacity, zone,
    bottom_left_x, bottom_left_y, bottom_right_x, bottom_right_y,
    top_left_x, top_left_y, top_right_x, top_right_y,
    grid_x, grid_y, is_active
) VALUES (
    @camera_id_1, @space_id_1, 'F1-D3', 1, 'Floor 1 Study Area',
    550, 248, 900, 253, 900, 610, 550, 610,
    0, 1, TRUE
);

-- Desk 4 (Bottom-Right: grid 1,1)
INSERT INTO Desks (
    camera_id, space_id, name, capacity, zone,
    bottom_left_x, bottom_left_y, bottom_right_x, bottom_right_y,
    top_left_x, top_left_y, top_right_x, top_right_y,
    grid_x, grid_y, is_active
) VALUES (
    @camera_id_1, @space_id_1, 'F1-D4', 1, 'Floor 1 Study Area',
    560, 680, 550, 1070, 900, 1100, 900, 700,
    1, 1, TRUE
);

-- ============================================================================
-- FLOOR 2
-- ============================================================================

INSERT INTO Space (name, building_id, total_capacity, grid_width, grid_height)
VALUES ('Floor 2', @building_id, 4, 2, 2);
SET @space_id_2 = LAST_INSERT_ID();

INSERT INTO Camera (space_id, name, stream_url, resolution_x, resolution_y, is_active)
VALUES (@space_id_2, 'Floor 2 Camera', NULL, 1920, 1080, TRUE);
SET @camera_id_2 = LAST_INSERT_ID();

INSERT INTO Desks (
    camera_id, space_id, name, capacity, zone,
    bottom_left_x, bottom_left_y, bottom_right_x, bottom_right_y,
    top_left_x, top_left_y, top_right_x, top_right_y,
    grid_x, grid_y, is_active
) VALUES
(@camera_id_2, @space_id_2, 'F2-D1', 1, 'Floor 2 Study Area', 500, 670, 1, 670, 20, 1062, 500, 1062, 0, 0, TRUE),
(@camera_id_2, @space_id_2, 'F2-D2', 1, 'Floor 2 Study Area', 500, 600, 10, 600, 10, 10, 500, 10, 1, 0, TRUE),
(@camera_id_2, @space_id_2, 'F2-D3', 1, 'Floor 2 Study Area', 550, 248, 900, 253, 900, 610, 550, 610, 0, 1, TRUE),
(@camera_id_2, @space_id_2, 'F2-D4', 1, 'Floor 2 Study Area', 560, 680, 550, 1070, 900, 1100, 900, 700, 1, 1, TRUE);

-- ============================================================================
-- FLOOR 3
-- ============================================================================

INSERT INTO Space (name, building_id, total_capacity, grid_width, grid_height)
VALUES ('Floor 3', @building_id, 4, 2, 2);
SET @space_id_3 = LAST_INSERT_ID();

INSERT INTO Camera (space_id, name, stream_url, resolution_x, resolution_y, is_active)
VALUES (@space_id_3, 'Floor 3 Camera', NULL, 1920, 1080, TRUE);
SET @camera_id_3 = LAST_INSERT_ID();

INSERT INTO Desks (
    camera_id, space_id, name, capacity, zone,
    bottom_left_x, bottom_left_y, bottom_right_x, bottom_right_y,
    top_left_x, top_left_y, top_right_x, top_right_y,
    grid_x, grid_y, is_active
) VALUES
(@camera_id_3, @space_id_3, 'F3-D1', 1, 'Floor 3 Study Area', 500, 670, 1, 670, 20, 1062, 500, 1062, 0, 0, TRUE),
(@camera_id_3, @space_id_3, 'F3-D2', 1, 'Floor 3 Study Area', 500, 600, 10, 600, 10, 10, 500, 10, 1, 0, TRUE),
(@camera_id_3, @space_id_3, 'F3-D3', 1, 'Floor 3 Study Area', 550, 248, 900, 253, 900, 610, 550, 610, 0, 1, TRUE),
(@camera_id_3, @space_id_3, 'F3-D4', 1, 'Floor 3 Study Area', 560, 680, 550, 1070, 900, 1100, 900, 700, 1, 1, TRUE);

-- ============================================================================
-- FLOOR 4
-- ============================================================================

INSERT INTO Space (name, building_id, total_capacity, grid_width, grid_height)
VALUES ('Floor 4', @building_id, 4, 2, 2);
SET @space_id_4 = LAST_INSERT_ID();

INSERT INTO Camera (space_id, name, stream_url, resolution_x, resolution_y, is_active)
VALUES (@space_id_4, 'Floor 4 Camera', NULL, 1920, 1080, TRUE);
SET @camera_id_4 = LAST_INSERT_ID();

INSERT INTO Desks (
    camera_id, space_id, name, capacity, zone,
    bottom_left_x, bottom_left_y, bottom_right_x, bottom_right_y,
    top_left_x, top_left_y, top_right_x, top_right_y,
    grid_x, grid_y, is_active
) VALUES
(@camera_id_4, @space_id_4, 'F4-D1', 1, 'Floor 4 Study Area', 500, 670, 1, 670, 20, 1062, 500, 1062, 0, 0, TRUE),
(@camera_id_4, @space_id_4, 'F4-D2', 1, 'Floor 4 Study Area', 500, 600, 10, 600, 10, 10, 500, 10, 1, 0, TRUE),
(@camera_id_4, @space_id_4, 'F4-D3', 1, 'Floor 4 Study Area', 550, 248, 900, 253, 900, 610, 550, 610, 0, 1, TRUE),
(@camera_id_4, @space_id_4, 'F4-D4', 1, 'Floor 4 Study Area', 560, 680, 550, 1070, 900, 1100, 900, 700, 1, 1, TRUE);

-- ============================================================================
-- FLOOR 5
-- ============================================================================

INSERT INTO Space (name, building_id, total_capacity, grid_width, grid_height)
VALUES ('Floor 5', @building_id, 4, 2, 2);
SET @space_id_5 = LAST_INSERT_ID();

INSERT INTO Camera (space_id, name, stream_url, resolution_x, resolution_y, is_active)
VALUES (@space_id_5, 'Floor 5 Camera', NULL, 1920, 1080, TRUE);
SET @camera_id_5 = LAST_INSERT_ID();

INSERT INTO Desks (
    camera_id, space_id, name, capacity, zone,
    bottom_left_x, bottom_left_y, bottom_right_x, bottom_right_y,
    top_left_x, top_left_y, top_right_x, top_right_y,
    grid_x, grid_y, is_active
) VALUES
(@camera_id_5, @space_id_5, 'F5-D1', 1, 'Floor 5 Study Area', 500, 670, 1, 670, 20, 1062, 500, 1062, 0, 0, TRUE),
(@camera_id_5, @space_id_5, 'F5-D2', 1, 'Floor 5 Study Area', 500, 600, 10, 600, 10, 10, 500, 10, 1, 0, TRUE),
(@camera_id_5, @space_id_5, 'F5-D3', 1, 'Floor 5 Study Area', 550, 248, 900, 253, 900, 610, 550, 610, 0, 1, TRUE),
(@camera_id_5, @space_id_5, 'F5-D4', 1, 'Floor 5 Study Area', 560, 680, 550, 1070, 900, 1100, 900, 700, 1, 1, TRUE);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 'Building Created:' as Info;
SELECT * FROM Building WHERE building_id = @building_id;

SELECT '' as '';
SELECT 'Spaces Created:' as Info;
SELECT space_id, name, building_id, grid_width, grid_height, total_capacity
FROM Space
WHERE building_id = @building_id
ORDER BY name;

SELECT '' as '';
SELECT 'Cameras Created:' as Info;
SELECT c.camera_id, c.name, s.name as space_name, c.resolution_x, c.resolution_y
FROM Camera c
JOIN Space s ON c.space_id = s.space_id
WHERE s.building_id = @building_id
ORDER BY s.name;

SELECT '' as '';
SELECT 'Desks Created:' as Info;
SELECT d.desk_id, d.name, s.name as space_name, d.zone, d.grid_x, d.grid_y, d.capacity
FROM Desks d
JOIN Space s ON d.space_id = s.space_id
WHERE s.building_id = @building_id
ORDER BY s.name, d.grid_y, d.grid_x;

SELECT '' as '';
SELECT 'Summary:' as Info;
SELECT
    '5 floors, 5 cameras, 20 desks total' as Description,
    COUNT(DISTINCT s.space_id) as Floors,
    COUNT(DISTINCT c.camera_id) as Cameras,
    COUNT(d.desk_id) as Total_Desks
FROM Space s
JOIN Camera c ON c.space_id = s.space_id
JOIN Desks d ON d.space_id = s.space_id
WHERE s.building_id = @building_id;
