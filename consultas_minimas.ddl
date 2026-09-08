--------------------------------------------------------------------------------
-- Sistema de Gestión del Metro de Nueva York (MTA NYCT)
-- Archivo: consultas_minimas.ddl
-- Propósito: Las 15 Consultas Mínimas Obligatorias del Proyecto
--
-- Modo de Ejecución:
--   1. En VS Code (Oracle Extension):
--      Ubica el cursor sobre cualquier consulta y presiona Ctrl + Enter.
--      Los encabezados de las columnas aparecerán automáticamente en la cuadrícula.
--   2. En SQL*Plus:
--      sqlplus METRO_NY/MetroPass123@localhost:1521/FREEPDB1 @consultas_minimas.ddl
--------------------------------------------------------------------------------

SET ECHO OFF;
SET FEEDBACK ON;
SET LINESIZE 180;
SET PAGESIZE 60;
SET TRIMSPOOL ON;

PROMPT ==============================================================================
PROMPT  SISTEMA DE GESTIÓN DEL METRO DE NUEVA YORK (MTA NYCT)
PROMPT  EJECUCIÓN DE LAS 15 CONSULTAS MÍNIMAS DEL ENUNCIADO
PROMPT ==============================================================================


--------------------------------------------------------------------------------
-- CONSULTA 1: ¿Qué líneas pasan por una estación determinada?
-- Relación N:M entre Línea y Estación resuelta mediante LINEA_ESTACION.
--------------------------------------------------------------------------------
PROMPT 
PROMPT ------------------------------------------------------------------------------
PROMPT 1/15. ¿Qué líneas pasan por una estación determinada? (Ej: Times Sq - 42 St)
PROMPT ------------------------------------------------------------------------------

SELECT e.nombre AS "Estación",
       l.codigo AS "Línea",
       l.nombre AS "Nombre Oficial de Línea",
       l.color  AS "Color Dist.",
       le.orden AS "Orden"
FROM ESTACION e
JOIN LINEA_ESTACION le ON e.id_estacion = le.estacion_id
JOIN LINEA l           ON le.linea_id = l.id_linea
WHERE e.codigo = 'TSQ42'
ORDER BY le.orden;


--------------------------------------------------------------------------------
-- CONSULTA 2: ¿Cuáles son las estaciones de una ruta y en qué orden se visitan?
-- Secuencia física de paradas de una ruta (orden_llegada) y tipo de detención.
--------------------------------------------------------------------------------
PROMPT 
PROMPT ------------------------------------------------------------------------------
PROMPT 2/15. ¿Cuáles son las estaciones de una ruta y en qué orden se visitan?
PROMPT       (Ej: Ruta Local Línea 1 hacia el Sur: RUT-1-SB)
PROMPT ------------------------------------------------------------------------------

SELECT r.codigo         AS "Código Ruta",
       r.sentido        AS "Sentido de Viaje",
       rd.orden_llegada AS "Sec.",
       e.nombre         AS "Estación en Ruta",
       CASE rd.se_detiene WHEN 'S' THEN 'Sí (Parada)' ELSE 'Pasa Expreso' END AS "¿Se Detiene?"
FROM RUTA r
JOIN RUTA_DETALLE rd ON r.id_ruta = rd.ruta_id
JOIN ESTACION e      ON rd.estacion_id = e.id_estacion
WHERE r.codigo = 'RUT-1-SB'
ORDER BY rd.orden_llegada;


--------------------------------------------------------------------------------
-- CONSULTA 3: ¿Qué estaciones permiten transferencia entre líneas?
-- Identifica conexiones peatonales y tiempos de transferencia intramodal.
--------------------------------------------------------------------------------
PROMPT 
PROMPT ------------------------------------------------------------------------------
PROMPT 3/15. ¿Qué estaciones permiten transferencia entre líneas?
PROMPT ------------------------------------------------------------------------------

