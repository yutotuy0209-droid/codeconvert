# ROADMAP

コード理解・言語変換・AIコンテキスト効率化・プレゼン資料化を同じ中間表現の上で扱う。

## Core architecture

```text
Python ─┐
C/C++ ──┼─> language adapters ─> code IR
MATLAB ─┤                         ├─> SVG / Mermaid / JSON
JS etc ─┘                         ├─> PPTX / motion storyboard / optional GIF
                                  ├─> language conversion
                                  └─> minimal AI context
```

## Candidate backlog

- [x] C01 Python parser
- [x] C02 lightweight C/C++ parser
- [x] C03 lightweight MATLAB parser
- [ ] C04 JavaScript parser
- [x] C05 common function IR (initial)
- [x] C06 function SVG
- [x] C07 file relationship map
- [x] C08 repository map (initial)
- [x] C09 call graph (conservative cross-file call edges)
- [ ] C10 data-flow graph
- [ ] C11 entry-point detection
- [ ] C12 dead-code candidates
- [ ] C13 duplicate/similar-code detection
- [ ] C14 Python → C++ conversion workflow
- [ ] C15 MATLAB → Python conversion workflow
- [ ] C16 MATLAB → C++ conversion workflow
- [ ] C17 C++ → Python verification port
- [ ] C18 cross-language function mapping
- [ ] C19 mathematical/algorithm equivalence metadata
- [ ] C20 standard-library / external-library delegation candidates
- [x] C21 token/context size estimator (initial repo_map)
- [x] C22 minimal-context extractor (initial)
- [ ] C23 dependency-aware context expansion
- [ ] C24 code-summary cache
- [ ] C25 Git-diff-aware reanalysis
- [ ] C26 function/file content hashes for cache invalidation
- [x] C27 code → human explanation (initial dashboard)
- [ ] C28 code → teaching material
- [x] C29 code diagrams → presentation handoff (SVG / PPTX / storyboard)
- [x] C30 conversion equivalence tests (initial TDD for mapping/export)

## Current presentation workflow

```text
multiple files/folders
  ↓
project_mapper.py
  ↓
repo_map.json + file_relationships.json
  ↓
file_relationships.svg / .mmd
  ↓
presentation_export.py
  ↓
relationship_deck.pptx
motion_storyboard.html
relationship_motion.gif (optional Pillow)
```

## Remaining hard problems

- C/C++ macro/template-aware parsing
- include graph vs call graph separation in large projects
- true data-flow graph
- entry-point detection
- PowerPoint design presets
- GIF generation without optional Pillow
- changed-file-only incremental reanalysis

## Efficiency principle

一度理解したコードを毎回LLMへ全文投入しない。

```text
repo index
  ↓
changed files/functions
  ↓
cached summaries + dependency graph
  ↓
only required source ranges
```

変換は「AIに全文を書き直させる」だけにせず、対応関係・テスト・差分を保存して再利用する。
