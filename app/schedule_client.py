from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import requests

from app.config import AppConfig


def build_window_dates(today: date, days_before: int, days_after: int) -> tuple[str, str]:
    start = today - timedelta(days=days_before)
    finish = today + timedelta(days=days_after)
    return start.isoformat(), finish.isoformat()


class ScheduleClient:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def download_raw_schedule(self, output_dir: Path) -> dict[int, list[dict]]:
        output_dir.mkdir(parents=True, exist_ok=True)
        start, finish = build_window_dates(
            today=date.today(),
            days_before=self.config.schedule_window.days_before_today,
            days_after=self.config.schedule_window.days_after_today,
        )

        all_payloads: dict[int, list[dict]] = {}

        for building_number, building_oid in self.config.buildings.items():
            url = self.config.base_url.format(building_oid=building_oid)
            params = {"start": start, "finish": finish, "lng": 1}

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            payload = response.json()
            all_payloads[building_number] = payload

            filename = (
                output_dir
                / f"schedule_building_{building_number}_{start}_to_{finish}.json"
            )
            with filename.open("w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)

        return all_payloads