SELECT e.nombre AS "Estación de Conexión",
       e.distrito AS "Distrito",
       lo.codigo || ' (' || lo.color || ')' AS "Línea Origen",
       ld.codigo || ' (' || ld.color || ')' AS "Línea Destino",
       t.tiempo_estimado_min AS "Min. Caminata"
FROM TRANSFERENCIA t
JOIN ESTACION e  ON t.estacion_id = e.id_estacion
JOIN LINEA lo    ON t.linea_origen_id = lo.id_linea
JOIN LINEA ld    ON t.linea_destino_id = ld.id_linea
ORDER BY e.nombre, t.tiempo_estimado_min;


--------------------------------------------------------------------------------
-- CONSULTA 4: ¿Qué viajes están programados para una fecha?
-- Muestra la asignación operativa de tren físico y conductor para una fecha.
--------------------------------------------------------------------------------
PROMPT 
PROMPT ------------------------------------------------------------------------------
PROMPT 4/15. ¿Qué viajes están programados para una fecha? (Ej: 2026-09-01)
PROMPT ------------------------------------------------------------------------------

SELECT vp.numero_viaje AS "Número Viaje",
       r.codigo        AS "Ruta",
       TO_CHAR(vp.hora_prog_salida, 'HH24:MI') AS "Hora Prog.",
       t.codigo_interno AS "Tren",
       e.nombre_completo AS "Conductor Asignado",
       vp.estado       AS "Estado"
FROM VIAJE_PROGRAMADO vp
JOIN RUTA r     ON vp.ruta_id = r.id_ruta
JOIN TREN t     ON vp.tren_id = t.id_tren
JOIN EMPLEADO e ON vp.conductor_id = e.id_empleado
WHERE vp.fecha = TO_DATE('2026-09-01', 'YYYY-MM-DD')
ORDER BY vp.hora_prog_salida;


--------------------------------------------------------------------------------
-- CONSULTA 5: ¿Qué viajes presentan retrasos mayores a 15 minutos?
-- Aritmética de fechas en Oracle: (salida_real - salida_prog) * 1440 minutos.
--------------------------------------------------------------------------------
PROMPT 
PROMPT ------------------------------------------------------------------------------
PROMPT 5/15. ¿Qué viajes presentan retrasos mayores a 15 minutos?
PROMPT ------------------------------------------------------------------------------

SELECT vp.numero_viaje  AS "Número Viaje",
       r.codigo         AS "Ruta Afectada",
       TO_CHAR(vp.hora_prog_salida, 'HH24:MI') AS "Salida Prog.",
       TO_CHAR(vp.hora_real_salida, 'HH24:MI') AS "Salida Real",
       ROUND((CAST(vp.hora_real_salida AS DATE) - CAST(vp.hora_prog_salida AS DATE)) * 24 * 60) AS "Min. Retraso",
       vp.estado        AS "Estado"
FROM VIAJE_PROGRAMADO vp
JOIN RUTA r ON vp.ruta_id = r.id_ruta
WHERE vp.hora_real_salida IS NOT NULL
  AND (CAST(vp.hora_real_salida AS DATE) - CAST(vp.hora_prog_salida AS DATE)) * 24 * 60 > 15
ORDER BY "Min. Retraso" DESC;


--------------------------------------------------------------------------------
-- CONSULTA 6: ¿Qué trenes están disponibles?
-- Lista el material rodante con estado operativo 'Disponible'.
--------------------------------------------------------------------------------
PROMPT 
PROMPT ------------------------------------------------------------------------------
PROMPT 6/15. ¿Qué trenes están disponibles para operar en el sistema?
PROMPT ------------------------------------------------------------------------------

SELECT t.codigo_interno  AS "Código",
       m.nombre_modelo   AS "Modelo",
       m.fabricante      AS "Fabricante",
       NVL(d.nombre, 'Sin Depósito') AS "Depósito Base",
       t.estado_operativo AS "Estado"
