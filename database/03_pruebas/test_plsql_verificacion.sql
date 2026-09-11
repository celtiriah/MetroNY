-- ======================================================================
-- SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]
-- Script de Verificacion Funcional de la Capa PL/SQL
-- Archivo: database/03_pruebas/test_plsql_verificacion.sql
-- ======================================================================

SET ECHO OFF
SET FEEDBACK ON
SET LINESIZE 160
SET PAGESIZE 50
SET SERVEROUTPUT ON

PROMPT ======================================================================
PROMPT 1. PRUEBA DE VISTAS ANALITICAS (VW_*)
PROMPT ======================================================================

PROMPT [1.1] VW_ESTADO_LINEAS:
SELECT codigo_linea, nombre_linea, color, total_estaciones, incidentes_activos 
FROM VW_ESTADO_LINEAS 
WHERE ROWNUM <= 4;

PROMPT [1.2] VW_TRENES_DISPONIBLES:
SELECT codigo_interno, nombre_modelo, fabricante, deposito, estado_operativo 
FROM VW_TRENES_DISPONIBLES 
WHERE ROWNUM <= 3;

PROMPT ======================================================================
PROMPT 2. PRUEBA DE FUNCIONES DE NEGOCIO (FN_*)
PROMPT ======================================================================

PROMPT [2.1] FN_SALDO_TARJETA y FN_TARJETA_VALIDA:
SELECT numero_tarjeta, saldo_disponible, 
       FN_SALDO_TARJETA(numero_tarjeta) AS saldo_fn, 
       FN_TARJETA_VALIDA(numero_tarjeta) AS es_valida 
FROM TARJETA 
WHERE ROWNUM <= 3;

PROMPT [2.2] FN_TREN_DISPONIBLE:
SELECT id_tren, codigo_interno, estado_operativo, 
       FN_TREN_DISPONIBLE(id_tren) AS disponible_fn 
FROM TREN 
WHERE ROWNUM <= 3;

PROMPT ======================================================================
PROMPT 3. PRUEBA DE PROCEDIMIENTOS ALMACENADOS (SP_*)
PROMPT ======================================================================

PROMPT [3.1] SP_RECARGAR_TARJETA (Recargando .00 a OMNY-1001-0001):
VARIABLE v_saldo NUMBER;
VARIABLE v_tx VARCHAR2(30);
EXEC SP_RECARGAR_TARJETA('OMNY-1001-0001', 15.00, 'Efectivo', 'Torniquete Central', :v_saldo, :v_tx);
PRINT v_saldo;
PRINT v_tx;

PROMPT [3.2] SP_REGISTRAR_INGRESO (Validando paso en torniquete estacion 1):
VARIABLE v_res VARCHAR2(30);
VARIABLE v_msg VARCHAR2(200);
VARIABLE v_cobrado NUMBER;
VARIABLE v_nuevo_saldo NUMBER;
EXEC SP_REGISTRAR_INGRESO('OMNY-1001-0001', 1, NULL, :v_res, :v_msg, :v_cobrado, :v_nuevo_saldo);
PRINT v_res;
PRINT v_msg;

PROMPT ======================================================================
PROMPT 4. PRUEBA DE TRIGGERS (TRG_*)
PROMPT ======================================================================

PROMPT [4.1] TRG_TARJETA_SALDO_NO_NEGATIVO (Debe rechazar saldo < 0):
BEGIN
    UPDATE TARJETA SET saldo_disponible = -10.00 WHERE numero_tarjeta = 'OMNY-1001-0001';
    DBMS_OUTPUT.PUT_LINE('ERROR: El trigger debio lanzar excepcion.');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('EXITO: Trigger bloqueo saldo negativo -> ' || SQLERRM);
END;
/

PROMPT [4.2] TRG_TREN_CAMBIO_ESTADO y BITACORA de Auditoria:
UPDATE TREN SET estado_operativo = 'En Mantenimiento' WHERE id_tren = 1;
SELECT id_bitacora, tabla_afectada, operacion, usuario, descripcion 
FROM BITACORA 
WHERE tabla_afectada = 'TREN' AND ROWNUM <= 1 
ORDER BY id_bitacora DESC;

PROMPT ======================================================================
PROMPT FIN DE PRUEBAS - Revirtiendo transacciones de prueba (ROLLBACK)
PROMPT ======================================================================
ROLLBACK;
EXIT;
