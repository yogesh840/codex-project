"""FastAPI server and runtime coordinator for HID Guardian."""
from __future__ import annotations

import threading
import time
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel

from src.features.engine import cursor_features, keystroke_features
from src.models.infer import InferenceEngine
from src.models.train import CursorModel, KeystrokeModels
from src.response.policy import PolicyEngine
from src.risk.scoring import RiskScorer
from src.sensors.cursor import CursorSensor
from src.sensors.keystroke import KeystrokeSensor
from src.sensors.usb import USBMonitor
from src.storage.db import Database, RiskRecord


class RegisterPayload(BaseModel):
    username: str
    keystrokes: list[dict]
    cursor_events: list[dict]


class Runtime:
    def __init__(self) -> None:
        self.db = Database()
        self.keystroke = KeystrokeSensor()
        self.cursor = CursorSensor()
        self.usb = USBMonitor()
        self.risk_scorer = RiskScorer()
        self.key_models = KeystrokeModels()
        self.cursor_model = CursorModel()
        self.infer: InferenceEngine | None = None
        self.policy = PolicyEngine(self.db)
        self.username = "anonymous"
        self.current = {"risk_score": 0.0, "risk_level": "Low", "explanation": "warming up"}
        self._running = False
        self._thread: threading.Thread | None = None

    def bootstrap_models(self) -> None:
        normal_key = [
            {"dwell_mean": 0.11, "dwell_std": 0.04, "flight_mean": 0.09, "flight_std": 0.04, "typing_speed": 6.0, "digraph_entropy": 2.8},
            {"dwell_mean": 0.12, "dwell_std": 0.03, "flight_mean": 0.1, "flight_std": 0.03, "typing_speed": 5.8, "digraph_entropy": 2.6},
            {"dwell_mean": 0.1, "dwell_std": 0.05, "flight_mean": 0.11, "flight_std": 0.04, "typing_speed": 6.3, "digraph_entropy": 2.7},
        ] * 15
        normal_cur = [
            {"velocity_mean": 620, "velocity_std": 230, "accel_mean": 170, "direction_changes": 1.5, "click_rate": 0.35, "click_regularity": 0.55},
            {"velocity_mean": 550, "velocity_std": 210, "accel_mean": 140, "direction_changes": 1.3, "click_rate": 0.25, "click_regularity": 0.60},
            {"velocity_mean": 710, "velocity_std": 260, "accel_mean": 190, "direction_changes": 1.7, "click_rate": 0.32, "click_regularity": 0.52},
        ] * 20
        self.key_models.fit(normal_key)
        self.cursor_model.fit(normal_cur)
        self.infer = InferenceEngine(self.key_models, self.cursor_model)

    def start(self) -> None:
        self.bootstrap_models()
        self.keystroke.start()
        self.cursor.start()
        self.usb.start()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        while self._running and self.infer:
            k_window = self.keystroke.get_window()
            c_window = self.cursor.get_window()
            for evt in k_window[-4:]:
                self.db.log_sensor_event("keystroke", {**evt, "timestamp": evt["released_at"]})
            for evt in c_window[-4:]:
                self.db.log_sensor_event("cursor", evt)

            k_feat = keystroke_features(k_window)
            c_feat = cursor_features(c_window)
            k_score = self.infer.keystroke_score(k_feat)
            c_score = self.infer.cursor_score(c_feat)

            device_events = self.usb.get_events()
            device_score = 0.0
            for dev_evt in device_events:
                self.db.log_device_event(dev_evt)
                if dev_evt["action"] == "connect" and not dev_evt["trusted"] and dev_evt["class"] == "HID":
                    device_score = max(device_score, 0.5)

            result = self.risk_scorer.combine(k_score, c_score, device_score)
            record = RiskRecord(
                username=self.username,
                risk_score=result.score,
                risk_level=result.level,
                keystroke_score=k_score,
                cursor_score=c_score,
                device_score=device_score,
                explanation=result.explanation,
            )
            self.current = {**asdict(record), "explanation": result.explanation}
            self.policy.evaluate({"risk_level": result.level, "risk_score": result.score, "risk_record": record})
            time.sleep(1.5)

    def register(self, username: str, ks_events: list[dict], cursor_events: list[dict]) -> dict:
        self.username = username
        ks = keystroke_features(ks_events)
        cs = cursor_features(cursor_events)
        self.db.save_baseline(username, "keystroke", ks)
        self.db.save_baseline(username, "cursor", cs)
        return {"status": "ok", "username": username, "keystroke_baseline": ks, "cursor_baseline": cs}


runtime = Runtime()
app = FastAPI(title="HID Guardian")
UI_DIR = Path(__file__).resolve().parent
STATIC_DIR = UI_DIR / "static"
TEMPLATES_DIR = UI_DIR / "templates"

# Ensure static path exists even on clones where empty directories were dropped.
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.on_event("startup")
def startup() -> None:
    runtime.start()


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/registration", response_class=HTMLResponse)
def registration(request: Request):
    return templates.TemplateResponse("registration.html", {"request": request})


@app.post("/register")
def register(payload: RegisterPayload):
    return runtime.register(payload.username, payload.keystrokes, payload.cursor_events)


@app.get("/risk/current")
def risk_current():
    return runtime.current


@app.get("/alerts/recent")
def alerts_recent(limit: int = 20):
    return runtime.db.recent_alerts(limit)


@app.get("/risk/history")
def risk_history(limit: int = 60):
    return runtime.db.risk_history(limit)


@app.get("/devices")
def devices():
    return {"connected": runtime.usb.get_connected(), "recent": runtime.db.recent_devices(20)}


@app.get("/replay")
def replay(start_ts: float, end_ts: float):
    return runtime.db.replay(start_ts, end_ts)


@app.post("/simulate/robot")
def simulate_robot():
    runtime.keystroke.simulate(robotic=True, count=80)
    runtime.cursor.simulate(robotic=True, count=120)
    runtime.usb.simulate_untrusted()
    return {"status": "simulated"}


@app.get("/alerts/export", response_class=PlainTextResponse)
def export_alerts(limit: int = 100):
    rows = runtime.db.recent_alerts(limit)
    output = ["ts,username,risk_score,risk_level,explanation"]
    for row in rows:
        explanation = str(row.get("explanation", "")).replace(",", " ")
        output.append(
            f"{row.get('ts', '')},{row.get('username', '')},{row.get('risk_score', 0)},"
            f"{row.get('risk_level', '')},{explanation}"
        )
    return "\n".join(output)