FROM TREN t
JOIN MODELO_TREN m  ON t.modelo_id = m.id_modelo
LEFT JOIN DEPOSITO d ON t.deposito_id = d.id_deposito
WHERE t.estado_operativo = 'Disponible'
ORDER BY t.codigo_interno;


--------------------------------------------------------------------------------
-- CONSULTA 7: ¿Qué trenes tienen mantenimiento vencido?
-- Evalúa si la fecha de próxima inspección es menor a SYSDATE o si está en taller.
--------------------------------------------------------------------------------
PROMPT 
PROMPT ------------------------------------------------------------------------------
PROMPT 7/15. ¿Qué trenes tienen inspección preventiva vencida o están en taller?
PROMPT ------------------------------------------------------------------------------

SELECT t.codigo_interno  AS "Tren",
       m.nombre_modelo   AS "Modelo",
       t.kilometraje_acumulado AS "Kilometraje",
       TO_CHAR(t.fecha_ultima_inspeccion, 'YYYY-MM-DD') AS "Última Insp.",
       TO_CHAR(t.fecha_proxima_inspeccion, 'YYYY-MM-DD') AS "Próxima Insp.",
       CASE 
           WHEN t.estado_operativo = 'En Mantenimiento' THEN 'EN TALLER (Correctivo)'
           WHEN t.fecha_proxima_inspeccion < SYSDATE    THEN 'VENCIDO - INSPECCIONAR'
           ELSE 'Al Día'
       END AS "Condición"
FROM TREN t
JOIN MODELO_TREN m ON t.modelo_id = m.id_modelo
WHERE t.fecha_proxima_inspeccion < SYSDATE
   OR t.estado_operativo = 'En Mantenimiento'
ORDER BY t.fecha_proxima_inspeccion;


--------------------------------------------------------------------------------
-- CONSULTA 8: ¿Qué conductor fue asignado a cada viaje?
-- Relaciona cada viaje con el conductor y su licencia técnica de conducción.
--------------------------------------------------------------------------------
PROMPT 
PROMPT ------------------------------------------------------------------------------
PROMPT 8/15. ¿Qué conductor fue asignado a cada viaje programado?
PROMPT ------------------------------------------------------------------------------

SELECT vp.numero_viaje   AS "Viaje",
       r.codigo          AS "Ruta",
       emp.numero_empleado AS "Num. Empleado",
       emp.nombre_completo AS "Nombre Conductor",
       NVL(c.tipo_certificacion, 'Sin Certificar') AS "Certificación MTA",
       TO_CHAR(vp.fecha, 'YYYY-MM-DD') AS "Fecha Viaje"
FROM VIAJE_PROGRAMADO vp
JOIN RUTA r     ON vp.ruta_id = r.id_ruta
JOIN EMPLEADO emp ON vp.conductor_id = emp.id_empleado
LEFT JOIN CERTIFICACION c ON emp.id_empleado = c.empleado_id AND c.estado = 'Vigente'
ORDER BY vp.fecha, vp.hora_prog_salida;


--------------------------------------------------------------------------------
-- CONSULTA 9: ¿Cuántos pasajeros utilizaron cada línea durante un período?
-- Agregación de afluencia por línea con LEFT JOIN (las líneas sin viajes muestran 0).
--------------------------------------------------------------------------------
PROMPT 
PROMPT ------------------------------------------------------------------------------
PROMPT 9/15. ¿Cuántos pasajeros utilizaron cada línea durante el período de prueba?
PROMPT ------------------------------------------------------------------------------

SELECT l.codigo          AS "Línea",
       l.nombre          AS "Nombre de la Línea",
       COUNT(vp.id_viaje_pasajero) AS "Total Pasajeros"
