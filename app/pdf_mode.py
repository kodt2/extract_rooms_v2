from __future__ import annotations

from pathlib import Path

from app.config import AppConfig
from app.models import AllocationResult


class PdfPayloadBuilder:
    """Builds a lightweight printable payload for future PDF rendering."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def build_text_report(self, allocations: list[AllocationResult]) -> str:
        lines = ["Room allocation report", "====================", ""]
        if self._config.contact_fields:
            lines.append("Configured contacts:")
            for key, value in self._config.contact_fields.items():
                lines.append(f"- {key}: {value}")
            lines.append("")

        lines.append("Requests:")
        for item in allocations:
            lines.append(
                f"- {item.request.full_name} | {item.request.goal} | {item.request.day.isoformat()} "
                f"{item.request.slot.start.strftime('%H:%M')}-{item.request.slot.end.strftime('%H:%M')} "
                f"=> {item.room or item.status}"
            )

        return "\n".join(lines)

    def save_report(self, allocations: list[AllocationResult], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.build_text_report(allocations), encoding="utf-8")
        return output_path
