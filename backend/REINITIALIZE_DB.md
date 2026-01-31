# Database Reinitialization Guide

## What Changed
- Renamed **`Tables`** → **`Desks`**
- Renamed **`table_id`** → **`desk_id`**
- Renamed **`Table_Occupancy_Logs`** → **`Desk_Occupancy_Logs`**
- Updated all API endpoints and Python code

## How to Reinitialize the Database

### Option 1: Drop and Recreate (Clean Slate)

```bash
mysql -u root -p
```

Then run:
```sql
DROP DATABASE IF EXISTS occupancy_db;
CREATE DATABASE occupancy_db;
exit;
```

Now reinitialize the schema:
```bash
mysql -u root -p occupancy_db < databaseinitialisation.sql
```

### Option 2: Keep Database, Drop Tables Only

```bash
mysql -u root -p occupancy_db
```

Then run:
```sql
-- Disable foreign key checks
SET FOREIGN_KEY_CHECKS = 0;

-- Drop old tables
DROP TABLE IF EXISTS Table_Occupancy_Logs;
DROP TABLE IF EXISTS Tables;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Exit and reload schema
exit;
```

Then run the schema file:
```bash
mysql -u root -p occupancy_db < databaseinitialisation.sql
```

## Verify the Changes

After reinitializing, verify the new structure:
```sql
mysql -u root -p occupancy_db
```

```sql
-- Check tables exist
SHOW TABLES;

-- Should show:
-- Camera
-- Desks
-- Desk_Occupancy_Logs
-- Space

-- Check Desks structure
DESCRIBE Desks;

-- Check Desk_Occupancy_Logs structure
DESCRIBE Desk_Occupancy_Logs;

exit;
```

## Add Test Data

After reinitializing, add test camera and desk:
```bash
python setup_test_camera.py
```

This will create:
- Test Space
- Test Camera (linked to test_camera_1.jpg)
- Test Desk with your vertices

## Updated API Endpoints

The API endpoints have changed:

**Old:**
- `GET /api/tables`
- `GET /api/tables/<table_id>`
- `GET /api/spaces/<space_id>/tables`
- `GET /api/tables/<table_id>/history`

**New:**
- `GET /api/desks`
- `GET /api/desks/<desk_id>`
- `GET /api/spaces/<space_id>/desks`
- `GET /api/desks/<desk_id>/history`

## Files Updated

All backend files have been updated:
- ✓ databaseinitialisation.sql
- ✓ db_interface.py
- ✓ backend.py
- ✓ get.py (Flask API)
- ✓ setup_test_camera.py
- ✓ insert_test_data.sql

## Next Steps

1. Reinitialize database (Option 1 or 2 above)
2. Run `python setup_test_camera.py` to add test data
3. Start backend: `python backend.py`
4. Start API: `python get.py`
5. Update frontend to use new `/api/desks` endpoints
