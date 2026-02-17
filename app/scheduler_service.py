from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from time import sleep
from zoneinfo import ZoneInfo

from app.config import AppConfig
from app.schedule_client import ScheduleClient
from app.schedule_processor import ScheduleProcessor


class ScheduleRefreshService:
    """Refreshes schedule twice a day and saves trimmed data to disk."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.client = ScheduleClient(config)
        self.processor = ScheduleProcessor(config)

    def refresh_now(self) -> Path:
        storage_dir = Path(self.config.storage_path)
        raw_dir = storage_dir / "raw"
        trimmed_path = storage_dir / "trimmed_schedule.json"

        raw_payload = self.client.download_raw_schedule(raw_dir)
        trimmed = self.processor.trim_payload(raw_payload)
        self.processor.save_trimmed(trimmed, trimmed_path)
        return trimmed_path

    def run_forever(self) -> None:
        timezone = ZoneInfo(self.config.timezone)
        while True:
            next_run = self._next_run_time(datetime.now(tz=timezone))
            seconds_to_wait = max((next_run - datetime.now(tz=timezone)).total_seconds(), 1)
            sleep(seconds_to_wait)
            self.refresh_now()

    def _next_run_time(self, now: datetime) -> datetime:
        sorted_hours = sorted(self.config.update_hours_moscow)
        candidates = []
        for hour in sorted_hours:
            candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if candidate <= now:
                candidate += timedelta(days=1)
            candidates.append(candidate)

        return min(candidates)
