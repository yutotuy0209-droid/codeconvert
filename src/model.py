"""Language-neutral intermediate representation for code visualization."""

from __future__ import annotations
from dataclasses import dataclass, asdict
import json
from pathlib import Path


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


def write_json(items: list[FunctionInfo], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(item) for item in items], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
