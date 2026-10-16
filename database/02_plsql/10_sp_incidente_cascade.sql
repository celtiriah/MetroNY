-- ==============================================================================
-- METRO NY - SCRIPT PL/SQL: 10_sp_incidente_cascade.sql
-- Proposito: Actualizar SP_REGISTRAR_INCIDENTE y SP_CANCELAR_VIAJES_AFECTADOS
--            para cierre atomico de estaciones y cancelacion en cascada.
-- Esquema: METRO_NY en Oracle 23ai (FREEPDB1)
-- ==============================================================================

-- 1. SP_REGISTRAR_INCIDENTE
CREATE OR REPLACE PROCEDURE SP_REGISTRAR_INCIDENTE (
    p_tipo               IN VARCHAR2,
    p_descripcion        IN VARCHAR2,
    p_nivel_severidad    IN VARCHAR2,
    p_reportado_por_id   IN NUMBER,
    p_tipo_elemento      IN VARCHAR2 DEFAULT NULL,
    p_elemento_id        IN NUMBER DEFAULT NULL,
    o_numero_incidente   OUT VARCHAR2,
    o_id_incidente       OUT NUMBER
) IS
    v_seq_val    NUMBER;
    v_est_id     NUMBER := NULL;
    v_tren_id    NUMBER := NULL;
    v_ruta_id    NUMBER := NULL;
    v_linea_id   NUMBER := NULL;
    v_cancelados NUMBER := 0;
BEGIN
    v_seq_val := SEQ_INCIDENTE.NEXTVAL;
    o_id_incidente := v_seq_val;
    o_numero_incidente := 'INC-' || TO_CHAR(SYSDATE, 'YYYYMMDD') || '-' || LPAD(v_seq_val, 4, '0');

    -- Insertar incidente
    INSERT INTO INCIDENTE (
        id_incidente, numero_incidente, tipo, descripcion,
        fecha_hora_inicio, nivel_severidad, reportado_por_id,
        estado, pasajeros_afectados_estimado
    ) VALUES (
        o_id_incidente, o_numero_incidente, p_tipo, p_descripcion,
        SYSTIMESTAMP, p_nivel_severidad, p_reportado_por_id,
        'Abierto', 500
    );

    -- Asociar elemento afectado segun el tipo indicado
    IF p_tipo_elemento IS NOT NULL AND p_elemento_id IS NOT NULL THEN
        IF p_tipo_elemento = 'ESTACION' THEN
            v_est_id := p_elemento_id;
        ELSIF p_tipo_elemento = 'TREN' THEN
            v_tren_id := p_elemento_id;
        ELSIF p_tipo_elemento = 'RUTA' THEN
            v_ruta_id := p_elemento_id;
        ELSIF p_tipo_elemento = 'LINEA' THEN
            v_linea_id := p_elemento_id;
        END IF;

        INSERT INTO INCIDENTE_ELEMENTO_AFECTADO (
            id_incidente_elemento, incidente_id, tipo_elemento,
            estacion_id, tren_id, ruta_id, linea_id, tipo_afectacion
        ) VALUES (
            SEQ_INCIDENTE_ELEMENTO_AF_F066.NEXTVAL, o_id_incidente, p_tipo_elemento,
            v_est_id, v_tren_id, v_ruta_id, v_linea_id, 'Retraso'
        );

        -- Cierre atomico de estacion en incidentes criticos o altos y cancelacion en cascada
        IF p_tipo_elemento = 'ESTACION' AND p_nivel_severidad IN ('Crítico', 'Critico', 'Alto', 'Alta') THEN
            UPDATE ESTACION
            SET estado_operativo = 'Cerrada Temporalmente'
            WHERE id_estacion = p_elemento_id;

            SP_CANCELAR_VIAJES_AFECTADOS(o_id_incidente, v_cancelados);
        ELSIF p_tipo_elemento IN ('RUTA', 'LINEA', 'TREN') AND p_nivel_severidad IN ('Crítico', 'Critico', 'Alto', 'Alta') THEN
            SP_CANCELAR_VIAJES_AFECTADOS(o_id_incidente, v_cancelados);
        END IF;
    END IF;

    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END SP_REGISTRAR_INCIDENTE;
/

-- 2. SP_CANCELAR_VIAJES_AFECTADOS
CREATE OR REPLACE PROCEDURE SP_CANCELAR_VIAJES_AFECTADOS (
    p_incidente_id      IN NUMBER,
    o_viajes_cancelados OUT NUMBER
) IS
BEGIN
    o_viajes_cancelados := 0;

    -- Cancelar viajes programados que utilicen rutas asociadas al incidente, estacion o tren afectado
    UPDATE VIAJE_PROGRAMADO
    SET estado = 'Cancelado'
    WHERE estado IN ('Programado', 'En Abordaje')
      AND (
          ruta_id IN (
              SELECT ruta_id FROM INCIDENTE_ELEMENTO_AFECTADO
              WHERE incidente_id = p_incidente_id AND ruta_id IS NOT NULL
          )
          OR ruta_id IN (
              SELECT r.id_ruta FROM RUTA r
              JOIN INCIDENTE_ELEMENTO_AFECTADO a ON r.linea_id = a.linea_id
              WHERE a.incidente_id = p_incidente_id
          )
          OR ruta_id IN (
              SELECT rd.ruta_id FROM RUTA_DETALLE rd
              JOIN INCIDENTE_ELEMENTO_AFECTADO a ON rd.estacion_id = a.estacion_id
              WHERE a.incidente_id = p_incidente_id
          )
          OR tren_id IN (
              SELECT a.tren_id FROM INCIDENTE_ELEMENTO_AFECTADO a
              WHERE a.incidente_id = p_incidente_id AND a.tren_id IS NOT NULL
          )
      );

    o_viajes_cancelados := SQL%ROWCOUNT;
    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END SP_CANCELAR_VIAJES_AFECTADOS;
/
