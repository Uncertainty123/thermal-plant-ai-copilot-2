"""Static configuration for the thermal plant monitoring system."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class TagConstraint:
    min_value: float
    max_value: float
    warn_low: float | None = None
    warn_high: float | None = None
    trip_low: float | None = None
    trip_high: float | None = None
    unit: str = ""


@dataclass(frozen=True)
class PlantConfig:
    tags: Dict[str, TagConstraint] = field(default_factory=dict)
    auxiliaries: List[str] = field(default_factory=list)
    control_points: Dict[str, str] = field(default_factory=dict)
    tag_profiles: Dict[str, Dict[str, str]] = field(default_factory=dict)
    history_limit: int = 240


PLANT_CONFIG = PlantConfig(
    auxiliaries=["BFP", "SH", "DRUM", "FURNACE"],
    tags={
        "SH_TEMP": TagConstraint(
            min_value=500.0,
            max_value=545.0,
            warn_high=538.0,
            trip_high=545.0,
            unit="degC",
        ),
        "SH_PRESS": TagConstraint(
            min_value=160.0,
            max_value=180.0,
            warn_low=160.0,
            warn_high=180.0,
            trip_high=190.0,
            unit="bar",
        ),
        "DRUM_LEVEL": TagConstraint(
            min_value=-250.0,
            max_value=250.0,
            warn_low=-200.0,
            warn_high=200.0,
            trip_low=-250.0,
            trip_high=250.0,
            unit="mm",
        ),
        "BFP_FLOW": TagConstraint(
            min_value=780.0,
            max_value=1100.0,
            warn_low=820.0,
            unit="tph",
        ),
        "STEAM_FLOW": TagConstraint(
            min_value=430.0,
            max_value=560.0,
            warn_low=455.0,
            warn_high=545.0,
            unit="tph",
        ),
        "FURNACE_TEMP": TagConstraint(
            min_value=950.0,
            max_value=1250.0,
            warn_high=1200.0,
            trip_high=1250.0,
            unit="degC",
        ),
        "FURNACE_O2": TagConstraint(
            min_value=2.0,
            max_value=5.5,
            warn_low=2.5,
            warn_high=5.0,
            unit="pct",
        ),
        "FW_TEMP": TagConstraint(
            min_value=210.0,
            max_value=255.0,
            warn_low=220.0,
            unit="degC",
        ),
    },
    control_points={
        "COAL_FEED_CMD": "pct",
        "MASTER_FUEL_TRIP": "bool",
        "SH_SPRAY_WATER_CMD": "pct",
        "BFP_RECIRC_VALVE_CMD": "pct",
        "FEEDWATER_CV_CMD": "pct",
    },
    tag_profiles={
        "generic": {
            "SH_TEMP": "SH_TEMP",
            "SH_PRESS": "SH_PRESS",
            "DRUM_LEVEL": "DRUM_LEVEL",
            "BFP_FLOW": "BFP_FLOW",
            "STEAM_FLOW": "STEAM_FLOW",
            "FURNACE_TEMP": "FURNACE_TEMP",
            "FURNACE_O2": "FURNACE_O2",
            "FW_TEMP": "FW_TEMP",
        },
        "dcs_style": {
            "SH_TEMP": "01SH01AIT001.PV",
            "SH_PRESS": "01SH01PIT001.PV",
            "DRUM_LEVEL": "01DRM01LIT001.PV",
            "BFP_FLOW": "01BFP01FIT001.PV",
            "STEAM_FLOW": "01MSH01FIT001.PV",
            "FURNACE_TEMP": "01FRN01TIT001.PV",
            "FURNACE_O2": "01FRN01AIT002.PV",
            "FW_TEMP": "01FW01TIT003.PV",
        },
        "plc_style": {
            "SH_TEMP": "AI_SH_OUTLET_TEMP",
            "SH_PRESS": "AI_SH_HDR_PRESS",
            "DRUM_LEVEL": "AI_DRUM_LEVEL_MM",
            "BFP_FLOW": "AI_BFP_DISCH_FLOW",
            "STEAM_FLOW": "AI_MAIN_STEAM_FLOW",
            "FURNACE_TEMP": "AI_FURNACE_EXIT_TEMP",
            "FURNACE_O2": "AI_FG_O2",
            "FW_TEMP": "AI_FW_TEMP",
        },
        "scada_historian_style": {
            "SH_TEMP": "PLANT1.BOILER1.SH.TEMP.OUT",
            "SH_PRESS": "PLANT1.BOILER1.SH.PRESS.OUT",
            "DRUM_LEVEL": "PLANT1.BOILER1.DRUM.LEVEL",
            "BFP_FLOW": "PLANT1.BFPA.FLOW",
            "STEAM_FLOW": "PLANT1.BOILER1.MS.FLOW",
            "FURNACE_TEMP": "PLANT1.BOILER1.FURNACE.EXIT.TEMP",
            "FURNACE_O2": "PLANT1.BOILER1.FG.O2",
            "FW_TEMP": "PLANT1.BOILER1.FW.TEMP",
        },
    },
)
