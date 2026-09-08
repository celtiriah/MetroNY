--------------------------------------------------------------------------------
-- Sistema de Gestión del Metro de Nueva York
-- Script 02: Índices B-Tree de Optimización y Rendimiento
-- Basado en las recomendaciones de la Lección 12 (Oracle Índices)
--
-- Propósito:
--   1. Indexar todas las Claves Foráneas (FK) para evitar Table Locks en
--      operaciones DML concurrentes y acelerar las consultas con JOIN.
--   2. Indexar columnas de búsqueda frecuente (WHERE, ORDER BY, GROUP BY)
--      según las consultas mínimas requeridas por el enunciado del proyecto.
--
-- Momento de ejecución recomendado:
--   Ejecutar después de crear las tablas (DDL) o inmediatamente después
--   de la carga masiva inicial de datos (para no ralentizar las inserciones).
--------------------------------------------------------------------------------

PROMPT ====================================================================
PROMPT Creando Índices B-Tree para Claves Foráneas (FK)...
PROMPT ====================================================================

-- -----------------------------------------------------------------------------
-- 1. RED E INFRAESTRUCTURA
-- -----------------------------------------------------------------------------
CREATE INDEX IDX_LINEA_EST_ORIGEN_ID        ON LINEA (estacion_origen_id);
CREATE INDEX IDX_LINEA_EST_DESTINO_ID       ON LINEA (estacion_destino_id);
CREATE INDEX IDX_LINEA_EST_LINEA_ID         ON LINEA_ESTACION (linea_id);
CREATE INDEX IDX_LINEA_EST_ESTACION_ID      ON LINEA_ESTACION (estacion_id);
CREATE INDEX IDX_PLATAFORMA_ESTACION_ID     ON PLATAFORMA (estacion_id);
CREATE INDEX IDX_EST_SERV_ESTACION_ID       ON ESTACION_SERVICIO (estacion_id);
CREATE INDEX IDX_HORARIO_EST_ESTACION_ID    ON HORARIO_ESTACION (estacion_id);
CREATE INDEX IDX_TRANSF_ESTACION_ID         ON TRANSFERENCIA (estacion_id);
CREATE INDEX IDX_TRANSF_LINEA_ORIGEN_ID     ON TRANSFERENCIA (linea_origen_id);
CREATE INDEX IDX_TRANSF_LINEA_DESTINO_ID    ON TRANSFERENCIA (linea_destino_id);

-- -----------------------------------------------------------------------------
-- 2. RUTAS Y HORARIOS
-- -----------------------------------------------------------------------------
CREATE INDEX IDX_RUTA_LINEA_ID              ON RUTA (linea_id);
CREATE INDEX IDX_RUTA_EST_ORIGEN_ID         ON RUTA (estacion_origen_id);
CREATE INDEX IDX_RUTA_EST_DESTINO_ID        ON RUTA (estacion_destino_id);
CREATE INDEX IDX_RUTA_DET_RUTA_ID           ON RUTA_DETALLE (ruta_id);
CREATE INDEX IDX_RUTA_DET_ESTACION_ID       ON RUTA_DETALLE (estacion_id);
CREATE INDEX IDX_HORARIO_RUTA_ID            ON HORARIO (ruta_id);
CREATE INDEX IDX_VIAJE_PROG_RUTA_ID         ON VIAJE_PROGRAMADO (ruta_id);
CREATE INDEX IDX_VIAJE_PROG_HORARIO_ID      ON VIAJE_PROGRAMADO (horario_id);
CREATE INDEX IDX_VIAJE_PROG_TREN_ID         ON VIAJE_PROGRAMADO (tren_id);
CREATE INDEX IDX_VIAJE_PROG_CONDUCTOR_ID    ON VIAJE_PROGRAMADO (conductor_id);

