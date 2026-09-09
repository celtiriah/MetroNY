@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ======================================================================
echo    SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]
echo    Iniciando Aplicacion de Escritorio Nativa (PyQt5)...
echo ======================================================================
echo.

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python no fue encontrado en el PATH.
    echo Por favor instala Python 3.10 o superior para ejecutar la aplicacion.
    pause
    exit /b 1
)

echo [1/2] Verificando dependencias (PyQt5 y oracledb)...
python -c "import PyQt5, oracledb" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Instalando dependencias desde requirements.txt...
    python -m pip install -r requirements.txt
)

echo [2/2] Abriendo la ventana de la aplicacion...
python app.py
