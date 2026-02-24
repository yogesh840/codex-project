# HID Guardian

HID Guardian is a minimal desktop security app that monitors keyboard behavior, cursor behavior, and USB HID device activity, then computes a per-session risk score.

## What you get
- FastAPI backend + local dashboard (HTML/Bootstrap)
- Baseline registration (typing + mouse capture)
- Real-time risk scoring from:
  - keystroke anomaly score
  - cursor anomaly score
  - USB device risk contribution
- SQLite persistence for baselines, sensor events, device events, and risk alerts
- Replay endpoint for time-range event/risk review
- Policy engine via `policies.yaml`

## Project layout
```text
main.py
policies.yaml
requirements.txt
scripts/
  check_env.py
src/
  sensors/
  features/
  models/
  risk/
  response/
  storage/
  ui/
```

## Prerequisites
- Python **3.11+**
- OS: Windows first, but code remains portable for Linux/macOS

## Quick start (Windows PowerShell)
```powershell
cd <repo-path>
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/check_env.py
python main.py
```

## Quick start (Linux/macOS)
```bash
cd <repo-path>
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/check_env.py
python main.py
```

App URL: `http://127.0.0.1:8000`

## First-run flow
1. Open the dashboard in your browser.
2. Enter a username in **User Registration & Baseline Capture**.
3. Click **Capture Baseline**.
4. For ~15 seconds:
   - type `The quick brown fox jumps over the lazy dog` at least 3 times
   - move mouse and click randomly
5. Baseline stats are saved in SQLite.

## Useful endpoints
- `GET /risk/current` → current risk score/level/explanation
- `GET /alerts/recent` → recent risk alerts
- `GET /devices` → connected HID devices + recent device events
- `GET /replay?start_ts=<unix>&end_ts=<unix>` → historical events + risk timeline

## Simulate suspicious behavior
### Via dashboard
Click **Simulate Robotic Attack**.

### Via script
```bash
python -m src.models.simulate_attack --mode robotic --count 80
curl http://127.0.0.1:8000/risk/current
```

## Runtime configuration
You can override bind values without editing code:

```bash
export HID_GUARDIAN_HOST=0.0.0.0
export HID_GUARDIAN_PORT=8000
export HID_GUARDIAN_RELOAD=true
python main.py
```

Windows PowerShell:
```powershell
$env:HID_GUARDIAN_HOST = "0.0.0.0"
$env:HID_GUARDIAN_PORT = "8000"
$env:HID_GUARDIAN_RELOAD = "true"
python main.py
```

## Troubleshooting
- If `ModuleNotFoundError` appears, re-activate venv and run `pip install -r requirements.txt`.
- If global input capture seems empty, OS permissions may block `pynput`; run with elevated permissions and allow input monitoring.
- USB monitoring currently uses a portable polling stub with a Windows integration hook in `src/sensors/usb.py`.

## Notes
- The policy engine is configured in `policies.yaml`.
- Actions like `lock_screen` / `block_device` are currently stubs for future OS-specific implementation.
