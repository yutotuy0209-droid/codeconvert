#!/usr/bin/env python3
"""Generate reusable SVG documentation for Python functions.

Examples:
    python src/function_to_svg.py sample.py --out output/sample.svg
    python src/function_to_svg.py sample.py --split output/functions
    python src/function_to_svg.py sample.py --function process --out output/process.svg
    python src/function_to_svg.py sample.py --json output/sample.json

The implementation intentionally uses only the Python standard library so it can
be dropped into small personal projects without adding a visualization stack.
"""

from __future__ import annotations

import argparse
import ast
import html
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class FunctionInfo:
    name: str
    qualified_name: str
    kind: str
    lineno: int
    end_lineno: int
    arguments: list[str]
    decorators: list[str]
    doc: str
    calls: list[str]
    returns: list[str]


def safe_unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return node.__class__.__name__


def short(text: str, limit: int = 96) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def slugify(text: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")
    return value or "function"


def call_name(node: ast.Call) -> str:
    fn = node.func
    if isinstance(fn, ast.Name):
        return fn.id
    if isinstance(fn, ast.Attribute):
        parts: list[str] = [fn.attr]
        value = fn.value
        while isinstance(value, ast.Attribute):
            parts.append(value.attr)
            value = value.value
        if isinstance(value, ast.Name):
            parts.append(value.id)
        return ".".join(reversed(parts))
    return safe_unparse(fn)


def format_arg(arg: ast.arg, default: ast.AST | None = None) -> str:
    text = arg.arg
    if arg.annotation is not None:
        text += f": {safe_unparse(arg.annotation)}"
    if default is not None:
        text += f" = {safe_unparse(default)}"
    return text


def function_arguments(args: ast.arguments) -> list[str]:
    result: list[str] = []
    positional = [*args.posonlyargs, *args.args]
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)

    for arg, default in zip(positional, defaults):
        result.append(format_arg(arg, default))

    if args.vararg:
        result.append("*" + format_arg(args.vararg))
    elif args.kwonlyargs:
        result.append("*")

    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        result.append(format_arg(arg, default))

    if args.kwarg:
        result.append("**" + format_arg(args.kwarg))

    return result


class FunctionCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.stack: list[str] = []
        self.items: list[FunctionInfo] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qualified = ".".join([*self.stack, node.name]) if self.stack else node.name
        calls = sorted({call_name(n) for n in ast.walk(node) if isinstance(n, ast.Call)})
        returns = [
            short(safe_unparse(n.value), 120) if n.value is not None else "None"
            for n in ast.walk(node)
            if isinstance(n, ast.Return)
        ]
        doc = ast.get_docstring(node) or ""
        decorators = [safe_unparse(d) for d in node.decorator_list]

        self.items.append(
            FunctionInfo(
                name=node.name,
                qualified_name=qualified,
                kind="async function" if isinstance(node, ast.AsyncFunctionDef) else "function",
                lineno=node.lineno,
                end_lineno=getattr(node, "end_lineno", node.lineno),
                arguments=function_arguments(node.args),
                decorators=decorators,
                doc=short(doc, 220),
                calls=calls,
                returns=returns[:8],
            )
        )

        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)


def analyze_python(path: Path) -> list[FunctionInfo]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    collector = FunctionCollector()
    collector.visit(tree)
    return collector.items


def esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def wrap_lines(text: str, width: int = 76) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
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
    sections: list[tuple[str, list[str]]] = [
        ("Arguments", info.arguments or ["(none)"]),
        ("Calls", info.calls or ["(none detected)"]),
        ("Returns", info.returns or ["(no explicit return)"]),
    ]
    if info.decorators:
        sections.insert(0, ("Decorators", info.decorators))

    doc_lines = wrap_lines(info.doc, 80) if info.doc else ["No docstring."]
    content_lines = len(doc_lines) + sum(1 + len(items) for _, items in sections)
    height = max(540, 260 + content_lines * 30)
    width = 1080

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
        parts.append(svg_text(68, y, line, 16, 400, "#111827"))
        y += 26

    y = max(326, y + 22)
    colors = ["#EFF6FF", "#F0FDF4", "#FFF7ED", "#FAF5FF"]
    borders = ["#93C5FD", "#86EFAC", "#FDBA74", "#D8B4FE"]

    for index, (title, items) in enumerate(sections):
        section_height = 54 + max(1, len(items)) * 28
        parts.append(
            f'<rect x="40" y="{y}" width="1000" height="{section_height}" rx="18" '
            f'fill="{colors[index % len(colors)]}" stroke="{borders[index % len(borders)]}"/>'
        )
        parts.append(svg_text(68, y + 32, title, 18, 700, "#334155"))
        line_y = y + 62
        for item in items:
            parts.append(svg_text(84, line_y, "• " + short(item, 105), 16, 400, "#111827"))
            line_y += 28
        y += section_height + 18

    parts.append("</svg>")
    return "\n".join(parts)


def render_module_svg(items: list[FunctionInfo], source_name: str) -> str:
    width = 1280
    card_w = 570
    card_h = 210
    gap_x = 60
    gap_y = 34
    columns = 2
    rows = max(1, (len(items) + columns - 1) // columns)
    height = 150 + rows * (card_h + gap_y) + 50

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#F8FAFC"/>',
        svg_text(50, 62, f"Function Map · {source_name}", 30, 700, "#0F172A"),
        svg_text(50, 94, f"{len(items)} functions detected", 16, 400, "#64748B"),
    ]

    for i, info in enumerate(items):
        col = i % columns
        row = i // columns
        x = 50 + col * (card_w + gap_x)
        y = 126 + row * (card_h + gap_y)
        parts.append(
            f'<rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="18" '
            'fill="#FFFFFF" stroke="#CBD5E1"/>'
        )
        parts.append(svg_text(x + 24, y + 38, info.qualified_name, 20, 700, "#0F172A"))
        parts.append(svg_text(x + 24, y + 66, f"lines {info.lineno}-{info.end_lineno}", 14, 400, "#64748B"))
        summary = info.doc or "No docstring."
        for j, line in enumerate(wrap_lines(short(summary, 140), 64)[:2]):
            parts.append(svg_text(x + 24, y + 98 + j * 23, line, 14, 400, "#334155"))
        calls = ", ".join(info.calls[:5]) if info.calls else "(none detected)"
        parts.append(svg_text(x + 24, y + 158, "Calls", 14, 700, "#475569"))
        parts.append(svg_text(x + 24, y + 184, short(calls, 72), 14, 400, "#111827"))

    parts.append("</svg>")
    return "\n".join(parts)


def write_json(items: Iterable[FunctionInfo], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(item) for item in items], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate function documentation as SVG.")
    parser.add_argument("source", type=Path, help="Python source file")
    parser.add_argument("--out", type=Path, help="SVG output path")
    parser.add_argument("--json", dest="json_path", type=Path, help="Optional JSON output path")
    parser.add_argument("--function", dest="function_name", help="Render one qualified/simple function name")
    parser.add_argument("--split", type=Path, help="Write one SVG per detected function into this directory")
    args = parser.parse_args()

    items = analyze_python(args.source)
    if not items:
        raise SystemExit("No functions were detected.")

    if args.json_path:
        write_json(items, args.json_path)

    if args.split:
        args.split.mkdir(parents=True, exist_ok=True)
        for item in items:
            path = args.split / f"{slugify(item.qualified_name)}.svg"
            path.write_text(render_function_svg(item, args.source.name), encoding="utf-8")

    if args.function_name:
        matches = [i for i in items if i.qualified_name == args.function_name or i.name == args.function_name]
        if not matches:
            available = ", ".join(i.qualified_name for i in items)
            raise SystemExit(f"Function not found: {args.function_name}. Available: {available}")
        svg = render_function_svg(matches[0], args.source.name)
    else:
        svg = render_module_svg(items, args.source.name)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(svg, encoding="utf-8")
    elif not args.split:
        print(svg)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
