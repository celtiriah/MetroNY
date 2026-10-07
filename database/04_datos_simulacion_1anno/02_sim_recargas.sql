-- ==============================================================================
-- PROYECTO: METRO NY - GESTION INTEGRAL DEL SUBWAY DE NUEVA YORK
-- ARCHIVO:  database/04_datos_simulacion_1anno/02_sim_recargas.sql
-- PROPOSITO: Generar 900 transacciones de recarga financiera distribuidas en 1 ano.
-- ==============================================================================

SET SERVEROUTPUT ON SIZE UNLIMITED;

PROMPT ==============================================================================
PROMPT [FASE 2] Generando 900 Recargas de Saldo OMNY/MetroCard (Simulacion Anual)...
PROMPT ==============================================================================

DECLARE
    TYPE t_num_list IS TABLE OF NUMBER;
    TYPE t_str_list IS TABLE OF VARCHAR2(50);
    
    v_tarjetas t_num_list := t_num_list();
    v_montos t_num_list := t_num_list(5.80, 10.00, 20.00, 34.00, 50.00, 20.00, 10.00, 34.00);
    v_medios t_str_list := t_str_list('Efectivo', 'Tarjeta Débito', 'Tarjeta Crédito', 'App Móvil', 'Transferencia');
    v_canales t_str_list := t_str_list(
        'MVM-TSQ42 (Torniquete)', 'MVM-GCT42 (Mezzanine)', 'Taquilla Central 42nd St',
        'OMNY App Móvil', 'MVM-14USQ (Norte)', 'MVM-ATL (Terminal)', 'Portal Web OMNY',
        'MVM-FLTN (Fulton Center)'
    );

    v_rec_id NUMBER;
    v_tar_id NUMBER;
    v_dias_atras NUMBER;
    v_fecha TIMESTAMP;
    v_monto NUMBER(8,2);
    v_medio VARCHAR2(50);
    v_canal VARCHAR2(50);
    v_saldo_ant NUMBER(8,2);
    v_saldo_pos NUMBER(8,2);
    v_count NUMBER := 0;
BEGIN
    -- Cargar los IDs de las tarjetas simuladas
    SELECT id_tarjeta BULK COLLECT INTO v_tarjetas
    FROM TARJETA
    WHERE numero_tarjeta LIKE 'OMNY-SIM-%'
    ORDER BY id_tarjeta ASC;

    IF v_tarjetas.COUNT = 0 THEN
        DBMS_OUTPUT.PUT_LINE('Error: No se encontraron tarjetas con prefijo OMNY-SIM-. Ejecute Fase 1 primero.');
        RETURN;
    END IF;

    FOR i IN 1..900 LOOP
        -- Seleccionar tarjeta rotativamente
        v_tar_id := v_tarjetas(MOD(i, v_tarjetas.COUNT) + 1);
        
        -- Distribuir en los ultimos 360 dias
        v_dias_atras := 360 - TRUNC(i * 355 / 900);
        v_fecha := NUMTODSINTERVAL(MOD(i * 137, 86400), 'SECOND') + (TRUNC(SYSDATE) - v_dias_atras);

        v_monto := v_montos(MOD(i, v_montos.COUNT) + 1);
        v_medio := v_medios(MOD(i, v_medios.COUNT) + 1);
        v_canal := v_canales(MOD(i, v_canales.COUNT) + 1);

        v_saldo_ant := ROUND(MOD(i * 3.75, 22.50), 2);
        v_saldo_pos := v_saldo_ant + v_monto;

        SELECT SEQ_RECARGA.NEXTVAL INTO v_rec_id FROM DUAL;

        INSERT INTO RECARGA (
            id_recarga, numero_transaccion, tarjeta_id, fecha_hora,
            monto, medio_pago, estacion_canal, saldo_anterior, saldo_posterior
        ) VALUES (
            v_rec_id,
            'TXN-REC-SIM-' || TO_CHAR(v_fecha, 'YYYYMMDD') || '-' || LPAD(i, 4, '0'),
            v_tar_id,
            v_fecha,
            v_monto,
            v_medio,
            v_canal,
            v_saldo_ant,
            v_saldo_pos
        );
        v_count := v_count + 1;
    END LOOP;

    DBMS_OUTPUT.PUT_LINE('Se generaron ' || v_count || ' recargas financieras exitosamente.');
END;
/

COMMIT;
PROMPT [FASE 2] Insercion de recargas finalizada exitosamente.

