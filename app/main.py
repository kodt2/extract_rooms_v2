from __future__ import annotations

import argparse
from pathlib import Path

from app.bot_stub import TelegramBotStub
from app.config import load_config
from app.scheduler_service import ScheduleRefreshService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="UNN room allocation service")
    parser.add_argument(
        "mode",
        choices=["refresh", "scheduler", "allocate", "pdf"],
        help="Mode of operation",
    )
    parser.add_argument("--config", default="config.json", help="Path to config")
    parser.add_argument("--request", action="append", default=[], help="Request line")
    parser.add_argument("--pdf-path", default="output/report.pdf", help="Path to output PDF")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(Path(args.config))

    if args.mode == "refresh":
        path = ScheduleRefreshService(config).refresh_now()
        print(f"Trimmed schedule saved: {path}")
        return

    if args.mode == "scheduler":
        ScheduleRefreshService(config).run_forever()
        return

    bot = TelegramBotStub(config)

    if args.mode == "allocate":
        for row in bot.handle_allocation_requests(args.request):
            print(row)
        return

    if args.mode == "pdf":
        pdf_path = bot.handle_pdf_requests(args.request, Path(args.pdf_path))
        print(f"Report saved: {pdf_path}")


if __name__ == "__main__":
    main()
