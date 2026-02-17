from __future__ import annotations

from collections import defaultdict
from datetime import date, time

from app.config import AppConfig
from app.models import AllocationResult, BookingRequest, LessonEntry, RoomCandidate


def time_overlap(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    return max(start_a, start_b) < min(end_a, end_b)


class RoomAllocator:
    def __init__(self, config: AppConfig, schedule_entries: list[LessonEntry]) -> None:
        self.config = config
        self.schedule_entries = schedule_entries
        self.busy_by_date_room = self._build_busy_index(schedule_entries)
        self.capacity_by_room = self._build_capacity_index(schedule_entries)

    @staticmethod
    def _build_busy_index(
        schedule_entries: list[LessonEntry],
    ) -> dict[tuple[date, int, str], list[tuple[time, time]]]:
        busy: dict[tuple[date, int, str], list[tuple[time, time]]] = defaultdict(list)
        for entry in schedule_entries:
            busy[(entry.date, entry.building_number, entry.auditorium)].append(
                (entry.slot.start, entry.slot.end)
            )
        return busy

    @staticmethod
    def _build_capacity_index(
        schedule_entries: list[LessonEntry],
    ) -> dict[tuple[int, str], int]:
        capacity: dict[tuple[int, str], int] = {}
        for entry in schedule_entries:
            key = (entry.building_number, entry.auditorium)
            capacity[key] = max(capacity.get(key, 0), entry.capacity)
        return capacity

    def allocate_batch(self, requests: list[BookingRequest]) -> list[AllocationResult]:
        results: list[AllocationResult] = []
        reserved_in_batch: dict[tuple[date, int, str], list[tuple[time, time]]] = defaultdict(list)
        schedule_days = {item.date for item in self.schedule_entries}

        for request in requests:
            if request.requested_date not in schedule_days:
                results.append(
                    AllocationResult(
                        request=request,
                        assigned_room="no day in schedule",
                        status="no_day_in_schedule",
                    )
                )
                continue

            room = self._find_free_room(request, reserved_in_batch)
            if room is None:
                results.append(
                    AllocationResult(
                        request=request,
                        assigned_room="no free room",
                        status="no_free_room",
                    )
                )
                continue

            key = (request.requested_date, room.building_number, room.room)
            reserved_in_batch[key].append((request.start_time, request.end_time))
            results.append(
                AllocationResult(
                    request=request,
                    assigned_room=f"{room.room} (корпус {room.building_number})",
                    status="ok",
                )
            )

        return results

    def _find_free_room(
        self,
        request: BookingRequest,
        reserved_in_batch: dict[tuple[date, int, str], list[tuple[time, time]]],
    ) -> RoomCandidate | None:
        candidates = self._select_candidates(request.room_type)

        for candidate in candidates:
            key = (request.requested_date, candidate.building_number, candidate.room)
            busy_slots = self.busy_by_date_room.get(key, []) + reserved_in_batch.get(key, [])
            conflict = any(
                time_overlap(request.start_time, request.end_time, start, end)
                for start, end in busy_slots
            )
            if not conflict:
                return candidate

        return None

    def _select_candidates(self, room_type: str) -> list[RoomCandidate]:
        all_candidates = [
            RoomCandidate(building_number=b, room=r, capacity=cap)
            for (b, r), cap in self.capacity_by_room.items()
        ]

        if room_type == "any":
            return sorted(all_candidates, key=lambda item: (item.building_number, item.room))
        if room_type == "any2":
            return [c for c in all_candidates if c.building_number == 2]
        if room_type == "any6":
            return [c for c in all_candidates if c.building_number == 6]
        if room_type == "big":
            return [c for c in all_candidates if c.capacity >= self.config.big_room_min_capacity]
        if room_type == "big2":
            return [
                c
                for c in all_candidates
                if c.building_number == 2 and c.capacity >= self.config.big_room_min_capacity
            ]
        if room_type == "big6":
            return [
                c
                for c in all_candidates
                if c.building_number == 6 and c.capacity >= self.config.big_room_min_capacity
            ]

        target = str(room_type)
        return [candidate for candidate in all_candidates if candidate.room == target]
