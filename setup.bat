@echo off
chcp 65001 >nul
set NLS_LANG=FRENCH_FRANCE.AL32UTF8

echo ======================================================================
echo    SISTEMA DE GESTION DEL METRO DE NUEVA YORK (MTA NYCT)
echo    Instalador Automatizado de Base de Datos Oracle
echo ======================================================================
echo.

echo [1/4] Configurando tablespaces (TS_METRO_DATA, TS_METRO_IDX) y usuario METRO_NY...
sqlplus -S / as sysdba @01_configuracion_usuario.ddl
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en la configuracion del usuario o tablespaces.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/4] Creando 33 tablas normalizadas (3FN), claves primarias y foraneas...
sqlplus -S METRO_NY/MetroPass123@localhost:1521/FREEPDB1 @02_ddl_tablas.ddl
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en la creacion de tablas.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [3/4] Insertando 208 registros de datos de prueba reales y sincronizando secuencias...
sqlplus -S METRO_NY/MetroPass123@localhost:1521/FREEPDB1 @03_datos_prueba.ddl
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en la carga de datos de prueba.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [4/4] Construyendo 63 indices B-Tree fisicos en TS_METRO_IDX...
sqlplus -S METRO_NY/MetroPass123@localhost:1521/FREEPDB1 @04_indices.ddl
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en la creacion de indices.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ======================================================================
echo    ¡INSTALACION COMPLETADA CON EXITO!
echo    - 33 Tablas creadas en TS_METRO_DATA
echo    - 208 Registros iniciales listos
echo    - 63 Indices B-Tree optimizados en TS_METRO_IDX
echo.
echo    Puedes probar las 15 consultas del proyecto ejecutando:
echo    sqlplus METRO_NY/MetroPass123@localhost:1521/FREEPDB1 @consultas_minimas.ddl
echo ======================================================================
echo.
pause
