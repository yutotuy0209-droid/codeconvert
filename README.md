# codeconvert

個人利用を中心に、コードを「読みやすい中間表現」と「説明用の図」へ変換するための再利用ツール置き場です。

特定の卒業研究コードだけに依存せず、別プロジェクトにも持ち込める小さな道具を保存します。

## Current feature: Python function → SVG

`src/function_to_svg.py` は Python ファイルを解析し、関数情報を抽出して SVG にします。外部依存はありません。

### ファイル全体の概要図

```bash
python src/function_to_svg.py path/to/sample.py --out output/sample.svg
```

### 関数ごとにSVGを分割

```bash
python src/function_to_svg.py path/to/sample.py --split output/functions
```

### 特定関数だけ出力

```bash
python src/function_to_svg.py path/to/sample.py --function analyze --out output/analyze.svg
```

### 中間JSONも保存

```bash
python src/function_to_svg.py path/to/sample.py --json output/sample.json --out output/sample.svg
```

## Structure

```text
codeconvert/
├─ src/
│  └─ function_to_svg.py
├─ presets/
│  └─ function-detail-default.json
├─ skills/
│  └─ code-visualization/
│     └─ SKILL.md
└─ tests/
   ├─ test_function_to_svg.py
   └─ fixtures/
      └─ sample.py
```

## Design principle

使い切りの変換コードを増やすのではなく、次回も呼び出せる関数・CLI・中間JSON・ルールとして残します。

今後は Python 以外も、各言語の解析部分だけを追加し、同じ中間形式とSVGレンダラーを再利用する構成を目指します。
