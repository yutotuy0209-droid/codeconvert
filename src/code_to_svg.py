#!/usr/bin/env python3
"""Language-neutral CLI: source code -> normalized model -> SVG/JSON."""

from __future__ import annotations
import argparse
import ast
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from model import FunctionInfo, write_json
from renderer import render_function_svg, render_module_svg, slugify
from cpp_adapter import analyze_cpp
from matlab_adapter import analyze_matlab


def safe_unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return node.__class__.__name__


def analyze_python(path: Path) -> list[FunctionInfo]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    items: list[FunctionInfo] = []

    class Collector(ast.NodeVisitor):
        def __init__(self):
            self.stack = []

        def visit_ClassDef(self, node):
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def collect(self, node):
            q = ".".join([*self.stack, node.name]) if self.stack else node.name
            args = [a.arg + (f": {safe_unparse(a.annotation)}" if a.annotation else "") for a in [*node.args.posonlyargs, *node.args.args]]
            calls = sorted({safe_unparse(n.func) for n in ast.walk(node) if isinstance(n, ast.Call)})
            returns = [safe_unparse(n.value) if n.value else "None" for n in ast.walk(node) if isinstance(n, ast.Return)]
            items.append(FunctionInfo(
                node.name, q,
                "Python async function" if isinstance(node, ast.AsyncFunctionDef) else "Python function",
                node.lineno, getattr(node, "end_lineno", node.lineno),
                args, [safe_unparse(d) for d in node.decorator_list],
                (ast.get_docstring(node) or "")[:220], calls[:24], returns[:8]
            ))
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_FunctionDef(self, node): self.collect(node)
        def visit_AsyncFunctionDef(self, node): self.collect(node)

    Collector().visit(tree)
    return items


def analyze(path: Path) -> list[FunctionInfo]:
    ext = path.suffix.lower()
    if ext == ".py":
        return analyze_python(path)
    if ext in {".cpp", ".cc", ".cxx", ".c", ".hpp", ".hxx", ".h"}:
        return analyze_cpp(path)
    if ext == ".m":
        return analyze_matlab(path)
    raise SystemExit(f"Unsupported extension: {ext}")


def main() -> int:
    p = argparse.ArgumentParser(description="Generate reusable function SVG documentation.")
    p.add_argument("source", type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--json", dest="json_path", type=Path)
    p.add_argument("--function", dest="function_name")
    p.add_argument("--line", type=int, help="Select a function by its definition start line; disambiguates repeated names.")
    p.add_argument("--split", type=Path)
    args = p.parse_args()
    if args.line is not None and not args.function_name:
        p.error("--line requires --function")

    items = analyze(args.source)
    if not items:
        raise SystemExit("No functions were detected.")

    if args.json_path:
        write_json(items, args.json_path)

    if args.split:
        args.split.mkdir(parents=True, exist_ok=True)
        for item in items:
            duplicate = sum(i.qualified_name == item.qualified_name for i in items) > 1
            suffix = f"-L{item.lineno}" if duplicate else ""
            (args.split / f"{slugify(item.qualified_name)}{suffix}.svg").write_text(
                render_function_svg(item, args.source.name), encoding="utf-8"
            )

    if args.function_name:
        matches = [i for i in items if i.qualified_name == args.function_name or i.name == args.function_name]
        if not matches:
            raise SystemExit("Function not found. Available: " + ", ".join(i.qualified_name for i in items))
        if args.line is not None:
            matches = [i for i in matches if i.lineno == args.line]
            if not matches:
                raise SystemExit("No matching function at line " + str(args.line))
        if len(matches) != 1:
            raise SystemExit("Ambiguous function; use --line. Definition lines: " + ", ".join(str(i.lineno) for i in matches))
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
