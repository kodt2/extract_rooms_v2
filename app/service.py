from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

from app.allocator import RoomAllocator
from app.config import AppConfig
from app.models import AllocationResult, Request
from app.pdf_mode import PdfPayloadBuilder
from app.ruz_client import RuzScheduleClient

MSK_TZ = ZoneInfo("Europe/Moscow")
REFRESH_TIMES = (time(hour=4, minute=0), time(hour=16, minute=0))


class RoomService:
    """Main application service with two modes: allocation and report generation."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._client = RuzScheduleClient(config)
        self._allocator = RoomAllocator(config)
        self._report_builder = PdfPayloadBuilder(config)

    def allocate(self, requests: list[Request]) -> list[AllocationResult]:
        occupied = self._client.fetch_occupied_slots()
        return self._allocator.allocate_batch(requests=requests, occupied=occupied)

    def generate_pdf_payload(self, allocations: list[AllocationResult]) -> str:
        return self._report_builder.build_text_report(allocations)


def should_refresh(now: datetime | None = None) -> bool:
    """Returns True around 04:00 and 16:00 MSK (exact minute)."""
    now = now.astimezone(MSK_TZ) if now else datetime.now(MSK_TZ)
    return any(now.hour == slot.hour and now.minute == slot.minute for slot in REFRESH_TIMES)
