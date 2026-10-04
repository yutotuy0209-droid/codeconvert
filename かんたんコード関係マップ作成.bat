@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

echo ==============================================================================
echo [codeconvert] 複数ファイル / フォルダ 関係マップ + プレゼン素材パック
echo.
echo 使い方:
echo   1. このBATへ複数の .py / .cpp / .hpp / .h / .m / フォルダをドラッグ＆ドロップ
echo   2. SVG / Mermaid / JSON / HTML / PPTX / GIF用ストーリーボードを自動生成
echo.
echo 矢印:
echo   青実線   = 解決できた関数呼び出し
echo   灰破線   = repository-local Python import
echo   include = C/C++ヘッダ関係として今後拡張対象
echo ==============================================================================

set "BASE_DIR=%~dp0"
set "PYTHON_EXE=C:\Users\yu_ci\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "!PYTHON_EXE!" set "PYTHON_EXE=python"

if "%~1"=="" goto default_mode

set "MAP_DIR=!BASE_DIR!output\dropped_relationship_map"
set "PACK_DIR=!BASE_DIR!output\presentation_pack"

echo.
echo [1/2] ドロップされた対象から関係マップを生成します...
"!PYTHON_EXE!" "!BASE_DIR!src\project_mapper.py" %* --out "!MAP_DIR!"
if errorlevel 1 goto failed

echo.
echo [2/2] PowerPoint / motion storyboard を生成します...
"!PYTHON_EXE!" "!BASE_DIR!src\presentation_export.py" "!MAP_DIR!" --out "!PACK_DIR!"
if errorlevel 1 goto failed

echo.
echo [DONE]
echo   HTML       : !MAP_DIR!\index.html
echo   SVG        : !MAP_DIR!\file_relationships.svg
echo   Mermaid    : !MAP_DIR!\file_relationships.mmd
echo   JSON       : !MAP_DIR!\file_relationships.json
echo   PowerPoint : !PACK_DIR!\relationship_deck.pptx
echo   Motion HTML: !PACK_DIR!\motion\motion_storyboard.html
echo   GIF        : !PACK_DIR!\motion\relationship_motion.gif  ^(Pillowがある場合のみ^)
echo.
echo PowerPointには file_relationships.svg または relationship_deck.pptx を使ってください。
start "" "!MAP_DIR!\index.html"
start "" "!PACK_DIR!\motion\motion_storyboard.html"
goto end

:default_mode
echo.
echo [INFO] 引数がないため、既定の卒研Pythonフォルダを解析します。
set "DEFAULT_TARGET=C:\Users\yu_ci\Desktop\realcode\functions"
set "MAP_DIR=!BASE_DIR!output\python_map"
set "PACK_DIR=!BASE_DIR!output\python_presentation_pack"
if not exist "!DEFAULT_TARGET!" (
    echo [ERROR] 既定フォルダが見つかりません。
    echo ファイルまたはフォルダをこのBATへドラッグ＆ドロップしてください。
    goto failed
)

"!PYTHON_EXE!" "!BASE_DIR!src\project_mapper.py" "!DEFAULT_TARGET!" --out "!MAP_DIR!"
if errorlevel 1 goto failed
"!PYTHON_EXE!" "!BASE_DIR!src\presentation_export.py" "!MAP_DIR!" --out "!PACK_DIR!"
if errorlevel 1 goto failed
start "" "!MAP_DIR!\index.html"
start "" "!PACK_DIR!\motion\motion_storyboard.html"
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
