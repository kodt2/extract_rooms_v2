from __future__ import annotations

from collections import defaultdict

from app.config import AppConfig
from app.models import AllocationResult, Request, TimeRange

NO_ROOM = "no free room"
NO_DAY = "no day in shulde"


class RoomAllocator:
    """Allocates free rooms for a batch of requests without cross-request conflicts."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def allocate_batch(
        self,
        requests: list[Request],
        occupied: dict[str, dict[str, list[TimeRange]]],
    ) -> list[AllocationResult]:
        results: list[AllocationResult] = []
        reserved_by_batch: dict[str, dict[str, list[TimeRange]]] = defaultdict(lambda: defaultdict(list))

        for request in requests:
            day_key = request.day.isoformat()
            if day_key not in occupied:
                results.append(AllocationResult(request=request, room="", status=NO_DAY))
                continue

            selected_room = self._pick_room(request, occupied[day_key], reserved_by_batch[day_key])
            if not selected_room:
                results.append(AllocationResult(request=request, room="", status=NO_ROOM))
                continue

            reserved_by_batch[day_key][selected_room].append(request.slot)
            results.append(AllocationResult(request=request, room=selected_room, status="ok"))

        return results

    def _pick_room(
        self,
        request: Request,
        occupied_for_day: dict[str, list[TimeRange]],
        reserved_for_day: dict[str, list[TimeRange]],
    ) -> str | None:
        candidates = self._candidate_rooms(request.room_type)
        for room in candidates:
            day_busy = occupied_for_day.get(room, [])
            batch_busy = reserved_for_day.get(room, [])
            if _is_free(request.slot, day_busy) and _is_free(request.slot, batch_busy):
                return room
        return None

    def _candidate_rooms(self, room_type: str) -> list[str]:
        room_type = room_type.lower()
        all_rooms = [room for rooms in self._config.allowed_rooms.values() for room in rooms]

        if room_type == "any":
            return all_rooms
        if room_type == "any2":
            return self._config.allowed_rooms.get(2, [])
        if room_type == "any6":
            return self._config.allowed_rooms.get(6, [])
        if room_type == "big":
            return [room for rooms in self._config.big_rooms.values() for room in rooms]
        if room_type == "big2":
            return self._config.big_rooms.get(2, [])
        if room_type == "big6":
            return self._config.big_rooms.get(6, [])

        return [room_type]


def _is_free(request_slot: TimeRange, occupied_slots: list[TimeRange]) -> bool:
    return not any(request_slot.overlaps(slot) for slot in occupied_slots)
