from datetime import date, time

from app.allocator import NO_DAY, NO_ROOM, RoomAllocator
from app.config import AppConfig
from app.models import Request, TimeRange


def _config() -> AppConfig:
    return AppConfig(
        base_url="http://example/{building_oid}",
        buildings={2: 145, 6: 147},
        allowed_rooms={2: ["212", "305"], 6: ["610"]},
        big_rooms={2: ["305"], 6: ["610"]},
        contact_fields={},
        schedule_window_days_before=1,
        schedule_window_months_after=1,
<<<<<<< codex/implement-schedule-management-system-msv8qj
        schedule_range_start_param="start",
        schedule_range_finish_param="finish",
        schedule_range_date_format="%Y-%m-%d",
        schedule_lang_param="lng",
        schedule_lang_value=1,
=======
        schedule_range_from_param="dateFrom",
        schedule_range_to_param="dateTo",
        schedule_range_date_format="%Y-%m-%d",
>>>>>>> main
        schedule_cache_path="data/test_cache.json",
        refresh_poll_seconds=30,
    )


def test_allocates_without_batch_overlap() -> None:
    allocator = RoomAllocator(_config())
    occupied = {
        "2026-01-01": {
            "212": [TimeRange(start=time(10, 0), end=time(11, 0))],
            "305": [],
            "610": [],
        }
    }
    requests = [
        Request("A B", "goal", date(2026, 1, 1), TimeRange(time(10, 0), time(11, 0)), "any"),
        Request("C D", "goal", date(2026, 1, 1), TimeRange(time(10, 30), time(11, 30)), "any"),
    ]

    results = allocator.allocate_batch(requests, occupied)

    assert results[0].status == "ok"
    assert results[1].status == "ok"
    assert results[0].room != results[1].room


def test_returns_no_day_and_no_room() -> None:
    allocator = RoomAllocator(_config())
    occupied = {"2026-01-01": {"212": [TimeRange(time(8, 0), time(20, 0))]}}
    requests = [
        Request("A B", "goal", date(2026, 1, 2), TimeRange(time(10, 0), time(11, 0)), "any"),
        Request("C D", "goal", date(2026, 1, 1), TimeRange(time(10, 0), time(11, 0)), "212"),
    ]

    results = allocator.allocate_batch(requests, occupied)
    assert results[0].status == NO_DAY
    assert results[1].status == NO_ROOM
