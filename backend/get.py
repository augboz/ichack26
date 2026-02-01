from flask import Flask, jsonify, request
from flask_cors import CORS
from db_interface import OccupancyDatabase

app = Flask(__name__)
CORS(app)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'occupancy_db',
    'user': 'root',
    'password': 'yazool921'  # Update with actual password
}


def get_latest_desk_status(desk_id: int, lookback_seconds: int = 30) -> dict:
    """
    Get the latest occupancy status for a table using majority voting over recent samples.

    Args:
        desk_id: The table ID
        lookback_seconds: How many seconds to look back for samples (default 30)

    Returns:
        Dictionary with table status information
    """
    db = OccupancyDatabase(**DB_CONFIG)
    try:
        cur = db.conn.cursor(dictionary=True)
        try:
            # Get recent logs for this table
            cur.execute("""
                SELECT is_occupied, timestamp
                FROM Desk_Occupancy_Logs
                WHERE desk_id = %s
                  AND timestamp >= DATE_SUB(NOW(), INTERVAL %s SECOND)
                ORDER BY timestamp DESC
            """, (desk_id, lookback_seconds))

            logs = cur.fetchall()

            if not logs:
                return {
                    'desk_id': desk_id,
                    'occupied': False,
                    'confidence': 0.0,
                    'last_updated': None,
                    'sample_count': 0
                }

            # Calculate occupancy based on majority voting
            occupied_count = sum(1 for log in logs if log['is_occupied'])
            total_count = len(logs)
            confidence = occupied_count / total_count
            is_occupied = confidence >= 0.5  # Majority vote

            return {
                'desk_id': desk_id,
                'occupied': is_occupied,
                'confidence': round(confidence, 2),
                'last_updated': logs[0]['timestamp'].isoformat() if logs else None,
                'sample_count': total_count
            }
        finally:
            cur.close()
    finally:
        db.close()


@app.route('/api/buildings', methods=['GET'])
def get_all_buildings():
    """Return all buildings with occupancy statistics"""
    db = OccupancyDatabase(**DB_CONFIG)
    try:
        cur = db.conn.cursor(dictionary=True)
        try:
            # Get all buildings
            cur.execute("""
                SELECT building_id, name, map_latitude, map_longitude, address
                FROM Building
                ORDER BY name
            """)
            buildings = cur.fetchall()

            # For each building, calculate overall occupancy
            result = []
            for building in buildings:
                # Get all desks in all spaces in this building
                cur.execute("""
                    SELECT d.desk_id, d.capacity
                    FROM Desks d
                    JOIN Space s ON d.space_id = s.space_id
                    WHERE s.building_id = %s AND d.is_active = TRUE
                """, (building['building_id'],))
                desks = cur.fetchall()

                if not desks:
                    result.append({
                        'building_id': building['building_id'],
                        'name': building['name'],
                        'latitude': float(building['map_latitude']) if building['map_latitude'] else 0,
                        'longitude': float(building['map_longitude']) if building['map_longitude'] else 0,
                        'address': building['address'],
                        'total_capacity': 0,
                        'free_seats': 0,
                        'occupied_seats': 0,
                        'occupancy_percentage': 0
                    })
                    continue

                # Calculate occupancy for all desks
                total_capacity = sum(d['capacity'] for d in desks)
                free_seats = 0
                occupied_seats = 0

                for desk in desks:
                    status = get_latest_desk_status(desk['desk_id'], 30)
                    if status['occupied']:
                        occupied_seats += desk['capacity']
                    else:
                        free_seats += desk['capacity']

                result.append({
                    'building_id': building['building_id'],
                    'name': building['name'],
                    'latitude': float(building['map_latitude']) if building['map_latitude'] else 0,
                    'longitude': float(building['map_longitude']) if building['map_longitude'] else 0,
                    'address': building['address'],
                    'total_capacity': total_capacity,
                    'free_seats': free_seats,
                    'occupied_seats': occupied_seats,
                    'occupancy_percentage': round((occupied_seats / total_capacity * 100) if total_capacity > 0 else 0, 1)
                })

            return jsonify(result)
        finally:
            cur.close()
    finally:
        db.close()


