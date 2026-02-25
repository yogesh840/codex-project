"""Inference wrappers to produce normalized anomaly scores (0..1)."""
from __future__ import annotations

import numpy as np

from src.models.train import CursorModel, KeystrokeModels


class InferenceEngine:
    def __init__(self, key_models: KeystrokeModels, cursor_model: CursorModel) -> None:
        self.key_models = key_models
        self.cursor_model = cursor_model

    @staticmethod
    def _scale(score: float, lo: float = -0.8, hi: float = 0.8) -> float:
        val = (score - lo) / (hi - lo)
        return float(min(1.0, max(0.0, 1 - val)))

    def keystroke_score(self, feat: dict[str, float]) -> float:
        x = np.array([[feat[k] for k in self.key_models.feature_order]])
        iso = self.key_models.iso.decision_function(x)[0]
        sup = self.key_models.sup.predict_proba(x)[0][1]
        return float(min(1.0, max(0.0, (self._scale(iso) + sup) / 2)))

    def cursor_score(self, feat: dict[str, float]) -> float:
        x = np.array([[feat[k] for k in self.cursor_model.feature_order]])
        iso = self.cursor_model.iso.decision_function(x)[0]
        return self._scale(iso)
