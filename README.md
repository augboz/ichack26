# LibSpace — real-time library occupancy

Built at **IC Hack 2026**. LibSpace estimates how many seats are free in a
university library in real time using computer vision on camera feeds, and
surfaces it in a live dashboard so students can find space without walking
floor to floor.

<!-- Add a screenshot or GIF here, e.g. ![dashboard](docs/dashboard.png) -->

## How it works
- **Detection** — a Faster R-CNN (Inception v2, COCO) model detects people and
  desks in each frame to decide which seats are occupied.
- **Occupancy pipeline** — detections are aggregated into per-zone occupancy and
  written to a SQL store, with heatmaps and trends over time.
- **Dashboard** — a React frontend reads the live data and shows free vs. busy
  space at a glance.

## Stack
- **Computer vision / backend:** Python, OpenCV, TensorFlow (Faster R-CNN
  Inception v2), SQL
- **Frontend:** Vite + React + TypeScript + shadcn/ui (Tailwind)

## Layout
- `backend/` — detection, occupancy generation, database, API
- `frontend/` — the live dashboard

> Hackathon project — built over the IC Hack 2026 weekend.
