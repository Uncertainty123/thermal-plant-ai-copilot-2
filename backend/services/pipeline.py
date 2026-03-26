"""Orchestrates simulator and agents into a single monitoring loop."""

from __future__ import annotations

from typing import List

from backend.agents.guardrail import GuardrailAgent
from backend.agents.llm import OptionalLLMAgent
from backend.agents.monitor import MonitorAgent
from backend.agents.reasoner import ReasonerAgent
from backend.models import PipelineResult, TelemetrySnapshot
from backend.services.audit import AuditLogger
from backend.simulator import TelemetrySimulator


class PlantMonitoringSystem:
    def __init__(self) -> None:
        self.simulator = TelemetrySimulator()
        self.monitor = MonitorAgent()
        self.reasoner = ReasonerAgent()
        self.guardrail = GuardrailAgent()
        self.llm_agent = OptionalLLMAgent()
        self.audit_logger = AuditLogger()

    def run_cycle(self) -> PipelineResult:
        snapshot = self.simulator.generate_snapshot()
        detection = self.monitor.evaluate(snapshot)
        diagnosis = self.reasoner.diagnose(snapshot, detection)
        guardrail = self.guardrail.validate(snapshot, diagnosis)
        llm_summary, llm_status = self.llm_agent.summarize(snapshot, detection, diagnosis)

        result = PipelineResult(
            snapshot=snapshot,
            detection=detection,
            diagnosis=diagnosis,
            guardrail=guardrail,
            llm_summary=llm_summary,
            llm_status=llm_status,
        )
        self.audit_logger.log(result)
        return result

    def warmup(self, count: int = 30) -> List[TelemetrySnapshot]:
        snapshots: List[TelemetrySnapshot] = []
        for _ in range(count):
            snapshots.append(self.simulator.generate_snapshot())
        return snapshots

    def history(self) -> List[TelemetrySnapshot]:
        return self.simulator.get_history()
