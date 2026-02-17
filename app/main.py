from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.config import load_config
from app.parser import RequestParser
from app.pdf_mode import PdfPayloadBuilder
from app.service import RoomService
from app.telegram_bot import run_bot


def run() -> None:
    parser = argparse.ArgumentParser(description="Allocate classrooms from RUZ schedule")
    parser.add_argument("--config", default="config.json", help="Path to config JSON")
    parser.add_argument("--input", help="Path to text file with one request per line")
    parser.add_argument(
        "--mode",
        choices=["allocate", "pdf", "refresh", "bot"],
        default="allocate",
        help="allocate = print decisions, pdf = save printable payload, refresh = update cache, bot = run bot stub",
    )
    parser.add_argument("--output", default="output/report.txt", help="Output file for pdf mode")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_config(config_path)
    service = RoomService(config)

    if args.mode == "refresh":
        occupied = service.refresh_schedule_cache()
        print(f"Cache updated: {config.schedule_cache_path}. Days loaded: {len(occupied)}")
        return

    if args.mode == "bot":
        run_bot(config_path)
        return

    if not args.input:
        raise ValueError("--input is required for allocate/pdf mode")

    lines = [line for line in Path(args.input).read_text(encoding="utf-8").splitlines() if line.strip()]
    requests = [RequestParser.parse(line) for line in lines]

    allocations = service.allocate(requests)

    if args.mode == "allocate":
        print(
            json.dumps(
                [
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
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    builder = PdfPayloadBuilder(config)
    result_path = builder.save_report(allocations, Path(args.output))
    print(f"Saved report payload to: {result_path}")


if __name__ == "__main__":
    run()
