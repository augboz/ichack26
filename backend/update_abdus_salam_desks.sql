-- ============================================================================
-- Update Desk Coordinates: Abdus Salam Library
-- ============================================================================
-- Updates all 20 desks (4 per floor, 5 floors) with new quadrilateral coordinates
-- ============================================================================

USE occupancy_db;

-- Get the building ID for Abdus Salam Library
SET @building_id = (SELECT building_id FROM Building WHERE name = 'Abdus Salam Library');

-- Update all D1 desks (grid 0,0) across all floors
UPDATE Desks d
JOIN Space s ON d.space_id = s.space_id
SET
    d.bottom_left_x = 80,
    d.bottom_left_y = 200,
    d.bottom_right_x = 100,
    d.bottom_right_y = 1600,
    d.top_left_x = 1400,
    d.top_left_y = 100,
    d.top_right_x = 1400,
    d.top_right_y = 1600
WHERE s.building_id = @building_id
  AND d.grid_x = 0
  AND d.grid_y = 0;

-- Update all D2 desks (grid 1,0) across all floors
UPDATE Desks d
JOIN Space s ON d.space_id = s.space_id
SET
    d.bottom_left_x = 1600,
    d.bottom_left_y = 200,
    d.bottom_right_x = 1600,
    d.bottom_right_y = 1600,
    d.top_left_x = 2800,
    d.top_left_y = 300,
    d.top_right_x = 2700,
    d.top_right_y = 1600
WHERE s.building_id = @building_id
  AND d.grid_x = 1
  AND d.grid_y = 0;

-- Update all D3 desks (grid 0,1) across all floors
UPDATE Desks d
JOIN Space s ON d.space_id = s.space_id
SET
    d.bottom_left_x = 130,
    d.bottom_left_y = 1800,
    d.bottom_right_x = 1300,
    d.bottom_right_y = 1900,
    d.top_left_x = 160,
    d.top_left_y = 3200,
    d.top_right_x = 1300,
    d.top_right_y = 3200
WHERE s.building_id = @building_id
  AND d.grid_x = 0
  AND d.grid_y = 1;

-- Update all D4 desks (grid 1,1) across all floors
UPDATE Desks d
JOIN Space s ON d.space_id = s.space_id
SET
    d.bottom_left_x = 1600,
    d.bottom_left_y = 2000,
    d.bottom_right_x = 2800,
    d.bottom_right_y = 2000,
    d.top_left_x = 1600,
    d.top_left_y = 3200,
    d.top_right_x = 2800,
    d.top_right_y = 3200
WHERE s.building_id = @building_id
  AND d.grid_x = 1
  AND d.grid_y = 1;

-- Verification
SELECT 'Updated Desks:' as Info;
SELECT
    d.name,
    s.name as space_name,
    d.grid_x,
    d.grid_y,
    d.bottom_left_x, d.bottom_left_y,
    d.bottom_right_x, d.bottom_right_y,
    d.top_left_x, d.top_left_y,
    d.top_right_x, d.top_right_y
FROM Desks d
JOIN Space s ON d.space_id = s.space_id
WHERE s.building_id = @building_id
ORDER BY s.name, d.grid_y, d.grid_x;
