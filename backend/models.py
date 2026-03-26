"""Data models used across the monitoring pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass
class TelemetrySnapshot:
    timestamp: datetime
    values: Dict[str, float]
    control_state: Dict[str, float] = field(default_factory=dict)
    source_records: Dict[str, str] = field(default_factory=dict)
    anomaly_mode: str = "normal"


@dataclass
class DetectionResult:
    severity: str
    anomalies: List[str] = field(default_factory=list)
    fault_probability: float = 0.0
    evidence: List[str] = field(default_factory=list)
    triggered_interlocks: List[str] = field(default_factory=list)


@dataclass
class DiagnosisResult:
    summary: str
    likely_causes: List[str]
    recommended_actions: List[str]
    recommended_commands: Dict[str, float] = field(default_factory=dict)


@dataclass
class GuardrailResult:
    safe: bool
    approved_actions: List[str]
    blocked_actions: List[str]
    notes: List[str]
    enforced_commands: Dict[str, float] = field(default_factory=dict)
    blocked_commands: Dict[str, float] = field(default_factory=dict)


@dataclass
class PipelineResult:
    snapshot: TelemetrySnapshot
    detection: DetectionResult
    diagnosis: DiagnosisResult
    guardrail: GuardrailResult
    llm_summary: str
    llm_status: str = "disabled"
