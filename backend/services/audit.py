"""Audit trail utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from backend.models import PipelineResult


class AuditLogger:
    def __init__(self, path: str = "logs/audit_log.jsonl") -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, result: PipelineResult) -> None:
        record: Dict[str, Any] = {
            "timestamp": result.snapshot.timestamp.isoformat(),
            "mode": result.snapshot.anomaly_mode,
            "values": result.snapshot.values,
            "severity": result.detection.severity,
            "fault_probability": result.detection.fault_probability,
            "anomalies": result.detection.anomalies,
            "evidence": result.detection.evidence,
            "interlocks": result.detection.triggered_interlocks,
            "summary": result.diagnosis.summary,
            "causes": result.diagnosis.likely_causes,
            "approved_actions": result.guardrail.approved_actions,
            "blocked_actions": result.guardrail.blocked_actions,
            "enforced_commands": result.guardrail.enforced_commands,
            "blocked_commands": result.guardrail.blocked_commands,
            "guardrail_notes": result.guardrail.notes,
            "llm_summary": result.llm_summary,
            "llm_status": result.llm_status,
        }
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

    @property
    def path(self) -> Path:
        return self._path
