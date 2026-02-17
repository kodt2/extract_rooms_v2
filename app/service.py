from __future__ import annotations

import time as sleep_time
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from app.allocator import RoomAllocator
from app.config import AppConfig
from app.models import AllocationResult, Request, TimeRange
from app.pdf_mode import PdfPayloadBuilder
from app.ruz_client import FetchStats, RuzScheduleClient
from app.schedule_cache import ScheduleCacheRepository

MSK_TZ = ZoneInfo("Europe/Moscow")
REFRESH_TIMES = (time(hour=4, minute=0), time(hour=16, minute=0))


class RoomService:
    """Main application service with cached schedule and report mode."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._client = RuzScheduleClient(config)
        self._allocator = RoomAllocator(config)
        self._report_builder = PdfPayloadBuilder(config)
        self._cache = ScheduleCacheRepository(Path(config.schedule_cache_path))
        self._last_fetch_stats: FetchStats | None = None

    def ensure_schedule_cache(self) -> dict[str, dict[str, list[TimeRange]]]:
        if self._cache.exists():
            return self._cache.load()
        return self.refresh_schedule_cache()

    def refresh_schedule_cache(self) -> dict[str, dict[str, list[TimeRange]]]:
        result = self._client.fetch_occupied_slots_with_stats()
        self._last_fetch_stats = result.stats
        self._cache.save(result.occupied)
        return result.occupied

    @property
    def last_fetch_stats(self) -> FetchStats | None:
        return self._last_fetch_stats

    def allocate(self, requests: list[Request]) -> list[AllocationResult]:
        occupied = self.ensure_schedule_cache()
        return self._allocator.allocate_batch(requests=requests, occupied=occupied)

    def generate_pdf_payload(self, allocations: list[AllocationResult]) -> str:
        return self._report_builder.build_text_report(allocations)


class ScheduleRefresher:
    """Background-friendly refresher for 04:00/16:00 MSK schedule updates."""

    def __init__(self, service: RoomService, poll_seconds: int) -> None:
        self._service = service
        self._poll_seconds = max(poll_seconds, 5)
        self._last_refresh_key: str | None = None

    def tick(self, now: datetime | None = None) -> bool:
        now = now.astimezone(MSK_TZ) if now else datetime.now(MSK_TZ)
        refresh_key = now.strftime("%Y-%m-%d %H:%M")
        if should_refresh(now) and self._last_refresh_key != refresh_key:
            self._service.refresh_schedule_cache()
            self._last_refresh_key = refresh_key
            return True
        return False

    def run_forever(self) -> None:
        while True:
            self.tick()
            sleep_time.sleep(self._poll_seconds)


def should_refresh(now: datetime | None = None) -> bool:
    """Returns True around 04:00 and 16:00 MSK (exact minute)."""
    now = now.astimezone(MSK_TZ) if now else datetime.now(MSK_TZ)
    return any(now.hour == slot.hour and now.minute == slot.minute for slot in REFRESH_TIMES)
