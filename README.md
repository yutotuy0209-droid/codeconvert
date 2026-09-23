# codeconvert

個人利用を中心に、コードを「共通の中間表現」と「説明用SVG」へ変換するための再利用ツール置き場です。

## Supported

- Python
- C / C++
- MATLAB

`src/code_to_svg.py` が共通入口です。各言語の解析結果を同じ `FunctionInfo` へ正規化し、同じSVG rendererを使います。

```text
Python ─┐
C/C++ ──┼─> adapter ─> FunctionInfo ─┬─> JSON
MATLAB ─┘                            └─> SVG
```

## Usage

### ファイル全体の概要図

```bash
python src/code_to_svg.py path/to/source.cpp --out output/source.svg
```

### 関数ごとにSVGを自動生成

```bash
python src/code_to_svg.py path/to/source.py --split output/functions
python src/code_to_svg.py path/to/source.cpp --split output/functions
python src/code_to_svg.py path/to/source.m --split output/functions
```

### 特定関数だけ

```bash
python src/code_to_svg.py path/to/source.cpp --function func_xy --out output/func_xy.svg
```

### 中間JSONも保存

```bash
python src/code_to_svg.py path/to/source.m --json output/source.json --out output/source.svg
```

## Structure

```text
src/
├─ code_to_svg.py       # 共通CLI
├─ model.py             # 言語非依存の中間表現
├─ renderer.py          # 共通SVG renderer
├─ cpp_adapter.py       # C/C++
├─ matlab_adapter.py    # MATLAB
└─ function_to_svg.py   # 初期Python版（互換用）
```

## Design

使い切りコードではなく、

**source → language adapter → common model → renderer**

という構造にしています。今後、JavaScript等を追加する場合もadapterを追加するだけで、SVG側を作り直さない方針です。

C/C++ adapterは軽量な静的抽出器で、コンパイラではありません。複雑なmacro/templateまで厳密に解析する必要が出た場合はClangベースのadapterを追加し、共通モデル以降はそのまま再利用します。

## Personal-first

まず自分の研究・開発で毎回使えることを優先します。他の人にも使える部分は研究固有情報を含めず汎用化して残します。
