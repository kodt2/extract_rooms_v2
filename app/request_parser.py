from __future__ import annotations

from datetime import datetime

from app.models import BookingRequest


class RequestParser:
    """Parses lines in format: Имя Фамилия Цель дд.мм чч:мм чч:мм тип."""

    @staticmethod
    def parse_line(line: str) -> BookingRequest:
        parts = line.strip().split()
        if len(parts) < 7:
            raise ValueError("Expected at least 7 tokens in request line")

        full_name = f"{parts[0]} {parts[1]}"
        purpose = parts[2]
        date_value = datetime.strptime(parts[3], "%d.%m").date()
        date_value = date_value.replace(year=datetime.now().year)
        start_time = datetime.strptime(parts[4], "%H:%M").time()
        end_time = datetime.strptime(parts[5], "%H:%M").time()
        room_type = parts[6]

        return BookingRequest(
            full_name=full_name,
            purpose=purpose,
            requested_date=date_value,
            start_time=start_time,
            end_time=end_time,
            room_type=room_type,
        )
