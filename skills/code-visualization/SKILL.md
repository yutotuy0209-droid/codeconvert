# Code Visualization Skill

## Use when

You need to understand or explain an unfamiliar source file by function rather than by reading the whole file line by line.

## Goal

Produce a small, reusable visual explanation of each function and a lightweight overview of the module.

## Default workflow

1. Parse the source structurally.
2. Extract function name, arguments, source range, docstring, called functions, and return expressions.
3. Save the extracted structure as JSON when later reuse is likely.
4. Generate one SVG per function for detailed explanation.
5. Generate one overview SVG for the file.
6. Keep the source code as the source of truth; the diagram is documentation, not a replacement.

## Visualization rules

- One function diagram should answer one main question.
- Prefer input → processing → output over full syntax-tree detail.
- Show helper calls, but do not give them the same visual weight as the function being explained.
- Do not include every local variable by default.
- Use source line ranges so the reader can jump back to the implementation.
- Regenerate diagrams after code changes rather than editing SVG manually.

## Current implementation

`src/function_to_svg.py` supports Python using only the standard library.

Future language adapters should normalize into the same intermediate structure before rendering so C++, MATLAB, and other languages can share the renderer.
