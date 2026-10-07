-- ==============================================================================
-- PROYECTO: METRO NY - GESTION INTEGRAL DEL SUBWAY DE NUEVA YORK
-- ARCHIVO:  database/04_datos_simulacion_1anno/revertir_simulacion_1anno.sql
-- PROPOSITO: Revertir completamente (Rollback) todas las inserciones de simulacion,
--            restaurando el estado exacto original de la base de datos sin afectar
--            los datos base y resincronizando las 33 secuencias de Oracle.
-- ==============================================================================

SET SERVEROUTPUT ON SIZE UNLIMITED;

PROMPT ==============================================================================
PROMPT [REVERSION] Iniciando reversor total de datos de simulacion anual (SIM)...
PROMPT ==============================================================================

-- 1. Desactivar temporalmente los triggers que bloquean eliminacion fisica por auditoria
PROMPT [1/5] Desactivando temporalmente triggers de auditoria restrictivos...
ALTER TRIGGER TRG_VIAJE_PASAJERO_AUDITORIA DISABLE;
ALTER TRIGGER TRG_RECARGA_PREVENIR_DELETE DISABLE;
ALTER TRIGGER TRG_ORDEN_MANT_HISTORICO DISABLE;
ALTER TRIGGER TRG_ORDEN_TECNICO_VALIDAR DISABLE;
ALTER TRIGGER TRG_CONSUMO_REPUESTO_STOCK DISABLE;
ALTER TRIGGER TRG_INCIDENTE_RETENCION_HISTORICA DISABLE;

-- 2. Eliminacion en cascada inversa de registros con tag SIM
PROMPT [2/5] Purgando registros simulados en orden inverso de dependencias...
DECLARE
    v_c_vp NUMBER := 0;
    v_c_rec NUMBER := 0;
    v_c_tar NUMBER := 0;
    v_c_pas NUMBER := 0;
    v_c_vpr NUMBER := 0;
    v_c_tur NUMBER := 0;
    v_c_orep NUMBER := 0;
    v_c_otec NUMBER := 0;
    v_c_oman NUMBER := 0;
    v_c_ielem NUMBER := 0;
    v_c_inc NUMBER := 0;
    v_c_bit NUMBER := 0;
BEGIN
    DELETE FROM VIAJE_PASAJERO WHERE numero_transaccion LIKE 'TXN-VP-SIM-%';
    v_c_vp := SQL%ROWCOUNT;

    DELETE FROM RECARGA WHERE numero_transaccion LIKE 'TXN-REC-SIM-%';
    v_c_rec := SQL%ROWCOUNT;

    DELETE FROM TARJETA WHERE numero_tarjeta LIKE 'OMNY-SIM-%';
    v_c_tar := SQL%ROWCOUNT;

    DELETE FROM PASAJERO WHERE identificador LIKE 'PAS-SIM-%';
    v_c_pas := SQL%ROWCOUNT;

    DELETE FROM VIAJE_PROGRAMADO WHERE numero_viaje LIKE 'VP-SIM-%';
    v_c_vpr := SQL%ROWCOUNT;

    DELETE FROM TURNO WHERE codigo_turno LIKE 'TUR-SIM-%';
    v_c_tur := SQL%ROWCOUNT;

    DELETE FROM ORDEN_REPUESTO WHERE orden_id IN (SELECT id_orden FROM ORDEN_MANTENIMIENTO WHERE numero_orden LIKE 'OT-SIM-%');
    v_c_orep := SQL%ROWCOUNT;

    DELETE FROM ORDEN_TECNICO WHERE orden_id IN (SELECT id_orden FROM ORDEN_MANTENIMIENTO WHERE numero_orden LIKE 'OT-SIM-%');
    v_c_otec := SQL%ROWCOUNT;

    DELETE FROM ORDEN_MANTENIMIENTO WHERE numero_orden LIKE 'OT-SIM-%';
    v_c_oman := SQL%ROWCOUNT;

    DELETE FROM INCIDENTE_ELEMENTO_AFECTADO WHERE incidente_id IN (SELECT id_incidente FROM INCIDENTE WHERE numero_incidente LIKE 'INC-SIM-%');
    v_c_ielem := SQL%ROWCOUNT;

    DELETE FROM INCIDENTE WHERE numero_incidente LIKE 'INC-SIM-%';
    v_c_inc := SQL%ROWCOUNT;

    DELETE FROM BITACORA WHERE descripcion LIKE '%[SIMULACION]%';
    v_c_bit := SQL%ROWCOUNT;

    DBMS_OUTPUT.PUT_LINE('--- REGISTROS PURGADOS ---');
    DBMS_OUTPUT.PUT_LINE('• VIAJE_PASAJERO:               ' || v_c_vp);
    DBMS_OUTPUT.PUT_LINE('• RECARGA:                      ' || v_c_rec);
    DBMS_OUTPUT.PUT_LINE('• TARJETA:                      ' || v_c_tar);
    DBMS_OUTPUT.PUT_LINE('• PASAJERO:                     ' || v_c_pas);
    DBMS_OUTPUT.PUT_LINE('• VIAJE_PROGRAMADO:             ' || v_c_vpr);
    DBMS_OUTPUT.PUT_LINE('• TURNO:                        ' || v_c_tur);
    DBMS_OUTPUT.PUT_LINE('• ORDEN_REPUESTO:               ' || v_c_orep);
    DBMS_OUTPUT.PUT_LINE('• ORDEN_TECNICO:                ' || v_c_otec);
    DBMS_OUTPUT.PUT_LINE('• ORDEN_MANTENIMIENTO:          ' || v_c_oman);
    DBMS_OUTPUT.PUT_LINE('• INCIDENTE_ELEMENTO_AFECTADO:  ' || v_c_ielem);
    DBMS_OUTPUT.PUT_LINE('• INCIDENTE:                    ' || v_c_inc);
    DBMS_OUTPUT.PUT_LINE('• BITACORA:                     ' || v_c_bit);
    DBMS_OUTPUT.PUT_LINE('Total registros eliminados:     ' || (v_c_vp + v_c_rec + v_c_tar + v_c_pas + v_c_vpr + v_c_tur + v_c_orep + v_c_otec + v_c_oman + v_c_ielem + v_c_inc + v_c_bit));
END;
/

-- 3. Restaurar stock base de repuestos (50 unidades originales)
PROMPT [3/5] Restaurando stock base de inventario de repuestos...
UPDATE REPUESTO
SET stock_disponible = 50;

-- 4. Reactivar los triggers de auditoria
PROMPT [4/5] Reactivando triggers de auditoria...
ALTER TRIGGER TRG_VIAJE_PASAJERO_AUDITORIA ENABLE;
ALTER TRIGGER TRG_RECARGA_PREVENIR_DELETE ENABLE;
ALTER TRIGGER TRG_ORDEN_MANT_HISTORICO ENABLE;
ALTER TRIGGER TRG_ORDEN_TECNICO_VALIDAR ENABLE;
ALTER TRIGGER TRG_CONSUMO_REPUESTO_STOCK ENABLE;
ALTER TRIGGER TRG_INCIDENTE_RETENCION_HISTORICA ENABLE;

-- 5. Resincronizar todas las secuencias al maximo de los datos base remanentes
PROMPT [5/5] Re-sincronizando todas las secuencias al estado previo...
BEGIN
    SP_SINCRONIZAR_TODAS_SECUENCIAS;
END;
/

COMMIT;

PROMPT ==============================================================================
PROMPT [REVERSION] Base de datos revertida exitosamente al estado base original.
PROMPT ==============================================================================

