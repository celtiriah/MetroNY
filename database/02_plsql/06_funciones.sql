-- ======================================================================
-- SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]
-- Capa de Programacion PL/SQL - 06_funciones.sql
-- 9 Funciones de Calculo de Negocio
-- ======================================================================

-- 1. Funcion: Duracion real o estimada de un viaje en minutos
CREATE OR REPLACE FUNCTION FN_DURACION_VIAJE(p_id_viaje IN NUMBER) 
RETURN NUMBER IS
    v_duracion NUMBER := 0;
    v_salida   TIMESTAMP;
    v_llegada  TIMESTAMP;
BEGIN
    SELECT hora_real_salida, hora_real_llegada
    INTO v_salida, v_llegada
    FROM VIAJE_PROGRAMADO
    WHERE id_viaje = p_id_viaje;

    IF v_salida IS NOT NULL AND v_llegada IS NOT NULL THEN
        v_duracion := ROUND((CAST(v_llegada AS DATE) - CAST(v_salida AS DATE)) * 24 * 60);
    ELSE
        -- Si no hay registro real, calcular con las horas programadas
        SELECT ROUND((CAST(hora_prog_llegada AS DATE) - CAST(hora_prog_salida AS DATE)) * 24 * 60)
        INTO v_duracion
        FROM VIAJE_PROGRAMADO
        WHERE id_viaje = p_id_viaje;
    END IF;

    RETURN NVL(v_duracion, 0);
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN 0;
    WHEN OTHERS THEN
        RETURN 0;
END FN_DURACION_VIAJE;
/

-- 2. Funcion: Minutos de retraso en la salida de un viaje
CREATE OR REPLACE FUNCTION FN_MINUTOS_RETRASO(p_id_viaje IN NUMBER) 
RETURN NUMBER IS
    v_retraso NUMBER := 0;
    v_prog    TIMESTAMP;
    v_real    TIMESTAMP;
BEGIN
    SELECT hora_prog_salida, hora_real_salida
    INTO v_prog, v_real
    FROM VIAJE_PROGRAMADO
    WHERE id_viaje = p_id_viaje;

    IF v_real IS NOT NULL AND v_real > v_prog THEN
        v_retraso := ROUND((CAST(v_real AS DATE) - CAST(v_prog AS DATE)) * 24 * 60);
    END IF;

    RETURN NVL(v_retraso, 0);
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN 0;
    WHEN OTHERS THEN
        RETURN 0;
END FN_MINUTOS_RETRASO;
/

-- 3. Funcion: Obtener saldo actual disponible de una tarjeta OMNY / MetroCard
CREATE OR REPLACE FUNCTION FN_SALDO_TARJETA(p_numero_tarjeta IN VARCHAR2) 
RETURN NUMBER IS
    v_saldo NUMBER(10,2) := 0;
BEGIN
    SELECT saldo_disponible
    INTO v_saldo
    FROM TARJETA
    WHERE numero_tarjeta = p_numero_tarjeta;

    RETURN NVL(v_saldo, 0);
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN -1;
    WHEN OTHERS THEN
        RETURN -1;
END FN_SALDO_TARJETA;
/

-- 4. Funcion: Determinar si una tarjeta es valida para ingresar al torniquete (retorna 1 o 0)
CREATE OR REPLACE FUNCTION FN_TARJETA_VALIDA(p_numero_tarjeta IN VARCHAR2) 
RETURN NUMBER IS
    v_estado VARCHAR2(30);
    v_vencimiento DATE;
    v_saldo NUMBER(10,2);
    v_tarifa_monto NUMBER(6,2);
BEGIN
    SELECT t.estado, t.fecha_vencimiento, t.saldo_disponible, tar.monto
    INTO v_estado, v_vencimiento, v_saldo, v_tarifa_monto
    FROM TARJETA t
    JOIN TARIFA tar ON t.tarifa_id = tar.id_tarifa
    WHERE t.numero_tarjeta = p_numero_tarjeta;

    -- Validaciones: activa, no vencida y con saldo suficiente
    IF v_estado = 'Activa' 
       AND v_vencimiento >= TRUNC(SYSDATE) 
       AND v_saldo >= v_tarifa_monto THEN
        RETURN 1;
    ELSE
        RETURN 0;
    END IF;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN 0;
    WHEN OTHERS THEN
        RETURN 0;
END FN_TARJETA_VALIDA;
/

-- 5. Funcion: Calcular ingresos totales de una estacion en una fecha dada
CREATE OR REPLACE FUNCTION FN_INGRESOS_ESTACION(p_id_estacion IN NUMBER, p_fecha IN DATE) 
RETURN NUMBER IS
    v_total NUMBER(12,2) := 0;
