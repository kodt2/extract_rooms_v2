from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("config.json")


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration loaded from JSON file."""

    base_url: str
    buildings: dict[int, int]
    allowed_rooms: dict[int, list[str]]
    big_rooms: dict[int, list[str]]
    contact_fields: dict[str, str]
    schedule_window_days_before: int
    schedule_window_months_after: int
    schedule_range_from_param: str
    schedule_range_to_param: str
    schedule_range_date_format: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "AppConfig":
        return AppConfig(
            base_url=data["base_url"],
            buildings={int(k): int(v) for k, v in data["buildings"].items()},
            allowed_rooms={int(k): [str(x) for x in v] for k, v in data["allowed_rooms"].items()},
            big_rooms={int(k): [str(x) for x in v] for k, v in data.get("big_rooms", {}).items()},
            contact_fields={str(k): str(v) for k, v in data.get("contact_fields", {}).items()},
            schedule_window_days_before=int(data.get("schedule_window_days_before", 1)),
            schedule_window_months_after=int(data.get("schedule_window_months_after", 1)),
            schedule_range_from_param=str(data.get("schedule_range_from_param", "dateFrom")),
            schedule_range_to_param=str(data.get("schedule_range_to_param", "dateTo")),
            schedule_range_date_format=str(data.get("schedule_range_date_format", "%Y-%m-%d")),
        )


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return AppConfig.from_dict(payload)
