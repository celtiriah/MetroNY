-- ==============================================================================
-- PROYECTO: METRO NY - GESTION INTEGRAL DEL SUBWAY DE NUEVA YORK
-- ARCHIVO:  database/04_datos_simulacion_1anno/03_sim_viajes_pasajeros.sql
-- PROPOSITO: Generar 2,400 validaciones en torniquetes (tap-in / tap-out)
--            a lo largo de 360 dias respetando horas pico y reglas antifraude.
-- ==============================================================================

SET SERVEROUTPUT ON SIZE UNLIMITED;

PROMPT ==============================================================================
PROMPT [FASE 3] Generando 2,400 Validaciones en Torniquetes (Simulacion Anual)...
PROMPT ==============================================================================

DECLARE
    TYPE t_num_list IS TABLE OF NUMBER;
    TYPE t_card_rec IS RECORD (
        id NUMBER,
        tarifa_id NUMBER
    );
    TYPE t_card_list IS TABLE OF t_card_rec;

    v_estaciones t_num_list := t_num_list();
    v_tarjetas t_card_list := t_card_list();
    
    v_viaje_id NUMBER;
    v_tar_idx NUMBER;
    v_card t_card_rec;
    v_est_in NUMBER;
    v_est_out NUMBER;
    v_fecha_base DATE;
    v_fecha_in TIMESTAMP;
    v_fecha_out TIMESTAMP;
    v_monto NUMBER(6,2);
    v_hora NUMBER;
    v_min NUMBER;
    v_duracion_min NUMBER;
    v_count NUMBER := 0;
    v_trips_today NUMBER;
BEGIN
    -- Cargar estaciones activas
    SELECT id_estacion BULK COLLECT INTO v_estaciones
    FROM ESTACION
    WHERE estado_operativo = 'Operativa'
    ORDER BY id_estacion ASC;

    -- Cargar tarjetas simuladas con su tarifa asociada
    FOR r IN (
        SELECT id_tarjeta, NVL(tarifa_id, 1) as t_id
        FROM TARJETA
        WHERE numero_tarjeta LIKE 'OMNY-SIM-%'
        ORDER BY id_tarjeta ASC
    ) LOOP
        v_tarjetas.EXTEND;
        v_tarjetas(v_tarjetas.COUNT).id := r.id_tarjeta;
        v_tarjetas(v_tarjetas.COUNT).tarifa_id := r.t_id;
    END LOOP;

    IF v_tarjetas.COUNT = 0 OR v_estaciones.COUNT = 0 THEN
        DBMS_OUTPUT.PUT_LINE('Error: Faltan estaciones o tarjetas simuladas. Ejecute Fases previas.');
        RETURN;
    END IF;

    -- Generar dia por dia en orden cronologico estricto (del dia 360 atras hasta hoy)
    FOR dia IN REVERSE 1..360 LOOP
        v_fecha_base := TRUNC(SYSDATE) - dia;
        
        -- Entre 6 y 8 viajes por dia para totalizar 2,400 viajes en 360 dias
        v_trips_today := 6 + MOD(dia, 3); -- 6, 7 o 8 viajes
        
        FOR t IN 1..v_trips_today LOOP
            v_count := v_count + 1;
            EXIT WHEN v_count > 2400;

            -- Seleccionar tarjeta rotativamente
            v_tar_idx := MOD(dia * 7 + t, v_tarjetas.COUNT) + 1;
            v_card := v_tarjetas(v_tar_idx);

            -- Horarios con predominio de horas pico
            IF MOD(t, 2) = 1 THEN
                -- Pico manana: entre 07:00 y 09:30
                v_hora := 7 + TRUNC(MOD(t * 13 + dia, 3));
                v_min := MOD((t * 29 + dia * 7), 59);
            ELSE
                -- Pico tarde/noche: entre 16:30 y 19:30
                v_hora := 16 + TRUNC(MOD(t * 11 + dia, 4));
                v_min := MOD((t * 31 + dia * 11), 59);
            END IF;

            v_fecha_in := NUMTODSINTERVAL(v_hora * 3600 + v_min * 60, 'SECOND') + v_fecha_base;
            v_duracion_min := 15 + MOD(t * 7 + dia, 35); -- 15 a 49 minutos de viaje
            v_fecha_out := NUMTODSINTERVAL(v_duracion_min * 60, 'SECOND') + v_fecha_in;

            -- Estaciones de ingreso y salida
            v_est_in := v_estaciones(MOD(t * 3 + dia, v_estaciones.COUNT) + 1);
            v_est_out := v_estaciones(MOD(t * 5 + dia + 2, v_estaciones.COUNT) + 1);

            -- Tarifa y monto cobrado
            IF v_card.tarifa_id = 1 THEN
                v_monto := 2.90;
            ELSIF v_card.tarifa_id IN (2, 3) THEN
                v_monto := 1.45;
            ELSIF v_card.tarifa_id = 6 THEN
                v_monto := 0.00;
            ELSE
                v_monto := 2.90;
            END IF;

            SELECT SEQ_VIAJE_PASAJERO.NEXTVAL INTO v_viaje_id FROM DUAL;

            INSERT INTO VIAJE_PASAJERO (
                id_viaje_pasajero, numero_transaccion, tarjeta_id,
                estacion_ingreso_id, fecha_hora_ingreso,
                estacion_salida_id, fecha_hora_salida,
                tarifa_id, monto_cobrado, viaje_programado_id, estado_transaccion
            ) VALUES (
                v_viaje_id,
                'TXN-VP-SIM-' || TO_CHAR(v_fecha_in, 'YYYYMMDD') || '-' || LPAD(v_count, 5, '0'),
                v_card.id,
                v_est_in,
                v_fecha_in,
                v_est_out,
                v_fecha_out,
                v_card.tarifa_id,
                v_monto,
                NULL,
                'Cerrada'
            );
        END LOOP;
        EXIT WHEN v_count >= 2400;
    END LOOP;

    DBMS_OUTPUT.PUT_LINE('Se generaron ' || v_count || ' viajes de pasajeros en torniquetes exitosamente.');
END;
/

COMMIT;
PROMPT [FASE 3] Insercion de viajes de pasajeros finalizada exitosamente.