-- -----------------------------------------------------------------------------
-- 3. TRENES Y FLOTA
-- -----------------------------------------------------------------------------
CREATE INDEX IDX_TREN_MODELO_ID             ON TREN (modelo_id);
CREATE INDEX IDX_TREN_DEPOSITO_ID           ON TREN (deposito_id);
CREATE INDEX IDX_TREN_VAGON_TREN_ID         ON TREN_VAGON (tren_id);
CREATE INDEX IDX_TREN_VAGON_VAGON_ID        ON TREN_VAGON (vagon_id);

-- -----------------------------------------------------------------------------
-- 4. PERSONAL Y TURNOS
-- -----------------------------------------------------------------------------
CREATE INDEX IDX_EMPLEADO_SUPERVISOR_ID     ON EMPLEADO (supervisor_id);
CREATE INDEX IDX_CERT_EMPLEADO_ID           ON CERTIFICACION (empleado_id);
CREATE INDEX IDX_CERT_MOD_CERT_ID           ON CERTIFICACION_MODELO (certificacion_id);
CREATE INDEX IDX_CERT_MOD_MODELO_ID         ON CERTIFICACION_MODELO (modelo_id);
CREATE INDEX IDX_TURNO_EMPLEADO_ID          ON TURNO (empleado_id);

-- -----------------------------------------------------------------------------
-- 5. PASAJEROS, TARJETAS Y VIAJES
-- -----------------------------------------------------------------------------
CREATE INDEX IDX_TARJETA_PASAJERO_ID        ON TARJETA (pasajero_id);
CREATE INDEX IDX_TARJETA_TARIFA_ID          ON TARJETA (tarifa_id);
CREATE INDEX IDX_RECARGA_TARJETA_ID         ON RECARGA (tarjeta_id);
CREATE INDEX IDX_VIAJE_PAS_TARJETA_ID       ON VIAJE_PASAJERO (tarjeta_id);
CREATE INDEX IDX_VIAJE_PAS_EST_INGRESO_ID   ON VIAJE_PASAJERO (estacion_ingreso_id);
CREATE INDEX IDX_VIAJE_PAS_EST_SALIDA_ID    ON VIAJE_PASAJERO (estacion_salida_id);
CREATE INDEX IDX_VIAJE_PAS_TARIFA_ID        ON VIAJE_PASAJERO (tarifa_id);
CREATE INDEX IDX_VIAJE_PAS_VIAJE_PROG_ID    ON VIAJE_PASAJERO (viaje_programado_id);

-- -----------------------------------------------------------------------------
-- 6. MANTENIMIENTO Y REPUESTOS
-- -----------------------------------------------------------------------------
CREATE INDEX IDX_ORDEN_MANT_EQUIPO_ID       ON ORDEN_MANTENIMIENTO (equipo_id);
CREATE INDEX IDX_ORD_TEC_ORDEN_ID           ON ORDEN_TECNICO (orden_id);
CREATE INDEX IDX_ORD_TEC_EMPLEADO_ID        ON ORDEN_TECNICO (empleado_id);
CREATE INDEX IDX_ORD_REP_ORDEN_ID           ON ORDEN_REPUESTO (orden_id);
CREATE INDEX IDX_ORD_REP_REPUESTO_ID        ON ORDEN_REPUESTO (repuesto_id);

