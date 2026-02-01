-- ============================================================================
-- Study Space Occupancy Tracking Database Schema (MySQL)
-- ============================================================================
-- Updated to include:
-- - Building entity with map coordinates
-- - Space-level grid coordinate system for unified floor layouts
-- - Multi-camera support with camera-specific pixel coordinates
-- ============================================================================

-- Drop tables if they exist (in reverse order of dependencies)
DROP DATABASE occupancy_db;
CREATE DATABASE occupancy_db;
USE occupancy_db;
-- ============================================================================
-- BUILDING TABLE (NEW)
-- ============================================================================
-- Represents p hysical buildings on campus with map coordinates
CREATE TABLE Building (
    building_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    map_latitude DECIMAL(10, 8),      -- For campus map positioning
    map_longitude DECIMAL(11, 8),     -- For campus map positioning
    address VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- SPACE TABLE (MODIFIED)
-- ============================================================================
-- Represents physical study spaces (e.g., library floors, study rooms)
-- Each space belongs to one building and has a unified grid layout
CREATE TABLE Space (
    space_id INT AUTO_INCREMENT PRIMARY KEY,
    building_id INT NOT NULL,         -- FK to Building (was VARCHAR building)
    name VARCHAR(100) NOT NULL,
    total_capacity INT,
    
    -- Grid layout dimensions for this space
    grid_width INT NOT NULL,          -- Number of columns in grid (NEW)
    grid_height INT NOT NULL,         -- Number of rows in grid (NEW)
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_grid_dimensions CHECK (grid_width > 0 AND grid_height > 0),
    CONSTRAINT fk_space_building FOREIGN KEY (building_id) REFERENCES Building(building_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- CAMERA TABLE (UNCHANGED)
-- ============================================================================
-- Represents cameras monitoring study spaces with top-down eagle eye view
-- Multiple cameras can monitor a single space
CREATE TABLE Camera (
    camera_id INT AUTO_INCREMENT PRIMARY KEY,
    space_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    stream_url VARCHAR(500),
    resolution_x INT NOT NULL,
    resolution_y INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT chk_resolution_x CHECK (resolution_x > 0),
    CONSTRAINT chk_resolution_y CHECK (resolution_y > 0),
    CONSTRAINT fk_camera_space FOREIGN KEY (space_id) REFERENCES Space(space_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- DESK TABLE (MODIFIED)
-- ============================================================================
-- Represents individual desks with dual coordinate systems:
-- 1. Pixel coordinates (relative to camera) - for CV detection
-- 2. Grid coordinates (relative to space) - for UI layout
CREATE TABLE Desks (
    desk_id INT AUTO_INCREMENT PRIMARY KEY,
    camera_id INT NOT NULL,
    space_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    capacity INT DEFAULT 1,
    zone VARCHAR(50),                 -- Zone/area name for grouping (e.g., "Quiet Row", "Window Seats")

    -- Pixel coordinate boundaries (relative to camera image) - for CV
    bottom_left_x INT NOT NULL,
    bottom_left_y INT NOT NULL,
    bottom_right_x INT NOT NULL,
    bottom_right_y INT NOT NULL,
    top_left_x INT NOT NULL,
    top_left_y INT NOT NULL,
    top_right_x INT NOT NULL,
    top_right_y INT NOT NULL,

    -- Grid coordinates (relative to space grid) - for UI layout (NEW)
    grid_x INT NOT NULL,              -- Column position in space grid
    grid_y INT NOT NULL,              -- Row position in space grid

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT chk_capacity CHECK (capacity > 0),
    CONSTRAINT chk_pixel_coordinates CHECK (
        bottom_left_x >= 0 AND bottom_left_y >= 0 AND
        bottom_right_x >= 0 AND bottom_right_y >= 0 AND
        top_left_x >= 0 AND top_left_y >= 0 AND
        top_right_x >= 0 AND top_right_y >= 0
    ),
    CONSTRAINT chk_grid_coordinates CHECK (grid_x >= 0 AND grid_y >= 0),
    CONSTRAINT fk_table_camera FOREIGN KEY (camera_id) REFERENCES Camera(camera_id) ON DELETE CASCADE,
    CONSTRAINT fk_table_space FOREIGN KEY (space_id) REFERENCES Space(space_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- DESK OCCUPANCY LOGS (UNCHANGED)
-- ============================================================================
CREATE TABLE Desk_Occupancy_Logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    desk_id INT NOT NULL,
    is_occupied BOOLEAN NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_log_desk FOREIGN KEY (desk_id) REFERENCES Desks(desk_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- INDEXES
-- ============================================================================
-- Building indexes
CREATE INDEX idx_building_name ON Building(name);

-- Space indexes
CREATE INDEX idx_space_name ON Space(name);
CREATE INDEX idx_space_building ON Space(building_id);

-- Camera indexes
CREATE INDEX idx_camera_space ON Camera(space_id);
CREATE INDEX idx_camera_active ON Camera(is_active);

-- Desk indexes
CREATE INDEX idx_desk_camera ON Desks(camera_id);
CREATE INDEX idx_desk_space ON Desks(space_id);
CREATE INDEX idx_desk_grid ON Desks(space_id, grid_x, grid_y);  -- NEW: for grid queries
CREATE INDEX idx_desk_zone ON Desks(space_id, zone);  -- NEW: for zone queries

-- Desk_Occupancy_Logs indexes
CREATE INDEX idx_logs_desk_time ON Desk_Occupancy_Logs(desk_id, timestamp DESC);
CREATE INDEX idx_logs_timestamp ON Desk_Occupancy_Logs(timestamp DESC);
CREATE INDEX idx_logs_occupied ON Desk_Occupancy_Logs(is_occupied);
