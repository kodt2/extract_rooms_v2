from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.config import load_config
from app.parser import RequestParser
from app.pdf_mode import PdfPayloadBuilder
from app.pdf_renderer import ConfigurablePdfRenderer
from app.service import RoomService


def run() -> None:
    parser = argparse.ArgumentParser(description="Allocate classrooms from RUZ schedule")
    parser.add_argument("--config", default="config.json", help="Path to config JSON")
    parser.add_argument("--input", help="Path to text file with one request per line")
    parser.add_argument(
        "--mode",
        choices=["allocate", "pdf", "render-pdf"],
        default="allocate",
        help="allocate = print decisions, pdf = save printable payload, render-pdf = build final PDF by template",
    )
    parser.add_argument("--output", default="output/report.txt", help="Output file for pdf mode")
    parser.add_argument("--template", help="Path to PDF template config (JSON) for render-pdf mode")
    parser.add_argument("--data", help="Path to input JSON data for render-pdf mode")
    args = parser.parse_args()

    if args.mode in {"allocate", "pdf"} and not args.input:
        raise SystemExit("allocate/pdf mode requires --input")

    if args.mode == "render-pdf":
        if not args.template or not args.data:
            raise SystemExit("render-pdf mode requires --template and --data")
        renderer = ConfigurablePdfRenderer.from_json(Path(args.template))
        data = json.loads(Path(args.data).read_text(encoding="utf-8"))
        output_path = Path(args.output)
        if output_path.suffix.lower() != ".pdf":
            output_path = output_path.with_suffix(".pdf")
        result_path = renderer.render_to_file(data, output_path)
        print(f"Saved PDF to: {result_path}")
        return

    config = load_config(Path(args.config))
    service = RoomService(config)

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
