from __future__ import annotations

import json
from calendar import monthrange
from datetime import date, datetime, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.config import AppConfig
from app.models import TimeRange


class RuzScheduleClient:
    """Loads schedules from RUZ API and normalizes the payload."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def fetch_occupied_slots(self) -> dict[str, dict[str, list[TimeRange]]]:
        occupied: dict[str, dict[str, list[TimeRange]]] = {}
        range_start, range_end = _build_schedule_window(
            today=date.today(),
            days_before=self._config.schedule_window_days_before,
            months_after=self._config.schedule_window_months_after,
        )

        for building_number, building_oid in self._config.buildings.items():
            base_url = self._config.base_url.format(building_oid=building_oid)
            url = _attach_range_query(
                base_url=base_url,
                range_start=range_start,
                range_end=range_end,
                from_param=self._config.schedule_range_from_param,
                to_param=self._config.schedule_range_to_param,
                date_format=self._config.schedule_range_date_format,
            )
            lessons = _load_json(url)
            allowed_rooms = set(self._config.allowed_rooms.get(building_number, []))

            for lesson in lessons:
                room = str(
                    lesson.get("auditorium")
                    or lesson.get("room")
                    or lesson.get("auditoriumName")
                    or ""
                ).strip()
                if not room or (allowed_rooms and room not in allowed_rooms):
                    continue

                date_token = lesson.get("date") or lesson.get("day") or lesson.get("lessonDate")
                start_token = lesson.get("beginLesson") or lesson.get("start")
                end_token = lesson.get("endLesson") or lesson.get("end")

                if not (date_token and start_token and end_token):
                    continue

                lesson_day = _parse_date(date_token)
                if lesson_day < range_start or lesson_day > range_end:
                    continue

                day_key = lesson_day.isoformat()
                start = _normalize_time(start_token)
                end = _normalize_time(end_token)

                occupied.setdefault(day_key, {}).setdefault(room, []).append(TimeRange(start=start, end=end))

        for day_rooms in occupied.values():
            for room, slots in day_rooms.items():
                day_rooms[room] = sorted(slots, key=lambda item: item.start)

        return occupied


def _load_json(url: str):
    request = Request(url, headers={"User-Agent": "extract-rooms-v2/1.0"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _parse_date(raw: str) -> date:
    token = raw[:19]
    for pattern in ("%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(token, pattern).date()
        except ValueError:
            continue
    raise ValueError(f"Unsupported date format: {raw}")


def _normalize_time(raw: str):
    token = raw[:5]
    return datetime.strptime(token, "%H:%M").time()


def _build_schedule_window(today: date, days_before: int, months_after: int) -> tuple[date, date]:
    range_start = today - timedelta(days=max(days_before, 0))
    range_end = _add_months(today, max(months_after, 0))
    return range_start, range_end


def _add_months(input_date: date, months: int) -> date:
    month_index = input_date.month - 1 + months
    target_year = input_date.year + month_index // 12
    target_month = month_index % 12 + 1
    target_day = min(input_date.day, monthrange(target_year, target_month)[1])
    return date(target_year, target_month, target_day)


def _attach_range_query(
    base_url: str,
    range_start: date,
    range_end: date,
    from_param: str,
    to_param: str,
    date_format: str,
) -> str:
    params = {
        from_param: range_start.strftime(date_format),
        to_param: range_end.strftime(date_format),
    }
    delimiter = "&" if "?" in base_url else "?"
    return f"{base_url}{delimiter}{urlencode(params)}"
