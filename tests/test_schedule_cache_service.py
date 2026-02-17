from datetime import datetime
from pathlib import Path

from app.config import AppConfig
from app.ruz_client import FetchResult, FetchStats
from app.service import RoomService, ScheduleRefresher


class _FakeClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def fetch_occupied_slots_with_stats(self):
        self.calls += 1
        return FetchResult(
            occupied=self.payload,
            stats=FetchStats(
                total_lessons=10,
                accepted_lessons=3,
                skipped_no_room=0,
                skipped_not_allowed_room=4,
                skipped_no_time_or_date=1,
                skipped_bad_date_or_time=1,
                skipped_out_of_range=1,
            ),
        )


def _config(cache_path: Path) -> AppConfig:
    return AppConfig(
        base_url="http://example/{building_oid}",
        buildings={2: 145},
        allowed_rooms={2: ["212"]},
        big_rooms={2: []},
        contact_fields={},
        schedule_window_days_before=1,
        schedule_window_months_after=1,
        schedule_range_from_param="dateFrom",
        schedule_range_to_param="dateTo",
        schedule_range_date_format="%Y-%m-%d",
        schedule_cache_path=str(cache_path),
        refresh_poll_seconds=1,
    )


def test_refresh_saves_cache_and_allocate_uses_cached_data(tmp_path: Path) -> None:
    config = _config(tmp_path / "clean_schedule.json")
    service = RoomService(config)
    fake_payload = {"2026-01-01": {"212": []}}
    fake_client = _FakeClient(fake_payload)
    service._client = fake_client  # type: ignore[attr-defined]

    service.refresh_schedule_cache()
    assert (tmp_path / "clean_schedule.json").exists()
    assert service.last_fetch_stats is not None
    assert service.last_fetch_stats.total_lessons == 10

    service.ensure_schedule_cache()
    assert fake_client.calls == 1


def test_refresher_triggers_once_per_target_minute(tmp_path: Path) -> None:
    config = _config(tmp_path / "clean_schedule.json")
    service = RoomService(config)
    fake_client = _FakeClient({"2026-01-01": {"212": []}})
    service._client = fake_client  # type: ignore[attr-defined]

    refresher = ScheduleRefresher(service, poll_seconds=5)
    now = datetime.fromisoformat("2026-03-12T04:00:00+03:00")

    assert refresher.tick(now) is True
    assert refresher.tick(now) is False
    assert fake_client.calls == 1
