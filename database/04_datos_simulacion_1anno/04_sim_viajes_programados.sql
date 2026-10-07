-- ==============================================================================
-- PROYECTO: METRO NY - GESTION INTEGRAL DEL SUBWAY DE NUEVA YORK
-- ARCHIVO:  database/04_datos_simulacion_1anno/04_sim_viajes_programados.sql
-- PROPOSITO: Generar 800 despachos de trenes en rutas activas a lo largo de 360 dias.
-- ==============================================================================

SET SERVEROUTPUT ON SIZE UNLIMITED;

PROMPT ==============================================================================
PROMPT [FASE 4] Generando 800 Despachos de Trenes en Rutas (Simulacion Anual)...
PROMPT ==============================================================================

DECLARE
    TYPE t_num_list IS TABLE OF NUMBER;
    v_rutas t_num_list := t_num_list();
    v_trenes t_num_list := t_num_list();

    v_viaje_id NUMBER;
    v_ruta_id NUMBER;
    v_tren_id NUMBER;
    v_cond_id NUMBER;
    v_fecha DATE;
    v_prog_sal TIMESTAMP;
    v_prog_lleg TIMESTAMP;
    v_real_sal TIMESTAMP;
    v_real_lleg TIMESTAMP;
    v_estado VARCHAR2(30);
    v_pasajeros NUMBER;
    v_hora NUMBER;
    v_min NUMBER;
    v_retraso_min NUMBER;
    v_count NUMBER := 0;
    v_trips_today NUMBER;
BEGIN
    -- Cargar rutas activas
    SELECT id_ruta BULK COLLECT INTO v_rutas
    FROM RUTA
    WHERE estado = 'Activa'
    ORDER BY id_ruta ASC;

    -- Cargar trenes operativos
    SELECT id_tren BULK COLLECT INTO v_trenes
    FROM TREN
    WHERE estado_operativo IN ('Disponible', 'En Operación', 'En Operacion')
    ORDER BY id_tren ASC;

    IF v_rutas.COUNT = 0 OR v_trenes.COUNT = 0 THEN
        DBMS_OUTPUT.PUT_LINE('Error: Faltan rutas o trenes activos en el sistema.');
        RETURN;
    END IF;

    -- Distribuir ~800 viajes a lo largo de 360 dias (2 a 3 por dia)
    FOR dia IN REVERSE 1..360 LOOP
        v_fecha := TRUNC(SYSDATE) - dia;
        v_trips_today := 2 + MOD(dia, 2); -- 2 o 3 viajes por dia

        FOR t IN 1..v_trips_today LOOP
            v_count := v_count + 1;
            EXIT WHEN v_count > 800;

            v_ruta_id := v_rutas(MOD(v_count, v_rutas.COUNT) + 1);
            v_tren_id := v_trenes(MOD(v_count, v_trenes.COUNT) + 1);

            -- Asignar conductor con certificacion tecnica vigente para la fecha del viaje
            -- Empleado 4 (vigente hasta 2027) y Empleado 5 (vigente hasta mayo 2026)
            IF v_fecha <= TO_DATE('2026-05-14', 'YYYY-MM-DD') AND MOD(v_count, 2) = 0 THEN
                v_cond_id := 5;
            ELSE
                v_cond_id := 4;
            END IF;

            -- Horas de salida
            v_hora := 6 + MOD(t * 5 + dia, 16);
            v_min := MOD(t * 17 + dia * 3, 50);

            v_prog_sal := NUMTODSINTERVAL(v_hora * 3600 + v_min * 60, 'SECOND') + v_fecha;
            v_prog_lleg := NUMTODSINTERVAL(45 * 60, 'SECOND') + v_prog_sal; -- 45 min duracion

            -- Estados realistas: 94% Completado, 4% Retrasado, 2% Cancelado
            IF MOD(v_count, 50) = 0 THEN
                v_estado := 'Cancelado';
                v_real_sal := NULL;
                v_real_lleg := NULL;
                v_pasajeros := 0;
            ELSIF MOD(v_count, 25) = 0 THEN
                v_estado := 'Retrasado';
                v_retraso_min := 15 + MOD(v_count, 20);
                v_real_sal := NUMTODSINTERVAL(v_retraso_min * 60, 'SECOND') + v_prog_sal;
                v_real_lleg := NUMTODSINTERVAL((45 + v_retraso_min + 5) * 60, 'SECOND') + v_prog_sal;
                v_pasajeros := 650 + MOD(v_count * 11, 400);
            ELSE
                v_estado := 'Completado';
                v_real_sal := NUMTODSINTERVAL(MOD(v_count, 3) * 60, 'SECOND') + v_prog_sal;
                v_real_lleg := NUMTODSINTERVAL((45 + MOD(v_count, 4)) * 60, 'SECOND') + v_prog_sal;
                v_pasajeros := 700 + MOD(v_count * 13, 500);
            END IF;

            SELECT SEQ_VIAJE_PROGRAMADO.NEXTVAL INTO v_viaje_id FROM DUAL;

            INSERT INTO VIAJE_PROGRAMADO (
                id_viaje, numero_viaje, ruta_id, horario_id, fecha,
                hora_prog_salida, hora_real_salida, hora_prog_llegada, hora_real_llegada,
                tren_id, conductor_id, estado, cantidad_estimada_pasajeros
            ) VALUES (
                v_viaje_id,
                'VP-SIM-' || TO_CHAR(v_fecha, 'YYYYMMDD') || '-' || LPAD(v_count, 4, '0'),
                v_ruta_id,
                NULL,
                v_fecha,
                v_prog_sal,
                v_real_sal,
                v_prog_lleg,
                v_real_lleg,
                v_tren_id,
                v_cond_id,
                v_estado,
                v_pasajeros
            );
        END LOOP;
        EXIT WHEN v_count >= 800;
    END LOOP;

    DBMS_OUTPUT.PUT_LINE('Se generaron ' || v_count || ' viajes programados de trenes exitosamente.');
END;
/

COMMIT;
PROMPT [FASE 4] Insercion de viajes programados finalizada exitosamente.

