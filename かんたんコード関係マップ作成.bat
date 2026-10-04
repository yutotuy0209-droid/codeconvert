@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

echo ==============================================================================
echo [codeconvert] 複数ファイル / フォルダ 関係マップ
echo.
echo 使い方:
echo   1. このBATへ複数の .py / .cpp / .h / .m / フォルダをドラッグ＆ドロップ
echo   2. file_relationships.svg / .mmd / .json / index.html を自動生成
echo.
echo 矢印:
echo   青実線   = 解決できた関数呼び出し
echo   灰破線   = repository-local Python import
echo ==============================================================================

set "BASE_DIR=%~dp0"
set "PYTHON_EXE=C:\Users\yu_ci\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "!PYTHON_EXE!" set "PYTHON_EXE=python"

if "%~1"=="" goto default_mode

echo.
echo [INPUT] ドロップされた対象を解析します...
"!PYTHON_EXE!" "!BASE_DIR!src\project_mapper.py" %* --out "!BASE_DIR!output\dropped_relationship_map"
if errorlevel 1 goto failed

echo.
echo [DONE]
echo   HTML    : !BASE_DIR!output\dropped_relationship_map\index.html
echo   SVG     : !BASE_DIR!output\dropped_relationship_map\file_relationships.svg
echo   Mermaid : !BASE_DIR!output\dropped_relationship_map\file_relationships.mmd
echo   JSON    : !BASE_DIR!output\dropped_relationship_map\file_relationships.json
echo.
echo PowerPointには file_relationships.svg をそのまま挿入できます。
start "" "!BASE_DIR!output\dropped_relationship_map\index.html"
goto end

:default_mode
echo.
echo [INFO] 引数がないため、既定の卒研Pythonフォルダを解析します。
set "DEFAULT_TARGET=C:\Users\yu_ci\Desktop\realcode\functions"
if not exist "!DEFAULT_TARGET!" (
    echo [ERROR] 既定フォルダが見つかりません。
    echo ファイルまたはフォルダをこのBATへドラッグ＆ドロップしてください。
    goto failed
)

"!PYTHON_EXE!" "!BASE_DIR!src\project_mapper.py" "!DEFAULT_TARGET!" --out "!BASE_DIR!output\python_map"
if errorlevel 1 goto failed
start "" "!BASE_DIR!output\python_map\index.html"
goto end

:failed
echo.
echo [FAILED] 関係マップ生成に失敗しました。
pause
exit /b 1

:end
echo.
echo 完了しました。
endlocal
