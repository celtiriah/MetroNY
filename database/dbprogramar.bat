@echo off
chcp 65001 >nul
set NLS_LANG=AMERICAN_AMERICA.AL32UTF8
cd /d "%~dp0"

echo ======================================================================
echo    SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]
echo    Paso 2: Compilacion de Logica PL/SQL en Oracle [Windows]
echo ======================================================================
echo.

echo Detectando servicio de base de datos Oracle activo [PDB]...
set PDB_NAME=
for /f "usebackq tokens=*" %%i in (`sqlplus -S / as sysdba @get_pdb.sql`) do set PDB_NAME=%%i

if "%PDB_NAME%"=="" (
    set PDB_NAME=FREEPDB1
)

echo Servicio Pluggable Database detectado: %PDB_NAME%
echo.

echo [1/4] Compilando 9 Vistas analiticas y operativas...
sqlplus -S METRO_NY/MetroPass123@localhost:1521/%PDB_NAME% @02_plsql\05_vistas.sql
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en la compilacion de vistas.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/4] Compilando 9 Funciones de negocio...
sqlplus -S METRO_NY/MetroPass123@localhost:1521/%PDB_NAME% @02_plsql\06_funciones.sql
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en la compilacion de funciones.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [3/4] Compilando 6 Procedimientos almacenados transaccionales (SPs)...
sqlplus -S METRO_NY/MetroPass123@localhost:1521/%PDB_NAME% @02_plsql\07_procedimientos.sql
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en la compilacion de procedimientos.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [4/4] Compilando 8 Triggers de integridad y auditoria...
sqlplus -S METRO_NY/MetroPass123@localhost:1521/%PDB_NAME% @02_plsql\08_triggers.sql
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en la compilacion de triggers.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Verificando estado de compilacion en Oracle...
(
echo SET PAGESIZE 50 LINESIZE 120
echo COLUMN name FORMAT A25
echo COLUMN type FORMAT A15
echo COLUMN text FORMAT A60
echo SELECT name, type, line, text FROM user_errors ORDER BY name, line;
echo EXIT;
) | sqlplus -S METRO_NY/MetroPass123@localhost:1521/%PDB_NAME%

echo.
echo ======================================================================
echo    ¡LOGICA PL/SQL COMPILADA EXITOSAMENTE EN %PDB_NAME%!
echo    - 9 Vistas creadas / reemplazadas (VW_*)
echo    - 9 Funciones de calculo compiladas (FN_*)
echo    - 6 Procedimientos almacenados listos (SP_*)
echo    - 8 Triggers activos en la base de datos (TRG_*)
echo.
echo    Puedes ejecutar las pruebas en:
echo    sqlplus METRO_NY/MetroPass123@localhost:1521/%PDB_NAME% @03_pruebas\prueba_15_consultas.sql
echo ======================================================================
echo.
pause