@app.route('/api/buildings/<int:building_id>/spaces', methods=['GET'])
def get_building_spaces(building_id):
    """Return all spaces for a building"""
    db = OccupancyDatabase(**DB_CONFIG)
    try:
        cur = db.conn.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT space_id, name, total_capacity, grid_width, grid_height
                FROM Space
                WHERE building_id = %s
                ORDER BY name
            """, (building_id,))
            return jsonify(cur.fetchall())
        finally:
            cur.close()
    finally:
        db.close()


@app.route('/api/spaces', methods=['GET'])
def get_all_spaces():
    """Return all spaces"""
    db = OccupancyDatabase(**DB_CONFIG)
    try:
        spaces = db.get_all_spaces()
        return jsonify(spaces)
    finally:
        db.close()


@app.route('/api/spaces/<int:space_id>/desks', methods=['GET'])
def get_space_tables(space_id):
    """Return all desks for a space with their current occupancy status and grid positions"""
    lookback = int(request.args.get('lookback', 30))  # seconds to look back

    db = OccupancyDatabase(**DB_CONFIG)
    try:
        # Get space grid dimensions
        cur = db.conn.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT grid_width, grid_height
                FROM Space
                WHERE space_id = %s
            """, (space_id,))
            space_data = cur.fetchone()

            if not space_data:
                return jsonify({'error': 'Space not found'}), 404

            grid_width = space_data['grid_width']
            grid_height = space_data['grid_height']

            # Get all desks for this space with grid coordinates
            cur.execute("""
                SELECT desk_id, name, capacity, grid_x, grid_y, is_active
                FROM Desks
                WHERE space_id = %s AND is_active = TRUE
                ORDER BY desk_id
            """, (space_id,))
            desks = cur.fetchall()
        finally:
            cur.close()

        # Get occupancy status for each table
        result = {
            'space_id': space_id,
            'grid_width': grid_width,
            'grid_height': grid_height,
            'desks': []
        }

        for desk in desks:
            status = get_latest_desk_status(desk['desk_id'], lookback)
            result['desks'].append({
                'desk_id': desk['desk_id'],
                'name': desk['name'],
                'capacity': desk['capacity'],
                'grid_x': desk['grid_x'],
                'grid_y': desk['grid_y'],
                'occupied': status['occupied'],
                'confidence': status['confidence'],
                'last_updated': status['last_updated'],
                'sample_count': status['sample_count']
            })

        return jsonify(result)
    finally:
        db.close()


@app.route('/api/spaces/<int:space_id>/zones', methods=['GET'])
def get_space_zones(space_id):
    """Return zone statistics for a space with real-time occupancy"""
    lookback = int(request.args.get('lookback', 30))  # seconds to look back

    db = OccupancyDatabase(**DB_CONFIG)
    try:
        cur = db.conn.cursor(dictionary=True)
        try:
            # Get all desks for this space grouped by zone
            cur.execute("""
                SELECT zone, desk_id, capacity
                FROM Desks
                WHERE space_id = %s AND is_active = TRUE
                ORDER BY zone, desk_id
            """, (space_id,))
            desks = cur.fetchall()
        finally:
            cur.close()

        # Group desks by zone and calculate statistics
        zones = {}
        for desk in desks:
            zone_name = desk['zone'] or 'Uncategorized'

            if zone_name not in zones:
                zones[zone_name] = {
                    'name': zone_name,
                    'total_capacity': 0,
                    'free_seats': 0,
                    'occupied_seats': 0,
                    'desk_ids': []
                }

            zones[zone_name]['total_capacity'] += desk['capacity']
            zones[zone_name]['desk_ids'].append(desk['desk_id'])

        # Get occupancy status for each zone
        for zone_name, zone_data in zones.items():
            for desk_id in zone_data['desk_ids']:
                status = get_latest_desk_status(desk_id, lookback)
                if status['occupied']:
                    zone_data['occupied_seats'] += 1
                else:
                    zone_data['free_seats'] += 1

        # Convert to list and add percentages
        result = []
        for zone_name, zone_data in zones.items():
            total = zone_data['total_capacity']
            free = zone_data['free_seats']
            occupied = zone_data['occupied_seats']

            result.append({
                'name': zone_name,
                'free': free,
                'occupied': occupied,
                'capacity': total,
                'free_percentage': round((free / total * 100) if total > 0 else 0, 1)
            })

        return jsonify(result)
    finally:
        db.close()


