from datetime import date

from app.ruz_client import (
    _add_months,
    _attach_range_query,
    _build_schedule_window,
    _candidate_date_formats,
    _normalize_time,
    _parse_date,
    _range_coverage_score,
)


def test_build_schedule_window_from_config_values() -> None:
    start, end = _build_schedule_window(today=date(2026, 3, 12), days_before=1, months_after=1)
    assert start.isoformat() == "2026-03-11"
    assert end.isoformat() == "2026-04-12"


def test_add_months_handles_month_end() -> None:
    assert _add_months(date(2026, 1, 31), 1).isoformat() == "2026-02-28"


def test_attach_range_query_uses_configurable_params() -> None:
    url = _attach_range_query(
        base_url="https://example/api",
        range_start=date(2026, 3, 11),
        range_end=date(2026, 4, 12),
        from_param="from",
        to_param="to",
        date_format="%Y-%m-%d",
    )
    assert url == "https://example/api?from=2026-03-11&to=2026-04-12"


def test_parse_date_supports_multiple_formats() -> None:
    assert _parse_date("2026-03-12").isoformat() == "2026-03-12"
    assert _parse_date("12.03.2026").isoformat() == "2026-03-12"
    assert _parse_date("2026-03-12T08:30:00").isoformat() == "2026-03-12"


def test_parse_date_supports_dotnet_date_nest() -> None:
    assert _parse_date("/Date(1770843600000+0300)/").isoformat() == "2026-02-12"


def test_normalize_time_supports_seconds() -> None:
    assert _normalize_time("07:30:00").strftime("%H:%M") == "07:30"


def test_candidate_date_formats_contains_fallbacks_without_duplicates() -> None:
    result = _candidate_date_formats("%Y-%m-%d")
    assert result[0] == "%Y-%m-%d"
    assert len(result) == len(set(result))
    assert "%Y.%m.%d" in result


def test_range_coverage_score_prefers_further_end_date() -> None:
    target_end = date(2026, 3, 19)
    short = [{"date": "2026-02-22"}, {"date": "2026-02-21"}]
    long = [{"date": "2026-03-19"}, {"date": "2026-03-18"}]
    assert _range_coverage_score(long, target_end) > _range_coverage_score(short, target_end)
