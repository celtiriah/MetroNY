-- ==============================================================================
-- PROYECTO: METRO NY - GESTION INTEGRAL DEL SUBWAY DE NUEVA YORK
-- ARCHIVO:  database/04_datos_simulacion_1anno/ejecutar_simulacion_1anno.sql
-- PROPOSITO: Orquestador maestro para ejecutar en orden todas las fases de
--            la simulacion anual de uso del sistema (~5,300 registros) y
--            garantizar la sincronizacion de secuencias de Oracle.
-- ==============================================================================

SET SERVEROUTPUT ON SIZE UNLIMITED;

PROMPT ==============================================================================
PROMPT    SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]
PROMPT    Carga de Datos de Simulacion Anual (~5,300 Registros Operativos)
PROMPT ==============================================================================
PROMPT.

-- Fase 0: Preparacion y sincronizacion inicial
@@00_preparacion_y_secuencias.sql

-- Fase 1: Pasajeros y Tarjetas
@@01_sim_pasajeros_tarjetas.sql

-- Fase 2: Recargas Financieras
@@02_sim_recargas.sql

-- Fase 3: Validaciones en Torniquetes
@@03_sim_viajes_pasajeros.sql

-- Fase 4: Despachos de Trenes
@@04_sim_viajes_programados.sql

-- Fase 5: Turnos de Personal
@@05_sim_turnos.sql

-- Fase 6: Mantenimiento y Repuestos
@@06_sim_mantenimiento.sql

-- Fase 7: Incidentes y Bitacora
@@07_sim_incidentes_bitacora.sql

-- Sincronizacion Final Global de las 33 Secuencias
PROMPT.
PROMPT ==============================================================================
PROMPT [FINAL] Ejecutando sincronizacion global de las 33 secuencias de Oracle...
PROMPT ==============================================================================

BEGIN
    SP_SINCRONIZAR_TODAS_SECUENCIAS;
END;
/

COMMIT;

PROMPT.
PROMPT ==============================================================================
PROMPT                   RESUMEN DE REGISTROS EN EL SISTEMA
PROMPT ==============================================================================

SELECT 'PASAJERO' AS TABLA, COUNT(*) AS TOTAL_REGISTROS FROM PASAJERO
UNION ALL SELECT 'TARJETA', COUNT(*) FROM TARJETA
UNION ALL SELECT 'RECARGA', COUNT(*) FROM RECARGA
UNION ALL SELECT 'VIAJE_PASAJERO', COUNT(*) FROM VIAJE_PASAJERO
UNION ALL SELECT 'VIAJE_PROGRAMADO', COUNT(*) FROM VIAJE_PROGRAMADO
UNION ALL SELECT 'TURNO', COUNT(*) FROM TURNO
UNION ALL SELECT 'ORDEN_MANTENIMIENTO', COUNT(*) FROM ORDEN_MANTENIMIENTO
UNION ALL SELECT 'ORDEN_TECNICO', COUNT(*) FROM ORDEN_TECNICO
UNION ALL SELECT 'ORDEN_REPUESTO', COUNT(*) FROM ORDEN_REPUESTO
UNION ALL SELECT 'INCIDENTE', COUNT(*) FROM INCIDENTE
UNION ALL SELECT 'INCIDENTE_ELEMENTO_AFECTADO', COUNT(*) FROM INCIDENTE_ELEMENTO_AFECTADO
UNION ALL SELECT 'BITACORA', COUNT(*) FROM BITACORA;

PROMPT.
PROMPT ==============================================================================
PROMPT [EXITO] Simulacion anual de 5,000+ registros completada y sincronizada.
PROMPT ==============================================================================

