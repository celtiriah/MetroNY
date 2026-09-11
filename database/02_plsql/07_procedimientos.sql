-- ======================================================================
-- SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]
-- Capa de Programacion PL/SQL - 07_procedimientos.sql
-- 6 Procedimientos Almacenados Transaccionales Obligatorios (SPs)
-- ======================================================================

-- 1. SP: Programar un nuevo viaje validando disponibilidad de tren, division y conductor
CREATE OR REPLACE PROCEDURE SP_PROGRAMAR_VIAJE (
    p_ruta_id           IN NUMBER,
    p_fecha             IN DATE,
    p_hora_prog_salida  IN TIMESTAMP,
    p_hora_prog_llegada IN TIMESTAMP,
    p_tren_id           IN NUMBER,
    p_conductor_id      IN NUMBER,
    p_horario_id        IN NUMBER DEFAULT NULL,
    o_numero_viaje      OUT VARCHAR2,
    o_id_viaje          OUT NUMBER
) IS
    v_tren_disponible     NUMBER;
    v_cert_valida         NUMBER := 0;
    v_solapamiento        NUMBER := 0;
    v_modelo_tren_id      NUMBER;
    v_seq_val             NUMBER;
BEGIN
    -- A. Validar que la hora de llegada sea posterior a la salida
    IF p_hora_prog_llegada <= p_hora_prog_salida THEN
        RAISE_APPLICATION_ERROR(-20002, 'La hora programada de llegada debe ser posterior a la hora de salida.');
    END IF;

    -- B. Validar disponibilidad del tren
    v_tren_disponible := FN_TREN_DISPONIBLE(p_tren_id);
    IF v_tren_disponible = 0 THEN
        RAISE_APPLICATION_ERROR(-20003, 'El tren seleccionado no se encuentra disponible o esta en taller de mantenimiento.');
    END IF;

    -- C. Obtener modelo del tren asignado
    SELECT modelo_id
    INTO v_modelo_tren_id
    FROM TREN
    WHERE id_tren = p_tren_id;

    -- D. Validar certificacion vigente del conductor para este modelo de tren
    SELECT COUNT(*)
    INTO v_cert_valida
    FROM CERTIFICACION c
    JOIN CERTIFICACION_MODELO cm ON c.id_certificacion = cm.certificacion_id
    WHERE c.empleado_id = p_conductor_id
      AND cm.modelo_id = v_modelo_tren_id
      AND c.estado = 'Vigente'
      AND c.fecha_vencimiento >= p_fecha;

    IF v_cert_valida = 0 THEN
        -- Si no tiene certificacion especifica de modelo, verificar si tiene licencia general vigente
        SELECT COUNT(*)
        INTO v_cert_valida
        FROM CERTIFICACION c
        WHERE c.empleado_id = p_conductor_id
          AND c.estado = 'Vigente'
          AND c.fecha_vencimiento >= p_fecha;
          
        IF v_cert_valida = 0 THEN
            RAISE_APPLICATION_ERROR(-20005, 'El conductor no posee una certificacion tecnica vigente para la fecha del viaje.');
        END IF;
    END IF;

    -- E. Validar que el conductor no tenga otro viaje superpuesto en el mismo horario
    SELECT COUNT(*)
    INTO v_solapamiento
    FROM VIAJE_PROGRAMADO
    WHERE conductor_id = p_conductor_id
      AND fecha = p_fecha
      AND estado NOT IN ('Cancelado', 'Completado')
      AND (
          (hora_prog_salida < p_hora_prog_llegada AND hora_prog_llegada > p_hora_prog_salida)
      );

    IF v_solapamiento > 0 THEN
        RAISE_APPLICATION_ERROR(-20006, 'Conflicto de programacion: El conductor ya tiene asignado otro viaje en ese intervalo horario.');
    END IF;

    -- F. Generar ID y codigo de viaje
    v_seq_val := SEQ_VIAJE_PROGRAMADO.NEXTVAL;
    o_id_viaje := v_seq_val;
    o_numero_viaje := 'VJ-' || TO_CHAR(p_fecha, 'YYYYMMDD') || '-' || LPAD(v_seq_val, 4, '0');

    -- G. Insertar en VIAJE_PROGRAMADO
    INSERT INTO VIAJE_PROGRAMADO (
        id_viaje, numero_viaje, ruta_id, horario_id, fecha,
        hora_prog_salida, hora_prog_llegada, tren_id, conductor_id,
        estado, cantidad_estimada_pasajeros
    ) VALUES (
        o_id_viaje, o_numero_viaje, p_ruta_id, p_horario_id, p_fecha,
        p_hora_prog_salida, p_hora_prog_llegada, p_tren_id, p_conductor_id,
        'Programado', 850
    );

    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END SP_PROGRAMAR_VIAJE;
