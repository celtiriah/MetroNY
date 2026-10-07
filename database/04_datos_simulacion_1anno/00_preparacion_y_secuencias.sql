-- ==============================================================================
-- PROYECTO: METRO NY - GESTION INTEGRAL DEL SUBWAY DE NUEVA YORK
-- ARCHIVO:  database/04_datos_simulacion_1anno/00_preparacion_y_secuencias.sql
-- PROPOSITO: Procedimiento de sincronizacion global de las 33 secuencias de Oracle
--            y preparacion de inventario de repuestos para el ano simulado.
-- ==============================================================================

SET SERVEROUTPUT ON SIZE UNLIMITED;

PROMPT ==============================================================================
PROMPT [FASE 0] Creando SP_SINCRONIZAR_TODAS_SECUENCIAS y preparando entorno...
PROMPT ==============================================================================

CREATE OR REPLACE PROCEDURE SP_SINCRONIZAR_TODAS_SECUENCIAS AS
    TYPE t_tab_seq IS RECORD (
        tabla VARCHAR2(30),
        pk_col VARCHAR2(30),
        secuencia VARCHAR2(30)
    );
    TYPE t_tab_list IS TABLE OF t_tab_seq;
    v_tabs t_tab_list := t_tab_list(
        t_tab_seq('BITACORA', 'ID_BITACORA', 'SEQ_BITACORA'),
        t_tab_seq('CERTIFICACION', 'ID_CERTIFICACION', 'SEQ_CERTIFICACION'),
        t_tab_seq('CERTIFICACION_MODELO', 'ID_CERTIFICACION_MODELO', 'SEQ_CERTIFICACION_MODELO'),
        t_tab_seq('DEPOSITO', 'ID_DEPOSITO', 'SEQ_DEPOSITO'),
        t_tab_seq('EMPLEADO', 'ID_EMPLEADO', 'SEQ_EMPLEADO'),
        t_tab_seq('EQUIPO', 'ID_EQUIPO', 'SEQ_EQUIPO'),
        t_tab_seq('ESTACION', 'ID_ESTACION', 'SEQ_ESTACION'),
        t_tab_seq('ESTACION_SERVICIO', 'ID_ESTACION_SERVICIO', 'SEQ_ESTACION_SERVICIO'),
        t_tab_seq('HORARIO', 'ID_HORARIO', 'SEQ_HORARIO'),
        t_tab_seq('HORARIO_ESTACION', 'ID_HORARIO_ESTACION', 'SEQ_HORARIO_ESTACION'),
        t_tab_seq('INCIDENTE', 'ID_INCIDENTE', 'SEQ_INCIDENTE'),
        t_tab_seq('INCIDENTE_ELEMENTO_AFECTADO', 'ID_INCIDENTE_ELEMENTO', 'SEQ_INCIDENTE_ELEMENTO_AF_F066'),
        t_tab_seq('LINEA', 'ID_LINEA', 'SEQ_LINEA'),
        t_tab_seq('LINEA_ESTACION', 'ID_LINEA_ESTACION', 'SEQ_LINEA_ESTACION'),
        t_tab_seq('MODELO_TREN', 'ID_MODELO', 'SEQ_MODELO_TREN'),
        t_tab_seq('ORDEN_MANTENIMIENTO', 'ID_ORDEN', 'SEQ_ORDEN_MANTENIMIENTO'),
        t_tab_seq('ORDEN_REPUESTO', 'ID_ORDEN_REPUESTO', 'SEQ_ORDEN_REPUESTO'),
        t_tab_seq('ORDEN_TECNICO', 'ID_ORDEN_TECNICO', 'SEQ_ORDEN_TECNICO'),
        t_tab_seq('PASAJERO', 'ID_PASAJERO', 'SEQ_PASAJERO'),
        t_tab_seq('PLATAFORMA', 'ID_PLATAFORMA', 'SEQ_PLATAFORMA'),
        t_tab_seq('RECARGA', 'ID_RECARGA', 'SEQ_RECARGA'),
        t_tab_seq('REPUESTO', 'ID_REPUESTO', 'SEQ_REPUESTO'),
        t_tab_seq('RUTA', 'ID_RUTA', 'SEQ_RUTA'),
        t_tab_seq('RUTA_DETALLE', 'ID_RUTA_DETALLE', 'SEQ_RUTA_DETALLE'),
        t_tab_seq('TARIFA', 'ID_TARIFA', 'SEQ_TARIFA'),
        t_tab_seq('TARJETA', 'ID_TARJETA', 'SEQ_TARJETA'),
        t_tab_seq('TRANSFERENCIA', 'ID_TRANSFERENCIA', 'SEQ_TRANSFERENCIA'),
        t_tab_seq('TREN', 'ID_TREN', 'SEQ_TREN'),
        t_tab_seq('TREN_VAGON', 'ID_TREN_VAGON', 'SEQ_TREN_VAGON'),
        t_tab_seq('TURNO', 'ID_TURNO', 'SEQ_TURNO'),
        t_tab_seq('VAGON', 'ID_VAGON', 'SEQ_VAGON'),
        t_tab_seq('VIAJE_PASAJERO', 'ID_VIAJE_PASAJERO', 'SEQ_VIAJE_PASAJERO'),
        t_tab_seq('VIAJE_PROGRAMADO', 'ID_VIAJE', 'SEQ_VIAJE_PROGRAMADO')
    );
    v_max NUMBER;
    v_curr NUMBER;
    v_diff NUMBER;
    v_dummy NUMBER;
    v_sync_count NUMBER := 0;
BEGIN
    FOR i IN 1..v_tabs.COUNT LOOP
        BEGIN
            EXECUTE IMMEDIATE 'SELECT NVL(MAX(' || v_tabs(i).pk_col || '), 0) FROM ' || v_tabs(i).tabla INTO v_max;
            EXECUTE IMMEDIATE 'SELECT ' || v_tabs(i).secuencia || '.NEXTVAL FROM DUAL' INTO v_curr;
            
            IF v_curr <= v_max + 10 THEN
                v_diff := (v_max + 15) - v_curr;
                EXECUTE IMMEDIATE 'ALTER SEQUENCE ' || v_tabs(i).secuencia || ' INCREMENT BY ' || v_diff;
                EXECUTE IMMEDIATE 'SELECT ' || v_tabs(i).secuencia || '.NEXTVAL FROM DUAL' INTO v_dummy;
                EXECUTE IMMEDIATE 'ALTER SEQUENCE ' || v_tabs(i).secuencia || ' INCREMENT BY 1';
                v_sync_count := v_sync_count + 1;
            END IF;
        EXCEPTION
            WHEN OTHERS THEN
                DBMS_OUTPUT.PUT_LINE('Aviso en ' || v_tabs(i).secuencia || ': ' || SQLERRM);
        END;
    END LOOP;
    DBMS_OUTPUT.PUT_LINE('Sincronizacion completada. Secuencias ajustadas: ' || v_sync_count || ' de ' || v_tabs.COUNT);
END;
/

-- Incrementar temporalmente el stock disponible para permitir consumos del ano
UPDATE REPUESTO
SET stock_disponible = stock_disponible + 200
WHERE stock_disponible < 100;

COMMIT;

-- Ejecutar la sincronizacion inicial
BEGIN
    SP_SINCRONIZAR_TODAS_SECUENCIAS;
END;
/

COMMIT;
PROMPT [FASE 0] Preparacion y sincronizacion inicial finalizadas exitosamente.

