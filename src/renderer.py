"""Shared SVG renderer for normalized FunctionInfo records."""

from __future__ import annotations
import html
import re
from model import FunctionInfo


def short(text: str, limit: int = 96) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def slugify(text: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")
    return value or "function"


def esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def wrap_lines(text: str, width: int = 76) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines, current = [], words[0]
    for word in words[1:]:
        if len(current) + 1 + len(word) <= width:
            current += " " + word
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def svg_text(x: int, y: int, text: str, size: int = 17, weight: int = 400, fill: str = "#111827") -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="Segoe UI, Noto Sans JP, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{esc(text)}</text>'
    )


def render_function_svg(info: FunctionInfo, source_name: str) -> str:
    sections = [
        ("Arguments", info.arguments or ["(none)"]),
        ("Calls", info.calls or ["(none detected)"]),
        ("Returns", info.returns or ["(no explicit return)"]),
    ]
    if info.decorators:
        sections.insert(0, ("Decorators", info.decorators))

    doc_lines = wrap_lines(info.doc, 80) if info.doc else ["No summary extracted."]
    content_lines = len(doc_lines) + sum(1 + len(items) for _, items in sections)
    height, width = max(540, 260 + content_lines * 30), 1080

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#F8FAFC"/>',
        '<rect x="40" y="36" width="1000" height="112" rx="20" fill="#0F172A"/>',
        svg_text(72, 82, info.qualified_name, 30, 700, "#FFFFFF"),
        svg_text(72, 118, f"{info.kind} · {source_name}:{info.lineno}-{info.end_lineno}", 16, 400, "#CBD5E1"),
        '<rect x="40" y="176" width="1000" height="118" rx="18" fill="#FFFFFF" stroke="#CBD5E1"/>',
        svg_text(68, 210, "Summary", 18, 700, "#334155"),
    ]

    y = 242
    for line in doc_lines:
        parts.append(svg_text(68, y, line, 16))
        y += 26
    y = max(326, y + 22)

    fills = ["#EFF6FF", "#F0FDF4", "#FFF7ED", "#FAF5FF"]
    borders = ["#93C5FD", "#86EFAC", "#FDBA74", "#D8B4FE"]
    for index, (title, values) in enumerate(sections):
        section_h = 54 + max(1, len(values)) * 28
        parts.append(f'<rect x="40" y="{y}" width="1000" height="{section_h}" rx="18" fill="{fills[index%4]}" stroke="{borders[index%4]}"/>')
        parts.append(svg_text(68, y + 32, title, 18, 700, "#334155"))
        line_y = y + 62
        for value in values:
            parts.append(svg_text(84, line_y, "• " + short(value, 105), 16))
            line_y += 28
        y += section_h + 18

    parts.append("</svg>")
    return "\n".join(parts)


def render_module_svg(items: list[FunctionInfo], source_name: str) -> str:
    width, card_w, card_h, gap_x, gap_y, columns = 1280, 570, 210, 60, 34, 2
    rows = max(1, (len(items) + columns - 1) // columns)
    height = 150 + rows * (card_h + gap_y) + 50
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#F8FAFC"/>',
        svg_text(50, 62, f"Function Map · {source_name}", 30, 700, "#0F172A"),
        svg_text(50, 94, f"{len(items)} functions detected", 16, 400, "#64748B"),
    ]
    for i, info in enumerate(items):
        x = 50 + (i % columns) * (card_w + gap_x)
        y = 126 + (i // columns) * (card_h + gap_y)
        parts.append(f'<rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="18" fill="#FFFFFF" stroke="#CBD5E1"/>')
        parts.append(svg_text(x + 24, y + 38, info.qualified_name, 20, 700, "#0F172A"))
        parts.append(svg_text(x + 24, y + 66, f"{info.kind} · lines {info.lineno}-{info.end_lineno}", 14, 400, "#64748B"))
        for j, line in enumerate(wrap_lines(short(info.doc or "No summary extracted.", 140), 64)[:2]):
            parts.append(svg_text(x + 24, y + 98 + j * 23, line, 14, 400, "#334155"))
        calls = ", ".join(info.calls[:5]) if info.calls else "(none detected)"
        parts.append(svg_text(x + 24, y + 158, "Calls", 14, 700, "#475569"))
        parts.append(svg_text(x + 24, y + 184, short(calls, 72), 14))
    parts.append("</svg>")
    return "\n".join(parts)
