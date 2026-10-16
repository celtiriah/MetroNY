@echo off
chcp 65001 >nul
set NLS_LANG=AMERICAN_AMERICA.AL32UTF8
cd /d "%~dp0"

echo ======================================================================
echo    SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]
echo    Insercion Masiva: Catalogo MTA + Simulacion Anual de Operaciones
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

echo Servicio Oracle PDB detectado: %PDB_NAME%
echo Esquema de Base de Datos: METRO_NY
echo.
echo Ejecutando todas las inserciones del sistema en orden...
echo [Fase 1] Catalogo Masivo MTA (Lineas, Estaciones, Trenes, Empleados)
echo [Fase 2] Simulacion Operativa Anual (~5,300 registros operativos)
echo.

(
    echo @realizar_todas_las_inserciones.sql
    echo exit
) | sqlplus -S METRO_NY/MetroPass123@localhost:1521/%PDB_NAME%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ======================================================================
    echo [ERROR] Ocurrio un fallo durante la ejecucion de las inserciones.
    echo Revise la conexion a Oracle o las credenciales de METRO_NY.
    echo ======================================================================
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ======================================================================
echo [EXITO] Todas las inserciones fueron ejecutadas correctamente en %PDB_NAME%!
echo ======================================================================
echo.
pause

