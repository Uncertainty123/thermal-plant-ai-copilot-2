"""Safety guardrails to block unsafe or contradictory actions."""

from __future__ import annotations

from backend.models import DiagnosisResult, GuardrailResult, TelemetrySnapshot


class GuardrailAgent:
    BLOCKED_PATTERNS = (
        "increase firing",
        "raise load",
        "ignore",
        "bypass",
        "disable trip",
    )

    def validate(self, snapshot: TelemetrySnapshot, diagnosis: DiagnosisResult) -> GuardrailResult:
        approved: list[str] = []
        blocked: list[str] = []
        notes: list[str] = []
        enforced_commands: dict[str, float] = {}
        blocked_commands: dict[str, float] = {}

        for action in diagnosis.recommended_actions:
            lower = action.lower()
            if any(pattern in lower for pattern in self.BLOCKED_PATTERNS):
                blocked.append(action)
                continue

            if snapshot.values["SH_TEMP"] >= 545 and "reduce firing rate" not in lower:
                blocked.append(action)
                notes.append("Only load reduction and cooling actions are allowed during SH overtemperature trip condition.")
                continue

            if abs(snapshot.values["DRUM_LEVEL"]) >= 250 and "restore feedwater" not in lower and "control feedwater" not in lower and "reduce boiler load" not in lower:
                blocked.append(action)
                notes.append("Drum level protection boundary reached. Only level-stabilizing actions are permitted.")
                continue

            approved.append(action)

        for command, value in diagnosis.recommended_commands.items():
            enforced_commands[command] = value

        if snapshot.values["SH_TEMP"] >= 545:
            enforced_commands["COAL_FEED_CMD"] = 0.0
            enforced_commands["MASTER_FUEL_TRIP"] = 1.0
            notes.append("SH temperature crossed the critical limit; coal feed is blocked and master fuel trip is asserted.")

        if abs(snapshot.values["DRUM_LEVEL"]) >= 250:
            enforced_commands["MASTER_FUEL_TRIP"] = 1.0
            enforced_commands["COAL_FEED_CMD"] = 0.0
            notes.append("Drum level crossed the protection band; only trip-safe commands are allowed.")

        if snapshot.values["FURNACE_O2"] < 2.0 and snapshot.values["FURNACE_TEMP"] > 1200:
            blocked_commands["COAL_FEED_CMD"] = diagnosis.recommended_commands.get("COAL_FEED_CMD", snapshot.control_state.get("COAL_FEED_CMD", 0.0))
            enforced_commands["COAL_FEED_CMD"] = 0.0
            notes.append("Combustion is too rich for any load increase; fuel demand is clamped to zero.")

        if not approved:
            approved.append("Place unit in a safe stabilized state and follow plant SOP/trip logic immediately")

        if not notes:
            notes.append("Guardrail check passed. Actions are limited to conservative operating responses.")

        return GuardrailResult(
            safe=len(blocked) == 0,
            approved_actions=approved,
            blocked_actions=blocked,
            notes=list(dict.fromkeys(notes)),
            enforced_commands=enforced_commands,
            blocked_commands=blocked_commands,
        )
