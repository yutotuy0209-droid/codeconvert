"""Lightweight MATLAB function extractor for documentation diagrams."""

from __future__ import annotations
import re
from pathlib import Path
from model import FunctionInfo

FUNC_RE = re.compile(
    r"^\s*function\s+(?:(?P<outs>\[[^\]]*\]|[A-Za-z_]\w*)\s*=\s*)?"
    r"(?P<name>[A-Za-z_]\w*)\s*(?:\((?P<args>[^)]*)\))?",
    re.MULTILINE,
)
CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
KEYWORDS = {"if", "elseif", "for", "while", "switch", "case", "function"}


def split_csv(text: str | None) -> list[str]:
    return [x.strip() for x in (text or "").split(",") if x.strip()]


def analyze_matlab(path: Path) -> list[FunctionInfo]:
    text = path.read_text(encoding="utf-8", errors="replace")
    matches = list(FUNC_RE.finditer(text))
    items: list[FunctionInfo] = []

    for i, match in enumerate(matches):
        start = match.start()
        stop = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[match.end():stop]
        name = match.group("name")
        calls = sorted({
            c for c in CALL_RE.findall(body)
            if c not in KEYWORDS and c != name
        })
        outs = match.group("outs") or ""
        outs = outs.strip("[]")
        returns = split_csv(outs)

        # Consecutive comment lines directly following the declaration become summary.
        doc_lines = []
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped:
                if doc_lines:
                    break
                continue
            if stripped.startswith("%"):
                doc_lines.append(stripped.lstrip("%").strip())
            else:
                break

        lineno = text.count("\n", 0, start) + 1
        end_lineno = text.count("\n", 0, stop) + (0 if stop == len(text) else 1)
        items.append(FunctionInfo(
            name=name,
            qualified_name=name,
            kind="MATLAB function",
            lineno=lineno,
            end_lineno=max(lineno, end_lineno),
            arguments=split_csv(match.group("args")),
            decorators=[],
            doc=" ".join(doc_lines)[:220],
            calls=calls[:24],
            returns=returns[:8],
        ))
    return items