/

-- 2. SP: Registrar el ingreso de un pasajero en torniquete y cobrar tarifa
CREATE OR REPLACE PROCEDURE SP_REGISTRAR_INGRESO (
    p_numero_tarjeta       IN VARCHAR2,
    p_estacion_id          IN NUMBER,
    p_viaje_programado_id  IN NUMBER DEFAULT NULL,
    o_resultado            OUT VARCHAR2,
    o_mensaje              OUT VARCHAR2,
    o_monto_cobrado        OUT NUMBER,
    o_nuevo_saldo          OUT NUMBER
) IS
    v_id_tarjeta      NUMBER;
    v_tarifa_id       NUMBER;
    v_tarifa_monto    NUMBER(6,2);
    v_saldo_actual    NUMBER(10,2);
    v_estado_tarjeta  VARCHAR2(30);
    v_vencimiento     DATE;
    v_estacion_estado VARCHAR2(30);
    v_tx_numero       VARCHAR2(50);
BEGIN
    o_monto_cobrado := 0;

    -- A. Verificar estado de la estacion
    SELECT estado_operativo
    INTO v_estacion_estado
    FROM ESTACION
    WHERE id_estacion = p_estacion_id;

    IF v_estacion_estado = 'Cerrada Temporalmente' THEN
        o_resultado := 'RECHAZADO';
        o_mensaje := 'Estacion temporalmente fuera de servicio. Ingreso no permitido.';
        RETURN;
    END IF;

    -- B. Verificar tarjeta
    SELECT t.id_tarjeta, t.tarifa_id, t.saldo_disponible, t.estado, t.fecha_vencimiento, tar.monto
    INTO v_id_tarjeta, v_tarifa_id, v_saldo_actual, v_estado_tarjeta, v_vencimiento, v_tarifa_monto
    FROM TARJETA t
    JOIN TARIFA tar ON t.tarifa_id = tar.id_tarifa
    WHERE t.numero_tarjeta = p_numero_tarjeta;

    -- Validar si esta bloqueada o vencida
    IF v_estado_tarjeta IN ('Bloqueada', 'Cancelada', 'Reportada Perdida') THEN
        o_resultado := 'RECHAZADO';
        o_mensaje := 'Tarjeta inhabilitada (Estado: ' || v_estado_tarjeta || ').';
        o_nuevo_saldo := v_saldo_actual;
        RETURN;
    END IF;

    IF v_vencimiento < TRUNC(SYSDATE) THEN
        o_resultado := 'RECHAZADO';
        o_mensaje := 'Tarjeta vencida con fecha ' || TO_CHAR(v_vencimiento, 'YYYY-MM-DD') || '.';
        o_nuevo_saldo := v_saldo_actual;
        RETURN;
    END IF;

    -- C. Validar saldo
    IF v_saldo_actual < v_tarifa_monto THEN
        o_resultado := 'SALDO_INSUFICIENTE';
        o_mensaje := 'Saldo insuficiente ($' || TO_CHAR(v_saldo_actual, '990.00') || '). Tarifa requerida: $' || TO_CHAR(v_tarifa_monto, '990.00') || '.';
        o_nuevo_saldo := v_saldo_actual;
        RETURN;
    END IF;

    -- D. Descontar saldo
    o_nuevo_saldo := v_saldo_actual - v_tarifa_monto;
    o_monto_cobrado := v_tarifa_monto;

    UPDATE TARJETA
    SET saldo_disponible = o_nuevo_saldo
    WHERE id_tarjeta = v_id_tarjeta;

    -- E. Registrar paso en VIAJE_PASAJERO
    v_tx_numero := 'TX-' || TO_CHAR(SYSDATE, 'YYYYMMDD') || '-' || LPAD(SEQ_VIAJE_PASAJERO.NEXTVAL, 8, '0');

    INSERT INTO VIAJE_PASAJERO (
        id_viaje_pasajero, numero_transaccion, tarjeta_id,
        estacion_ingreso_id, fecha_hora_ingreso, tarifa_id,
        monto_cobrado, viaje_programado_id, estado_transaccion
    ) VALUES (
        SEQ_VIAJE_PASAJERO.CURRVAL, v_tx_numero, v_id_tarjeta,
        p_estacion_id, SYSTIMESTAMP, v_tarifa_id,
        v_tarifa_monto, p_viaje_programado_id, 'Cerrada'
    );

    COMMIT;
    o_resultado := 'AUTORIZADO';
    o_mensaje := 'Paso autorizado. Cobro: $' || TO_CHAR(v_tarifa_monto, '990.00') || ' | Saldo restante: $' || TO_CHAR(o_nuevo_saldo, '990.00');
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        o_resultado := 'RECHAZADO';
        o_mensaje := 'Numero de tarjeta no registrado en el sistema.';
        o_nuevo_saldo := 0;
    WHEN OTHERS THEN
        ROLLBACK;
        o_resultado := 'ERROR';
        o_mensaje := 'Error interno al procesar ingreso: ' || SQLERRM;
        o_nuevo_saldo := 0;
