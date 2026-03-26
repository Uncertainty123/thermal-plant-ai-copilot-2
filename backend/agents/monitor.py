"""Rule-based anomaly monitor."""

from __future__ import annotations

from typing import List

from backend.config import PLANT_CONFIG
from backend.models import DetectionResult, TelemetrySnapshot


class MonitorAgent:
    def evaluate(self, snapshot: TelemetrySnapshot) -> DetectionResult:
        anomalies: List[str] = []
        evidence: List[str] = []
        triggered_interlocks: List[str] = []
        risk_points = 0.0

        for tag, value in snapshot.values.items():
            constraint = PLANT_CONFIG.tags[tag]
            if constraint.trip_high is not None and value > constraint.trip_high:
                anomalies.append(f"{tag} trip-high breach")
                evidence.append(f"{tag}={value} {constraint.unit} above trip limit {constraint.trip_high}")
                risk_points += 0.45
            elif constraint.trip_low is not None and value < constraint.trip_low:
                anomalies.append(f"{tag} trip-low breach")
                evidence.append(f"{tag}={value} {constraint.unit} below trip limit {constraint.trip_low}")
                risk_points += 0.45
            elif constraint.warn_high is not None and value > constraint.warn_high:
                anomalies.append(f"{tag} high warning")
                evidence.append(f"{tag}={value} {constraint.unit} above warning band {constraint.warn_high}")
                risk_points += 0.22
            elif constraint.warn_low is not None and value < constraint.warn_low:
                anomalies.append(f"{tag} low warning")
                evidence.append(f"{tag}={value} {constraint.unit} below warning band {constraint.warn_low}")
                risk_points += 0.22

        if snapshot.values["BFP_FLOW"] < 840 and snapshot.values["SH_PRESS"] < 165:
            anomalies.append("Feedwater starvation pattern")
            evidence.append("Low BFP flow is dragging SH pressure toward an attemperation risk region")
            risk_points += 0.18

        if snapshot.values["STEAM_FLOW"] > 540 and snapshot.values["BFP_FLOW"] < 860:
            anomalies.append("Steam-feedwater mass imbalance")
            evidence.append("Steam flow is high while BFP flow is low, indicating drum inventory depletion risk")
            risk_points += 0.18

        if snapshot.values["SH_TEMP"] > 540 and snapshot.values["FURNACE_TEMP"] > 1180:
            anomalies.append("Superheater heat absorption imbalance")
            evidence.append("High furnace temperature and SH outlet temperature indicate overheating risk")
            risk_points += 0.2

        if abs(snapshot.values["DRUM_LEVEL"]) > 220:
            anomalies.append("Drum level excursion")
            evidence.append("Drum level is near protection boundary and may trigger carryover or starvation")
            risk_points += 0.22

        if snapshot.values["FURNACE_O2"] < 2.5 and snapshot.values["FURNACE_TEMP"] > 1180:
            anomalies.append("Combustion instability")
            evidence.append("Low furnace O2 with elevated furnace temperature indicates rich combustion and slagging risk")
            risk_points += 0.18

        if snapshot.values["SH_TEMP"] >= 545:
            triggered_interlocks.append("SH overtemperature coal block")
        if abs(snapshot.values["DRUM_LEVEL"]) >= 250:
            triggered_interlocks.append("Drum level protection trip")
        if snapshot.values["FURNACE_TEMP"] >= 1245:
            triggered_interlocks.append("Furnace high temperature master fuel trip")

        fault_probability = max(0.0, min(0.99, round(risk_points, 2)))
        severity = "normal"
        if fault_probability >= 0.75:
            severity = "critical"
        elif fault_probability >= 0.4:
            severity = "warning"

        return DetectionResult(
            severity=severity,
            anomalies=sorted(set(anomalies)),
            fault_probability=fault_probability,
            evidence=evidence,
            triggered_interlocks=triggered_interlocks,
        )
