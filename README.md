# codeconvert

コードを「共通の中間表現」「説明用SVG」「Mermaid」「PowerPoint素材」へ変換するための再利用ツールです。

目的は、複数ファイルで管理している Python / C++ / HPP / MATLAB コードの関係を、人間とAIが同じ図で理解できるようにすることです。

## Supported

- Python
- C / C++ / HPP
- MATLAB

```text
複数ファイル / フォルダ
      ↓
language adapters
      ↓
FunctionInfo / file relations
      ↓
SVG / Mermaid / JSON / PPTX / motion storyboard
```

## いちばん簡単な使い方

Windowsでは、次のBATへファイルまたはフォルダをドラッグ＆ドロップします。

```text
かんたんコード関係マップ作成.bat
```

出力:

```text
output/dropped_relationship_map/
├─ index.html
├─ repo_map.md
├─ repo_map.json
├─ file_relationships.svg
├─ file_relationships.mmd
└─ file_relationships.json

output/presentation_pack/
├─ relationship_deck.pptx
└─ motion/
   ├─ motion_storyboard.html
   ├─ frames/frame_001.svg ...
   └─ relationship_motion.gif   # Pillowがある場合のみ
```

PowerPointへ入れる場合は、まず `file_relationships.svg` か `relationship_deck.pptx` を使います。GIF的に説明したい場合は `motion_storyboard.html` を開きます。

## CLI

### ファイル単体の概要図

```bash
python src/code_to_svg.py path/to/source.cpp --out output/source.svg
```

### 複数ファイル/フォルダの関係図

```bash
python src/project_mapper.py src/ include/ main.cpp --out output/project_map
```

生成される主なファイル:

```text
file_relationships.svg   # PowerPointに貼りやすい四角＋矢印
file_relationships.mmd   # Mermaid
file_relationships.json  # AI/後処理用
repo_map.md              # LLMへ渡す軽量要約
index.html               # 人間用ダッシュボード
```

### PPTX / GIF用素材へ変換

```bash
python src/presentation_export.py output/project_map --out output/presentation_pack
```

生成:

```text
relationship_deck.pptx
motion/motion_storyboard.html
motion/frames/*.svg
motion/relationship_motion.gif  # Pillowがあれば生成
```

## Relationship rules

現在の矢印:

| 種類 | 意味 |
|---|---|
| `call` | あるファイルの関数が、別ファイルで一意に定義された関数を呼ぶ |
| `import` | Pythonのrepository-local import |
| `include` | C/C++の `#include "..."` がrepository内のヘッダ等へ解決された |

同じ関数名が複数ファイルにある場合、勝手に推測せず `ambiguities` に記録します。

## Structure

```text
src/
├─ code_to_svg.py          # 単一ファイル/関数のSVG化
├─ project_mapper.py       # 複数ファイル/フォルダの関係図生成
├─ presentation_export.py  # PPTX / motion storyboard 出力
├─ model.py                # 言語非依存の中間表現
├─ renderer.py             # 共通SVG renderer
├─ cpp_adapter.py          # C/C++
├─ matlab_adapter.py       # MATLAB
└─ function_to_svg.py      # 初期Python版（互換用）
```

## TDD

```bash
python -m unittest discover -s tests -p "test_*.py"
```

GitHub Actionsでも同じテストを実行します。

## Design

使い切りコードではなく、

```text
source → language adapter → common model → relationship map → presentation assets
```

という構造にしています。

今後、JavaScript等を追加する場合もadapterを追加するだけで、SVG/PPTX側を作り直さない方針です。

C/C++ adapterは軽量な静的抽出器で、コンパイラではありません。複雑なmacro/templateまで厳密に解析する必要が出た場合はClangベースのadapterを追加し、共通モデル以降はそのまま再利用します。
