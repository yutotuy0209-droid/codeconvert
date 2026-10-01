# Changelog

## 2026-10-01

- Reject ambiguous function-name selection instead of silently drawing the first definition.
- Add explicit definition-start-line selection with `--function NAME --line N`.
- Preserve repeated definitions in split SVG output with line-number suffixes; retain existing filenames for unique names.
- Add CLI regression tests without copying project source or research results into this repository.
- Compute function SVG canvas height from actual section geometry so return values are not clipped; test all section bounds.