BEGIN
    SELECT NVL(SUM(monto_cobrado), 0)
    INTO v_total
    FROM VIAJE_PASAJERO
    WHERE estacion_ingreso_id = p_id_estacion
      AND TRUNC(CAST(fecha_hora_ingreso AS DATE)) = TRUNC(p_fecha);

    RETURN v_total;
EXCEPTION
    WHEN OTHERS THEN
        RETURN 0;
END FN_INGRESOS_ESTACION;
/

-- 6. Funcion: Obtener cantidad de pasajeros transportados por una linea en un periodo
CREATE OR REPLACE FUNCTION FN_PASAJEROS_LINEA(
    p_id_linea     IN NUMBER,
    p_fecha_inicio IN DATE,
    p_fecha_fin    IN DATE
) 
RETURN NUMBER IS
    v_total NUMBER := 0;
BEGIN
    SELECT COUNT(vp.id_viaje_pasajero)
    INTO v_total
    FROM VIAJE_PASAJERO vp
    JOIN VIAJE_PROGRAMADO vprog ON vp.viaje_programado_id = vprog.id_viaje
    JOIN RUTA r                ON vprog.ruta_id = r.id_ruta
    WHERE r.linea_id = p_id_linea
      AND TRUNC(CAST(vp.fecha_hora_ingreso AS DATE)) BETWEEN TRUNC(p_fecha_inicio) AND TRUNC(p_fecha_fin);

    RETURN v_total;
EXCEPTION
    WHEN OTHERS THEN
        RETURN 0;
END FN_PASAJEROS_LINEA;
/

-- 7. Funcion: Verificar si un tren esta disponible (retorna 1 o 0)
CREATE OR REPLACE FUNCTION FN_TREN_DISPONIBLE(p_id_tren IN NUMBER) 
RETURN NUMBER IS
    v_estado VARCHAR2(30);
    v_ordenes_abiertas NUMBER := 0;
BEGIN
    SELECT estado_operativo
    INTO v_estado
    FROM TREN
    WHERE id_tren = p_id_tren;

    IF v_estado != 'Disponible' THEN
        RETURN 0;
    END IF;

    -- Comprobar si tiene ordenes de mantenimiento activas
    SELECT COUNT(*)
    INTO v_ordenes_abiertas
    FROM EQUIPO eq
    JOIN ORDEN_MANTENIMIENTO om ON eq.id_equipo = om.equipo_id
    WHERE eq.tipo_referencia = 'TREN'
      AND eq.referencia_id = p_id_tren
      AND om.estado IN ('Solicitada', 'Programada', 'En Ejecución', 'En Ejecucion');

    IF v_ordenes_abiertas > 0 THEN
        RETURN 0;
    END IF;

    RETURN 1;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN 0;
    WHEN OTHERS THEN
        RETURN 0;
END FN_TREN_DISPONIBLE;
/

-- 8. Funcion: Determinar si una ruta se encuentra operativa (retorna 1 o 0)
CREATE OR REPLACE FUNCTION FN_RUTA_OPERATIVA(p_id_ruta IN NUMBER) 
RETURN NUMBER IS
    v_afectaciones NUMBER := 0;
BEGIN
    -- Comprobar si la ruta o sus estaciones tienen incidentes abiertos
    SELECT COUNT(*)
    INTO v_afectaciones
    FROM INCIDENTE_ELEMENTO_AFECTADO a
    JOIN INCIDENTE i ON a.incidente_id = i.id_incidente
    WHERE i.estado != 'Cerrado'
      AND (
          a.ruta_id = p_id_ruta
          OR a.estacion_id IN (SELECT estacion_id FROM RUTA_DETALLE WHERE ruta_id = p_id_ruta)
      );

    IF v_afectaciones > 0 THEN
        RETURN 0;
    ELSE
        RETURN 1;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RETURN 1;
END FN_RUTA_OPERATIVA;
/

-- 9. Funcion: Calcular el costo total de una orden de mantenimiento
CREATE OR REPLACE FUNCTION FN_COSTO_ORDEN_MANTENIMIENTO(p_id_orden IN NUMBER) 
RETURN NUMBER IS
    v_costo_base      NUMBER(12,2) := 0;
    v_costo_repuestos NUMBER(12,2) := 0;
BEGIN
    SELECT NVL(costo, 0)
    INTO v_costo_base
    FROM ORDEN_MANTENIMIENTO
    WHERE id_orden = p_id_orden;

    SELECT NVL(SUM(costo_total), 0)
    INTO v_costo_repuestos
    FROM ORDEN_REPUESTO
    WHERE orden_id = p_id_orden;

    RETURN v_costo_base + v_costo_repuestos;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN 0;
    WHEN OTHERS THEN
        RETURN 0;
END FN_COSTO_ORDEN_MANTENIMIENTO;
/

EXIT;
