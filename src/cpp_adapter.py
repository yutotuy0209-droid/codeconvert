"""Lightweight C/C++ function extractor.

This intentionally avoids compiler dependencies. It targets documentation and
overview diagrams, not semantic compilation. Complex macros/templates may need
a future clang-based adapter.
"""

from __future__ import annotations
import re
from pathlib import Path
from model import FunctionInfo

CONTROL = {"if", "for", "while", "switch", "catch"}
CALL_RE = re.compile(r"\b([A-Za-z_]\w*(?:::\w+)*)\s*\(")
FUNC_RE = re.compile(
    r"(?P<prefix>(?:template\s*<[^;{}]+>\s*)?(?:[\w:&*<>~,\[\]\s]+?))"
    r"(?P<name>[A-Za-z_]\w*(?:::\w+)*)\s*"
    r"\((?P<args>[^;{}()]*(?:\([^)]*\)[^;{}()]*)*)\)\s*"
    r"(?P<suffix>(?:const\s*)?(?:noexcept\s*)?(?:->\s*[^\{]+)?)\{",
    re.MULTILINE,
)


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def split_args(text: str) -> list[str]:
    if not text.strip() or text.strip() == "void":
        return []
    result, current, depth = [], [], 0
    for ch in text:
        if ch in "(<[{":
            depth += 1
        elif ch in ")>]}":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            result.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        result.append("".join(current).strip())
    return [x for x in result if x]


def matching_brace(text: str, start: int) -> int:
    depth = 0
    in_string = None
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == in_string:
                in_string = None
            continue
        if ch in {'"', "'"}:
            in_string = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    return len(text) - 1


def analyze_cpp(path: Path) -> list[FunctionInfo]:
    original = path.read_text(encoding="utf-8", errors="replace")
    text = strip_comments(original)
    items: list[FunctionInfo] = []

    for match in FUNC_RE.finditer(text):
        name = match.group("name")
        simple = name.split("::")[-1]
        if simple in CONTROL:
            continue

        brace = text.find("{", match.start(), match.end())
        end = matching_brace(text, brace)
        body = text[brace + 1:end]
        calls = sorted({
            c for c in CALL_RE.findall(body)
            if c.split("::")[-1] not in CONTROL and c != simple
        })
        returns = [r.strip() or "void" for r in re.findall(r"\breturn\s*([^;]*);", body)]
        lineno = text.count("\n", 0, match.start()) + 1
        end_lineno = text.count("\n", 0, end) + 1

        prefix = " ".join(match.group("prefix").split())
        kind = "method" if "::" in name else "function"
        items.append(FunctionInfo(
            name=simple,
            qualified_name=name,
            kind=f"C++ {kind}",
            lineno=lineno,
            end_lineno=end_lineno,
            arguments=split_args(match.group("args")),
            decorators=[],
            doc=prefix.strip(),
            calls=calls[:24],
            returns=returns[:8],
        ))
    return items