FROM LINEA l
LEFT JOIN RUTA r             ON l.id_linea = r.linea_id
LEFT JOIN VIAJE_PROGRAMADO vprog ON r.id_ruta = vprog.ruta_id
LEFT JOIN VIAJE_PASAJERO vp  ON vprog.id_viaje = vp.viaje_programado_id
GROUP BY l.codigo, l.nombre
ORDER BY "Total Pasajeros" DESC;


--------------------------------------------------------------------------------
-- CONSULTA 10: ¿Cuánto dinero se recaudó por día, estación y tipo de tarifa?
-- Agrupación contable por fecha de validación en torniquete, estación y perfil.
--------------------------------------------------------------------------------
PROMPT 
PROMPT ------------------------------------------------------------------------------
PROMPT 10/15. ¿Cuánto dinero se recaudó por día, estación y tipo de tarifa?
PROMPT ------------------------------------------------------------------------------

SELECT TO_CHAR(CAST(vp.fecha_hora_ingreso AS DATE), 'YYYY-MM-DD') AS "Fecha",
       e.nombre  AS "Estación de Ingreso",
       t.nombre  AS "Perfil Tarifa",
       COUNT(vp.id_viaje_pasajero) AS "Pasajes",
       SUM(vp.monto_cobrado)       AS "Total Recaudado"
FROM VIAJE_PASAJERO vp
JOIN ESTACION e ON vp.estacion_ingreso_id = e.id_estacion
JOIN TARIFA t   ON vp.tarifa_id = t.id_tarifa
GROUP BY TO_CHAR(CAST(vp.fecha_hora_ingreso AS DATE), 'YYYY-MM-DD'), e.nombre, t.nombre
ORDER BY "Fecha", "Estación de Ingreso", "Total Recaudado" DESC;


--------------------------------------------------------------------------------
-- CONSULTA 11: ¿Cuáles son las estaciones con mayor flujo de pasajeros?
-- Ranking de afluencia por estación según ingresos validados.
--------------------------------------------------------------------------------
PROMPT 
PROMPT ------------------------------------------------------------------------------
PROMPT 11/15. ¿Cuáles son las estaciones con mayor flujo de pasajeros (afluencia)?
PROMPT ------------------------------------------------------------------------------

SELECT e.nombre   AS "Estación",
       e.distrito AS "Distrito (Borough)",
       COUNT(vp.id_viaje_pasajero) AS "Total Ingresos"
FROM ESTACION e
JOIN VIAJE_PASAJERO vp ON e.id_estacion = vp.estacion_ingreso_id
GROUP BY e.nombre, e.distrito
ORDER BY "Total Ingresos" DESC;


--------------------------------------------------------------------------------
-- CONSULTA 12: ¿Qué incidentes permanecen abiertos?
-- Incidentes no resueltos (estado != 'Cerrado') resolviendo el Arco Exclusivo.
--------------------------------------------------------------------------------
PROMPT 
PROMPT ------------------------------------------------------------------------------
PROMPT 12/15. ¿Qué incidentes permanecen abiertos en la red del metro?
PROMPT ------------------------------------------------------------------------------

SELECT i.numero_incidente AS "Código Incidente",
       i.tipo             AS "Tipo de Incidente",
       i.nivel_severidad  AS "Severidad",
       TO_CHAR(i.fecha_hora_inicio, 'YYYY-MM-DD HH24:MI') AS "Fecha y Hora",
       i.estado           AS "Estado",
       NVL(e.nombre, NVL(t.codigo_interno, NVL(r.codigo, 'General de Red'))) AS "Elemento Afectado"
FROM INCIDENTE i
LEFT JOIN INCIDENTE_ELEMENTO_AFECTADO a ON i.id_incidente = a.incidente_id
LEFT JOIN ESTACION e ON a.estacion_id = e.id_estacion
LEFT JOIN TREN t     ON a.tren_id = t.id_tren
LEFT JOIN RUTA r     ON a.ruta_id = r.id_ruta
WHERE i.estado != 'Cerrado'
ORDER BY i.fecha_hora_inicio DESC;


