from flask import Flask, jsonify
from flask_cors import CORS
from table_id import TableStatusTracker

app = Flask(__name__)
CORS(app)
tracker = TableStatusTracker()

@app.route('/api/tables', methods=['GET'])
def get_table_statuses():
    """Return current status of all tables"""
    return jsonify(tracker.status)

@app.route('/api/tables/<int:table_id>', methods=['GET'])
def get_table_status(table_id):
    """Return status of a specific table"""
    if table_id in tracker.status:
        return jsonify({
            'table_id': table_id,
            'occupied': tracker.status[table_id]
        })
    return jsonify({'error': 'Table not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)