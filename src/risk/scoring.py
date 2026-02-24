"""Risk correlation and explanation generation."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskResult:
    score: float
    level: str
    explanation: str


class RiskScorer:
    def __init__(self, w_k: float = 0.45, w_c: float = 0.35, w_d: float = 0.20) -> None:
        self.w_k = w_k
        self.w_c = w_c
        self.w_d = w_d

    def combine(self, keystroke_score: float, cursor_score: float, device_score: float) -> RiskResult:
        score = self.w_k * keystroke_score + self.w_c * cursor_score + self.w_d * device_score
        level = "Low" if score < 0.3 else "Medium" if score < 0.7 else "High"

        reasons = []
        if keystroke_score > 0.7:
            reasons.append("high keystroke anomaly")
        if cursor_score > 0.7:
            reasons.append("high cursor anomaly")
        if device_score > 0.3:
            reasons.append("new/untrusted HID device")
        explanation = " and ".join(reasons) if reasons else "behavior within baseline"

        return RiskResult(score=round(score, 3), level=level, explanation=explanation)