-- -----------------------------------------------------------------------------
-- 7. INCIDENTES Y ELEMENTOS AFECTADOS (ARCO EXCLUSIVO)
-- -----------------------------------------------------------------------------
CREATE INDEX IDX_INCIDENTE_REPORTADO_POR    ON INCIDENTE (reportado_por_id);
CREATE INDEX IDX_INC_ELEM_INCIDENTE_ID      ON INCIDENTE_ELEMENTO_AFECTADO (incidente_id);
CREATE INDEX IDX_INC_ELEM_ESTACION_ID       ON INCIDENTE_ELEMENTO_AFECTADO (estacion_id);
CREATE INDEX IDX_INC_ELEM_TREN_ID           ON INCIDENTE_ELEMENTO_AFECTADO (tren_id);
CREATE INDEX IDX_INC_ELEM_RUTA_ID           ON INCIDENTE_ELEMENTO_AFECTADO (ruta_id);
CREATE INDEX IDX_INC_ELEM_EQUIPO_ID         ON INCIDENTE_ELEMENTO_AFECTADO (equipo_id);
CREATE INDEX IDX_INC_ELEM_VIAJE_ID          ON INCIDENTE_ELEMENTO_AFECTADO (viaje_id);
CREATE INDEX IDX_INC_ELEM_LINEA_ID          ON INCIDENTE_ELEMENTO_AFECTADO (linea_id);

PROMPT Total de índices de claves foráneas creados: 50.

PROMPT ====================================================================
PROMPT Creando Índices B-Tree para Consultas y Filtros Frecuentes...
PROMPT ====================================================================

-- Viajes programados por fecha y estado operativo (Consulta 4 y 5)
CREATE INDEX IDX_VIAJE_PROG_FECHA_ESTADO    ON VIAJE_PROGRAMADO (fecha, estado);

-- Horarios reales de salida para cálculo de retrasos mayores a 15 min (Consulta 5)
CREATE INDEX IDX_VIAJE_PROG_HORA_SALIDA     ON VIAJE_PROGRAMADO (hora_prog_salida, hora_real_salida);

-- Trenes por estado operativo para identificar disponibilidad (Consulta 6)
CREATE INDEX IDX_TREN_ESTADO_OPERATIVO      ON TREN (estado_operativo);

-- Trenes por fecha de próxima inspección para mantenimiento preventivo (Consulta 7)
CREATE INDEX IDX_TREN_PROX_INSPECCION       ON TREN (fecha_proxima_inspeccion);

-- Asignación de conductores por viaje y fecha (Consulta 8)
CREATE INDEX IDX_VIAJE_PROG_COND_FECHA      ON VIAJE_PROGRAMADO (conductor_id, fecha);

-- Histórico de validación de pasajeros por fecha/hora de ingreso (Consultas 9, 10 y 11)
CREATE INDEX IDX_VIAJE_PAS_FECHA_INGRESO    ON VIAJE_PASAJERO (fecha_hora_ingreso);

-- Recaudación por estación, tarifa y fecha (Consulta 10)
CREATE INDEX IDX_VIAJE_PAS_EST_FECHA        ON VIAJE_PASAJERO (estacion_ingreso_id, fecha_hora_ingreso);

-- Incidentes abiertos por severidad y fecha de inicio (Consulta 12)
CREATE INDEX IDX_INCIDENTE_ESTADO_FECHA     ON INCIDENTE (estado, fecha_hora_inicio);

-- Estado de tarjetas y vencimiento (Consulta 14)
CREATE INDEX IDX_TARJETA_ESTADO_VENC        ON TARJETA (estado, fecha_vencimiento);

-- Empleados por cargo y estado laboral para turnos y cuadrillas
CREATE INDEX IDX_EMPLEADO_CARGO_ESTADO      ON EMPLEADO (cargo, estado_laboral);

-- Turnos programados por fecha y estado de asistencia
CREATE INDEX IDX_TURNO_FECHA_ESTADO         ON TURNO (fecha, estado_asistencia);

-- Auditoría de bitácora por fecha/hora y tabla afectada
CREATE INDEX IDX_BITACORA_FECHA_TABLA       ON BITACORA (fecha_hora, tabla_afectada);

-- Órdenes de mantenimiento por estado y prioridad
CREATE INDEX IDX_ORDEN_MANT_ESTADO_PRIOR    ON ORDEN_MANTENIMIENTO (estado, prioridad);

PROMPT Total de índices de consulta creados: 13.
PROMPT Script de índices B-Tree completado exitosamente (63 índices totales).
