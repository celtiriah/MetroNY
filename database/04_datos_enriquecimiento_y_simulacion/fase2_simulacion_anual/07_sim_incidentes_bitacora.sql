-- ==============================================================================
-- PROYECTO: METRO NY - GESTION INTEGRAL DEL SUBWAY DE NUEVA YORK
-- ARCHIVO:  database/04_datos_simulacion_1anno/07_sim_incidentes_bitacora.sql
-- PROPOSITO: Generar 60 incidentes, 60 elementos afectados y 180 trazas de bitacora.
-- ==============================================================================

SET SERVEROUTPUT ON SIZE UNLIMITED;

PROMPT ==============================================================================
PROMPT [FASE 7] Generando 60 Incidentes, Elementos Afectados y 180 Trazas de Bitacora...
PROMPT ==============================================================================

DECLARE
    TYPE t_str_list IS TABLE OF VARCHAR2(50);
    TYPE t_num_list IS TABLE OF NUMBER;

    v_tipos t_str_list := t_str_list(
        'Falla de Señalización', 'Emergencia Médica', 'Falla Mecánica',
        'Congestión', 'Objeto en la Vía', 'Mantenimiento no Programado'
    );
    v_severidades t_str_list := t_str_list('Bajo', 'Medio', 'Alto', 'Bajo', 'Medio');
    v_afectaciones t_str_list := t_str_list('Retraso', 'Cierre de Estación', 'Cambio de Ruta', 'Retiro de Tren');
    v_tablas_bit t_str_list := t_str_list('VIAJE_PROGRAMADO', 'ORDEN_MANTENIMIENTO', 'INCIDENTE', 'TURNO', 'TARJETA');

    v_estaciones t_num_list := t_num_list();
    v_trenes t_num_list := t_num_list(1, 2, 3, 4);

    v_inc_id NUMBER;
    v_elem_id NUMBER;
    v_bit_id NUMBER;
    v_tipo VARCHAR2(50);
    v_sev VARCHAR2(20);
    v_fecha TIMESTAMP;
    v_fecha_fin TIMESTAMP;
    v_est_id NUMBER;
    v_tren_id NUMBER;
    v_duracion_min NUMBER;
    v_pas_estimados NUMBER;
    v_causa VARCHAR2(200);
    v_acciones VARCHAR2(200);
    v_resolucion VARCHAR2(200);
    v_tabla_nombre VARCHAR2(50);

    v_count_inc NUMBER := 0;
    v_count_elem NUMBER := 0;
    v_count_bit NUMBER := 0;
BEGIN
    -- Cargar estaciones activas
    SELECT id_estacion BULK COLLECT INTO v_estaciones
    FROM ESTACION
    WHERE estado_operativo = 'Operativa'
    ORDER BY id_estacion ASC;

    -- 1. Insertar 60 Incidentes y 60 Elementos Afectados
    FOR i IN 1..60 LOOP
        v_tipo := v_tipos(MOD(i, v_tipos.COUNT) + 1);
        v_sev := v_severidades(MOD(i, v_severidades.COUNT) + 1);
        
        -- Distribuir en los ultimos 350 dias
        v_fecha := NUMTODSINTERVAL(MOD(i * 137, 86400), 'SECOND') + (TRUNC(SYSDATE) - (350 - TRUNC(i * 340 / 60)));
        v_duracion_min := 20 + MOD(i * 17, 75);
        v_fecha_fin := NUMTODSINTERVAL(v_duracion_min * 60, 'SECOND') + v_fecha;
        v_pas_estimados := 120 + MOD(i * 47, 850);

        v_causa := 'Diagnostico preliminar de ' || LOWER(v_tipo) || ' detectado por telemetria y reporte de cabina.';
        v_acciones := 'Despacho de brigada de respuesta rapida y coordinacion con torre de control.';
        v_resolucion := 'Inspeccion fisica completada y autorizacion de reanudacion normal de servicio.';

        SELECT SEQ_INCIDENTE.NEXTVAL INTO v_inc_id FROM DUAL;

        INSERT INTO INCIDENTE (
            id_incidente, numero_incidente, tipo, descripcion,
            fecha_hora_inicio, fecha_hora_fin, nivel_severidad,
            reportado_por_id, estado, causa_identificada,
            acciones_realizadas, resolucion, pasajeros_afectados_estimado
        ) VALUES (
            v_inc_id,
            'INC-SIM-' || TO_CHAR(v_fecha, 'YYYYMMDD') || '-' || LPAD(i, 3, '0'),
            v_tipo,
            'Incidente operacional simulado: ' || v_tipo || ' en sector metropolitano.',
            v_fecha,
            v_fecha_fin,
            v_sev,
            1, -- Reportado por supervisor central
            'Cerrado',
            v_causa,
            v_acciones,
            v_resolucion,
            v_pas_estimados
        );
        v_count_inc := v_count_inc + 1;

        -- 2. Elemento afectado asociado (Estacion o Tren)
        SELECT SEQ_INCIDENTE_ELEMENTO_AF_F066.NEXTVAL INTO v_elem_id FROM DUAL;

        IF MOD(i, 2) = 0 THEN
            v_est_id := v_estaciones(MOD(i, v_estaciones.COUNT) + 1);
            INSERT INTO INCIDENTE_ELEMENTO_AFECTADO (
                id_incidente_elemento, incidente_id, tipo_elemento,
                estacion_id, tren_id, linea_id, tipo_afectacion
            ) VALUES (
                v_elem_id,
                v_inc_id,
                'ESTACION',
                v_est_id,
                NULL,
                NULL,
                'Retraso'
            );
        ELSE
            v_tren_id := v_trenes(MOD(i, v_trenes.COUNT) + 1);
            INSERT INTO INCIDENTE_ELEMENTO_AFECTADO (
                id_incidente_elemento, incidente_id, tipo_elemento,
                estacion_id, tren_id, linea_id, tipo_afectacion
            ) VALUES (
                v_elem_id,
                v_inc_id,
                'TREN',
                NULL,
                v_tren_id,
                NULL,
                'Retraso'
            );
        END IF;
        v_count_elem := v_count_elem + 1;
    END LOOP;

    -- 3. Generar 180 Trazas de Bitacora de Auditoria
    FOR b IN 1..180 LOOP
        v_fecha := NUMTODSINTERVAL(MOD(b * 431, 86400), 'SECOND') + (TRUNC(SYSDATE) - (350 - TRUNC(b * 340 / 180)));
        v_tabla_nombre := v_tablas_bit(MOD(b, v_tablas_bit.COUNT) + 1);
        SELECT SEQ_BITACORA.NEXTVAL INTO v_bit_id FROM DUAL;

        INSERT INTO BITACORA (
            id_bitacora, fecha_hora, tabla_afectada,
            operacion, registro_id, usuario, descripcion
        ) VALUES (
            v_bit_id,
            v_fecha,
            v_tabla_nombre,
            'INSERT',
            b * 3,
            'SISTEMA_SIM',
            '[SIMULACION] Registro y validacion periodica de auditoria operativa anual #' || b
        );
        v_count_bit := v_count_bit + 1;
    END LOOP;

    DBMS_OUTPUT.PUT_LINE('Se generaron ' || v_count_inc || ' incidentes, ' || v_count_elem || ' elementos afectados y ' || v_count_bit || ' registros de bitacora.');
END;
/

COMMIT;
PROMPT [FASE 7] Insercion de incidentes y bitacora finalizada exitosamente.

