"""SQLite storage for HID Guardian."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class RiskRecord:
    username: str
    risk_score: float
    risk_level: str
    keystroke_score: float
    cursor_score: float
    device_score: float
    explanation: str


class Database:
    def __init__(self, path: str = "hid_guardian.db") -> None:
        self.path = Path(path)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS baselines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    baseline_type TEXT NOT NULL,
                    stats_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );
                CREATE TABLE IF NOT EXISTS device_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    action TEXT NOT NULL,
                    vid TEXT,
                    pid TEXT,
                    product TEXT,
                    device_class TEXT,
                    trusted INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS risk_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    username TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    risk_level TEXT NOT NULL,
                    keystroke_score REAL NOT NULL,
                    cursor_score REAL NOT NULL,
                    device_score REAL NOT NULL,
                    explanation TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sensor_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    sensor_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                """
            )

    def upsert_user(self, username: str) -> int:
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (username, created_at) VALUES (?, ?)",
                (username, now),
            )
            row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            return int(row["id"])

    def save_baseline(self, username: str, baseline_type: str, stats: dict[str, Any]) -> None:
        user_id = self.upsert_user(username)
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO baselines (user_id, baseline_type, stats_json, created_at) VALUES (?, ?, ?, ?)",
                (user_id, baseline_type, json.dumps(stats), now),
            )

    def log_device_event(self, event: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO device_events (ts, action, vid, pid, product, device_class, trusted)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(),
                    event.get("action", "unknown"),
                    event.get("vid"),
                    event.get("pid"),
                    event.get("product"),
                    event.get("class"),
                    int(event.get("trusted", False)),
                ),
            )

    def log_risk(self, record: RiskRecord) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO risk_events (ts, username, risk_score, risk_level, keystroke_score, cursor_score, device_score, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(),
                    record.username,
                    record.risk_score,
                    record.risk_level,
                    record.keystroke_score,
                    record.cursor_score,
                    record.device_score,
                    record.explanation,
                ),
            )

    def log_sensor_event(self, sensor_type: str, payload: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO sensor_events (ts, sensor_type, payload_json) VALUES (?, ?, ?)",
                (payload.get("timestamp", 0.0), sensor_type, json.dumps(payload)),
            )

    def recent_alerts(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT ts, username, risk_level, risk_score, explanation FROM risk_events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def recent_devices(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT ts, action, vid, pid, product, device_class, trusted FROM device_events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def replay(self, start_ts: float, end_ts: float) -> dict[str, Any]:
        with self.connect() as conn:
            sensor_rows = conn.execute(
                "SELECT ts, sensor_type, payload_json FROM sensor_events WHERE ts BETWEEN ? AND ? ORDER BY ts",
                (start_ts, end_ts),
            ).fetchall()
            risk_rows = conn.execute(
                "SELECT ts, risk_score, risk_level, explanation FROM risk_events WHERE ts BETWEEN datetime(?) AND datetime(?) ORDER BY ts",
                (datetime.fromtimestamp(start_ts).isoformat(), datetime.fromtimestamp(end_ts).isoformat()),
            ).fetchall()
        return {
            "sensor_events": [
                {"ts": r["ts"], "sensor_type": r["sensor_type"], "payload": json.loads(r["payload_json"])}
                for r in sensor_rows
            ],
            "risk_events": [dict(r) for r in risk_rows],
        }
