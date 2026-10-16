-- ==============================================================================
-- PROYECTO: METRO NY - GESTION INTEGRAL DEL SUBWAY DE NUEVA YORK
-- ARCHIVO:  database/04_datos_simulacion_1anno/05_sim_turnos.sql
-- PROPOSITO: Generar 400 asignaciones de turnos laborales respetando jornadas
--            y previniendo solapamientos por empleado (TRG_TURNO_NO_SOLAPADO).
-- ==============================================================================

SET SERVEROUTPUT ON SIZE UNLIMITED;

PROMPT ==============================================================================
PROMPT [FASE 5] Generando 400 Turnos de Personal MTA (Simulacion Anual)...
PROMPT ==============================================================================

DECLARE
    TYPE t_emp_rec IS RECORD (
        id NUMBER,
        cargo VARCHAR2(100)
    );
    TYPE t_emp_list IS TABLE OF t_emp_rec;
    v_empleados t_emp_list := t_emp_list();

    v_turno_id NUMBER;
    v_emp t_emp_rec;
    v_fecha DATE;
    v_hora_in TIMESTAMP;
    v_hora_out TIMESTAMP;
    v_tipo_lugar VARCHAR2(30);
    v_lugar_id NUMBER;
    v_tipo_turno NUMBER;
    v_count NUMBER := 0;
BEGIN
    -- Cargar empleados activos con su cargo
    FOR r IN (
        SELECT id_empleado, cargo
        FROM EMPLEADO
        WHERE estado_laboral = 'Activo'
        ORDER BY id_empleado ASC
    ) LOOP
        v_empleados.EXTEND;
        v_empleados(v_empleados.COUNT).id := r.id_empleado;
        v_empleados(v_empleados.COUNT).cargo := r.cargo;
    END LOOP;

    IF v_empleados.COUNT = 0 THEN
        DBMS_OUTPUT.PUT_LINE('Error: No hay empleados activos en el sistema.');
        RETURN;
    END IF;

    -- Generar 400 turnos distribuidos en 360 dias asegurando maximo 1 turno por empleado al dia
    FOR dia IN REVERSE 1..360 LOOP
        v_fecha := TRUNC(SYSDATE) - dia;
        
        -- Asignar 1 o 2 empleados distintos en este dia
        FOR emp_idx IN 1..2 LOOP
            v_count := v_count + 1;
            EXIT WHEN v_count > 400;

            -- Rotar empleados garantizando que no se repitan el mismo dia
            v_emp := v_empleados(MOD((dia * 2 + emp_idx), v_empleados.COUNT) + 1);

            v_tipo_turno := MOD(dia + emp_idx, 2);
            IF v_tipo_turno = 0 THEN
                -- Turno Matutino: 06:00 a 14:00 (8 horas)
                v_hora_in := NUMTODSINTERVAL(6 * 3600, 'SECOND') + v_fecha;
                v_hora_out := NUMTODSINTERVAL(14 * 3600, 'SECOND') + v_fecha;
            ELSE
                -- Turno Vespertino: 14:00 a 22:00 (8 horas)
                v_hora_in := NUMTODSINTERVAL(14 * 3600, 'SECOND') + v_fecha;
                v_hora_out := NUMTODSINTERVAL(22 * 3600, 'SECOND') + v_fecha;
            END IF;

            -- Asignar lugar coherente con el cargo
            IF v_emp.cargo LIKE '%Control%' THEN
                v_tipo_lugar := 'Centro de Control';
                v_lugar_id := 1;
            ELSIF v_emp.cargo LIKE '%Supervisor%' OR v_emp.cargo LIKE '%Atención%' OR v_emp.cargo LIKE '%Atencion%' THEN
                v_tipo_lugar := 'Estación';
                v_lugar_id := 1 + MOD(dia, 12);
            ELSIF v_emp.cargo LIKE '%Conductor%' THEN
                v_tipo_lugar := 'Tren';
                v_lugar_id := 1 + MOD(dia, 5);
            ELSE
                v_tipo_lugar := 'Depósito';
                v_lugar_id := 1 + MOD(dia, 4);
            END IF;

            SELECT SEQ_TURNO.NEXTVAL INTO v_turno_id FROM DUAL;

            INSERT INTO TURNO (
                id_turno, codigo_turno, empleado_id, fecha,
                hora_inicio, hora_fin, tipo_lugar, lugar_id,
                funcion, estado_asistencia
            ) VALUES (
                v_turno_id,
                'TUR-SIM-' || LPAD(v_count, 4, '0'),
                v_emp.id,
                v_fecha,
                v_hora_in,
                v_hora_out,
                v_tipo_lugar,
                v_lugar_id,
                v_emp.cargo,
                'Presente'
            );
        END LOOP;
        EXIT WHEN v_count >= 400;
    END LOOP;

    DBMS_OUTPUT.PUT_LINE('Se generaron ' || v_count || ' turnos de personal exitosamente.');
END;
/

COMMIT;
PROMPT [FASE 5] Insercion de turnos de personal finalizada exitosamente.

