from __future__ import annotations

from pathlib import Path

from app.config import AppConfig
from app.models import AllocationResult


class PdfGenerator:
    """Stub PDF generator. Writes plain text payload with .pdf extension for now."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def generate(self, allocations: list[AllocationResult], output_file: Path) -> None:
        output_file.parent.mkdir(parents=True, exist_ok=True)

        lines: list[str] = ["Room allocation report", ""]
        lines.append("Configured contact fields:")
        for key, value in self.config.pdf_contact_fields.items():
            lines.append(f"- {key}: {value}")

        lines.append("")
        lines.append("Allocations:")

        for item in allocations:
            req = item.request
            lines.append(
                f"{req.full_name} | {req.requested_date.isoformat()} {req.start_time.strftime('%H:%M')}-{req.end_time.strftime('%H:%M')} "
                f"| {item.assigned_room}"
            )

        output_file.write_text("\n".join(lines), encoding="utf-8")
