from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.models import TimeRange


class ScheduleCacheRepository:
    """Stores trimmed schedule on disk and restores it on startup."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def exists(self) -> bool:
        return self._path.exists()

    def load(self) -> dict[str, dict[str, list[TimeRange]]]:
        if not self._path.exists():
            return {}
        payload = json.loads(self._path.read_text(encoding="utf-8"))
        result: dict[str, dict[str, list[TimeRange]]] = {}

        for day, rooms in payload.items():
            result[day] = {}
            for room, slots in rooms.items():
                result[day][room] = [
                    TimeRange(
                        start=datetime.strptime(slot["start"], "%H:%M").time(),
                        end=datetime.strptime(slot["end"], "%H:%M").time(),
                    )
                    for slot in slots
                ]
        return result

    def save(self, occupied: dict[str, dict[str, list[TimeRange]]]) -> Path:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            day: {
                room: [
                    {"start": slot.start.strftime("%H:%M"), "end": slot.end.strftime("%H:%M")}
                    for slot in slots
                ]
                for room, slots in rooms.items()
            }
            for day, rooms in occupied.items()
        }
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return self._path
