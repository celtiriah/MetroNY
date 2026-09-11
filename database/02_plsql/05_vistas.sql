-- ======================================================================
-- SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]
-- Capa de Programacion PL/SQL - 05_vistas.sql
-- 9 Vistas Operativas y Analiticas de Monitoreo
-- ======================================================================

-- 1. Vista: Estado actual y caracteristicas operativas de las lineas
CREATE OR REPLACE VIEW VW_ESTADO_LINEAS AS
SELECT l.id_linea,
       l.codigo AS codigo_linea,
       l.nombre AS nombre_linea,
       l.color,
       l.tipo_servicio_principal,
       eo.nombre AS terminal_origen,
       ed.nombre AS terminal_destino,
       l.estado_operativo,
       l.longitud_km,
       l.operador_responsable,
       COUNT(DISTINCT le.estacion_id) AS total_estaciones,
       (SELECT COUNT(*) FROM INCIDENTE_ELEMENTO_AFECTADO a 
        JOIN INCIDENTE i ON a.incidente_id = i.id_incidente 
        WHERE a.linea_id = l.id_linea AND i.estado != 'Cerrado') AS incidentes_activos
FROM LINEA l
LEFT JOIN ESTACION eo ON l.estacion_origen_id = eo.id_estacion
LEFT JOIN ESTACION ed ON l.estacion_destino_id = ed.id_estacion
LEFT JOIN LINEA_ESTACION le ON l.id_linea = le.linea_id
GROUP BY l.id_linea, l.codigo, l.nombre, l.color, l.tipo_servicio_principal,
         eo.nombre, ed.nombre, l.estado_operativo, l.longitud_km, l.operador_responsable;

-- 2. Vista: Proximas salidas programadas ordenadas por estacion
CREATE OR REPLACE VIEW VW_PROXIMAS_SALIDAS_ESTACION AS
SELECT vp.id_viaje,
       vp.numero_viaje,
       r.codigo AS codigo_ruta,
       r.sentido,
       l.codigo AS codigo_linea,
       l.color  AS color_linea,
       e.nombre AS estacion,
       e.distrito,
       rd.orden_llegada AS secuencia_parada,
       TO_CHAR(vp.fecha, 'YYYY-MM-DD') AS fecha_viaje,
       TO_CHAR(vp.hora_prog_salida, 'HH24:MI') AS hora_prog_salida,
       t.codigo_interno AS tren_asignado,
       emp.nombre_completo AS conductor,
       vp.estado AS estado_viaje
FROM VIAJE_PROGRAMADO vp
JOIN RUTA r            ON vp.ruta_id = r.id_ruta
JOIN LINEA l           ON r.linea_id = l.id_linea
JOIN RUTA_DETALLE rd   ON r.id_ruta = rd.ruta_id
JOIN ESTACION e        ON rd.estacion_id = e.id_estacion
JOIN TREN t            ON vp.tren_id = t.id_tren
JOIN EMPLEADO emp      ON vp.conductor_id = emp.id_empleado
WHERE rd.se_detiene = 'S'
ORDER BY vp.fecha, vp.hora_prog_salida, rd.orden_llegada;

-- 3. Vista: Viajes que presentan retrasos respecto a la hora programada
CREATE OR REPLACE VIEW VW_VIAJES_RETRASADOS AS
SELECT vp.id_viaje,
       vp.numero_viaje,
       r.codigo AS codigo_ruta,
       l.codigo AS codigo_linea,
       l.color  AS color_linea,
       TO_CHAR(vp.fecha, 'YYYY-MM-DD') AS fecha,
       TO_CHAR(vp.hora_prog_salida, 'HH24:MI') AS hora_prog_salida,
       TO_CHAR(vp.hora_real_salida, 'HH24:MI') AS hora_real_salida,
       ROUND((CAST(vp.hora_real_salida AS DATE) - CAST(vp.hora_prog_salida AS DATE)) * 24 * 60) AS minutos_retraso,
       t.codigo_interno AS tren,
       emp.nombre_completo AS conductor,
       vp.estado AS estado_viaje
FROM VIAJE_PROGRAMADO vp
JOIN RUTA r       ON vp.ruta_id = r.id_ruta
JOIN LINEA l      ON r.linea_id = l.id_linea
JOIN TREN t       ON vp.tren_id = t.id_tren
JOIN EMPLEADO emp ON vp.conductor_id = emp.id_empleado
WHERE vp.hora_real_salida IS NOT NULL
  AND vp.hora_real_salida > vp.hora_prog_salida;

-- 4. Vista: Trenes disponibles aptos para asignacion operativa
CREATE OR REPLACE VIEW VW_TRENES_DISPONIBLES AS
SELECT t.id_tren,
       t.codigo_interno,
       m.nombre_modelo,
       m.fabricante,
       t.capacidad_total,
       NVL(d.nombre, 'Sin Deposito Asignado') AS deposito,
       t.kilometraje_acumulado,
       t.estado_operativo,
       TO_CHAR(t.fecha_ultima_inspeccion, 'YYYY-MM-DD') AS ultima_inspeccion,
       TO_CHAR(t.fecha_proxima_inspeccion, 'YYYY-MM-DD') AS proxima_inspeccion
FROM TREN t
JOIN MODELO_TREN m   ON t.modelo_id = m.id_modelo
LEFT JOIN DEPOSITO d ON t.deposito_id = d.id_deposito
WHERE t.estado_operativo = 'Disponible';

