-- ==============================================================================
-- PROYECTO: METRO NY - GESTION INTEGRAL DEL SUBWAY DE NUEVA YORK
-- ARCHIVO:  database/04_datos_simulacion_1anno/01_sim_pasajeros_tarjetas.sql
-- PROPOSITO: Generar 50 pasajeros frecuentes y 60 tarjetas OMNY/MetroCard
--            con vigencia a lo largo de un ano de operacion.
-- ==============================================================================

SET SERVEROUTPUT ON SIZE UNLIMITED;

PROMPT ==============================================================================
PROMPT [FASE 1] Generando 50 Pasajeros y 60 Tarjetas OMNY/MetroCard (Simulacion Anual)...
PROMPT ==============================================================================

DECLARE
    TYPE t_str_array IS TABLE OF VARCHAR2(50);
    v_nombres t_str_array := t_str_array(
        'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
        'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
        'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Lisa',
        'Matthew', 'Betty', 'Anthony', 'Margaret', 'Donald', 'Sandra', 'Mark', 'Ashley',
        'Paul', 'Kimberly', 'Steven', 'Emily', 'Andrew', 'Donna', 'Kenneth', 'Michelle',
        'Joshua', 'Dorothy', 'Kevin', 'Carol', 'Brian', 'Amanda', 'George', 'Melissa',
        'Edward', 'Deborah'
    );
    v_apellidos t_str_array := t_str_array(
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
        'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas',
        'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White',
        'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young',
        'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores',
        'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell',
        'Carter', 'Roberts'
    );

    v_pas_id NUMBER;
    v_tar_id NUMBER;
    v_tipo_pas VARCHAR2(30);
    v_tarifa_id NUMBER;
    v_fecha_reg DATE;
    v_fecha_emision DATE;
    v_fecha_nac DATE;
    v_saldo NUMBER(8,2);
    v_pas_ids t_str_array := t_str_array();
    v_pas_tipos t_str_array := t_str_array();
    v_count_pas NUMBER := 0;
    v_count_tar NUMBER := 0;
BEGIN
    v_pas_ids.EXTEND(50);
    v_pas_tipos.EXTEND(50);

    -- 1. Insertar 50 Pasajeros Frecuentes
    FOR i IN 1..50 LOOP
        IF i <= 35 THEN
            v_tipo_pas := 'Regular';
            v_tarifa_id := 1;
        ELSIF i <= 42 THEN
            v_tipo_pas := 'Estudiante';
            v_tarifa_id := 6;
        ELSIF i <= 47 THEN
            v_tipo_pas := 'Adulto Mayor';
            v_tarifa_id := 2;
        ELSE
            v_tipo_pas := 'Persona con Discapacidad';
            v_tarifa_id := 3;
        END IF;

        v_fecha_reg := TRUNC(SYSDATE) - (365 - MOD(i * 7, 330));
        v_fecha_nac := TO_DATE('1970-01-01', 'YYYY-MM-DD') + (MOD(i * 180, 11000) - 5000);

        SELECT SEQ_PASAJERO.NEXTVAL INTO v_pas_id FROM DUAL;
        v_pas_ids(i) := TO_CHAR(v_pas_id);
        v_pas_tipos(i) := v_tipo_pas;

        INSERT INTO PASAJERO (
            id_pasajero, identificador, nombre, fecha_nacimiento,
            correo_electronico, telefono, tipo_pasajero, fecha_registro, estado
        ) VALUES (
            v_pas_id,
            'PAS-SIM-' || LPAD(i, 3, '0'),
            v_nombres(i) || ' ' || v_apellidos(i),
            v_fecha_nac,
            LOWER(v_nombres(i)) || '.' || LOWER(v_apellidos(i)) || '.sim' || i || '@metrony.org',
            '+1-212-555-' || LPAD(1000 + i * 17, 4, '0'),
            v_tipo_pas,
            v_fecha_reg,
            'Activo'
        );
        v_count_pas := v_count_pas + 1;
    END LOOP;

    -- 2. Insertar 60 Tarjetas OMNY / MetroCard
    FOR i IN 1..60 LOOP
        v_fecha_emision := TRUNC(SYSDATE) - (350 - MOD(i * 5, 320));
        v_saldo := ROUND(15.00 + MOD(i * 7.50, 65.00), 2);

        IF i <= 50 THEN
            v_pas_id := TO_NUMBER(v_pas_ids(i));
            IF v_pas_tipos(i) = 'Regular' THEN
                v_tarifa_id := 1;
            ELSIF v_pas_tipos(i) = 'Adulto Mayor' THEN
                v_tarifa_id := 2;
            ELSIF v_pas_tipos(i) = 'Persona con Discapacidad' THEN
                v_tarifa_id := 3;
            ELSIF v_pas_tipos(i) = 'Estudiante' THEN
                v_tarifa_id := 6;
            ELSE
                v_tarifa_id := 1;
            END IF;
        ELSE
            -- Tarjetas anónimas prepagadas de estación
            v_pas_id := NULL;
            v_tarifa_id := 1;
        END IF;

        SELECT SEQ_TARJETA.NEXTVAL INTO v_tar_id FROM DUAL;

        INSERT INTO TARJETA (
            id_tarjeta, numero_tarjeta, pasajero_id, fecha_emision,
            fecha_vencimiento, saldo_disponible, tarifa_id, estado,
            uid_nfc, tipo_soporte, pase_fecha_inicio, pase_fecha_fin
        ) VALUES (
            v_tar_id,
            'OMNY-SIM-' || LPAD(i, 4, '0'),
            v_pas_id,
            v_fecha_emision,
            v_fecha_emision + 1825,
            v_saldo,
            v_tarifa_id,
            'Activa',
            'UID-SIM-' || LPAD(i, 4, '0'),
            'Tarjeta',
            NULL,
            NULL
        );
        v_count_tar := v_count_tar + 1;
    END LOOP;

    DBMS_OUTPUT.PUT_LINE('Se generaron ' || v_count_pas || ' pasajeros y ' || v_count_tar || ' tarjetas exitosamente.');
END;
/

COMMIT;
PROMPT [FASE 1] Insercion de pasajeros y tarjetas finalizada exitosamente.

