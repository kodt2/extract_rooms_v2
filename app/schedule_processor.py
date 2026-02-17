from __future__ import annotations

import json
from datetime import date, time
from pathlib import Path

from app.config import AppConfig
from app.models import LessonEntry, TimeSlot


def parse_time(value: str) -> time:
    return time.fromisoformat(value)


class ScheduleProcessor:
    """Converts raw API payload into compact occupancy data."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def trim_payload(self, payload_by_building: dict[int, list[dict]]) -> list[LessonEntry]:
        entries: list[LessonEntry] = []

        for building_number, lessons in payload_by_building.items():
            allowed_rooms = set(self.config.allowed_rooms.get(building_number, []))
            for item in lessons:
                room = str(item.get("auditorium", "")).strip()
                if not room or room not in allowed_rooms:
                    continue

                lesson = LessonEntry(
                    date=date.fromisoformat(item["date"]),
                    building_number=building_number,
                    auditorium=room,
                    capacity=int(item.get("auditoriumAmount") or 0),
                    slot=TimeSlot(
                        start=parse_time(item["beginLesson"]),
                        end=parse_time(item["endLesson"]),
                    ),
                )
                entries.append(lesson)

        return entries

    def save_trimmed(self, entries: list[LessonEntry], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        serialized = [
            {
                "date": item.date.isoformat(),
                "building_number": item.building_number,
                "auditorium": item.auditorium,
                "capacity": item.capacity,
                "begin_lesson": item.slot.start.strftime("%H:%M"),
                "end_lesson": item.slot.end.strftime("%H:%M"),
            }
            for item in entries
        ]
        with output_path.open("w", encoding="utf-8") as fh:
            json.dump(serialized, fh, ensure_ascii=False, indent=2)

    def load_trimmed(self, input_path: Path) -> list[LessonEntry]:
        with input_path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)

        return [
            LessonEntry(
                date=date.fromisoformat(item["date"]),
                building_number=int(item["building_number"]),
                auditorium=str(item["auditorium"]),
                capacity=int(item["capacity"]),
                slot=TimeSlot(
                    start=parse_time(item["begin_lesson"]),
                    end=parse_time(item["end_lesson"]),
                ),
            )
            for item in payload
        ]
