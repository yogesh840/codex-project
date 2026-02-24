"""Policy execution module."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from src.storage.db import Database


class PolicyEngine:
    def __init__(self, db: Database, policy_file: str = "policies.yaml") -> None:
        self.db = db
        self.policy_file = policy_file
        self.policies = self._load(policy_file)

    def _load(self, path: str) -> dict[str, Any]:
        p = Path(path)
        if not p.exists():
            return {"rules": []}
        if p.suffix.lower() == ".json":
            return json.loads(p.read_text())
        return yaml.safe_load(p.read_text()) or {"rules": []}

    def evaluate(self, context: dict[str, Any]) -> list[str]:
        fired = []
        for rule in self.policies.get("rules", []):
            cond = rule.get("condition", "False")
            try:
                if bool(eval(cond, {}, context)):
                    for action in rule.get("actions", []):
                        self._run_action(action, context)
                    fired.append(rule.get("name", "unnamed"))
            except Exception as exc:
                self._run_action("log_event", {**context, "explanation": f"policy eval error: {exc}"})
        return fired

    def _run_action(self, action: str, context: dict[str, Any]) -> None:
        if action == "show_alert":
            # UI polls recent risk events, so persisting event doubles as alert transport.
            pass
        elif action == "log_event":
            self.db.log_risk(context["risk_record"])
        elif action == "lock_screen":
            # Future OS-specific behavior (currently stubbed).
            self.db.log_risk(context["risk_record"])
        elif action == "block_device":
            self.db.log_risk(context["risk_record"])
