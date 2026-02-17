from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path

from app.config import AppConfig, load_config
from app.parser import RequestParser
from app.service import RoomService, ScheduleRefresher


@dataclass(frozen=True)
class IncomingMessage:
    """Minimal transport-agnostic message model for future Telegram integration."""

    chat_id: str
    text: str


class TelegramBotStub:
    """Skeleton for Telegram bot integration.

    Replace `_poll_updates` and `_send_message` with real Telegram API calls.
    """

    def __init__(self, config: AppConfig) -> None:
        self._service = RoomService(config)
        self._refresher = ScheduleRefresher(self._service, poll_seconds=config.refresh_poll_seconds)

    def run(self) -> None:
        self._service.ensure_schedule_cache()
        threading.Thread(target=self._refresher.run_forever, daemon=True).start()

        for message in self._poll_updates():
            self._handle_message(message)

    def _handle_message(self, message: IncomingMessage) -> None:
        requests = [RequestParser.parse(line) for line in message.text.splitlines() if line.strip()]
        allocations = self._service.allocate(requests)
        response = [
            {
                "name": item.request.full_name,
                "goal": item.request.goal,
                "date": item.request.day.isoformat(),
                "start": item.request.slot.start.strftime("%H:%M"),
                "end": item.request.slot.end.strftime("%H:%M"),
                "room": item.room,
                "status": item.status,
            }
            for item in allocations
        ]
        self._send_message(message.chat_id, json.dumps(response, ensure_ascii=False, indent=2))

    def _poll_updates(self) -> list[IncomingMessage]:
        """TODO: implement Telegram getUpdates polling or webhook adapter."""
        return []

    def _send_message(self, chat_id: str, text: str) -> None:
        """TODO: implement Telegram sendMessage call."""
        print(f"[{chat_id}] {text}")


def run_bot(config_path: Path = Path("config.json")) -> None:
    config = load_config(config_path)
    TelegramBotStub(config).run()
