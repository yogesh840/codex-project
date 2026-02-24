"""Feature engineering for keystroke and cursor windows."""
from __future__ import annotations

import math
from collections import Counter
from statistics import mean, pstdev


def _safe_stats(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    return float(mean(values)), float(pstdev(values)) if len(values) > 1 else 0.0


def keystroke_features(events: list[dict]) -> dict[str, float]:
    if len(events) < 2:
        return {k: 0.0 for k in ["dwell_mean", "dwell_std", "flight_mean", "flight_std", "typing_speed", "digraph_entropy"]}

    ordered = sorted(events, key=lambda e: e["pressed_at"])
    dwell = [max(0.0, e["released_at"] - e["pressed_at"]) for e in ordered]
    flight = [max(0.0, ordered[i]["pressed_at"] - ordered[i - 1]["released_at"]) for i in range(1, len(ordered))]
    total_t = max(ordered[-1]["released_at"] - ordered[0]["pressed_at"], 1e-6)
    speed = len(ordered) / total_t

    digraphs = [f"{ordered[i-1]['key']}>{ordered[i]['key']}" for i in range(1, len(ordered))]
    cnt = Counter(digraphs)
    probs = [c / len(digraphs) for c in cnt.values()] if digraphs else [1.0]
    entropy = -sum(p * math.log(p + 1e-9) for p in probs)

    dwell_m, dwell_s = _safe_stats(dwell)
    flight_m, flight_s = _safe_stats(flight)
    return {
        "dwell_mean": dwell_m,
        "dwell_std": dwell_s,
        "flight_mean": flight_m,
        "flight_std": flight_s,
        "typing_speed": speed,
        "digraph_entropy": entropy,
    }


def cursor_features(events: list[dict]) -> dict[str, float]:
    moves = [e for e in events if e.get("event_type") == "move"]
    clicks = [e for e in events if e.get("event_type") == "click"]
    if len(moves) < 3:
        return {k: 0.0 for k in ["velocity_mean", "velocity_std", "accel_mean", "direction_changes", "click_rate", "click_regularity"]}

    velocities = []
    directions = []
    for i in range(1, len(moves)):
        dx = moves[i]["x"] - moves[i - 1]["x"]
        dy = moves[i]["y"] - moves[i - 1]["y"]
        dt = max(moves[i]["timestamp"] - moves[i - 1]["timestamp"], 1e-6)
        velocities.append((dx**2 + dy**2) ** 0.5 / dt)
        directions.append(math.atan2(dy, dx))

    accels = [abs(velocities[i] - velocities[i - 1]) for i in range(1, len(velocities))]
    dir_changes = 0
    for i in range(1, len(directions)):
        if abs(directions[i] - directions[i - 1]) > 0.8:
            dir_changes += 1

    click_times = [c["timestamp"] for c in clicks]
    click_intervals = [click_times[i] - click_times[i - 1] for i in range(1, len(click_times))]
    v_m, v_s = _safe_stats(velocities)
    a_m, _ = _safe_stats(accels)
    c_m, c_s = _safe_stats(click_intervals)
    duration = max(moves[-1]["timestamp"] - moves[0]["timestamp"], 1e-6)

    return {
        "velocity_mean": v_m,
        "velocity_std": v_s,
        "accel_mean": a_m,
        "direction_changes": float(dir_changes) / max(duration, 1e-6),
        "click_rate": len(clicks) / duration,
        "click_regularity": 0.0 if c_m == 0 else c_s / c_m,
    }
