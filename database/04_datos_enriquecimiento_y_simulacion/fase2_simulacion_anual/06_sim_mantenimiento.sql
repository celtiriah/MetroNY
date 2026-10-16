-- ==============================================================================
-- PROYECTO: METRO NY - GESTION INTEGRAL DEL SUBWAY DE NUEVA YORK
-- ARCHIVO:  database/04_datos_simulacion_1anno/06_sim_mantenimiento.sql
-- PROPOSITO: Generar 150 ordenes de mantenimiento, 150 asignaciones tecnicas
--            y 100 consumos de repuestos respetando ciclos de auditoria.
-- ==============================================================================

SET SERVEROUTPUT ON SIZE UNLIMITED;

PROMPT ==============================================================================
PROMPT [FASE 6] Generando 150 Ordenes de Mantenimiento y Cuadrillas (Simulacion Anual)...
PROMPT ==============================================================================

DECLARE
    TYPE t_num_list IS TABLE OF NUMBER;
    v_equipos t_num_list := t_num_list(1, 2, 3, 5);
    v_tecnicos t_num_list := t_num_list(7, 8);
    
    TYPE t_cost_list IS TABLE OF NUMBER;
    v_costos_rep t_cost_list := t_cost_list(145.50, 380.00, 520.00, 890.00, 65.00, 115.00, 340.00, 1250.00);

    v_ord_id NUMBER;
    v_tec_ord_id NUMBER;
    v_rep_ord_id NUMBER;
    v_eq_id NUMBER;
    v_tec_id NUMBER;
    v_rep_id NUMBER;
    v_fecha DATE;
    v_tipo_mant VARCHAR2(40);
    v_prio VARCHAR2(20);
    v_costo NUMBER(10,2);
    v_costo_rep NUMBER(10,2);
    v_desc VARCHAR2(200);
    v_count_ord NUMBER := 0;
    v_count_tec NUMBER := 0;
    v_count_rep NUMBER := 0;
BEGIN
    FOR i IN 1..150 LOOP
        v_eq_id := v_equipos(MOD(i, v_equipos.COUNT) + 1);
        v_tec_id := v_tecnicos(MOD(i, v_tecnicos.COUNT) + 1);
        
        -- Distribuir en los ultimos 350 dias
        v_fecha := TRUNC(SYSDATE) - (350 - TRUNC(i * 345 / 150));

        IF MOD(i, 4) = 0 THEN
            v_tipo_mant := 'Correctivo';
            v_prio := 'Alta';
            v_desc := 'Reparacion correctiva por desgaste operativo y ajuste de componentes.';
            v_costo := 850.00 + MOD(i * 19, 400);
        ELSIF MOD(i, 4) = 1 THEN
            v_tipo_mant := 'Preventivo';
            v_prio := 'Media';
            v_desc := 'Inspeccion preventiva programada, lubricacion y calibracion de sistemas.';
            v_costo := 450.00 + MOD(i * 11, 200);
        ELSIF MOD(i, 4) = 2 THEN
            v_tipo_mant := 'Inspección de Seguridad';
            v_prio := 'Urgente';
            v_desc := 'Revision tecnica de seguridad estructural y pruebas de frenado.';
            v_costo := 620.00 + MOD(i * 13, 300);
        ELSE
            v_tipo_mant := 'Predictivo';
            v_prio := 'Baja';
            v_desc := 'Monitoreo de vibraciones, analisis termografico y telemetria.';
            v_costo := 350.00 + MOD(i * 7, 150);
        END IF;

        SELECT SEQ_ORDEN_MANTENIMIENTO.NEXTVAL INTO v_ord_id FROM DUAL;

        -- 1. Insertar orden con estado 'En Ejecucion' para permitir asignacion de tecnicos y repuestos
        INSERT INTO ORDEN_MANTENIMIENTO (
            id_orden, numero_orden, equipo_id, tipo_mantenimiento,
            descripcion_trabajo, fecha_solicitud, fecha_programada,
            fecha_inicio, fecha_finalizacion, prioridad, costo, estado
        ) VALUES (
            v_ord_id,
            'OT-SIM-' || TO_CHAR(v_fecha, 'YYYYMMDD') || '-' || LPAD(i, 4, '0'),
            v_eq_id,
            v_tipo_mant,
            v_desc,
            v_fecha,
            v_fecha + 1,
            v_fecha + 1,
            v_fecha + 2,
            v_prio,
            v_costo,
            'En Ejecución'
        );
        v_count_ord := v_count_ord + 1;

        -- 2. Asignar tecnico en cuadrilla
        SELECT SEQ_ORDEN_TECNICO.NEXTVAL INTO v_tec_ord_id FROM DUAL;
        INSERT INTO ORDEN_TECNICO (
            id_orden_tecnico, orden_id, empleado_id, rol_en_orden
        ) VALUES (
            v_tec_ord_id,
            v_ord_id,
            v_tec_id,
            'Técnico Principal'
        );
        v_count_tec := v_count_tec + 1;

        -- 3. Consumir repuesto para las primeras 100 ordenes
        IF i <= 100 THEN
            v_rep_id := 1 + MOD(i, 8);
            v_costo_rep := v_costos_rep(v_rep_id);

            SELECT SEQ_ORDEN_REPUESTO.NEXTVAL INTO v_rep_ord_id FROM DUAL;
            INSERT INTO ORDEN_REPUESTO (
                id_orden_repuesto, orden_id, repuesto_id, cantidad, costo_total
            ) VALUES (
                v_rep_ord_id,
                v_ord_id,
                v_rep_id,
                1,
                v_costo_rep
            );
            v_count_rep := v_count_rep + 1;
        END IF;

        -- 4. Cerrar la orden como 'Completada' para las primeras 140 ordenes (dejar 10 en ejecucion)
        IF i <= 140 THEN
            UPDATE ORDEN_MANTENIMIENTO
            SET estado = 'Completada',
                descripcion_trabajo = v_desc || ' Trabajo concluido satisfactoriamente con pruebas operativas aprobadas.'
            WHERE id_orden = v_ord_id;
        END IF;
    END LOOP;

    DBMS_OUTPUT.PUT_LINE('Se generaron ' || v_count_ord || ' ordenes, ' || v_count_tec || ' asignaciones tecnicas y ' || v_count_rep || ' consumos de repuestos.');
END;
/

COMMIT;
PROMPT [FASE 6] Insercion de ordenes de mantenimiento finalizada exitosamente.