END SP_REGISTRAR_INGRESO;
/

-- 3. SP: Recargar saldo a una tarjeta OMNY
CREATE OR REPLACE PROCEDURE SP_RECARGAR_TARJETA (
    p_numero_tarjeta    IN VARCHAR2,
    p_monto             IN NUMBER,
    p_medio_pago        IN VARCHAR2,
    p_estacion_canal    IN VARCHAR2 DEFAULT 'Torniquete Estacion',
    o_nuevo_saldo       OUT NUMBER,
    o_num_transaccion   OUT VARCHAR2
) IS
    v_id_tarjeta     NUMBER;
    v_saldo_ant      NUMBER(10,2);
    v_estado_tarjeta VARCHAR2(30);
BEGIN
    IF p_monto <= 0 THEN
        RAISE_APPLICATION_ERROR(-20007, 'El monto de recarga debe ser estrictamente positivo.');
    END IF;

    SELECT id_tarjeta, saldo_disponible, estado
    INTO v_id_tarjeta, v_saldo_ant, v_estado_tarjeta
    FROM TARJETA
    WHERE numero_tarjeta = p_numero_tarjeta;

    IF v_estado_tarjeta = 'Cancelada' THEN
        RAISE_APPLICATION_ERROR(-20008, 'No es posible recargar una tarjeta cancelada.');
    END IF;

    o_nuevo_saldo := v_saldo_ant + p_monto;
    o_num_transaccion := 'REC-' || TO_CHAR(SYSDATE, 'YYYYMMDD') || '-' || LPAD(SEQ_RECARGA.NEXTVAL, 6, '0');

    -- Actualizar saldo en tarjeta
    UPDATE TARJETA
    SET saldo_disponible = o_nuevo_saldo
    WHERE id_tarjeta = v_id_tarjeta;

    -- Registrar transaccion en historial
    INSERT INTO RECARGA (
        id_recarga, numero_transaccion, tarjeta_id, fecha_hora,
        monto, medio_pago, estacion_canal, saldo_anterior, saldo_posterior
    ) VALUES (
        SEQ_RECARGA.CURRVAL, o_num_transaccion, v_id_tarjeta, SYSTIMESTAMP,
        p_monto, p_medio_pago, p_estacion_canal, v_saldo_ant, o_nuevo_saldo
    );

    COMMIT;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RAISE_APPLICATION_ERROR(-20009, 'La tarjeta indicada no existe.');
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END SP_RECARGAR_TARJETA;
/

