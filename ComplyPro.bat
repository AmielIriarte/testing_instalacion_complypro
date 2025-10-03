@echo off
chcp 65001 >nul

@REM ============================================================
@REM Instalación de Python 3.11 si no está presente
@REM ============================================================

set PROJECT_DIR=%~dp0

@REM Verificar si existe Python 3.11
python --version 2>nul | findstr /r "^Python 3\.11" >nul
if %errorlevel%==0 (
    echo Usando Python 3.11
    goto end-instalation
)

echo Instalando Python 3.11...
@REM Ruta donde querés guardar el instalador
set DEST_DIR=C:\Drv

@REM Nombre del instalador (asegurate de que coincida)
set INSTALLER=python-3.11.5-amd64.exe

@REM Crear carpeta destino si no existe
if not exist "%DEST_DIR%" (
    echo Error al instalar Python 3.11
    goto end
)
if not exist "%PROJECT_DIR%\%INSTALLER%" (
    echo No se encontró el instalador de Python 3.11
    goto end
)

@REM Copio el instalador desde la carpeta del .bat (%~dp0) al destino
copy "%PROJECT_DIR%\%INSTALLER%" "%DEST_DIR%"

@REM Ir a la carpeta destino
cd /d "%DEST_DIR%"

@REM Ejecutar instalador en modo silencioso (ajustá a tus necesidades)
"%DEST_DIR%\%INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1

@REM Intentar detectar rutas típicas de instalación
set PYTHON_SYS_DIR=C:\Program Files\Python311
set PYTHON_USER_DIR=%LOCALAPPDATA%\Programs\Python\Python311

@REM Reseteo el archivo para que reconozca Python desde las variables de Windows
start "ComplyPro" cmd /k "%~f0"
exit

:end-instalation

@REM ============================================================
@REM Ejecución de ComplyPro
@REM ============================================================

cd /d "%PROJECT_DIR%"

REM Revisa si el entorno virtual ya existe, si no, lo crea
if not exist "%PROJECT_DIR%\.venv" (
    echo Creando entorno virtual...
    python -m venv "%PROJECT_DIR%\.venv"
)

set VENV_DIR=%PROJECT_DIR%\.venv\Scripts
set PYTHON=%VENV_DIR%\python.exe

REM Instala y verifica uv
"%PYTHON%" -m pip install uv

REM Actualiza las dependencias de proyect.toml
"%PYTHON%" -m uv sync

REM Ejecuta update_script.py
echo Buscando actualizaciones...
"%PYTHON%" "%PROJECT_DIR%\update_script.py"

REM Actualiza las dependencias de requirements.txt
"%PYTHON%" -m uv pip install -r requirements.txt

REM Ejecuuta la aplicación principal
echo Iniciando aplicación...
"%PYTHON%" -m streamlit run "%PROJECT_DIR%\app\main.py"

:end
pause
