"""Project-wide Code Relationship Mapper & Token-Optimizer.

狙い:
  1. 【トークンの省エネ化】:
     AI (LLM) に数万行のソースコードを丸ごと読ませる代わりに、
     正規化された関数シグネチャ・入出力・呼び出し関係・行番号を極小トークン（約1〜2KB）
     の Markdown / JSON に圧縮して提供する。
  2. 【人間の省エネ化】:
     AGENTS.md 10大原則準拠のコード地図SVGを一括生成し、
     全体をブラウザで俯瞰・クリック探索できるHTMLビューアを出力する。
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import asdict, dataclass
import html
import json
from pathlib import Path
import re
import sys

from code_to_svg import analyze
from model import FunctionInfo
from renderer import render_code_map_svg, render_function_svg, slugify


@dataclass(frozen=True)
class FileRelation:
    source: str
    target: str
    relation: str
    labels: tuple[str, ...] = ()


def _node_id(path: str) -> str:
    return "n_" + re.sub(r"[^A-Za-z0-9_]+", "_", path).strip("_")


def _python_import_targets(path: Path, root: Path, known_files: set[str]) -> set[str]:
    """Resolve only repository-local Python imports that can be identified safely."""
    if path.suffix.lower() != ".py":
        return set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except Exception:
        return set()

    rel = path.relative_to(root)
    package_parts = list(rel.with_suffix("").parts[:-1])
    targets: set[str] = set()

    def candidate_paths(module_parts: list[str]) -> list[str]:
        if not module_parts:
            return []
        base = "/".join(module_parts)
        return [base + ".py", base + "/__init__.py"]

    for node in ast.walk(tree):
        modules: list[list[str]] = []
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name.split("."))
        elif isinstance(node, ast.ImportFrom):
            base_parts = node.module.split(".") if node.module else []
            if node.level:
                prefix = package_parts[: max(0, len(package_parts) - node.level + 1)]
                base_parts = prefix + base_parts
            if base_parts:
                modules.append(base_parts)
            for alias in node.names:
                if alias.name != "*":
                    modules.append(base_parts + alias.name.split("."))

        for parts in modules:
            for candidate in candidate_paths(parts):
                if candidate in known_files and candidate != rel.as_posix():
                    targets.add(candidate)
                    break
    return targets


def build_file_relations(
    target_dir: Path,
    project_items: dict[str, list[FunctionInfo]],
) -> tuple[list[FileRelation], list[dict[str, object]]]:
    """Resolve repository-local file edges conservatively.

    Function-call edges are added only when a called symbol resolves to exactly one
    other file. Ambiguous names are reported instead of guessed.
    """
    known_files = set(project_items)
    symbol_files: dict[str, set[str]] = {}
    for file_name, funcs in project_items.items():
        for func in funcs:
            for symbol in {func.name, func.qualified_name, func.qualified_name.split(".")[-1]}:
                symbol_files.setdefault(symbol, set()).add(file_name)

    edge_labels: dict[tuple[str, str, str], set[str]] = {}
    ambiguities: list[dict[str, object]] = []

    def add_edge(source: str, target: str, relation: str, label: str = "") -> None:
        if source == target:
            return
        key = (source, target, relation)
        edge_labels.setdefault(key, set())
        if label:
            edge_labels[key].add(label)

    for source, funcs in project_items.items():
        for func in funcs:
            for call in func.calls:
                symbol = call.split(".")[-1]
                candidates = {
                    f for f in symbol_files.get(symbol, set())
                    if f != source
                }
                if len(candidates) == 1:
                    add_edge(source, next(iter(candidates)), "call", symbol)
                elif len(candidates) > 1:
                    ambiguities.append({
                        "source": source,
                        "caller": func.qualified_name,
                        "symbol": symbol,
                        "candidates": sorted(candidates),
                    })

        source_path = target_dir / source
        for target in _python_import_targets(source_path, target_dir, known_files):
            add_edge(source, target, "import", "")

    relations = [
        FileRelation(source=s, target=t, relation=kind, labels=tuple(sorted(labels)))
        for (s, t, kind), labels in sorted(edge_labels.items())
    ]
    return relations, ambiguities


def generate_mermaid(
    project_items: dict[str, list[FunctionInfo]],
    relations: list[FileRelation],
) -> str:
    lines = ["flowchart LR"]
    for file_name in sorted(project_items):
        node = _node_id(file_name)
        label = file_name.replace('"', "'")
        lines.append(f'  {node}["{label}"]')
    for rel in relations:
        source = _node_id(rel.source)
        target = _node_id(rel.target)
        label = rel.relation.upper()
        if rel.labels:
            label += ": " + ", ".join(rel.labels[:4])
            if len(rel.labels) > 4:
                label += " …"
        lines.append(f'  {source} -->|"{label}"| {target}')
    return "\n".join(lines) + "\n"


def _svg_text(x: int, y: int, text: str, size: int = 14, weight: int = 400, fill: str = "#111827") -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="Yu Gothic, Segoe UI, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">'
        f'{html.escape(text)}</text>'
    )


def generate_relationship_svg(
    project_items: dict[str, list[FunctionInfo]],
    relations: list[FileRelation],
) -> str:
    """PowerPoint-friendly file relationship map using native SVG primitives."""
    files = sorted(project_items)
    if not files:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="240"></svg>'

    width = 1500
    box_w, box_h = 330, 96
    cols = 3
    gap_x, gap_y = 130, 105
    margin_x, margin_y = 70, 120
    rows = (len(files) + cols - 1) // cols
    height = margin_y + rows * (box_h + gap_y) + 90

    positions: dict[str, tuple[int, int]] = {}
    for i, file_name in enumerate(files):
        row, col = divmod(i, cols)
        positions[file_name] = (
            margin_x + col * (box_w + gap_x),
            margin_y + row * (box_h + gap_y),
        )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<defs>",
        '<marker id="arrow-call" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#2563EB"/></marker>',
        '<marker id="arrow-import" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#64748B"/></marker>',
        "</defs>",
        '<rect width="100%" height="100%" fill="#F8FAFC"/>',
        _svg_text(60, 48, "Project File Relationship Map", 28, 700, "#0F172A"),
        _svg_text(60, 78, "Arrow direction: caller/importer → dependency", 14, 400, "#64748B"),
    ]

    # Draw edges first so boxes stay on top.
    for rel in relations:
        if rel.source not in positions or rel.target not in positions:
            continue
        sx, sy = positions[rel.source]
        tx, ty = positions[rel.target]
        x1, y1 = sx + box_w / 2, sy + box_h / 2
        x2, y2 = tx + box_w / 2, ty + box_h / 2
        color = "#2563EB" if rel.relation == "call" else "#64748B"
        marker = "arrow-call" if rel.relation == "call" else "arrow-import"
        dash = "" if rel.relation == "call" else ' stroke-dasharray="7 5"'
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color}" stroke-width="2" marker-end="url(#{marker})"{dash}/>'
        )
        label = rel.relation.upper()
        if rel.labels:
            label += " · " + ", ".join(rel.labels[:2])
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 7
        parts.append(
            f'<rect x="{mx - 72}" y="{my - 15}" width="144" height="22" rx="5" fill="#F8FAFC" opacity="0.94"/>'
        )
        parts.append(_svg_text(int(mx - 66), int(my), label[:28], 11, 700, color))

    for file_name in files:
        x, y = positions[file_name]
        funcs = project_items[file_name]
        parts.append(
            f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="12" '
            'fill="#FFFFFF" stroke="#475569" stroke-width="1.5"/>'
        )
        short_name = file_name if len(file_name) <= 42 else "…" + file_name[-41:]
        parts.append(_svg_text(x + 16, y + 30, short_name, 14, 700, "#0F172A"))
        parts.append(_svg_text(x + 16, y + 55, f"{len(funcs)} functions", 12, 400, "#64748B"))
        sample = ", ".join(f.name for f in funcs[:3]) or "(no functions)"
        if len(sample) > 46:
            sample = sample[:45] + "…"
        parts.append(_svg_text(x + 16, y + 77, sample, 11, 400, "#334155"))

    parts += [
        _svg_text(60, height - 34, "Blue = resolved function call   /   Gray dashed = local Python import", 12, 400, "#64748B"),
        "</svg>",
    ]
    return "\n".join(parts)


def generate_token_map_markdown(project_items: dict[str, list[FunctionInfo]]) -> str:
    """AI (LLM) が最小トークンでコード全体と関連性を把握できる要約Markdownを生成する。"""
    lines = [
        "# Project Code Structure & Relationship Map",
        "> Auto-generated by codeconvert for Token Optimization & Zero-Cognitive-Load Context",
        "",
    ]

    total_funcs = sum(len(funcs) for funcs in project_items.values())
    lines.append(f"**Total Modules**: {len(project_items)} | **Total Functions**: {total_funcs}\n")

    for file_name, funcs in sorted(project_items.items()):
        lines.append(f"## File: `{file_name}`")
        for f in funcs:
            args = ", ".join(f.arguments) if f.arguments else "void"
            rets = ", ".join(f.returns) if f.returns else "void"
            calls = ", ".join(f.calls[:8]) if f.calls else "none"
            lines.append(
                f"- **`{f.qualified_name}({args}) -> {rets}`** [L{f.lineno}-L{f.end_lineno}]\n"
                f"  - Calls: `{calls}`"
            )
            if f.doc:
                first_line = f.doc.strip().split("\n")[0]
                lines.append(f"  - Summary: {first_line[:90]}")
        lines.append("")

    return "\n".join(lines)


def generate_html_dashboard(project_items: dict[str, list[FunctionInfo]], output_dir: Path) -> str:
    """人間が一目で全体と各ファイルのSVGを閲覧できるHTMLダッシュボードを生成する。"""
    items_html = []
    for file_name, funcs in sorted(project_items.items()):
        slug = slugify(file_name)
        svg_file = f"{slug}.svg"
        items_html.append(f"""
        <div class="card">
            <h3>📄 {file_name} <span class="badge">{len(funcs)} functions</span></h3>
            <p><a href="{svg_file}" target="_blank">🔍 SVGコード地図を開く</a></p>
            <ul>
        """)
        for f in funcs[:6]:
            items_html.append(f"<li><code>{f.name}</code> (L{f.lineno}-L{f.end_lineno})</li>")
        if len(funcs) > 6:
            items_html.append(f"<li>... 他 {len(funcs) - 6} 件</li>")
        items_html.append("""
            </ul>
        </div>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>コード関係地図 ＆ トークン省エネダッシュボード</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Yu Gothic", sans-serif; background: #0F172A; color: #F8FAFC; margin: 0; padding: 24px; }}
    h1 {{ color: #60A5FA; margin-bottom: 8px; }}
    .subtitle {{ color: #94A3B8; margin-bottom: 24px; font-size: 15px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 20px; }}
    .card {{ background: #1E293B; border: 1px solid #334155; border-radius: 12px; padding: 20px; }}
    .card h3 {{ margin-top: 0; color: #F1F5F9; font-size: 18px; }}
    .badge {{ background: #2563EB; color: #FFF; font-size: 12px; padding: 3px 8px; border-radius: 12px; }}
    a {{ color: #38BDF8; text-decoration: none; font-weight: bold; }}
    a:hover {{ text-decoration: underline; }}
    ul {{ padding-left: 20px; color: #CBD5E1; font-size: 14px; }}
    code {{ background: #0F172A; padding: 2px 6px; border-radius: 4px; color: #38BDF8; }}
    .btn {{ display: inline-block; background: #2563EB; color: white; padding: 10px 18px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-bottom: 24px; }}
    .btn:hover {{ background: #1D4ED8; }}
</style>
</head>
<body>
<h1>🧭 コード関係地図 ＆ トークン省エネダッシュボード</h1>
<div class="subtitle">AIトークンの省エネ化 ＆ 人間の認知負荷ゼロ化のための自動可視化システム</div>
<a class="btn" href="repo_map.md" target="_blank">📋 AI用トークン省エネ要約 (repo_map.md) を開く</a>
<div class="grid">
{''.join(items_html)}
</div>
</body>
</html>
"""
    return html_content


def scan_and_map_project(target_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    project_items: dict[str, list[FunctionInfo]] = {}

    extensions = {".cpp", ".hpp", ".c", ".h", ".py", ".m"}
    files = [
        p for p in target_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in extensions and "test" not in p.name.lower()
    ]

    print(f"[SCAN] Found {len(files)} source files in {target_dir}")

    for file_path in files:
        try:
            rel_name = file_path.relative_to(target_dir).as_posix()
            funcs = analyze(file_path)
            if funcs:
                project_items[rel_name] = funcs
                # SVG生成
                slug = slugify(rel_name)
                svg_content = render_code_map_svg(funcs, rel_name)
                (output_dir / f"{slug}.svg").write_text(svg_content, encoding="utf-8")
        except Exception as e:
            print(f"[WARN] Skipped {file_path.name}: {e}")

    relations, ambiguities = build_file_relations(target_dir, project_items)

    # 1. AI用トークン省エネ要約 Markdown
    token_md = generate_token_map_markdown(project_items)
    (output_dir / "repo_map.md").write_text(token_md, encoding="utf-8")

    # 2. JSON 中間表現
    summary_data = {
        name: [f.__dict__ for f in funcs]
        for name, funcs in project_items.items()
    }
    (output_dir / "repo_map.json").write_text(
        json.dumps(summary_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 3. ファイル間関係図: SVG / Mermaid / JSON
    (output_dir / "file_relationships.svg").write_text(
        generate_relationship_svg(project_items, relations), encoding="utf-8"
    )
    (output_dir / "file_relationships.mmd").write_text(
        generate_mermaid(project_items, relations), encoding="utf-8"
    )
    (output_dir / "file_relationships.json").write_text(
        json.dumps({
            "relations": [asdict(item) for item in relations],
            "ambiguities": ambiguities,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 4. 人間用 HTML ダッシュボード
    html = generate_html_dashboard(project_items, output_dir)
    html = html.replace(
        '<a class="btn" href="repo_map.md" target="_blank">📋 AI用トークン省エネ要約 (repo_map.md) を開く</a>',
        '<a class="btn" href="repo_map.md" target="_blank">📋 AI用トークン省エネ要約</a> '
        '<a class="btn" href="file_relationships.svg" target="_blank">🧭 ファイル関係SVG</a> '
        '<a class="btn" href="file_relationships.mmd" target="_blank">🧩 Mermaid</a>'
    )
    (output_dir / "index.html").write_text(html, encoding="utf-8")

    print(f"[SUCCESS] Code relationship maps generated at: {output_dir}")
    print(f"          - Human Map: {output_dir / 'index.html'}")
    print(f"          - File Relationship SVG: {output_dir / 'file_relationships.svg'}")
    print(f"          - Mermaid: {output_dir / 'file_relationships.mmd'}")
    print(f"          - AI Token Map: {output_dir / 'repo_map.md'}")
    if ambiguities:
        print(f"          - Ambiguous calls not guessed: {len(ambiguities)}")


def main():
    p = argparse.ArgumentParser(description="Map project code relationships and optimize AI tokens.")
    p.add_argument("target_dir", type=Path, help="Target directory containing source files")
    p.add_argument("--out", type=Path, default=Path("output/project_map"), help="Output directory")
    args = p.parse_args()

    scan_and_map_project(args.target_dir, args.out)


if __name__ == "__main__":
    main()
