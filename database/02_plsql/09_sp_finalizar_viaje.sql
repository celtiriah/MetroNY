-- ======================================================================
-- SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]
-- Procedimiento Almacenado Canónico: SP_FINALIZAR_VIAJE
-- Requerimiento: R4 - Finalizar Viaje, Registrar Llegada, Acumular Odómetro y Liberar Tren
-- ======================================================================

CREATE OR REPLACE PROCEDURE SP_FINALIZAR_VIAJE (
    p_id_viaje           IN NUMBER,
    p_hora_real_llegada  IN TIMESTAMP DEFAULT NULL,
    o_kilometros_sumados OUT NUMBER,
    o_nuevo_kilometraje  OUT NUMBER,
    o_mensaje            OUT VARCHAR2
) IS
    v_numero_viaje      VARCHAR2(30);
    v_ruta_id           NUMBER(8);
    v_tren_id           NUMBER(8);
    v_estado_actual     VARCHAR2(20);
    v_hora_salida       TIMESTAMP;
    v_hora_llegada      TIMESTAMP;
    v_distancia         NUMBER(6,2) := 0;
    v_km_actual         NUMBER(10,2) := 0;
    v_codigo_tren       VARCHAR2(20) := '';
BEGIN
    -- 1. Validar existencia del viaje y bloquear fila para evitar condiciones de carrera
    BEGIN
        SELECT numero_viaje, ruta_id, tren_id, estado, hora_real_salida
        INTO v_numero_viaje, v_ruta_id, v_tren_id, v_estado_actual, v_hora_salida
        FROM VIAJE_PROGRAMADO
        WHERE id_viaje = p_id_viaje
        FOR UPDATE;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE_APPLICATION_ERROR(-20030, 'El viaje especificado con ID ' || p_id_viaje || ' no existe en el sistema.');
    END;

    -- 2. Validar que el viaje no esté ya finalizado o cancelado (Guardia de Idempotencia)
    IF v_estado_actual = 'Completado' THEN
        RAISE_APPLICATION_ERROR(-20031, 'El viaje ' || v_numero_viaje || ' ya se encuentra en estado Completado.');
    ELSIF v_estado_actual = 'Cancelado' THEN
        RAISE_APPLICATION_ERROR(-20032, 'El viaje ' || v_numero_viaje || ' fue cancelado y no puede ser finalizado.');
    END IF;

    -- 3. Determinar hora real de llegada y validar consistencia temporal
    v_hora_llegada := NVL(p_hora_real_llegada, SYSTIMESTAMP);
    IF v_hora_salida IS NOT NULL AND v_hora_llegada < v_hora_salida THEN
        RAISE_APPLICATION_ERROR(-20033, 'La hora de llegada real (' || TO_CHAR(v_hora_llegada, 'YYYY-MM-DD HH24:MI:SS') || 
                                ') no puede ser anterior a la hora de salida (' || TO_CHAR(v_hora_salida, 'YYYY-MM-DD HH24:MI:SS') || ').');
    END IF;

    -- 4. Obtener distancia total de la ruta asociada
    IF v_ruta_id IS NOT NULL THEN
        BEGIN
            SELECT NVL(distancia_total_km, 0)
            INTO v_distancia
            FROM RUTA
            WHERE id_ruta = v_ruta_id;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                v_distancia := 0;
        END;
    END IF;

    -- 5. Acumular odómetro y liberar el tren a estado 'Disponible'
    IF v_tren_id IS NOT NULL THEN
        BEGIN
            SELECT NVL(kilometraje_acumulado, 0), codigo_interno
            INTO v_km_actual, v_codigo_tren
            FROM TREN
            WHERE id_tren = v_tren_id
            FOR UPDATE;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                v_km_actual := 0;
                v_codigo_tren := 'ID ' || v_tren_id;
        END;

        o_kilometros_sumados := v_distancia;
        o_nuevo_kilometraje  := v_km_actual + v_distancia;

        UPDATE TREN
        SET kilometraje_acumulado = o_nuevo_kilometraje,
            estado_operativo      = 'Disponible'
        WHERE id_tren = v_tren_id;
    ELSE
        o_kilometros_sumados := v_distancia;
        o_nuevo_kilometraje  := 0;
    END IF;

    -- 6. Actualizar VIAJE_PROGRAMADO a 'Completado' y registrar hora real de llegada
    UPDATE VIAJE_PROGRAMADO
    SET estado            = 'Completado',
        hora_real_llegada = v_hora_llegada
    WHERE id_viaje = p_id_viaje;

    -- 7. Mensaje de retorno
    o_mensaje := 'Viaje ' || v_numero_viaje || ' finalizado exitosamente. ' ||
                 'Kilometraje sumado: ' || TO_CHAR(o_kilometros_sumados, 'FM999990.00') || ' km. ' ||
                 'Nuevo odómetro del tren ' || v_codigo_tren || ': ' || TO_CHAR(o_nuevo_kilometraje, 'FM999990.00') || ' km. ' ||
                 'Unidad liberada a estado Disponible.';

    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END SP_FINALIZAR_VIAJE;
/
