from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time


@dataclass(frozen=True)
class TimeRange:
    """Half-open interval [start, end) for one day."""

    start: time
    end: time

    def overlaps(self, other: "TimeRange") -> bool:
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True)
class Request:
    """Incoming room booking request."""

    full_name: str
    goal: str
    day: date
    slot: TimeRange
    room_type: str


@dataclass(frozen=True)
class AllocationResult:
    """Result of allocation for a single request."""

    request: Request
    room: str
    status: str
