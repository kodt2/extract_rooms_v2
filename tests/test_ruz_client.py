from datetime import date

from app.ruz_client import _add_months, _attach_range_query, _build_schedule_window, _normalize_time, _parse_date


def test_build_schedule_window_from_config_values() -> None:
    start, end = _build_schedule_window(today=date(2026, 3, 12), days_before=1, months_after=1)
    assert start.isoformat() == "2026-03-11"
    assert end.isoformat() == "2026-04-12"


def test_add_months_handles_month_end() -> None:
    assert _add_months(date(2026, 1, 31), 1).isoformat() == "2026-02-28"


def test_attach_range_query_uses_start_finish_and_lng() -> None:
    url = _attach_range_query(
        base_url="https://example/api",
        range_start=date(2026, 3, 11),
        range_end=date(2026, 4, 12),
        start_param="start",
        finish_param="finish",
        lang_param="lng",
        lang_value=1,
        date_format="%Y-%m-%d",
    )
    assert url == "https://example/api?start=2026-03-11&finish=2026-04-12&lng=1"


def test_parse_date_supports_multiple_formats() -> None:
    assert _parse_date("2026-03-12").isoformat() == "2026-03-12"
    assert _parse_date("12.03.2026").isoformat() == "2026-03-12"
    assert _parse_date("2026-03-12T08:30:00").isoformat() == "2026-03-12"


def test_parse_date_supports_dotnet_date_nest() -> None:
    assert _parse_date("/Date(1770843600000+0300)/").isoformat() == "2026-02-12"


def test_normalize_time_supports_seconds() -> None:
    assert _normalize_time("07:30:00").strftime("%H:%M") == "07:30"
