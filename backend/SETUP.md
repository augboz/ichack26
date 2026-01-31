# Backend Setup Guide

## Prerequisites

1. **Python Dependencies**
   ```bash
   pip install opencv-python numpy mysql-connector-python flask flask-cors
   ```

2. **MySQL Database**
   - Install MySQL server
   - Create database: `CREATE DATABASE occupancy_db;`
   - Run initialization script: `mysql -u root -p occupancy_db < databaseinitialisation.sql`
   - Update password in backend.py (search for `password=""` and add your MySQL password)

3. **Object Detection Model Files**

   Download the SSD MobileNet V2 model files and place them in the `backend/` directory:

   - **Config file**: `ssd_mobilenet_v2_coco_2018_03_29.pbtxt`
   - **Weights file**: `ssd_mobilenet_v2_coco_2018_03_29.pb`

   Download links:
   - TensorFlow Model Zoo: https://github.com/opencv/opencv/wiki/TensorFlow-Object-Detection-API
   - Direct download: https://github.com/opencv/opencv_extra/tree/master/testdata/dnn

## Configuration

### Database Settings
Update the database credentials in `backend.py` for all functions that use `OccupancyDatabase`:
```python
db = OccupancyDatabase(
    host="localhost",
    database="occupancy_db",
    user="root",
    password="your_mysql_password"  # Update this
)
```

### Test Mode
The backend runs in TEST_MODE by default, which loads images from files instead of camera streams.

To switch to production mode (using camera streams):
```python
TEST_MODE = False  # In backend.py, line 11
```

### Test Images
When in TEST_MODE, the system expects test images named:
- `test_camera_1.jpg`
- `test_camera_2.jpg`
- etc.

Place these in the `backend/` directory.

## How It Works

1. **Camera Processing Loop** (`backend.py`)
   - Gets all active camera IDs from database
   - For each camera:
     - Captures image (from file in TEST_MODE, from stream in production)
     - Gets table boundaries from database
     - Detects persons using OpenCV DNN
     - Determines which tables are occupied
     - Logs occupancy status to database

2. **Object Detection** (`opencvcv.py` integrated into `backend.py`)
   - Uses SSD MobileNet V2 (fast) or Faster R-CNN (accurate)
   - Detects persons in camera images
   - Checks if detected persons overlap with table boundaries
   - Returns occupancy status for each table

3. **Database Schema**
   - `Space`: Physical locations (library floors, study rooms)
   - `Camera`: Cameras monitoring spaces
   - `Tables`: Individual tables with coordinate boundaries
   - `Table_Occupancy_Logs`: Time-series occupancy data

## Running the System

### 1. Start the Backend Processing Loop

```bash
cd backend
python backend.py
```

The system will:
1. Load the object detection model
2. Connect to the database
3. Continuously process camera feeds every second
4. Detect persons using OpenCV
5. Log occupancy status to the database

### 2. Start the Flask API Server

In a separate terminal:
```bash
cd backend
python get.py
```

The API will start on `http://localhost:5000` and provide the following endpoints:

#### API Endpoints

**Get all spaces**
```
GET /api/spaces
```

**Get all tables in a space**
```
GET /api/spaces/<space_id>/tables?lookback=30
```
- `lookback`: seconds to look back for occupancy data (default: 30)

**Get all tables**
```
GET /api/tables?lookback=30
```
- Returns all active tables with occupancy status

**Get specific table status**
```
GET /api/tables/<table_id>?lookback=30
```
- Returns current occupancy status based on recent samples

**Get table history**
```
GET /api/tables/<table_id>/history?hours=24
```
- Returns occupancy history for specified hours (default: 24)

#### Example API Response

```json
{
  "table_id": 1,
  "name": "Table 1",
  "capacity": 4,
  "occupied": true,
  "confidence": 0.85,
  "last_updated": "2026-01-31T10:30:45"
}
```

The `confidence` value indicates the percentage of recent samples showing occupancy. A value >= 0.5 means the table is considered occupied.

## Testing

1. Set up test data in database:
   ```sql
   -- Add a space
   INSERT INTO Space (name, building) VALUES ('Main Library', 'Central Campus');

   -- Add a camera
   INSERT INTO Camera (space_id, name, resolution_x, resolution_y)
   VALUES (1, 'Camera 1', 1920, 1080);

   -- Add tables with coordinates (adjust based on your image)
   INSERT INTO Tables (camera_id, space_id, name,
                       bottom_left_x, bottom_left_y,
                       bottom_right_x, bottom_right_y,
                       top_right_x, top_right_y,
                       top_left_x, top_left_y)
   VALUES (1, 1, 'Table 1', 100, 500, 300, 500, 300, 300, 100, 300);
   ```

2. Place test image at `backend/test_camera_1.jpg`

3. Run backend: `python backend.py`

4. Check logs in database:
   ```sql
   SELECT * FROM Table_Occupancy_Logs ORDER BY timestamp DESC LIMIT 10;
   ```

## Model Performance

- **SSD MobileNet V2**: Fast (~30-50 FPS), good for real-time on CPU
- **Faster R-CNN**: Slower (~5-10 FPS), more accurate, better for GPU

Change model in `backend.py` line 14:
```python
MODEL = "ssd"  # or "fasterrcnn"
```