@app.route('/api/desks', methods=['GET'])
def get_all_tables():
    """Return current status of all desks"""
    lookback = int(request.args.get('lookback', 30))  # seconds to look back

    db = OccupancyDatabase(**DB_CONFIG)
    try:
        # Get all active tables
        cur = db.conn.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT desk_id, space_id, name, capacity
                FROM Desks
                WHERE is_active = TRUE
                ORDER BY desk_id
            """, ())
            desks = cur.fetchall()
        finally:
            cur.close()

        # Get status for each table
        result = []
        for desk in desks:
            status = get_latest_desk_status(desk['desk_id'], lookback)
            result.append({
                'desk_id': desk['desk_id'],
                'space_id': desk['space_id'],
                'name': desk['name'],
                'capacity': desk['capacity'],
                'occupied': status['occupied'],
                'confidence': status['confidence'],
                'last_updated': status['last_updated']
            })

        return jsonify(result)
    finally:
        db.close()


@app.route('/api/desks/<int:desk_id>', methods=['GET'])
def get_table_status(desk_id):
    """Return status of a specific desk"""
    lookback = int(request.args.get('lookback', 30))  # seconds to look back

    try:
        status = get_latest_desk_status(desk_id, lookback)

        if status['sample_count'] == 0:
            return jsonify({'error': 'Desk not found or no recent data'}), 404

        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/desks/<int:desk_id>/history', methods=['GET'])
def get_table_history(desk_id):
    """Return occupancy history for a desk"""
    hours = int(request.args.get('hours', 24))  # hours to look back

    db = OccupancyDatabase(**DB_CONFIG)
    try:
        cur = db.conn.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT log_id, is_occupied, timestamp
                FROM Desk_Occupancy_Logs
                WHERE desk_id = %s
                  AND timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                ORDER BY timestamp DESC
                LIMIT 1000
            """, (desk_id, hours))

            logs = cur.fetchall()

            # Convert timestamps to ISO format
            for log in logs:
                log['timestamp'] = log['timestamp'].isoformat()

            return jsonify(logs)
        finally:
            cur.close()
    finally:
        db.close()


