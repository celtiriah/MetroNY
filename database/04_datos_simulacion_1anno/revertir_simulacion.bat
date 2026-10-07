@echo off
chcp 65001 >nul
set NLS_LANG=AMERICAN_AMERICA.AL32UTF8
cd /d "%~dp0"

echo ======================================================================
echo    SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]
echo    Reversion Total de Datos de Simulacion Anual (Rollback)
echo ======================================================================
echo.

set PDB_NAME=
if exist "..\get_pdb.sql" (
    for /f "usebackq tokens=*" %%i in (`sqlplus -S / as sysdba @..\get_pdb.sql`) do set PDB_NAME=%%i
)

if "%PDB_NAME%"=="" (
    set PDB_NAME=FREEPDB1
)

echo Servicio Oracle PDB: %PDB_NAME%
echo.
echo Revertiendo registros de simulacion y restaurando estado base...
echo.

(
    echo @revertir_simulacion_1anno.sql
    echo exit
) | sqlplus -S METRO_NY/MetroPass123@localhost:1521/%PDB_NAME%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Ocurrio un fallo durante la reversion de la simulacion.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ======================================================================
echo [EXITO] Base de datos restaurada exactamente a su estado original.
echo ======================================================================
pause

