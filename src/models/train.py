"""Model training helpers for HID Guardian."""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier


class KeystrokeModels:
    def __init__(self) -> None:
        self.iso = IsolationForest(contamination=0.12, random_state=42)
        self.sup = RandomForestClassifier(n_estimators=80, random_state=42)
        self.feature_order = ["dwell_mean", "dwell_std", "flight_mean", "flight_std", "typing_speed", "digraph_entropy"]
        self._fitted = False

    def fit(self, normal_rows: list[dict]) -> None:
        x_normal = np.array([[row[k] for k in self.feature_order] for row in normal_rows])
        anomalies = self._synthetic_anomalies(len(normal_rows))

        self.iso.fit(x_normal)
        x_sup = np.vstack([x_normal, anomalies])
        y_sup = np.array([0] * len(x_normal) + [1] * len(anomalies))
        self.sup.fit(x_sup, y_sup)
        self._fitted = True

    def _synthetic_anomalies(self, n: int) -> np.ndarray:
        # Simulate robotic typing: tiny variance, very high speed.
        base = np.zeros((n, len(self.feature_order)))
        base[:, 0] = np.random.uniform(0.02, 0.04, size=n)
        base[:, 1] = np.random.uniform(0.0001, 0.003, size=n)
        base[:, 2] = np.random.uniform(0.005, 0.03, size=n)
        base[:, 3] = np.random.uniform(0.0001, 0.002, size=n)
        base[:, 4] = np.random.uniform(14, 30, size=n)
        base[:, 5] = np.random.uniform(0.01, 0.2, size=n)
        return base


class CursorModel:
    def __init__(self) -> None:
        self.iso = IsolationForest(contamination=0.1, random_state=42)
        self.feature_order = ["velocity_mean", "velocity_std", "accel_mean", "direction_changes", "click_rate", "click_regularity"]
        self._fitted = False

    def fit(self, normal_rows: list[dict]) -> None:
        x = np.array([[row[k] for k in self.feature_order] for row in normal_rows])
        self.iso.fit(x)
        self._fitted = True
