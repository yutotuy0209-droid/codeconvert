"""Shared SVG renderer for normalized FunctionInfo records.

Complies with AGENTS.md 10-principle C++ code map harness specification.
"""

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
        f'<text x="{x}" y="{y}" font-family="Yu Gothic, Segoe UI, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{esc(text)}</text>'
    )


def render_function_svg(info: FunctionInfo, source_name: str) -> str:
    sections = [
        ("【入力】", info.arguments or ["(なし)"]),
        ("【主な処理】", info.calls or ["(内部直接処理)"]),
        ("【戻り値】", info.returns or ["void"]),
    ]
    if info.decorators:
        sections.insert(0, ("修飾子", info.decorators))

    doc_lines = wrap_lines(info.doc, 80) if info.doc else ["No summary extracted."]
    summary_h = max(118, 66 + 26 * len(doc_lines))
    section_start = max(326, 242 + 26 * len(doc_lines) + 22, 176 + summary_h + 32)
    height = section_start + sum(54 + max(1, len(values)) * 28 + 18 for _, values in sections) + 12
    width = 1080

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#F8FAFC"/>',
        '<rect x="40" y="36" width="1000" height="112" rx="20" fill="#0F172A"/>',
        svg_text(72, 82, info.qualified_name, 30, 700, "#FFFFFF"),
        # Principle 2: #5965A8 location badge
        f'<rect x="72" y="98" width="500" height="34" rx="6" fill="#F3F4F6" stroke="#5965A8" stroke-width="1.5"/>',
        svg_text(84, 121, f"場所: {source_name} : L{info.lineno}-L{info.end_lineno}", 14, 700, "#5965A8"),
        f'<rect x="40" y="176" width="1000" height="{summary_h}" rx="18" fill="#FFFFFF" stroke="#CBD5E1"/>',
        svg_text(68, 210, "Summary", 18, 700, "#334155"),
    ]

    y = 242
    for line in doc_lines:
        parts.append(svg_text(68, y, line, 16))
        y += 26
    y = section_start

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


def render_code_map_svg(items: list[FunctionInfo], source_name: str) -> str:
    """AGENTS.md 10-principle C++ code map SVG generator."""
    width = 840
    box_w = 740
    box_x = 50
    arrow_gap = 56

    boxes = []
    total_y = 120
    for info in items:
        name = info.name
        if name.startswith("func_") or name.startswith("run_"):
            fill, stroke = "#EFF6FF", "#3B82F6"  # Public function (Thin blue)
        elif "pipeline" in name.lower() or "control" in name.lower():
            fill, stroke = "#F0FDF4", "#22C55E"  # Pipeline / Control (Thin green)
        elif "struct" in info.kind.lower() or "class" in info.kind.lower():
            fill, stroke = "#FAF5FF", "#A855F7"  # Struct / Type (Thin purple)
        else:
            fill, stroke = "#FFFFFF", "#94A3B8"  # Internal helper (White / Slate border)

        args_text = ", ".join(info.arguments) if info.arguments else "(なし)"
        calls_text = ", ".join(info.calls) if info.calls else "(内部直接計算)"
        rets_text = ", ".join(info.returns) if info.returns else "void"

        h = 220
        boxes.append({
            "info": info,
            "fill": fill,
            "stroke": stroke,
            "args": args_text,
            "calls": calls_text,
            "rets": rets_text,
            "y": total_y,
            "h": h
        })
        total_y += h + arrow_gap

    height = total_y + 40

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<defs>',
        f'  <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        f'    <path d="M 0 1 L 10 5 L 0 9 z" fill="#475569"/>',
        f'  </marker>',
        f'  <marker id="arrow-dash" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        f'    <path d="M 0 1 L 10 5 L 0 9 z" fill="#64748B"/>',
        f'  </marker>',
        f'</defs>',
        '<rect width="100%" height="100%" fill="#F8FAFC"/>',
        svg_text(50, 52, f"C++ コード関係地図 · {source_name}", 24, 700, "#0F172A"),
        svg_text(50, 84, f"検出関数: {len(items)}件 ｜ スマホ閲覧対応（シングルカラム・実行順・文字重なりゼロ）", 14, 400, "#64748B"),
    ]

    for i, b in enumerate(boxes):
        y = b["y"]
        h = b["h"]
        info = b["info"]

        # Outer card box
        parts.append(f'<rect x="{box_x}" y="{y}" width="{box_w}" height="{h}" rx="14" fill="{b["fill"]}" stroke="{b["stroke"]}" stroke-width="1.8"/>')

        # Tier 1: Function Name
        parts.append(svg_text(box_x + 24, y + 34, f"{info.qualified_name}(...)", 19, 700, "#0F172A"))
        parts.append(f'<line x1="{box_x + 20}" y1="{y + 46}" x2="{box_x + box_w - 20}" y2="{y + 46}" stroke="{b["stroke"]}" stroke-width="0.8" opacity="0.4"/>')

        # Tier 2: 【入力】
        parts.append(svg_text(box_x + 24, y + 70, f"【入力】 {short(b['args'], 80)}", 14, 600, "#334155"))

        # Tier 3: 【主な処理】
        parts.append(svg_text(box_x + 24, y + 98, f"【主な処理】 {short(b['calls'], 80)}", 14, 400, "#475569"))

        # Tier 4: 【戻り値】
        parts.append(svg_text(box_x + 24, y + 126, f"【戻り値】 {short(b['rets'], 80)}", 14, 600, "#0F766E"))

        # Location Badge (Principle 2: #5965A8)
        badge_y = y + 154
        badge_w = box_w - 48
        badge_h = 42
        loc_text = f"場所: {source_name} : L{info.lineno}-L{info.end_lineno}"
        parts.append(f'<rect x="{box_x + 24}" y="{badge_y}" width="{badge_w}" height="{badge_h}" rx="8" fill="#F3F4F6" stroke="#5965A8" stroke-width="1.5"/>')
        parts.append(svg_text(box_x + 40, badge_y + 26, loc_text, 14, 700, "#5965A8"))

        # Arrow to next box
        if i < len(boxes) - 1:
            arrow_start_y = y + h
            arrow_end_y = arrow_start_y + arrow_gap
            mid_x = box_x + box_w // 2

            next_info = boxes[i+1]["info"]
            is_caller = next_info.name in info.calls or any(c in next_info.qualified_name for c in info.calls)
            stroke_style = 'stroke="#475569" stroke-width="2" marker-end="url(#arrow)"' if is_caller else 'stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="5,4" marker-end="url(#arrow-dash)"'
            parts.append(f'<line x1="{mid_x}" y1="{arrow_start_y}" x2="{mid_x}" y2="{arrow_end_y - 8}" {stroke_style}/>')

            data_label = short(next_info.arguments[0] if next_info.arguments else "data", 30)
            parts.append(svg_text(mid_x + 12, arrow_start_y + arrow_gap // 2 + 4, f"渡すデータ: {data_label}", 12, 500, "#64748B"))

    parts.append("</svg>")
    return "\n".join(parts)


def render_module_svg(items: list[FunctionInfo], source_name: str) -> str:
    """Default to the 10-principle single-column code map."""
    return render_code_map_svg(items, source_name)
