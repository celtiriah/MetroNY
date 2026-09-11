@echo off
chcp 65001 >nul
set NLS_LANG=AMERICAN_AMERICA.AL32UTF8
cd /d "%~dp0"

echo ======================================================================
echo    SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]
echo    Paso 1: Configuracion Inicial y Creacion de Tablas [Windows]
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

echo [1/4] Configurando tablespaces y usuario METRO_NY en %PDB_NAME%...
sqlplus -S / as sysdba @01_setup\01_configuracion_usuario.ddl
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en la configuracion del usuario.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/4] Creando 33 tablas normalizadas (3NF), claves foraneas y secuencias...
sqlplus -S METRO_NY/MetroPass123@localhost:1521/%PDB_NAME% @01_setup\02_ddl_tablas.ddl
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en la creacion de tablas.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [3/4] Insertando 208 registros de datos de prueba del Metro de NY...
sqlplus -S METRO_NY/MetroPass123@localhost:1521/%PDB_NAME% @01_setup\03_datos_prueba.ddl
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en la carga de datos.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [4/4] Construyendo 63 indices B-Tree de rendimiento en TS_METRO_IDX...
sqlplus -S METRO_NY/MetroPass123@localhost:1521/%PDB_NAME% @01_setup\04_indices.ddl
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en la creacion de indices.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ======================================================================
echo    CONFIGURACION INICIAL COMPLETADA EN %PDB_NAME%!
echo    - 33 Tablas creadas en TS_METRO_DATA
echo    - 208 Registros iniciales cargados
echo    - 63 Indices B-Tree creados en TS_METRO_IDX
echo.
echo    SIGUIENTE PASO:
echo    Ejecuta 'dbprogramar.bat' para compilar la logica PL/SQL
echo    (Vistas, Funciones, Procedimientos y Triggers).
echo ======================================================================
echo.
pause

