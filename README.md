# HID Guardian

HID Guardian is a minimal desktop security application that monitors keyboard, cursor, and USB HID behavior, then computes a per-session risk score.

## Features
- FastAPI backend with local HTML dashboard
- User registration with baseline capture tasks
- Real-time keystroke and cursor feature extraction
- USB HID monitoring abstraction (Windows-ready, Linux fallback)
- Anomaly models (Isolation Forest + Logistic Regression)
- Weighted risk scoring with explanations
- Policy engine for alerting/logging actions
- SQLite storage and replay endpoints

## Project layout
```
main.py
policies.yaml
requirements.txt
src/
  sensors/
  features/
  models/
  risk/
  response/
  storage/
  ui/
```

## Install
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Run (development)
```bash
python main.py
```
The server starts on `http://127.0.0.1:8000`.

## Simulate a high-risk event
In a second terminal:
```bash
python -m src.models.simulate_attack --mode robotic --count 80
```
Then refresh the dashboard or call:
```bash
curl http://127.0.0.1:8000/risk/current
```

## Notes
- Global input capture with `pynput` may require permissions depending on OS.
- USB monitoring is implemented with a portable interface and a polling fallback. Windows-specific enhancements are marked in code.
