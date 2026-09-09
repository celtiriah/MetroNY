@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ======================================================================
echo    SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]
echo    Iniciando Servidor Web y Mini-Backend Python...
echo ======================================================================
echo.

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python no fue encontrado en el PATH.
    echo Por favor instala Python 3.10 o superior para ejecutar el servidor.
    pause
    exit /b 1
)

echo [1/2] Verificando dependencias de Python (Flask y oracledb)...
python -c "import flask, oracledb" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Instalando librerias necesarias desde backend\requirements.txt...
    python -m pip install -r backend\requirements.txt
)

echo [2/2] Abriendo el navegador en http://localhost:5000...
start "" http://localhost:5000

echo.
echo ======================================================================
echo  Servidor en ejecucion. Para detenerlo presiona Ctrl + C en esta ventana.
echo ======================================================================
echo.
python backend\app.py
pause

