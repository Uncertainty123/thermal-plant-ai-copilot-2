"""Physics-based reasoning layer."""

from __future__ import annotations

from backend.models import DetectionResult, DiagnosisResult, TelemetrySnapshot


class ReasonerAgent:
    def diagnose(self, snapshot: TelemetrySnapshot, detection: DetectionResult) -> DiagnosisResult:
        values = snapshot.values
        causes: list[str] = []
        actions: list[str] = []
        commands: dict[str, float] = {}

        if values["BFP_FLOW"] < 840:
            causes.append("Boiler Feed Pump flow is insufficient for current steam-side demand")
            actions.append("Inspect BFP suction/discharge conditions and verify recirculation valve position")
            commands["BFP_RECIRC_VALVE_CMD"] = min(100.0, snapshot.control_state.get("BFP_RECIRC_VALVE_CMD", 20.0) + 10.0)

        if values["SH_TEMP"] > 538:
            causes.append("Superheater outlet temperature is approaching or exceeding metallurgical limit")
            actions.append("Reduce firing rate or increase spray attemperation within operating procedure")
            commands["SH_SPRAY_WATER_CMD"] = min(100.0, snapshot.control_state.get("SH_SPRAY_WATER_CMD", 25.0) + 12.0)
            commands["COAL_FEED_CMD"] = max(0.0, snapshot.control_state.get("COAL_FEED_CMD", 70.0) - 15.0)

        if values["SH_PRESS"] > 180:
            causes.append("Superheater pressure indicates steam-side restriction or excess heat input")
            actions.append("Check downstream steam path restrictions and confirm coordinated boiler-turbine control response")

        if values["SH_PRESS"] < 165 and values["BFP_FLOW"] < 850:
            causes.append("Feedwater deficiency is causing steam generation instability and reduced SH pressure")
            actions.append("Stabilize feedwater flow before demanding additional load")

        if values["DRUM_LEVEL"] > 200:
            causes.append("Drum swell can produce moisture carryover to superheater sections")
            actions.append("Control feedwater and firing mismatch; avoid abrupt manual corrections")
            commands["FEEDWATER_CV_CMD"] = max(15.0, snapshot.control_state.get("FEEDWATER_CV_CMD", 50.0) - 10.0)
        elif values["DRUM_LEVEL"] < -200:
            causes.append("Low drum level risks tube exposure and circulation upset")
            actions.append("Reduce boiler load and restore feedwater inventory promptly")
            commands["FEEDWATER_CV_CMD"] = min(100.0, snapshot.control_state.get("FEEDWATER_CV_CMD", 50.0) + 15.0)
            commands["COAL_FEED_CMD"] = max(0.0, snapshot.control_state.get("COAL_FEED_CMD", 70.0) - 20.0)

        if values["FURNACE_O2"] < 2.5:
            causes.append("Low furnace oxygen suggests incomplete combustion and localized overheating risk")
            actions.append("Verify air-fuel ratio and draft controls while holding or reducing firing demand")
            commands["COAL_FEED_CMD"] = max(0.0, min(commands.get("COAL_FEED_CMD", snapshot.control_state.get("COAL_FEED_CMD", 70.0)), snapshot.control_state.get("COAL_FEED_CMD", 70.0) - 10.0))

        if not causes:
            causes.append("All monitored auxiliaries are operating within expected thermal and hydraulic envelopes")
            actions.append("Continue monitoring and maintain present operating conditions")

        if detection.severity == "critical":
            summary = "Critical auxiliary upset detected. Protective intervention may be required."
        elif detection.severity == "warning":
            summary = "Abnormal thermal or hydraulic trend detected. Corrective action is recommended."
        else:
            summary = "Plant auxiliaries are stable."

        return DiagnosisResult(
            summary=summary,
            likely_causes=list(dict.fromkeys(causes)),
            recommended_actions=list(dict.fromkeys(actions)),
            recommended_commands=commands,
        )
