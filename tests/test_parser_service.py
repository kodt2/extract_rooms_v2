from datetime import datetime

from app.parser import RequestParser
from app.service import should_refresh


def test_parser() -> None:
    req = RequestParser.parse("[Иван Иванов Консультация по проекту 12.03 10:10 11:45 big2]", year=2026)
    assert req.full_name == "Иван Иванов"
    assert req.goal == "Консультация по проекту"
    assert req.day.isoformat() == "2026-03-12"
    assert req.room_type == "big2"


def test_should_refresh_msk_points() -> None:
    assert should_refresh(datetime.fromisoformat("2026-03-12T04:00:00+03:00")) is True
    assert should_refresh(datetime.fromisoformat("2026-03-12T16:00:00+03:00")) is True
    assert should_refresh(datetime.fromisoformat("2026-03-12T16:01:00+03:00")) is False
