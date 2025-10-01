@echo off
chcp 65001 >nul

@REM Define project and virtual environment directories using existing absolute paths
set PROJECT_DIR=%~dp0

cd /d "%PROJECT_DIR%"

REM Step 1: Check if virtual environment exists, if not, create it
if not exist "%PROJECT_DIR%\.venv" (
    echo Creando entorno virtual...
    python -m venv "%PROJECT_DIR%\.venv"
)

set VENV_DIR=%PROJECT_DIR%\.venv\Scripts
set PYTHON=%VENV_DIR%\python.exe

REM Step 3: Install or verify uv
"%PYTHON%" -m pip install uv

REM Step 4: Update dependencies with uv
"%PYTHON%" -m uv sync

REM Step 5: Execute update_script.py
echo Ejecutando update_script.py...
"%PYTHON%" "%PROJECT_DIR%\update_script.py"

REM Step 6: Update dependencies with uv
@REM "%PYTHON%" -m uv sync
"%PYTHON%" -m uv pip install -r requirements.txt

REM Step 7: Execute main.py
echo Iniciando aplicación...
"%PYTHON%" -m streamlit run "%PROJECT_DIR%\app\main.py"

echo Process completed.

:end
pause