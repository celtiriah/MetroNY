@echo off
chcp 65001 >nul
set NLS_LANG=AMERICAN_AMERICA.AL32UTF8

echo ======================================================================
echo    SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]
echo    Instalador Automatizado de Base de Datos Oracle [Windows]
echo ======================================================================
echo.

echo Detectando servicio de base de datos Oracle activo [PDB]...
set PDB_NAME=
for /f "usebackq tokens=*" %%i in (`sqlplus -S / as sysdba @database\get_pdb.sql`) do set PDB_NAME=%%i

if "%PDB_NAME%"=="" (
    set PDB_NAME=FREEPDB1
)

echo Servicio Pluggable Database detectado: %PDB_NAME%
echo.

echo [1/4] Configurando tablespaces y usuario METRO_NY en %PDB_NAME%...
sqlplus -S / as sysdba @database\01_configuracion_usuario.ddl
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en la configuracion inicial.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/4] Creando 33 tablas normalizadas, claves foraneas y secuencias...
sqlplus -S METRO_NY/MetroPass123@localhost:1521/%PDB_NAME% @database\02_ddl_tablas.ddl
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en la creacion de tablas.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [3/4] Insertando 208 registros de datos de prueba reales del Metro de NY...
sqlplus -S METRO_NY/MetroPass123@localhost:1521/%PDB_NAME% @database\03_datos_prueba.ddl
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en la carga de datos.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [4/4] Construyendo 63 indices B-Tree de rendimiento en TS_METRO_IDX...
sqlplus -S METRO_NY/MetroPass123@localhost:1521/%PDB_NAME% @database\04_indices.ddl
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en la creacion de indices.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ======================================================================
echo    INSTALACION COMPLETADA CON EXITO EN %PDB_NAME%!
echo    - 33 Tablas creadas en TS_METRO_DATA
echo    - 208 Registros iniciales listos
echo    - 63 Indices B-Tree optimizados en TS_METRO_IDX
echo.
echo    Puedes probar las 15 consultas del proyecto ejecutando:
echo    sqlplus METRO_NY/MetroPass123@localhost:1521/%PDB_NAME% @database\consultas_minimas.ddl
echo ======================================================================
echo.
pause
