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
    'password': ''  # Update with actual password
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
    """Return all desks for a space with their current occupancy status"""
    lookback = int(request.args.get('lookback', 30))  # seconds to look back

    db = OccupancyDatabase(**DB_CONFIG)
    try:
        # Get all desks for this space
        cur = db.conn.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT desk_id, name, capacity, is_active
                FROM Desks
                WHERE space_id = %s AND is_active = TRUE
                ORDER BY desk_id
            """, (space_id,))
            desks = cur.fetchall()
        finally:
            cur.close()

        # Get occupancy status for each table
        result = []
        for desk in desks:
            status = get_latest_desk_status(desk['desk_id'], lookback)
            result.append({
                'desk_id': desk['desk_id'],
                'name': desk['name'],
                'capacity': desk['capacity'],
                'occupied': status['occupied'],
                'confidence': status['confidence'],
                'last_updated': status['last_updated'],
                'sample_count': status['sample_count']
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


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')