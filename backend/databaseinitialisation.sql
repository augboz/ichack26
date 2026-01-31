-- ============================================================================
-- Study Space Occupancy Tracking Database Schema
-- ============================================================================
-- This schema tracks table occupancy across multiple study spaces using
-- camera-based detection with coordinate-based boundaries.
-- 
-- Note: Sampling and decision-making (majority voting over time windows) is
-- handled in the backend. This schema only stores the final committed
-- occupancy state changes.
-- ============================================================================

-- Drop tables if they exist (in reverse order of dependencies)
DROP TABLE IF EXISTS Table_Occupancy_Logs CASCADE;
DROP TABLE IF EXISTS "Table" CASCADE;
DROP TABLE IF EXISTS Camera CASCADE;
DROP TABLE IF EXISTS Space CASCADE;

-- ============================================================================
-- SPACE TABLE
-- ============================================================================
-- Represents physical study spaces (e.g., library floors, study rooms)
CREATE TABLE Space (
    space_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    building VARCHAR(100),
    total_capacity INT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CAMERA TABLE
-- ============================================================================
-- Represents cameras monitoring study spaces with top-down eagle eye view
CREATE TABLE Camera (
    camera_id SERIAL PRIMARY KEY,
    space_id INT NOT NULL REFERENCES Space(space_id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    stream_url VARCHAR(500),
    resolution_x INT NOT NULL,
    resolution_y INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_resolution_x CHECK (resolution_x > 0),
    CONSTRAINT chk_resolution_y CHECK (resolution_y > 0)
);

-- ============================================================================
-- TABLE
-- ============================================================================
CREATE TABLE Table (  -- Add quotes here
    table_id SERIAL PRIMARY KEY,
    camera_id INT NOT NULL REFERENCES Camera(camera_id) ON DELETE CASCADE,
    space_id INT NOT NULL REFERENCES Space(space_id) ON DELETE CASCADE,
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
    
    is_active BOOLEAN DEFAULT TRUE,  -- Add this back
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_capacity CHECK (capacity > 0),
    CONSTRAINT chk_coordinates CHECK (
        bottom_left_x >= 0 AND bottom_left_y >= 0 AND
        bottom_right_x >= 0 AND bottom_right_y >= 0 AND
        top_left_x >= 0 AND top_left_y >= 0 AND
        top_right_x >= 0 AND top_right_y >= 0
    )
);

CREATE TABLE Table_Occupancy_Logs (
    log_id SERIAL PRIMARY KEY,
    table_id INT NOT NULL REFERENCES "Table"(table_id) ON DELETE CASCADE,
    is_occupied BOOLEAN NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    -- Remove the confidence_score constraint entirely
);

-- Space indexes
CREATE INDEX idx_space_name ON Space(name);

-- Camera indexes
CREATE INDEX idx_camera_space ON Camera(space_id);
CREATE INDEX idx_camera_active ON Camera(is_active);

-- Table indexes
CREATE INDEX idx_table_camera ON "Table"(camera_id);
CREATE INDEX idx_table_space ON "Table"(space_id);

-- Table_Occupancy_Logs indexes
CREATE INDEX idx_logs_table_time ON Table_Occupancy_Logs(table_id, timestamp DESC);
CREATE INDEX idx_logs_timestamp ON Table_Occupancy_Logs(timestamp DESC);
CREATE INDEX idx_logs_occupied ON Table_Occupancy_Logs(is_occupied);