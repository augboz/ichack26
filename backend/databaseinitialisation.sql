-- ============================================================================
-- Study Space Occupancy Tracking Database Schema (MySQL)
-- ============================================================================
-- This schema tracks table occupancy across multiple study spaces using
-- camera-based detection with coordinate-based boundaries.
--
-- Note: Sampling and decision-making (majority voting over time windows) is
-- handled in the backend. This schema only stores the final committed
-- occupancy state changes.
-- ============================================================================

-- Drop tables if they exist (in reverse order of dependencies)
DROP TABLE IF EXISTS Table_Occupancy_Logs;
DROP TABLE IF EXISTS Tables;
DROP TABLE IF EXISTS Camera;
DROP TABLE IF EXISTS Space;

-- ============================================================================
-- SPACE TABLE
-- ============================================================================
-- Represents physical study spaces (e.g., library floors, study rooms)
CREATE TABLE Space (
    space_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    building VARCHAR(100),
    total_capacity INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- CAMERA TABLE
-- ============================================================================
-- Represents cameras monitoring study spaces with top-down eagle eye view
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
-- TABLE
-- ============================================================================
CREATE TABLE Tables (
    table_id INT AUTO_INCREMENT PRIMARY KEY,
    camera_id INT NOT NULL,
    space_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    capacity INT DEFAULT 1,

    -- Coordinate boundaries (relative to camera image)
    bottom_left_x INT NOT NULL,
    bottom_left_y INT NOT NULL,
    bottom_right_x INT NOT NULL,
    bottom_right_y INT NOT NULL,
    top_left_x INT NOT NULL,
    top_left_y INT NOT NULL,
    top_right_x INT NOT NULL,
    top_right_y INT NOT NULL,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT chk_capacity CHECK (capacity > 0),
    CONSTRAINT chk_coordinates CHECK (
        bottom_left_x >= 0 AND bottom_left_y >= 0 AND
        bottom_right_x >= 0 AND bottom_right_y >= 0 AND
        top_left_x >= 0 AND top_left_y >= 0 AND
        top_right_x >= 0 AND top_right_y >= 0
    ),
    CONSTRAINT fk_table_camera FOREIGN KEY (camera_id) REFERENCES Camera(camera_id) ON DELETE CASCADE,
    CONSTRAINT fk_table_space FOREIGN KEY (space_id) REFERENCES Space(space_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- TABLE OCCUPANCY LOGS
-- ============================================================================
CREATE TABLE Table_Occupancy_Logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    table_id INT NOT NULL,
    is_occupied BOOLEAN NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_log_table FOREIGN KEY (table_id) REFERENCES Tables(table_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- INDEXES
-- ============================================================================
-- Space indexes
CREATE INDEX idx_space_name ON Space(name);

-- Camera indexes
CREATE INDEX idx_camera_space ON Camera(space_id);
CREATE INDEX idx_camera_active ON Camera(is_active);

-- Table indexes
CREATE INDEX idx_table_camera ON Tables(camera_id);
CREATE INDEX idx_table_space ON Tables(space_id);

-- Table_Occupancy_Logs indexes
CREATE INDEX idx_logs_table_time ON Table_Occupancy_Logs(table_id, timestamp DESC);
CREATE INDEX idx_logs_timestamp ON Table_Occupancy_Logs(timestamp DESC);
CREATE INDEX idx_logs_occupied ON Table_Occupancy_Logs(is_occupied);