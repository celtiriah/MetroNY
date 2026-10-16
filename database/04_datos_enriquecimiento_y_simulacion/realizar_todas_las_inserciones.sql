-- ==============================================================================
-- PROYECTO: METRO NY - GESTION INTEGRAL DEL SUBWAY DE NUEVA YORK [MTA NYCT]
-- ARCHIVO:  database/04_datos_enriquecimiento_y_simulacion/realizar_todas_las_inserciones.sql
-- PROPOSITO: Orquestador maestro que ejecuta:
--            1. Fase 1: Catálogo Canónico Masivo MTA (26 líneas, 45 estaciones, 24 trenes, 36 empleados)
--            2. Fase 2: Simulación Operativa Anual (~5,300 registros: viajes, turnos, incidentes, etc.)
--            3. Sincronización Global de Secuencias de Base de Datos
-- ==============================================================================

SET DEFINE OFF;
SET SERVEROUTPUT ON SIZE UNLIMITED;
SET SQLBLANKLINES ON;
SET FEEDBACK ON;
ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD';
ALTER SESSION SET NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS';

PROMPT ==============================================================================
PROMPT    SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]
PROMPT    CARGA COMPLETA: ENRIQUECIMIENTO CANONICO MTA + SIMULACION ANUAL
PROMPT ==============================================================================
PROMPT.

-- ------------------------------------------------------------------------------
-- FASE 1: ENRIQUECIMIENTO DEL CATALOGO CANONICO MTA
-- ------------------------------------------------------------------------------
PROMPT ==============================================================================
PROMPT [FASE 1/2] EJECUTANDO ENRIQUECIMIENTO MASIVO DEL CATALOGO MTA NYCT...
PROMPT ==============================================================================
@fase1_catalogo_mta\01_mta_catalogo_enriquecido.sql

-- ------------------------------------------------------------------------------
-- FASE 2: SIMULACION OPERATIVA ANUAL (~5,300 REGISTROS)
-- ------------------------------------------------------------------------------
PROMPT ==============================================================================
PROMPT [FASE 2/2] EJECUTANDO SIMULACION OPERATIVA ANUAL DE 1 ANNO...
PROMPT ==============================================================================
@fase2_simulacion_anual\ejecutar_simulacion_1anno.sql

-- ------------------------------------------------------------------------------
-- SINCRONIZACION FINAL DE SECUENCIAS
-- ------------------------------------------------------------------------------
PROMPT.
PROMPT ==============================================================================
PROMPT [FINAL] Sincronizando las 33 secuencias del sistema Oracle...
PROMPT ==============================================================================
BEGIN
    SP_SINCRONIZAR_TODAS_SECUENCIAS;
END;
/
COMMIT;

PROMPT.
PROMPT ==============================================================================
PROMPT        CONSOLIDADO GLOBAL DE ELEMENTOS CARGADOS EN METRO_NY
PROMPT ==============================================================================
COLUMN item FORMAT A38
COLUMN cantidad FORMAT 999990
SELECT 'Lineas de Metro Activas' AS item, COUNT(*) AS cantidad FROM LINEA
UNION ALL SELECT 'Estaciones en 5 Distritos', COUNT(*) FROM ESTACION
UNION ALL SELECT 'Plataformas de Estacion', COUNT(*) FROM PLATAFORMA
UNION ALL SELECT 'Rutas Operativas', COUNT(*) FROM RUTA
UNION ALL SELECT 'Flota de Trenes Activos', COUNT(*) FROM TREN
UNION ALL SELECT 'Vagones en Servicio', COUNT(*) FROM VAGON
UNION ALL SELECT 'Empleados Registrados', COUNT(*) FROM EMPLEADO
UNION ALL SELECT 'Certificaciones Vigentes', COUNT(*) FROM CERTIFICACION
UNION ALL SELECT 'Equipos de Estacion y Tren', COUNT(*) FROM EQUIPO
UNION ALL SELECT 'Catalogo de Repuestos', COUNT(*) FROM REPUESTO
UNION ALL SELECT 'Pasajeros Registrados', COUNT(*) FROM PASAJERO
UNION ALL SELECT 'Tarjetas Emitidas', COUNT(*) FROM TARJETA
UNION ALL SELECT 'Recargas Realizadas', COUNT(*) FROM RECARGA
UNION ALL SELECT 'Viajes de Pasajeros', COUNT(*) FROM VIAJE_PASAJERO
UNION ALL SELECT 'Viajes Programados de Trenes', COUNT(*) FROM VIAJE_PROGRAMADO
UNION ALL SELECT 'Turnos de Personal Asignados', COUNT(*) FROM TURNO
UNION ALL SELECT 'Ordenes de Mantenimiento', COUNT(*) FROM ORDEN_MANTENIMIENTO
UNION ALL SELECT 'Incidentes Operativos Registrados', COUNT(*) FROM INCIDENTE;

PROMPT.
PROMPT ==============================================================================
PROMPT [EXITO] TODAS LAS INSERCIONES FUERON COMPLETADAS SATISFACTORIAMENTE.
PROMPT ==============================================================================
