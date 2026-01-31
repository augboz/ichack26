# System Architecture Overview

## Components

### 1. Database Layer (MySQL)
- **Schema**: [databaseinitialisation.sql](databaseinitialisation.sql)
- **Interface**: [db_interface.py](db_interface.py)
- **Tables**:
  - `Space`: Physical locations (library floors, study rooms)
  - `Camera`: Cameras monitoring spaces with stream URLs
  - `Tables`: Individual tables with 4-vertex polygon boundaries
  - `Table_Occupancy_Logs`: Time-series occupancy samples

### 2. Detection & Processing ([backend.py](backend.py))
- **Main Loop**: Processes all active cameras every second
- **Object Detection**: Uses OpenCV DNN with SSD MobileNet V2
- **Person Detection**: Detects persons in camera images
- **Occupancy Logic**: Checks if persons intersect with table polygons
- **Logging**: Stores raw occupancy samples in database

**Key Functions**:
- `get_camera_ids()`: Retrieves active camera IDs from database
- `get_image(camera_id)`: Gets image from file (TEST_MODE) or stream
- `get_trect_map(camera_id)`: Gets table boundaries from database
- `get_table_occupations(img, t_id_rect_map)`: Detects occupancy using OpenCV
- `update_table_samples(tid_occ_list)`: Logs occupancy to database

### 3. Object Detection ([opencvcv.py](opencvcv.py))
- **Models**: SSD MobileNet V2 (fast) or Faster R-CNN (accurate)
- **Detection Functions**: Integrated into backend.py
- **Features**:
  - Person detection using COCO-trained models
  - Baseline subtraction to ignore static objects
  - ROI (Region of Interest) support for table boundaries

### 4. Sampling & Smoothing ([table_id.py](table_id.py))
- **TableStatusTracker**: Sliding window with majority voting
- **Purpose**: Prevents flickering from momentary detection errors
- **Config**:
  - `window_size=20`: Stores last 20 samples
  - `occ_threshold=0.7`: Requires 70% of samples to mark as occupied
  - `update_rate=5`: Updates every 5 cycles

**Note**: Currently integrated into the API layer for real-time smoothing

### 5. REST API ([get.py](get.py))
- **Framework**: Flask with CORS support
- **Function**: Serves occupancy data to frontend
- **Smoothing**: Uses majority voting over recent samples (30s default)

**Endpoints**:
- `GET /api/spaces` - List all spaces
- `GET /api/spaces/<id>/tables` - Tables in a space with status
- `GET /api/tables` - All tables with current status
- `GET /api/tables/<id>` - Specific table status
- `GET /api/tables/<id>/history` - Historical occupancy data

### 6. Test Images ([images/](images/))
- Sample images for testing object detection
- Used when `TEST_MODE = True` in backend.py

### 7. Jupyter Notebook ([compv.ipynb](compv.ipynb))
- Testing and experimentation with object detection models
- Downloads TensorFlow models for testing

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         Camera Feeds                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      backend.py (Main Loop)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ get_image()  │→│  OpenCV DNN  │→│ get_table_occupations│  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                           │                      │               │
│                           ▼                      ▼               │
│                    Person Detection      Table Intersection     │
│                                                  │               │
│                                                  ▼               │
│                                      ┌───────────────────────┐  │
│                                      │ update_table_samples()│  │
│                                      └───────────────────────┘  │
└──────────────────────────────────────────┬──────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         MySQL Database                          │
│                    Table_Occupancy_Logs                         │
│              (Stores raw occupancy samples)                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    get.py (Flask API)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Reads recent logs → Majority voting → Returns status    │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (React)                           │
│              Displays real-time table occupancy                 │
└─────────────────────────────────────────────────────────────────┘
```

## Processing Logic

### Occupancy Detection Algorithm

1. **Capture Image**: Get frame from camera (file or stream)

2. **Retrieve Table Boundaries**: Query database for table polygons
   - Each table has 4 vertices: (bottom-left, bottom-right, top-right, top-left)

3. **Person Detection**: Run OpenCV DNN model on image
   - Input: Camera image
   - Output: Bounding boxes for detected persons
   - Model: SSD MobileNet V2 (COCO dataset)
   - Confidence threshold: 0.3

4. **Intersection Test**: For each table polygon:
   - Check if any person bounding box intersects with table polygon
   - Methods:
     - Check if box corners are inside polygon
     - Check if box center is inside polygon
   - Result: `is_occupied = True/False`

5. **Log Sample**: Store occupancy status in database
   - Table: `Table_Occupancy_Logs`
   - Fields: `table_id`, `is_occupied`, `timestamp`

6. **Repeat**: Process all cameras every 1 second

### API Smoothing Algorithm

When frontend requests table status:

1. **Query Recent Logs**: Get last 30 seconds of samples (configurable)
   ```sql
   SELECT is_occupied FROM Table_Occupancy_Logs
   WHERE table_id = ? AND timestamp >= NOW() - INTERVAL 30 SECOND
   ```

2. **Majority Vote**: Calculate occupancy percentage
   ```python
   confidence = occupied_count / total_count
   is_occupied = confidence >= 0.5  # 50% threshold
   ```

3. **Return Status**: JSON response with confidence level
   ```json
   {
     "occupied": true,
     "confidence": 0.85,  // 85% of samples showed occupancy
     "sample_count": 20
   }
   ```

This approach:
- Filters out momentary false positives/negatives
- Provides confidence metric for UI display
- Handles intermittent detection failures gracefully

## Configuration

### Database
- **File**: All files using `OccupancyDatabase`
- **Settings**: host, database, user, password
- **Default**: localhost, occupancy_db, root, ""

### Detection Model
- **File**: [backend.py](backend.py) lines 14-28
- **Options**: "ssd" (fast) or "fasterrcnn" (accurate)
- **Threshold**: 0.3 (line 30)

### Test Mode
- **File**: [backend.py](backend.py) line 11
- **TEST_MODE = True**: Load from test_camera_X.jpg files
- **TEST_MODE = False**: Capture from camera stream URLs

### Smoothing
- **File**: [get.py](get.py)
- **Lookback window**: 30 seconds (query parameter `?lookback=30`)
- **Threshold**: 0.5 (50% majority)

## Deployment Considerations

### Production Checklist

1. ✅ Set `TEST_MODE = False` in backend.py
2. ✅ Update MySQL password in all files
3. ✅ Ensure model files (*.pb, *.pbtxt) are present
4. ✅ Configure camera stream URLs in database
5. ✅ Set up camera positions and table boundaries
6. ✅ Test detection accuracy with sample images
7. ✅ Tune confidence threshold if needed
8. ✅ Consider GPU acceleration for multiple cameras
9. ✅ Set up proper logging and monitoring
10. ✅ Use production WSGI server (gunicorn) for Flask API

### Performance

- **SSD MobileNet V2**: ~30-50 FPS on CPU (recommended)
- **Faster R-CNN**: ~5-10 FPS on CPU, faster on GPU
- **Database**: Index on (table_id, timestamp) for fast queries
- **Scaling**: Use ThreadPoolExecutor (max 5 workers) for parallel camera processing

### Security

- Change default MySQL password
- Use environment variables for credentials
- Enable HTTPS for production API
- Implement API authentication if needed
- Restrict camera stream access
