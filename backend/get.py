from flask import Flask, jsonify
from flask_cors import CORS
from table_id import TableStatusTracker
import threading, time, random
from collections import defaultdict


app = Flask(__name__)
CORS(app)
tracker = TableStatusTracker()
TARGET_FREE = 15          # hover around 15 free
TICK_SECONDS = 1.0        # update every second
WIGGLE = 3                # allow +-3 free naturally

# shared state: seat_id -> occupied (True/False)
seat_state = {}

def init_state():
    # start near target free
    total = len(SEATS)
    target_occupied = max(0, min(total, total - TARGET_FREE))
    ids = [s["id"] for s in SEATS]
    occupied_ids = set(random.sample(ids, k=target_occupied))
    for sid in ids:
      seat_state[sid] = (sid in occupied_ids)

def simulator_loop():
    init_state()
    ids = [s["id"] for s in SEATS]

    while True:
        total = len(ids)
        free = sum(1 for sid in ids if not seat_state[sid])

        # small random noise: flip 1 seat sometimes
        if random.random() < 0.35:
            sid = random.choice(ids)
            seat_state[sid] = not seat_state[sid]

        # bias toward target band [TARGET_FREE-WIGGLE, TARGET_FREE+WIGGLE]
        free = sum(1 for sid in ids if not seat_state[sid])
        low = TARGET_FREE - WIGGLE
        high = TARGET_FREE + WIGGLE

        if free < low:
            # too full: free up 1-3 occupied seats
            occ_ids = [sid for sid in ids if seat_state[sid]]
            for sid in random.sample(occ_ids, k=min(len(occ_ids), random.randint(1, 3))):
                seat_state[sid] = False

        elif free > high:
            # too empty: occupy 1-3 free seats
            free_ids = [sid for sid in ids if not seat_state[sid]]
            for sid in random.sample(free_ids, k=min(len(free_ids), random.randint(1, 3))):
                seat_state[sid] = True

        time.sleep(TICK_SECONDS)


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

from flask import Flask, jsonify
from flask_cors import CORS
from table_id import TableStatusTracker
from collections import defaultdict

app = Flask(__name__)
CORS(app)
tracker = TableStatusTracker()

SEATS = [
  # Tables 1–4
  {"id": "T1-1", "x": 8,  "y": 20, "zone": "Tables 1–4"},
  {"id": "T1-2", "x": 14, "y": 20, "zone": "Tables 1–4"},
  {"id": "T1-3", "x": 8,  "y": 28, "zone": "Tables 1–4"},
  {"id": "T1-4", "x": 14, "y": 28, "zone": "Tables 1–4"},
  {"id": "T2-1", "x": 8,  "y": 40, "zone": "Tables 1–4"},
  {"id": "T2-2", "x": 14, "y": 40, "zone": "Tables 1–4"},
  {"id": "T2-3", "x": 8,  "y": 48, "zone": "Tables 1–4"},
  {"id": "T2-4", "x": 14, "y": 48, "zone": "Tables 1–4"},
  {"id": "T3-1", "x": 8,  "y": 60, "zone": "Tables 1–4"},
  {"id": "T3-2", "x": 14, "y": 60, "zone": "Tables 1–4"},
  {"id": "T3-3", "x": 8,  "y": 68, "zone": "Tables 1–4"},
  {"id": "T3-4", "x": 14, "y": 68, "zone": "Tables 1–4"},

  # Quiet Row
  {"id": "Q1",  "x": 38, "y": 20, "zone": "Quiet Row"},
  {"id": "Q2",  "x": 44, "y": 20, "zone": "Quiet Row"},
  {"id": "Q3",  "x": 50, "y": 20, "zone": "Quiet Row"},
  {"id": "Q4",  "x": 56, "y": 20, "zone": "Quiet Row"},
  {"id": "Q5",  "x": 62, "y": 20, "zone": "Quiet Row"},
  {"id": "Q6",  "x": 38, "y": 28, "zone": "Quiet Row"},
  {"id": "Q7",  "x": 44, "y": 28, "zone": "Quiet Row"},
  {"id": "Q8",  "x": 50, "y": 28, "zone": "Quiet Row"},
  {"id": "Q9",  "x": 56, "y": 28, "zone": "Quiet Row"},
  {"id": "Q10", "x": 62, "y": 28, "zone": "Quiet Row"},

  # Window Seats
  {"id": "W1", "x": 82, "y": 20, "zone": "Window Seats"},
  {"id": "W2", "x": 88, "y": 20, "zone": "Window Seats"},
  {"id": "W3", "x": 82, "y": 32, "zone": "Window Seats"},
  {"id": "W4", "x": 88, "y": 32, "zone": "Window Seats"},
  {"id": "W5", "x": 82, "y": 44, "zone": "Window Seats"},
  {"id": "W6", "x": 88, "y": 44, "zone": "Window Seats"},
  {"id": "W7", "x": 82, "y": 56, "zone": "Window Seats"},
  {"id": "W8", "x": 88, "y": 56, "zone": "Window Seats"},
]

def zone_state(free, cap):
    r = free / max(cap, 1)
    if r > 0.4: return "green"
    if r > 0.15: return "yellow"
    return "red"

@app.route("/status", methods=["GET"])
def status():
    zones = defaultdict(lambda: {"free": 0, "capacity": 0})

    seats_out = []
    for s in SEATS:
        sid = s["id"]
        occupied = bool(seat_state.get(sid, False))
        seats_out.append({**s, "occupied": occupied})

        zones[s["zone"]]["capacity"] += 1
        if not occupied:
            zones[s["zone"]]["free"] += 1

    zones_out = []
    total_free = 0
    total_capacity = 0
    for name, z in zones.items():
        total_free += z["free"]
        total_capacity += z["capacity"]
        zones_out.append({
            "id": name.replace(" ", "_"),
            "name": name,
            "free": z["free"],
            "capacity": z["capacity"],
            "state": zone_state(z["free"], z["capacity"]),
        })

    return jsonify({
        "updated_at": time.time(),
        "total_free": total_free,
        "total_capacity": total_capacity,
        "zones": zones_out,
        "seats": seats_out
    })

if __name__ == "__main__":
    threading.Thread(target=simulator_loop, daemon=True).start()
    app.run(debug=True, port=5000)
