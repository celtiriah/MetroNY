--------------------------------------------------------------------------------
-- Sistema de Gestión del Metro de Nueva York
-- Script 01: Configuración Inicial de Base de Datos, Tablespaces y Usuario
--
-- Modo de Ejecución:
--   Debe ejecutarse como Administrador del Sistema (SYSDBA):
--   sqlplus / as sysdba @01_configuracion_usuario.ddl
--------------------------------------------------------------------------------

-- 1. Cambiar a la base de datos del proyecto
ALTER SESSION SET CONTAINER = FREEPDB1;

-- 2. Borrar el usuario anterior con todos sus objetos
BEGIN
    EXECUTE IMMEDIATE 'DROP USER METRO_NY CASCADE';
EXCEPTION
    WHEN OTHERS THEN NULL;
END;
/

-- 3. Borrar los tablespaces viejos eliminando sus archivos físicos (.dbf)
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLESPACE TS_METRO_DATA INCLUDING CONTENTS AND DATAFILES';
EXCEPTION
    WHEN OTHERS THEN NULL;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLESPACE TS_METRO_IDX INCLUDING CONTENTS AND DATAFILES';
EXCEPTION
    WHEN OTHERS THEN NULL;
END;
/

-- 4. Crear los nuevos Tablespaces portables
CREATE TABLESPACE TS_METRO_DATA 
    DATAFILE 'ts_metro_data01.dbf' 
    SIZE 100M 
    AUTOEXTEND ON NEXT 50M MAXSIZE UNLIMITED;

CREATE TABLESPACE TS_METRO_IDX 
    DATAFILE 'ts_metro_idx01.dbf' 
    SIZE 50M 
    AUTOEXTEND ON NEXT 25M MAXSIZE UNLIMITED;

-- 5. Crear el usuario limpio con sus tablespaces asignados
CREATE USER METRO_NY IDENTIFIED BY "MetroPass123"
    DEFAULT TABLESPACE TS_METRO_DATA
    TEMPORARY TABLESPACE TEMP
    QUOTA UNLIMITED ON TS_METRO_DATA
    QUOTA UNLIMITED ON TS_METRO_IDX;

GRANT CONNECT, RESOURCE, CREATE VIEW, CREATE PROCEDURE, CREATE SEQUENCE, CREATE TRIGGER TO METRO_NY;

EXIT;