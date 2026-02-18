from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_TEMPLATE_RE = re.compile(r"{{\s*([\w.]+)\s*}}")


@dataclass
class PdfTemplateConfig:
    page_width: float
    page_height: float
    default_font: str
    default_font_size: float
    pages: list[dict[str, Any]]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PdfTemplateConfig":
        page = payload.get("page", {})
        return cls(
            page_width=float(page.get("width", 595.28)),
            page_height=float(page.get("height", 841.89)),
            default_font=str(payload.get("default_font", {}).get("name", "Helvetica")),
            default_font_size=float(payload.get("default_font", {}).get("size", 12)),
            pages=list(payload.get("pages", [])),
        )


class TemplateRenderError(ValueError):
    """Raised when template payload is malformed."""


class ConfigurablePdfRenderer:
    def __init__(self, config: PdfTemplateConfig):
        self.config = config

    @classmethod
    def from_json(cls, path: Path) -> "ConfigurablePdfRenderer":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(PdfTemplateConfig.from_dict(payload))

    def render_to_file(self, data: dict[str, Any], output_path: Path) -> Path:
        pages = self._build_pages(data)
        pdf_bytes = _PdfWriter(self.config.page_width, self.config.page_height).build(pages)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(pdf_bytes)
        return output_path

    def _build_pages(self, data: dict[str, Any]) -> list[list[dict[str, Any]]]:
        built_pages: list[list[dict[str, Any]]] = []
        if not self.config.pages:
            raise TemplateRenderError("Template config does not contain pages")

        for page_spec in self.config.pages:
            repeat_for = page_spec.get("repeat_for")
            if repeat_for:
                source = _resolve_path(data, repeat_for)
                if not isinstance(source, list):
                    raise TemplateRenderError(f"repeat_for path '{repeat_for}' is not an array")
                for index, item in enumerate(source):
                    page_context = {**data, "item": item, "index": index}
                    built_pages.append(self._build_page_items(page_spec, page_context))
            else:
                built_pages.append(self._build_page_items(page_spec, data))

        return built_pages

    def _build_page_items(self, page_spec: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in page_spec.get("items", []):
            item_type = item.get("type", "text")
            if item_type == "text":
                result.append(self._materialize_text(item, context))
                continue
            if item_type == "array_text":
                result.extend(self._materialize_array_text(item, context))
                continue
            raise TemplateRenderError(f"Unsupported item type: {item_type}")
        return result

    def _materialize_text(self, item: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        text = _render_template(str(item.get("value", "")), context)
        return {
            "text": text,
            "align": item.get("align", "left"),
            "top": item.get("top"),
            "bottom": item.get("bottom"),
            "margin_left": float(item.get("margin_left", 0)),
            "margin_right": float(item.get("margin_right", 0)),
            "font": item.get("font", self.config.default_font),
            "font_size": float(item.get("font_size", self.config.default_font_size)),
        }

    def _materialize_array_text(self, item: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
        source_name = item.get("source")
        if not source_name:
            raise TemplateRenderError("array_text item requires source")
        source = _resolve_path(context, source_name)
        if not isinstance(source, list):
            raise TemplateRenderError(f"array_text source '{source_name}' is not an array")

        start_top = float(item.get("top", 0))
        line_height = float(item.get("line_height", item.get("font_size", self.config.default_font_size) + 2))
        template = str(item.get("item_template", "{{item}}"))

        rows: list[dict[str, Any]] = []
        for index, entry in enumerate(source):
            line_context = {**context, "item": entry, "index": index}
            rows.append(
                {
                    "text": _render_template(template, line_context),
                    "align": item.get("align", "left"),
                    "top": start_top + line_height * index,
                    "bottom": item.get("bottom"),
                    "margin_left": float(item.get("margin_left", 0)),
                    "margin_right": float(item.get("margin_right", 0)),
                    "font": item.get("font", self.config.default_font),
                    "font_size": float(item.get("font_size", self.config.default_font_size)),
                }
            )
        return rows


def _resolve_path(context: dict[str, Any], path: str) -> Any:
    value: Any = context
    for segment in path.split("."):
        if isinstance(value, dict) and segment in value:
            value = value[segment]
            continue
        raise TemplateRenderError(f"Unknown template path: {path}")
    return value


def _render_template(raw: str, context: dict[str, Any]) -> str:
    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        value = _resolve_path(context, key)
        return str(value)

    return _TEMPLATE_RE.sub(_replace, raw)


class _PdfWriter:
    def __init__(self, page_width: float, page_height: float):
        self.page_width = page_width
        self.page_height = page_height

    def build(self, pages: list[list[dict[str, Any]]]) -> bytes:
        if not pages:
            raise TemplateRenderError("No pages to render")

        objects: list[bytes] = []
        font_object_id = 3
        content_object_start_id = 4
        page_object_start_id = content_object_start_id + len(pages)

        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")

        page_refs = " ".join(f"{page_object_start_id + i} 0 R" for i in range(len(pages)))
        objects.append(f"<< /Type /Pages /Count {len(pages)} /Kids [{page_refs}] >>".encode("utf-8"))
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

        for page in pages:
            stream = self._build_page_stream(page)
            objects.append(
                f"<< /Length {len(stream)} >>\nstream\n".encode("utf-8") + stream + b"\nendstream"
            )

        for i in range(len(pages)):
            content_obj = content_object_start_id + i
            objects.append(
                (
                    "<< /Type /Page /Parent 2 0 R "
                    f"/MediaBox [0 0 {self.page_width:.2f} {self.page_height:.2f}] "
                    "/Resources << /Font << /F1 3 0 R >> >> "
                    f"/Contents {content_obj} 0 R >>"
                ).encode("utf-8")
            )

        return self._serialize(objects)

    def _build_page_stream(self, page: list[dict[str, Any]]) -> bytes:
        lines = [b"BT"]
        for item in page:
            text = _escape_pdf_string(item["text"])
            font_size = float(item.get("font_size", 12))
            x, y = self._resolve_position(item, text, font_size)
            lines.append(f"/F1 {font_size:.2f} Tf".encode("utf-8"))
            lines.append(f"1 0 0 1 {x:.2f} {y:.2f} Tm".encode("utf-8"))
            lines.append(f"({text}) Tj".encode("utf-8"))
        lines.append(b"ET")
        return b"\n".join(lines)

    def _resolve_position(self, item: dict[str, Any], text: str, font_size: float) -> tuple[float, float]:
        margin_left = float(item.get("margin_left", 0))
        margin_right = float(item.get("margin_right", 0))

        available_width = self.page_width - margin_left - margin_right
        text_width = _estimate_text_width(text, font_size)

        align = item.get("align", "left")
        if align == "left":
            x = margin_left
        elif align == "center":
            x = margin_left + max(0.0, (available_width - text_width) / 2)
        elif align == "right":
            x = self.page_width - margin_right - text_width
        else:
            raise TemplateRenderError(f"Unsupported align value: {align}")

        if item.get("top") is not None:
            y = self.page_height - float(item["top"]) - font_size
        elif item.get("bottom") is not None:
            y = float(item["bottom"])
        else:
            raise TemplateRenderError("Every text item must define top or bottom")

        return x, y

    def _serialize(self, object_bodies: list[bytes]) -> bytes:
        header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
        chunks = [header]
        offsets = [0]
        cursor = len(header)

        for index, body in enumerate(object_bodies, start=1):
            obj = f"{index} 0 obj\n".encode("utf-8") + body + b"\nendobj\n"
            offsets.append(cursor)
            chunks.append(obj)
            cursor += len(obj)

        xref_start = cursor
        xref_lines = [f"0 {len(object_bodies) + 1}", "0000000000 65535 f "]
        xref_lines.extend(f"{offset:010d} 00000 n " for offset in offsets[1:])
        xref_blob = "xref\n" + "\n".join(xref_lines) + "\n"
        trailer = (
            f"trailer\n<< /Size {len(object_bodies) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n"
        )
        chunks.append(xref_blob.encode("utf-8"))
        chunks.append(trailer.encode("utf-8"))
        return b"".join(chunks)


def _escape_pdf_string(text: str) -> str:
    text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return text.encode("cp1251", errors="replace").decode("cp1251")


def _estimate_text_width(text: str, font_size: float) -> float:
    return len(text) * font_size * 0.52
