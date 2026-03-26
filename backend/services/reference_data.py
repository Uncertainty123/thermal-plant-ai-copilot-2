"""Loads representative synthetic source data for simulator seeding and UI display."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


class ReferenceDataRepository:
    def __init__(self, data_dir: Path | None = None) -> None:
        self._data_dir = data_dir or DATA_DIR

    def load_seed_profiles(self) -> Dict[str, Dict[str, float]]:
        path = self._data_dir / "seed_profiles.json"
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def load_table(self, filename: str) -> List[Dict[str, str]]:
        path = self._data_dir / filename
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

