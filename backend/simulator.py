"""Telemetry simulator with realistic operating envelopes and injected events."""

from __future__ import annotations

import math
import random
from collections import deque
from datetime import datetime
from typing import Deque, Dict, List

from backend.config import PLANT_CONFIG
from backend.models import TelemetrySnapshot
from backend.services.reference_data import ReferenceDataRepository


class TelemetrySimulator:
    """Generates pseudo-realistic telemetry for the plant auxiliaries."""

    def __init__(self, seed: int = 42, history_limit: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._step = 0
        self._history_limit = history_limit or PLANT_CONFIG.history_limit
        self._history: Deque[TelemetrySnapshot] = deque(maxlen=self._history_limit)
        self._reference_data = ReferenceDataRepository()
        seed_profiles = self._reference_data.load_seed_profiles()
        self._profiles = seed_profiles or {
            "normal": {
                "SH_TEMP": 534.0,
                "SH_PRESS": 171.5,
                "DRUM_LEVEL": 15.0,
                "BFP_FLOW": 930.0,
                "STEAM_FLOW": 505.0,
                "FURNACE_TEMP": 1120.0,
                "FURNACE_O2": 3.5,
                "FW_TEMP": 238.0,
            }
        }
        self._last_values = dict(self._profiles["normal"])

    def generate_snapshot(self) -> TelemetrySnapshot:
        self._step += 1
        mode = self._select_mode()
        profile = self._profiles.get(mode, self._profiles["normal"])

        base = {
            "SH_TEMP": profile["SH_TEMP"] + 4.0 * math.sin(self._step / 9.0),
            "SH_PRESS": profile["SH_PRESS"] + 3.0 * math.sin(self._step / 12.0),
            "DRUM_LEVEL": profile["DRUM_LEVEL"] + 45.0 * math.sin(self._step / 7.0),
            "BFP_FLOW": profile["BFP_FLOW"] + 35.0 * math.sin(self._step / 8.0),
            "STEAM_FLOW": profile["STEAM_FLOW"] + 18.0 * math.sin(self._step / 9.5),
            "FURNACE_TEMP": profile["FURNACE_TEMP"] + 25.0 * math.sin(self._step / 10.0),
            "FURNACE_O2": profile["FURNACE_O2"] + 0.5 * math.sin(self._step / 11.0),
            "FW_TEMP": profile["FW_TEMP"] + 3.0 * math.sin(self._step / 14.0),
        }

        values = {
            tag: round(self._smooth(tag, value + self._rng.uniform(-1.5, 1.5)), 2)
            for tag, value in base.items()
        }
        values = self._apply_mode(values, mode)
        control_state = self._derive_control_state(values)
        source_records = self._derive_source_records(values)

        snapshot = TelemetrySnapshot(
            timestamp=datetime.now(),
            values=values,
            control_state=control_state,
            source_records=source_records,
            anomaly_mode=mode,
        )
        self._history.append(snapshot)
        return snapshot

    def get_history(self) -> List[TelemetrySnapshot]:
        return list(self._history)

    def _smooth(self, tag: str, value: float) -> float:
        previous = self._last_values[tag]
        smoothed = previous * 0.72 + value * 0.28
        self._last_values[tag] = smoothed
        return smoothed

    def _select_mode(self) -> str:
        cycle = self._step % 60
        if cycle in {14, 15, 16, 17}:
            return "bfp_degradation"
        if cycle in {26, 27, 28, 29}:
            return "superheater_overheat"
        if cycle in {38, 39, 40}:
            return "drum_level_swell"
        if cycle in {49, 50, 51}:
            return "furnace_oxygen_deficit"
        return "normal"

    def _apply_mode(self, values: Dict[str, float], mode: str) -> Dict[str, float]:
        adjusted = dict(values)
        if mode == "bfp_degradation":
            adjusted["BFP_FLOW"] -= self._rng.uniform(120.0, 165.0)
            adjusted["SH_PRESS"] -= self._rng.uniform(8.0, 14.0)
            adjusted["DRUM_LEVEL"] -= self._rng.uniform(40.0, 90.0)
            adjusted["STEAM_FLOW"] -= self._rng.uniform(20.0, 40.0)
        elif mode == "superheater_overheat":
            adjusted["SH_TEMP"] += self._rng.uniform(10.0, 18.0)
            adjusted["SH_PRESS"] += self._rng.uniform(11.0, 18.0)
            adjusted["FURNACE_TEMP"] += self._rng.uniform(30.0, 70.0)
            adjusted["FURNACE_O2"] -= self._rng.uniform(0.3, 0.9)
            adjusted["SH_PRESS"] += self._rng.uniform(2.0, 5.0)
        elif mode == "drum_level_swell":
            adjusted["DRUM_LEVEL"] += self._rng.uniform(210.0, 290.0)
            adjusted["BFP_FLOW"] += self._rng.uniform(30.0, 70.0)
            adjusted["SH_PRESS"] += self._rng.uniform(3.0, 8.0)
            adjusted["STEAM_FLOW"] += self._rng.uniform(15.0, 30.0)
        elif mode == "furnace_oxygen_deficit":
            adjusted["FURNACE_O2"] -= self._rng.uniform(1.0, 1.6)
            adjusted["FURNACE_TEMP"] += self._rng.uniform(35.0, 65.0)
            adjusted["SH_TEMP"] += self._rng.uniform(4.0, 9.0)
            adjusted["SH_PRESS"] += self._rng.uniform(4.0, 8.0)

        for tag, constraint in PLANT_CONFIG.tags.items():
            adjusted[tag] = round(
                min(constraint.max_value + 20.0, max(constraint.min_value - 20.0, adjusted[tag])),
                2,
            )
        return adjusted

    def _derive_control_state(self, values: Dict[str, float]) -> Dict[str, float]:
        spray = 24.0
        recirc = 18.0
        feedwater_cv = 52.0
        coal_feed = 68.0
        master_trip = 0.0

        if values["SH_TEMP"] > 538:
            spray = min(100.0, spray + (values["SH_TEMP"] - 538.0) * 4.0)
            coal_feed = max(20.0, coal_feed - (values["SH_TEMP"] - 538.0) * 3.0)

        if values["BFP_FLOW"] < 850:
            recirc = min(100.0, recirc + (850.0 - values["BFP_FLOW"]) * 0.4)
            feedwater_cv = min(100.0, feedwater_cv + (850.0 - values["BFP_FLOW"]) * 0.18)

        if abs(values["DRUM_LEVEL"]) > 200:
            feedwater_cv = max(15.0, feedwater_cv - abs(values["DRUM_LEVEL"]) * 0.05)

        if values["SH_TEMP"] >= 545 or values["FURNACE_TEMP"] >= 1245 or abs(values["DRUM_LEVEL"]) >= 250:
            coal_feed = 0.0
            master_trip = 1.0

        return {
            "COAL_FEED_CMD": round(coal_feed, 2),
            "MASTER_FUEL_TRIP": round(master_trip, 2),
            "SH_SPRAY_WATER_CMD": round(spray, 2),
            "BFP_RECIRC_VALVE_CMD": round(recirc, 2),
            "FEEDWATER_CV_CMD": round(feedwater_cv, 2),
        }

    def _derive_source_records(self, values: Dict[str, float]) -> Dict[str, str]:
        quality = "GOOD"
        if values["SH_TEMP"] >= 545 or abs(values["DRUM_LEVEL"]) >= 250:
            quality = "HARMFUL"
        elif values["BFP_FLOW"] < 840 or values["FURNACE_O2"] < 2.5:
            quality = "DEGRADED"
        return {
            "plc_packet": quality,
            "dcs_alarm_state": "ALARM" if quality != "GOOD" else "NORMAL",
            "scada_quality": quality,
        }