-- 5. Vista: Trenes en mantenimiento preventivo o correctivo
CREATE OR REPLACE VIEW VW_TRENES_MANTENIMIENTO AS
SELECT t.id_tren,
       t.codigo_interno AS codigo_tren,
       m.nombre_modelo,
       NVL(d.nombre, 'Sin Deposito') AS deposito,
       t.kilometraje_acumulado,
       om.numero_orden,
       om.tipo_mantenimiento,
       om.descripcion_trabaJo,
       om.prioridad,
       om.costo AS costo_orden,
       om.estado AS estado_orden,
       emp.nombre_completo AS tecnico_responsable,
       TO_CHAR(om.fecha_inicio, 'YYYY-MM-DD') AS fecha_ingreso_taller
FROM TREN t
JOIN MODELO_TREN m          ON t.modelo_id = m.id_modelo
LEFT JOIN DEPOSITO d        ON t.deposito_id = d.id_deposito
JOIN EQUIPO eq              ON eq.tipo_referencia = 'TREN' AND eq.referencia_id = t.id_tren
JOIN ORDEN_MANTENIMIENTO om ON eq.id_equipo = om.equipo_id
LEFT JOIN ORDEN_TECNICO ot  ON om.id_orden = ot.orden_id AND ot.rol_en_orden = 'Lider de Reparacion'
LEFT JOIN EMPLEADO emp      ON ot.empleado_id = emp.id_empleado
WHERE t.estado_operativo = 'En Mantenimiento'
   OR om.estado IN ('Solicitada', 'Programada', 'En Ejecucion');

-- 6. Vista: Incidentes activos no resueltos con elementos de red afectados
CREATE OR REPLACE VIEW VW_INCIDENTES_ABIERTOS AS
SELECT i.id_incidente,
       i.numero_incidente,
       i.tipo,
       i.nivel_severidad,
       TO_CHAR(i.fecha_hora_inicio, 'YYYY-MM-DD HH24:MI') AS fecha_hora_inicio,
       i.estado,
       i.descripcion,
       NVL(e.nombre, NVL(t.codigo_interno, NVL(r.codigo, NVL(lin.codigo, 'General de Red')))) AS elemento_afectado,
       a.tipo_elemento,
       a.tipo_afectacion,
       emp.nombre_completo AS reportado_por
FROM INCIDENTE i
LEFT JOIN INCIDENTE_ELEMENTO_AFECTADO a ON i.id_incidente = a.incidente_id
LEFT JOIN ESTACION e  ON a.estacion_id = e.id_estacion
LEFT JOIN TREN t      ON a.tren_id = t.id_tren
LEFT JOIN RUTA r      ON a.ruta_id = r.id_ruta
LEFT JOIN LINEA lin   ON a.linea_id = lin.id_linea
LEFT JOIN EMPLEADO emp ON i.reportado_por_id = emp.id_empleado
WHERE i.estado != 'Cerrado';

-- 7. Vista: Ingresos diarios consolidados por linea de metro
CREATE OR REPLACE VIEW VW_INGRESOS_DIARIOS_LINEA AS
SELECT TO_CHAR(CAST(vp.fecha_hora_ingreso AS DATE), 'YYYY-MM-DD') AS fecha,
       l.codigo AS codigo_linea,
       l.nombre AS nombre_linea,
       l.color  AS color_linea,
       COUNT(vp.id_viaje_pasajero) AS total_viajes_validados,
       SUM(vp.monto_cobrado)       AS total_recaudado
FROM VIAJE_PASAJERO vp
JOIN ESTACION e        ON vp.estacion_ingreso_id = e.id_estacion
JOIN LINEA_ESTACION le ON e.id_estacion = le.estacion_id
JOIN LINEA l           ON le.linea_id = l.id_linea
GROUP BY TO_CHAR(CAST(vp.fecha_hora_ingreso AS DATE), 'YYYY-MM-DD'),
         l.codigo, l.nombre, l.color;

-- 8. Vista: Estaciones con mayor flujo de pasajeros (torniquetes)
CREATE OR REPLACE VIEW VW_ESTACIONES_MAYOR_AFLUENCIA AS
SELECT e.id_estacion,
       e.codigo AS codigo_estacion,
       e.nombre AS nombre_estacion,
       e.distrito,
       COUNT(vp.id_viaje_pasajero) AS total_pasajeros_validados,
       NVL(SUM(vp.monto_cobrado), 0) AS total_ingresos_recaudados
FROM ESTACION e
LEFT JOIN VIAJE_PASAJERO vp ON e.id_estacion = vp.estacion_ingreso_id
GROUP BY e.id_estacion, e.codigo, e.nombre, e.distrito;

-- 9. Vista: Certificaciones de conductores proximas a vencer (en 30 dias)
CREATE OR REPLACE VIEW VW_CERTIFICACIONES_POR_VENCER AS
SELECT emp.id_empleado,
       emp.numero_empleado,
       emp.nombre_completo AS nombre_conductor,
       emp.cargo,
       c.tipo_certificacion,
       TO_CHAR(c.fecha_emision, 'YYYY-MM-DD') AS fecha_emision,
       TO_CHAR(c.fecha_vencimiento, 'YYYY-MM-DD') AS fecha_vencimiento,
       ROUND(CAST(c.fecha_vencimiento AS DATE) - SYSDATE) AS dias_restantes,
       c.estado AS estado_certificacion
FROM CERTIFICACION c
JOIN EMPLEADO emp ON c.empleado_id = emp.id_empleado
WHERE c.estado = 'Vigente'
  AND (CAST(c.fecha_vencimiento AS DATE) - SYSDATE) <= 30;

EXIT;