-- 4. SP: Crear una orden de mantenimiento y cambiar estado de equipo/tren
CREATE OR REPLACE PROCEDURE SP_CREAR_ORDEN_MANTENIMIENTO (
    p_equipo_id           IN NUMBER,
    p_tipo_mantenimiento  IN VARCHAR2,
    p_descripcion         IN VARCHAR2,
    p_prioridad           IN VARCHAR2,
    p_tecnico_id          IN NUMBER DEFAULT NULL,
    o_numero_orden        OUT VARCHAR2,
    o_id_orden            OUT NUMBER
) IS
    v_tipo_ref   VARCHAR2(30);
    v_ref_id     NUMBER;
    v_seq_val    NUMBER;
BEGIN
    v_seq_val := SEQ_ORDEN_MANTENIMIENTO.NEXTVAL;
    o_id_orden := v_seq_val;
    o_numero_orden := 'ORD-' || TO_CHAR(SYSDATE, 'YYYY') || '-' || LPAD(v_seq_val, 4, '0');

    -- Insertar orden
    INSERT INTO ORDEN_MANTENIMIENTO (
        id_orden, numero_orden, equipo_id, tipo_mantenimiento,
        descripcion_trabajo, fecha_solicitud, fecha_programada,
        fecha_inicio, prioridad, costo, estado
    ) VALUES (
        o_id_orden, o_numero_orden, p_equipo_id, p_tipo_mantenimiento,
        p_descripcion, SYSDATE, SYSDATE, SYSDATE, p_prioridad, 0, 'En Ejecución'
    );

    -- Si se especifico un tecnico lider, registrarlo
    IF p_tecnico_id IS NOT NULL THEN
        INSERT INTO ORDEN_TECNICO (
            id_orden_tecnico, orden_id, empleado_id, rol_en_orden
        ) VALUES (
            SEQ_ORDEN_TECNICO.NEXTVAL, o_id_orden, p_tecnico_id, 'Lider de Reparacion'
        );
    END IF;

    -- Si el equipo afectado es un tren, cambiar estado en TREN
    SELECT tipo_referencia, referencia_id
    INTO v_tipo_ref, v_ref_id
    FROM EQUIPO
    WHERE id_equipo = p_equipo_id;

    IF v_tipo_ref = 'TREN' AND v_ref_id IS NOT NULL THEN
        UPDATE TREN
        SET estado_operativo = 'En Mantenimiento'
        WHERE id_tren = v_ref_id;
    END IF;

    -- Actualizar estado del equipo
    UPDATE EQUIPO
    SET estado = 'En Mantenimiento',
        fecha_ultima_revision = SYSDATE
    WHERE id_equipo = p_equipo_id;

    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END SP_CREAR_ORDEN_MANTENIMIENTO;
/

-- 5. SP: Registrar un incidente operativo y asociar elemento afectado
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
    END IF;

    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END SP_REGISTRAR_INCIDENTE;
/

-- 6. SP: Cancelar automaticamente viajes afectados por cierre de estacion o ruta
CREATE OR REPLACE PROCEDURE SP_CANCELAR_VIAJES_AFECTADOS (
    p_incidente_id      IN NUMBER,
    o_viajes_cancelados OUT NUMBER
) IS
    v_afectaciones NUMBER := 0;
BEGIN
    o_viajes_cancelados := 0;

    -- Cancelar viajes programados que utilicen rutas asociadas al incidente
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
      );

    o_viajes_cancelados := SQL%ROWCOUNT;
    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END SP_CANCELAR_VIAJES_AFECTADOS;
/

EXIT;
