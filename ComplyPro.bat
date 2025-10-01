@echo off
chcp 65001 >nul

@REM Define project and virtual environment directories using existing absolute paths
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

@REM Mover instalador desde la carpeta del .bat (%~dp0) al destino
move "%PROJECT_DIR%\%INSTALLER%" "%DEST_DIR%"

@REM Ir a la carpeta destino
cd /d "%DEST_DIR%"

@REM Ejecutar instalador en modo silencioso (ajustá a tus necesidades)
"%DEST_DIR%\%INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1

@REM ===============================
@REM Intentar detectar rutas típicas de instalación
set PYTHON_SYS_DIR=C:\Program Files\Python311
set PYTHON_USER_DIR=%LOCALAPPDATA%\Programs\Python\Python311

@REM Verificar Python en la sesión actual
python --version
if %errorlevel%==0 (
    echo Instalación de Python completada y lista para usarse.
) else (
    echo Python aún no está disponible en la sesión actual.
    goto end
)

:end-instalation
@REM Ejecuta el script de python
call "%PROJECT_DIR%\run.bat"

:end
pause