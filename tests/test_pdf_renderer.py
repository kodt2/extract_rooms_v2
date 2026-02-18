import json
from pathlib import Path

from app.pdf_renderer import ConfigurablePdfRenderer, PdfTemplateConfig


def test_render_pdf_with_array_and_repeat_pages(tmp_path: Path) -> None:
    config = PdfTemplateConfig.from_dict(
        {
            "page": {"width": 300, "height": 300},
            "pages": [
                {
                    "items": [
                        {
                            "type": "text",
                            "value": "{{title}}",
                            "top": 20,
                            "align": "center",
                            "margin_left": 10,
                            "margin_right": 10,
                        },
                        {
                            "type": "array_text",
                            "source": "rows",
                            "item_template": "{{index}}: {{item}}",
                            "top": 50,
                            "line_height": 16,
                            "align": "left",
                            "margin_left": 10,
                        },
                    ]
                },
                {
                    "repeat_for": "appendix",
                    "items": [
                        {
                            "type": "text",
                            "value": "{{item.name}}",
                            "bottom": 10,
                            "align": "right",
                            "margin_right": 10,
                        }
                    ],
                },
            ],
        }
    )
    renderer = ConfigurablePdfRenderer(config)

    output = renderer.render_to_file(
        {
            "title": "Header",
            "rows": ["A", "B"],
            "appendix": [{"name": "P1"}, {"name": "P2"}],
        },
        tmp_path / "result.pdf",
    )

    assert output.exists()
    content = output.read_bytes()
    assert b"%PDF-1.4" in content
    assert b"/Count 3" in content
    assert b"(Header)" in content
    assert b"(0: A)" in content
    assert b"(P1)" in content
    assert b"(P2)" in content


def test_renderer_from_json(tmp_path: Path) -> None:
    template_path = tmp_path / "template.json"
    template_path.write_text(
        json.dumps({"page": {"width": 200, "height": 200}, "pages": [{"items": [{"type": "text", "value": "ok", "top": 10}]}]}),
        encoding="utf-8",
    )

    renderer = ConfigurablePdfRenderer.from_json(template_path)
    out = renderer.render_to_file({}, tmp_path / "o.pdf")
    assert out.exists()
