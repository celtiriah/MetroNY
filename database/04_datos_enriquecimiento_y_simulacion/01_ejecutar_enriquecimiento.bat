@echo off
chcp 65001 >nul
set NLS_LANG=AMERICAN_AMERICA.AL32UTF8
cd /d "%~dp0"

echo ======================================================================
echo    SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]
echo    [Fase 1] Enriquecimiento del Catalogo Masivo MTA
echo ======================================================================
echo.

set PDB_NAME=
if exist "..\get_pdb.sql" (
    for /f "usebackq tokens=*" %%i in (`sqlplus -S / as sysdba @..\get_pdb.sql`) do set PDB_NAME=%%i
)
if "%PDB_NAME%"=="" if exist "get_pdb.sql" (
    for /f "usebackq tokens=*" %%i in (`sqlplus -S / as sysdba @get_pdb.sql`) do set PDB_NAME=%%i
)
if "%PDB_NAME%"=="" (
    set PDB_NAME=FREEPDB1
)

echo Servicio Oracle PDB: %PDB_NAME%
echo Esquema: METRO_NY
echo.
echo Ejecutando enriquecimiento del catalogo de lineas, estaciones, trenes y personal...
echo.

(
    echo @fase1_catalogo_mta\01_mta_catalogo_enriquecido.sql
    echo exit
) | sqlplus -S METRO_NY/MetroPass123@localhost:1521/%PDB_NAME%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Ocurrio un fallo durante la ejecucion del catalogo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ======================================================================
echo [EXITO] Catalogo MTA cargado exitosamente en %PDB_NAME%!
echo ======================================================================
echo.
pause

