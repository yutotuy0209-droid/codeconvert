@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
echo ==============================================================================
echo [codeconvert] コード関係地図 ＆ トークン省エネマップ自動生成ツール
echo 狙い: AIトークンの省エネ化 ＆ 人間の認知負荷ゼロ化
echo ==============================================================================

set "BASE_DIR=%~dp0"
set "PYTHON_EXE=C:\Users\yu_ci\AppData\Local\Programs\Python\Python312\python.exe"

if not exist "!PYTHON_EXE!" (
    set "PYTHON_EXE=python"
)

echo.
echo [1/2] C++ コア (src_cpp) の関係性解析 ＆ SVG生成中...
"!PYTHON_EXE!" "!BASE_DIR!src\project_mapper.py" "C:\Users\yu_ci\Desktop\卒論整理\03_Git管理\メインリポジトリ\src_cpp\functions" --out "!BASE_DIR!output\cpp_map"

echo.
echo [2/2] Python 実コード (realcode/functions) の関係性解析 ＆ SVG生成中...
"!PYTHON_EXE!" "!BASE_DIR!src\project_mapper.py" "C:\Users\yu_ci\Desktop\realcode\functions" --out "!BASE_DIR!output\python_map"

echo.
echo ==============================================================================
echo [完了] コード関係地図 ＆ トークン省エネマップの生成が完了しました！
echo   - C++ ダッシュボード: !BASE_DIR!output\cpp_map\index.html
echo   - C++ AIトークン要約: !BASE_DIR!output\cpp_map\repo_map.md
echo   - Python ダッシュボード: !BASE_DIR!output\python_map\index.html
echo   - Python AIトークン要約: !BASE_DIR!output\python_map\repo_map.md
echo ==============================================================================

echo.
echo ブラウザで C++ コード関係地図を開きます...
start "" "!BASE_DIR!output\cpp_map\index.html"

endlocal