--------------------------------------------------------------------------------
-- CONSULTA 13: ¿Qué línea acumuló más retrasos?
-- Suma de minutos de demora en salidas reales versus programadas agrupado por línea.
--------------------------------------------------------------------------------
PROMPT 
PROMPT ------------------------------------------------------------------------------
PROMPT 13/15. ¿Qué línea acumuló mayor cantidad de minutos de retraso?
PROMPT ------------------------------------------------------------------------------

SELECT l.codigo AS "Línea",
       l.nombre AS "Nombre Línea",
       l.color  AS "Color",
       COUNT(vp.id_viaje) AS "Viajes Afect.",
       NVL(SUM(ROUND((CAST(vp.hora_real_salida AS DATE) - CAST(vp.hora_prog_salida AS DATE)) * 24 * 60)), 0) AS "Total Min. Demora"
FROM LINEA l
JOIN RUTA r ON l.id_linea = r.linea_id
JOIN VIAJE_PROGRAMADO vp ON r.id_ruta = vp.ruta_id
WHERE vp.hora_real_salida > vp.hora_prog_salida
GROUP BY l.codigo, l.nombre, l.color
ORDER BY "Total Min. Demora" DESC;


--------------------------------------------------------------------------------
-- CONSULTA 14: ¿Qué tarjetas fueron bloqueadas o vencieron?
-- Tarjetas con estado anormal o fecha_vencimiento anterior al día de hoy.
--------------------------------------------------------------------------------
PROMPT 
PROMPT ------------------------------------------------------------------------------
PROMPT 14/15. ¿Qué tarjetas fueron bloqueadas o presentan vencimiento?
PROMPT ------------------------------------------------------------------------------

SELECT t.numero_tarjeta        AS "Número Tarjeta",
       tar.nombre              AS "Perfil Tarifa",
       NVL(p.nombre, '(Tarjeta Anónima)') AS "Pasajero Titular",
       t.saldo_disponible      AS "Saldo",
       TO_CHAR(t.fecha_vencimiento, 'YYYY-MM-DD') AS "Vencimiento",
       t.estado                AS "Estado"
FROM TARJETA t
JOIN TARIFA tar ON t.tarifa_id = tar.id_tarifa
LEFT JOIN PASAJERO p ON t.pasajero_id = p.id_pasajero
WHERE t.estado IN ('Bloqueada', 'Vencida')
   OR t.fecha_vencimiento < SYSDATE
ORDER BY t.estado, t.fecha_vencimiento;


--------------------------------------------------------------------------------
-- CONSULTA 15: ¿Qué técnicos participaron en una orden de mantenimiento?
-- Cruce de órdenes con técnicos asignados y roles dentro de la orden.
--------------------------------------------------------------------------------
PROMPT 
PROMPT ------------------------------------------------------------------------------
PROMPT 15/15. ¿Qué técnicos participaron en cada orden de mantenimiento?
PROMPT ------------------------------------------------------------------------------

SELECT om.numero_orden    AS "Orden Trabajo",
       om.tipo_mantenimiento AS "Tipo Mantenimiento",
       eq.codigo_equipo   AS "Equipo",
       e.nombre_completo  AS "Técnico Asignado",
       ot.rol_en_orden    AS "Rol Desempeñado",
       om.estado          AS "Estado Orden"
FROM ORDEN_MANTENIMIENTO om
JOIN EQUIPO eq        ON om.equipo_id = eq.id_equipo
JOIN ORDEN_TECNICO ot ON om.id_orden = ot.orden_id
JOIN EMPLEADO e       ON ot.empleado_id = e.id_empleado
ORDER BY om.numero_orden, e.nombre_completo;

PROMPT ==============================================================================
PROMPT  ¡EJECUCIÓN DE LAS 15 CONSULTAS MÍNIMAS COMPLETADA EXITOSAMENTE!
PROMPT ==============================================================================

EXIT;