@app.route('/api/spaces/<int:space_id>/cameras', methods=['GET'])
def get_space_cameras(space_id):
    """Return all cameras monitoring a space"""
    db = OccupancyDatabase(**DB_CONFIG)
    try:
        cur = db.conn.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT camera_id, name, stream_url, resolution_x, resolution_y, is_active
                FROM Camera
                WHERE space_id = %s
                ORDER BY camera_id
            """, (space_id,))
            cameras = cur.fetchall()

            # For each camera, get the count of desks it monitors
            for camera in cameras:
                cur.execute("""
                    SELECT COUNT(*) as desk_count
                    FROM Desks
                    WHERE camera_id = %s AND is_active = TRUE
                """, (camera['camera_id'],))
                result = cur.fetchone()
                camera['desk_count'] = result['desk_count'] if result else 0

            return jsonify(cameras)
        finally:
            cur.close()
    finally:
        db.close()


@app.route('/api/spaces/<int:space_id>/heatmap', methods=['GET'])
def get_space_heatmap(space_id):
    """Return average occupancy percentage by hour for each day of the week"""
    days = request.args.get('days', None)  # days to look back, None = all data

    db = OccupancyDatabase(**DB_CONFIG)
    try:
        cur = db.conn.cursor(dictionary=True)
        try:
            # Get all desks for this space
            cur.execute("""
                SELECT desk_id, capacity
                FROM Desks
                WHERE space_id = %s AND is_active = TRUE
            """, (space_id,))
            desks = cur.fetchall()

            if not desks:
                return jsonify({'error': 'No desks found for this space'}), 404

            desk_ids = [d['desk_id'] for d in desks]
            total_capacity = sum(d['capacity'] for d in desks)

            # Build query with optional date filter
            # DAYOFWEEK: 1=Sunday, 2=Monday, ..., 7=Saturday
            # HOUR: 0-23
            placeholders = ','.join(['%s'] * len(desk_ids))

            if days is not None:
                # Filter by date range
                query = f"""
                    SELECT
                        DAYOFWEEK(timestamp) as day_of_week,
                        HOUR(timestamp) as hour,
                        AVG(CASE WHEN is_occupied THEN 1 ELSE 0 END) as avg_occupancy
                    FROM Desk_Occupancy_Logs
                    WHERE desk_id IN ({placeholders})
                      AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                    GROUP BY day_of_week, hour
                    ORDER BY day_of_week, hour
                """
                cur.execute(query, (*desk_ids, int(days)))
            else:
                # Use all available data for historical pattern
                query = f"""
                    SELECT
                        DAYOFWEEK(timestamp) as day_of_week,
                        HOUR(timestamp) as hour,
                        AVG(CASE WHEN is_occupied THEN 1 ELSE 0 END) as avg_occupancy
                    FROM Desk_Occupancy_Logs
                    WHERE desk_id IN ({placeholders})
                    GROUP BY day_of_week, hour
                    ORDER BY day_of_week, hour
                """
                cur.execute(query, desk_ids)

            results = cur.fetchall()

            # Initialize heatmap with zeros (7 days x 24 hours)
            # Convert day_of_week to standard format: 0=Monday, 6=Sunday
            heatmap = [[0 for _ in range(24)] for _ in range(7)]

            for row in results:
                dow = row['day_of_week']  # 1=Sunday, 2=Monday, ..., 7=Saturday
                # Convert to 0=Monday format
                day_index = (dow + 5) % 7  # 2->0 (Mon), 3->1 (Tue), ..., 1->6 (Sun)
                hour = row['hour']
                occupancy_pct = round(row['avg_occupancy'] * 100, 1)
                heatmap[day_index][hour] = occupancy_pct

            return jsonify({
                'space_id': space_id,
                'total_capacity': total_capacity,
                'days_analyzed': days if days is not None else 'all',
                'heatmap': heatmap,
                'day_labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'hour_labels': [f'{h:02d}:00' for h in range(24)]
            })
        finally:
            cur.close()
    finally:
        db.close()


@app.route('/api/find-space', methods=['GET'])
def find_available_space():
    """Find the nearest space with available seats for a group"""
    try:
        group_size = int(request.args.get('group_size', 1))
        user_lat = float(request.args.get('latitude'))
        user_lng = float(request.args.get('longitude'))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid parameters. Required: latitude, longitude. Optional: group_size (default 1)'}), 400

    if group_size < 1:
        return jsonify({'error': 'group_size must be at least 1'}), 400

    from math import radians, cos, sin, sqrt, atan2

    db = OccupancyDatabase(**DB_CONFIG)
    try:
        cur = db.conn.cursor(dictionary=True)
        try:
            # Get all buildings with their locations
            cur.execute("""
                SELECT building_id, name, map_latitude, map_longitude, address
                FROM Building
                ORDER BY name
            """)
            buildings = cur.fetchall()

            best_match = None
            best_distance = float('inf')

            for building in buildings:
                # Calculate distance from user to building (haversine formula)
                lat1, lon1 = user_lat, user_lng
                lat2, lon2 = float(building['map_latitude']), float(building['map_longitude'])

                # Simple distance calculation (in km, approximate)
                R = 6371  # Earth radius in km

                dlat = radians(lat2 - lat1)
                dlon = radians(lon2 - lon1)
                a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                distance = R * c

                # Get all spaces in this building
                cur.execute("""
                    SELECT space_id, name, grid_width, grid_height, total_capacity
                    FROM Space
                    WHERE building_id = %s
                    ORDER BY name
                """, (building['building_id'],))
                spaces = cur.fetchall()

                for space in spaces:
                    # Get all desks for this space with their status
                    cur.execute("""
                        SELECT desk_id, name, grid_x, grid_y, capacity
                        FROM Desks
                        WHERE space_id = %s AND is_active = TRUE
                        ORDER BY desk_id
                    """, (space['space_id'],))
                    desks = cur.fetchall()

                    # Get occupancy status for each desk
                    desk_statuses = {}
                    for desk in desks:
                        status = get_latest_desk_status(desk['desk_id'], 30)
                        desk_statuses[(desk['grid_x'], desk['grid_y'])] = {
                            'desk_id': desk['desk_id'],
                            'name': desk['name'],
                            'occupied': status['occupied'],
                            'capacity': desk['capacity']
                        }

                    # Find available adjacent seats for the group
                    if group_size == 1:
                        # Single person - just find any available desk
                        available = [d for d in desk_statuses.values() if not d['occupied']]
                        if available:
                            match = {
                                'building_id': building['building_id'],
                                'building_name': building['name'],
                                'building_address': building['address'],
                                'space_id': space['space_id'],
                                'space_name': space['name'],
                                'distance_km': round(distance, 2),
                                'available_seats': len(available),
                                'recommended_desks': [available[0]['name']],
                                'desk_ids': [available[0]['desk_id']]
                            }
                            if distance < best_distance:
                                best_distance = distance
                                best_match = match
                    else:
                        # Group - find adjacent available seats using BFS
                        available_positions = {pos for pos, desk in desk_statuses.items() if not desk['occupied']}

                        def find_adjacent_group(positions, size):
                            """Find a group of adjacent positions using BFS"""
                            for start_pos in positions:
                                visited = {start_pos}
                                queue = [start_pos]

                                while queue and len(visited) < size:
                                    x, y = queue.pop(0)
                                    # Check all 4 adjacent positions
                                    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                                        new_pos = (x + dx, y + dy)
                                        if new_pos in positions and new_pos not in visited:
                                            visited.add(new_pos)
                                            queue.append(new_pos)

                                if len(visited) >= size:
                                    return visited
                            return None

                        adjacent_group = find_adjacent_group(available_positions, group_size)

                        if adjacent_group:
                            desk_names = [desk_statuses[pos]['name'] for pos in adjacent_group]
                            desk_ids = [desk_statuses[pos]['desk_id'] for pos in adjacent_group]
                            match = {
                                'building_id': building['building_id'],
                                'building_name': building['name'],
                                'building_address': building['address'],
                                'space_id': space['space_id'],
                                'space_name': space['name'],
                                'distance_km': round(distance, 2),
                                'available_seats': len(available_positions),
                                'recommended_desks': sorted(desk_names)[:group_size],
                                'desk_ids': sorted(desk_ids)[:group_size]
                            }
                            if distance < best_distance:
                                best_distance = distance
                                best_match = match

            if best_match:
                return jsonify(best_match)
            else:
                return jsonify({'error': f'No available space found for group size {group_size}'}), 404

        finally:
            cur.close()
    finally:
        db.close()


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')