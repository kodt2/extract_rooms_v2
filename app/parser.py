from __future__ import annotations

from datetime import datetime

from app.models import Request, TimeRange


class RequestParser:
    """Parses incoming plain-text requests.

    Format:
    [Имя Фамилия Цель дд.мм чч:мм чч:мм тип_аудитории]
    """

    @staticmethod
    def parse(raw_line: str, year: int | None = None) -> Request:
        cleaned = raw_line.strip().strip("[]")
        parts = cleaned.split()
        if len(parts) < 6:
            raise ValueError(f"Invalid request format: {raw_line}")

        first_name, last_name = parts[0], parts[1]
        day_token, start_token, end_token, room_type = parts[-4], parts[-3], parts[-2], parts[-1]
        goal = " ".join(parts[2:-4])

        current_year = year or datetime.now().year
        day = datetime.strptime(f"{day_token}.{current_year}", "%d.%m.%Y").date()
        start = datetime.strptime(start_token, "%H:%M").time()
        end = datetime.strptime(end_token, "%H:%M").time()

        return Request(
            full_name=f"{first_name} {last_name}",
            goal=goal,
            day=day,
            slot=TimeRange(start=start, end=end),
            room_type=room_type,
        )
