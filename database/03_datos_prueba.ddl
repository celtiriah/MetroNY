--------------------------------------------------------------------------------
-- Sistema de Gestión del Metro de Nueva York
-- Script 03: Inserción de Datos de Prueba Iniciales (Seed Data)
-- Cobertura: 33 tablas del modelo relacional 3FN
--
-- Datos basados en la red real del New York City Subway (MTA):
--   - Líneas: 1 (Broadway Local), A (8th Ave Express), C (8th Ave Local), 
--             7 (Flushing Local/Express), L (14th St-Canarsie)
--   - Estaciones icónicas de Manhattan, Brooklyn, Queens y The Bronx
--   - Modelos de tren MTA: R142, R160, R179, R211
--   - Tarifas oficiales OMNY / MetroCard
--   - Casos para las 15 consultas mínimas del enunciado (retrasos > 15m,
--     trenes en mantenimiento, incidentes abiertos, viajes anónimos, etc.)
--
-- Modo de Ejecución:
--   Ejecutar conectado con el usuario del proyecto (METRO_NY):
--   sqlplus METRO_NY/MetroPass123@localhost:1521/FREEPDB1 @03_datos_prueba.ddl
--------------------------------------------------------------------------------

SET DEFINE OFF;
SET AUTOCOMMIT OFF;
ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD';
ALTER SESSION SET NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS';

PROMPT ====================================================================
PROMPT Insertando datos iniciales del Metro de Nueva York...
PROMPT ====================================================================

-- 1. MODELO_TREN
PROMPT 1/33. Insertando MODELO_TREN...
INSERT INTO MODELO_TREN (id_modelo, nombre_modelo, fabricante) VALUES (1, 'R142', 'Bombardier Transportation');
INSERT INTO MODELO_TREN (id_modelo, nombre_modelo, fabricante) VALUES (2, 'R160', 'Alstom / Kawasaki Heavy Industries');
INSERT INTO MODELO_TREN (id_modelo, nombre_modelo, fabricante) VALUES (3, 'R179', 'Bombardier Transportation');
INSERT INTO MODELO_TREN (id_modelo, nombre_modelo, fabricante) VALUES (4, 'R211', 'Kawasaki Rail Car');

-- 2. DEPOSITO
PROMPT 2/33. Insertando DEPOSITO...
INSERT INTO DEPOSITO (id_deposito, codigo, nombre, ubicacion, capacidad) VALUES (1, 'DEP-207', '207th Street Yard', 'Inwood, Manhattan (10th Ave & 207th St)', 35);
INSERT INTO DEPOSITO (id_deposito, codigo, nombre, ubicacion, capacidad) VALUES (2, 'DEP-CI', 'Coney Island Overhaul Yard', 'Avenue X, Brooklyn', 60);
INSERT INTO DEPOSITO (id_deposito, codigo, nombre, ubicacion, capacidad) VALUES (3, 'DEP-COR', 'Corona Yard', 'Flushing Meadows, Queens', 28);
INSERT INTO DEPOSITO (id_deposito, codigo, nombre, ubicacion, capacidad) VALUES (4, 'DEP-239', '239th Street Yard', 'Wakefield, The Bronx', 30);

-- 3. TARIFA
PROMPT 3/33. Insertando TARIFA...
INSERT INTO TARIFA (id_tarifa, codigo, nombre, descripcion, monto, tipo_pasajero, fecha_inicio_vigencia, fecha_fin_vigencia, cantidad_maxima_viajes, duracion_beneficio_dias, estado) VALUES (1, 'TAR-REG', 'Tarifa Base Estándar', 'Tarifa regular OMNY / MetroCard por viaje individual', 2.90, 'Regular', TO_DATE('2024-01-01', 'YYYY-MM-DD'), NULL, NULL, NULL, 'Vigente');
INSERT INTO TARIFA (id_tarifa, codigo, nombre, descripcion, monto, tipo_pasajero, fecha_inicio_vigencia, fecha_fin_vigencia, cantidad_maxima_viajes, duracion_beneficio_dias, estado) VALUES (2, 'TAR-SENIOR', 'Tarifa Reducida Adulto Mayor', '50% de descuento para mayores de 65 años', 1.45, 'Adulto Mayor', TO_DATE('2024-01-01', 'YYYY-MM-DD'), NULL, NULL, NULL, 'Vigente');
INSERT INTO TARIFA (id_tarifa, codigo, nombre, descripcion, monto, tipo_pasajero, fecha_inicio_vigencia, fecha_fin_vigencia, cantidad_maxima_viajes, duracion_beneficio_dias, estado) VALUES (3, 'TAR-DISAB', 'Tarifa Discapacidad', 'Tarifa reducida para pasajeros con movilidad reducida', 1.45, 'Persona con Discapacidad', TO_DATE('2024-01-01', 'YYYY-MM-DD'), NULL, NULL, NULL, 'Vigente');
INSERT INTO TARIFA (id_tarifa, codigo, nombre, descripcion, monto, tipo_pasajero, fecha_inicio_vigencia, fecha_fin_vigencia, cantidad_maxima_viajes, duracion_beneficio_dias, estado) VALUES (4, 'TAR-SEM-UNL', 'Pase Semanal Ilimitado', 'Viajes ilimitados durante 7 días consecutivos', 34.00, 'Regular', TO_DATE('2024-01-01', 'YYYY-MM-DD'), NULL, NULL, 7, 'Vigente');
INSERT INTO TARIFA (id_tarifa, codigo, nombre, descripcion, monto, tipo_pasajero, fecha_inicio_vigencia, fecha_fin_vigencia, cantidad_maxima_viajes, duracion_beneficio_dias, estado) VALUES (5, 'TAR-MES-UNL', 'Pase Mensual Ilimitado', 'Viajes ilimitados durante 30 días consecutivos', 132.00, 'Regular', TO_DATE('2024-01-01', 'YYYY-MM-DD'), NULL, NULL, 30, 'Vigente');
INSERT INTO TARIFA (id_tarifa, codigo, nombre, descripcion, monto, tipo_pasajero, fecha_inicio_vigencia, fecha_fin_vigencia, cantidad_maxima_viajes, duracion_beneficio_dias, estado) VALUES (6, 'TAR-ESTUD', 'Pase Escolar Gratuito', 'Subsidio escolar para estudiantes del DOE NY', 0.00, 'Estudiante', TO_DATE('2024-01-01', 'YYYY-MM-DD'), NULL, 3, NULL, 'Vigente');

-- 4. REPUESTO
PROMPT 4/33. Insertando REPUESTO...
INSERT INTO REPUESTO (id_repuesto, codigo, nombre, costo_unitario) VALUES (1, 'REP-BRK-01', 'Zapata de Freno Compuesto R160/R142', 145.50);
INSERT INTO REPUESTO (id_repuesto, codigo, nombre, costo_unitario) VALUES (2, 'REP-SHOE-02', 'Zapata de Contacto Tercer Riel (Third Rail Shoe)', 380.00);
INSERT INTO REPUESTO (id_repuesto, codigo, nombre, costo_unitario) VALUES (3, 'REP-DOR-03', 'Actuador Neumático de Puerta Automática', 520.00);
INSERT INTO REPUESTO (id_repuesto, codigo, nombre, costo_unitario) VALUES (4, 'REP-OPT-04', 'Sensor Óptico CBTC de Señalización', 890.00);
INSERT INTO REPUESTO (id_repuesto, codigo, nombre, costo_unitario) VALUES (5, 'REP-AIR-05', 'Filtro de Aire HVAC de Vagón Pasajero', 65.00);
INSERT INTO REPUESTO (id_repuesto, codigo, nombre, costo_unitario) VALUES (6, 'REP-LED-06', 'Módulo de Iluminación LED Cabina/Salón', 115.00);
INSERT INTO REPUESTO (id_repuesto, codigo, nombre, costo_unitario) VALUES (7, 'REP-REL-07', 'Relé de Seguridad Enclavamiento de Vía', 340.00);
INSERT INTO REPUESTO (id_repuesto, codigo, nombre, costo_unitario) VALUES (8, 'REP-ESC-08', 'Cadena de Tracción Escalera Eléctrica', 1250.00);

-- 5. ESTACION
PROMPT 5/33. Insertando ESTACION...
INSERT INTO ESTACION (id_estacion, codigo, nombre, direccion, distrito, latitud, longitud, fecha_inauguracion, cantidad_accesos, cantidad_plataformas, estado_operativo, horario_funcionamiento, elevadores_disponibles, escaleras_electricas_disponibles, accesible_discapacidad, tipo_estacion) VALUES (1, 'TSQ42', 'Times Sq - 42 St', 'Broadway & 42nd St', 'Manhattan', 40.7559, -73.9871, TO_DATE('1904-10-27', 'YYYY-MM-DD'), 14, 4, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia');
INSERT INTO ESTACION (id_estacion, codigo, nombre, direccion, distrito, latitud, longitud, fecha_inauguracion, cantidad_accesos, cantidad_plataformas, estado_operativo, horario_funcionamiento, elevadores_disponibles, escaleras_electricas_disponibles, accesible_discapacidad, tipo_estacion) VALUES (2, 'GCT42', 'Grand Central - 42 St', 'Park Ave & 42nd St', 'Manhattan', 40.7517, -73.9768, TO_DATE('1904-10-27', 'YYYY-MM-DD'), 12, 4, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia');
INSERT INTO ESTACION (id_estacion, codigo, nombre, direccion, distrito, latitud, longitud, fecha_inauguracion, cantidad_accesos, cantidad_plataformas, estado_operativo, horario_funcionamiento, elevadores_disponibles, escaleras_electricas_disponibles, accesible_discapacidad, tipo_estacion) VALUES (3, '14USQ', '14 St - Union Sq', 'Broadway & 14th St', 'Manhattan', 40.7359, -73.9906, TO_DATE('1904-10-27', 'YYYY-MM-DD'), 10, 4, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia');
INSERT INTO ESTACION (id_estacion, codigo, nombre, direccion, distrito, latitud, longitud, fecha_inauguracion, cantidad_accesos, cantidad_plataformas, estado_operativo, horario_funcionamiento, elevadores_disponibles, escaleras_electricas_disponibles, accesible_discapacidad, tipo_estacion) VALUES (4, 'W4ST', 'W 4 St - Washington Sq', '6th Ave & W 4th St', 'Manhattan', 40.7310, -74.0003, TO_DATE('1932-09-10', 'YYYY-MM-DD'), 8, 4, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia');
INSERT INTO ESTACION (id_estacion, codigo, nombre, direccion, distrito, latitud, longitud, fecha_inauguracion, cantidad_accesos, cantidad_plataformas, estado_operativo, horario_funcionamiento, elevadores_disponibles, escaleras_electricas_disponibles, accesible_discapacidad, tipo_estacion) VALUES (5, 'FLTN', 'Fulton St', 'Fulton St & Broadway', 'Manhattan', 40.7103, -74.0076, TO_DATE('1905-01-16', 'YYYY-MM-DD'), 16, 6, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia');
INSERT INTO ESTACION (id_estacion, codigo, nombre, direccion, distrito, latitud, longitud, fecha_inauguracion, cantidad_accesos, cantidad_plataformas, estado_operativo, horario_funcionamiento, elevadores_disponibles, escaleras_electricas_disponibles, accesible_discapacidad, tipo_estacion) VALUES (6, 'BCH', 'Brooklyn Bridge - City Hall', 'Centre St & Chambers St', 'Manhattan', 40.7130, -74.0041, TO_DATE('1904-10-27', 'YYYY-MM-DD'), 6, 2, 'Operativa', '24 horas', 'S', 'N', 'S', 'Terminal');
INSERT INTO ESTACION (id_estacion, codigo, nombre, direccion, distrito, latitud, longitud, fecha_inauguracion, cantidad_accesos, cantidad_plataformas, estado_operativo, horario_funcionamiento, elevadores_disponibles, escaleras_electricas_disponibles, accesible_discapacidad, tipo_estacion) VALUES (7, 'ATL', 'Atlantic Av - Barclays Ctr', 'Flatbush Ave & Atlantic Ave', 'Brooklyn', 40.6844, -73.9786, TO_DATE('1908-05-01', 'YYYY-MM-DD'), 11, 6, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia');
INSERT INTO ESTACION (id_estacion, codigo, nombre, direccion, distrito, latitud, longitud, fecha_inauguracion, cantidad_accesos, cantidad_plataformas, estado_operativo, horario_funcionamiento, elevadores_disponibles, escaleras_electricas_disponibles, accesible_discapacidad, tipo_estacion) VALUES (8, 'JAY', 'Jay St - MetroTech', 'Jay St & Willoughby St', 'Brooklyn', 40.6923, -73.9873, TO_DATE('1933-02-01', 'YYYY-MM-DD'), 7, 3, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia');
INSERT INTO ESTACION (id_estacion, codigo, nombre, direccion, distrito, latitud, longitud, fecha_inauguracion, cantidad_accesos, cantidad_plataformas, estado_operativo, horario_funcionamiento, elevadores_disponibles, escaleras_electricas_disponibles, accesible_discapacidad, tipo_estacion) VALUES (9, 'QBORO', 'Queensboro Plaza', 'Queens Plaza & 27th St', 'Queens', 40.7506, -73.9402, TO_DATE('1916-11-05', 'YYYY-MM-DD'), 5, 2, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia');
INSERT INTO ESTACION (id_estacion, codigo, nombre, direccion, distrito, latitud, longitud, fecha_inauguracion, cantidad_accesos, cantidad_plataformas, estado_operativo, horario_funcionamiento, elevadores_disponibles, escaleras_electricas_disponibles, accesible_discapacidad, tipo_estacion) VALUES (10, 'FLSH', 'Flushing - Main St', 'Main St & Roosevelt Ave', 'Queens', 40.7596, -73.8300, TO_DATE('1928-01-21', 'YYYY-MM-DD'), 8, 2, 'Operativa', '24 horas', 'S', 'S', 'S', 'Terminal');
INSERT INTO ESTACION (id_estacion, codigo, nombre, direccion, distrito, latitud, longitud, fecha_inauguracion, cantidad_accesos, cantidad_plataformas, estado_operativo, horario_funcionamiento, elevadores_disponibles, escaleras_electricas_disponibles, accesible_discapacidad, tipo_estacion) VALUES (11, 'CONEY', 'Coney Island - Stillwell Av', 'Surf Ave & Stillwell Ave', 'Brooklyn', 40.5771, -73.9812, TO_DATE('1919-05-30', 'YYYY-MM-DD'), 6, 8, 'Operativa', '24 horas', 'S', 'N', 'S', 'Terminal');
INSERT INTO ESTACION (id_estacion, codigo, nombre, direccion, distrito, latitud, longitud, fecha_inauguracion, cantidad_accesos, cantidad_plataformas, estado_operativo, horario_funcionamiento, elevadores_disponibles, escaleras_electricas_disponibles, accesible_discapacidad, tipo_estacion) VALUES (12, 'VDCRT', 'Van Cortlandt Park - 242 St', 'Broadway & 242nd St', 'The Bronx', 40.8892, -73.8986, TO_DATE('1908-08-01', 'YYYY-MM-DD'), 4, 2, 'Operativa', '24 horas', 'N', 'N', 'N', 'Terminal');

-- 6. HORARIO_ESTACION
PROMPT 6/33. Insertando HORARIO_ESTACION...
INSERT INTO HORARIO_ESTACION (id_horario_estacion, estacion_id, tipo_dia, hora_apertura, hora_cierre, es_24_horas, estado) VALUES (1, 1, 'Todos los Dias', '00:00', '23:59', 'S', 'Vigente');
INSERT INTO HORARIO_ESTACION (id_horario_estacion, estacion_id, tipo_dia, hora_apertura, hora_cierre, es_24_horas, estado) VALUES (2, 2, 'Todos los Dias', '00:00', '23:59', 'S', 'Vigente');
INSERT INTO HORARIO_ESTACION (id_horario_estacion, estacion_id, tipo_dia, hora_apertura, hora_cierre, es_24_horas, estado) VALUES (3, 3, 'Todos los Dias', '00:00', '23:59', 'S', 'Vigente');
INSERT INTO HORARIO_ESTACION (id_horario_estacion, estacion_id, tipo_dia, hora_apertura, hora_cierre, es_24_horas, estado) VALUES (4, 4, 'Todos los Dias', '00:00', '23:59', 'S', 'Vigente');
INSERT INTO HORARIO_ESTACION (id_horario_estacion, estacion_id, tipo_dia, hora_apertura, hora_cierre, es_24_horas, estado) VALUES (5, 5, 'Todos los Dias', '00:00', '23:59', 'S', 'Vigente');
INSERT INTO HORARIO_ESTACION (id_horario_estacion, estacion_id, tipo_dia, hora_apertura, hora_cierre, es_24_horas, estado) VALUES (6, 6, 'Todos los Dias', '00:00', '23:59', 'S', 'Vigente');
INSERT INTO HORARIO_ESTACION (id_horario_estacion, estacion_id, tipo_dia, hora_apertura, hora_cierre, es_24_horas, estado) VALUES (7, 7, 'Todos los Dias', '00:00', '23:59', 'S', 'Vigente');
INSERT INTO HORARIO_ESTACION (id_horario_estacion, estacion_id, tipo_dia, hora_apertura, hora_cierre, es_24_horas, estado) VALUES (8, 8, 'Todos los Dias', '00:00', '23:59', 'S', 'Vigente');
INSERT INTO HORARIO_ESTACION (id_horario_estacion, estacion_id, tipo_dia, hora_apertura, hora_cierre, es_24_horas, estado) VALUES (9, 9, 'Todos los Dias', '00:00', '23:59', 'S', 'Vigente');
INSERT INTO HORARIO_ESTACION (id_horario_estacion, estacion_id, tipo_dia, hora_apertura, hora_cierre, es_24_horas, estado) VALUES (10, 10, 'Todos los Dias', '00:00', '23:59', 'S', 'Vigente');
INSERT INTO HORARIO_ESTACION (id_horario_estacion, estacion_id, tipo_dia, hora_apertura, hora_cierre, es_24_horas, estado) VALUES (11, 11, 'Todos los Dias', '00:00', '23:59', 'S', 'Vigente');
INSERT INTO HORARIO_ESTACION (id_horario_estacion, estacion_id, tipo_dia, hora_apertura, hora_cierre, es_24_horas, estado) VALUES (12, 12, 'Todos los Dias', '00:00', '23:59', 'S', 'Vigente');

-- 7. PLATAFORMA
PROMPT 7/33. Insertando PLATAFORMA...
INSERT INTO PLATAFORMA (id_plataforma, estacion_id, identificador, direccion_viaje, capacidad_aproximada, estado_operativo) VALUES (1, 1, 'Plat 1-N', 'Uptown / The Bronx', 1500, 'Operativa');
INSERT INTO PLATAFORMA (id_plataforma, estacion_id, identificador, direccion_viaje, capacidad_aproximada, estado_operativo) VALUES (2, 1, 'Plat 1-S', 'Downtown / Brooklyn', 1500, 'Operativa');
INSERT INTO PLATAFORMA (id_plataforma, estacion_id, identificador, direccion_viaje, capacidad_aproximada, estado_operativo) VALUES (3, 1, 'Plat 7-E', 'Flushing - Queens', 1200, 'Operativa');
INSERT INTO PLATAFORMA (id_plataforma, estacion_id, identificador, direccion_viaje, capacidad_aproximada, estado_operativo) VALUES (4, 2, 'Plat 4/5/6-N', 'Uptown / The Bronx', 1400, 'Operativa');
INSERT INTO PLATAFORMA (id_plataforma, estacion_id, identificador, direccion_viaje, capacidad_aproximada, estado_operativo) VALUES (5, 2, 'Plat 4/5/6-S', 'Downtown / Brooklyn', 1400, 'Operativa');
INSERT INTO PLATAFORMA (id_plataforma, estacion_id, identificador, direccion_viaje, capacidad_aproximada, estado_operativo) VALUES (6, 3, 'Plat L-E', 'Brooklyn / Canarsie', 1100, 'Operativa');
INSERT INTO PLATAFORMA (id_plataforma, estacion_id, identificador, direccion_viaje, capacidad_aproximada, estado_operativo) VALUES (7, 3, 'Plat L-W', '8th Ave Manhattan', 1100, 'Operativa');
INSERT INTO PLATAFORMA (id_plataforma, estacion_id, identificador, direccion_viaje, capacidad_aproximada, estado_operativo) VALUES (8, 4, 'Plat A/C-N', 'Uptown / Washington Hts', 1300, 'Operativa');
INSERT INTO PLATAFORMA (id_plataforma, estacion_id, identificador, direccion_viaje, capacidad_aproximada, estado_operativo) VALUES (9, 4, 'Plat A/C-S', 'Downtown / Brooklyn', 1300, 'Operativa');
INSERT INTO PLATAFORMA (id_plataforma, estacion_id, identificador, direccion_viaje, capacidad_aproximada, estado_operativo) VALUES (10, 5, 'Plat A/C-N', 'Uptown / Manhattan', 1500, 'Operativa');
INSERT INTO PLATAFORMA (id_plataforma, estacion_id, identificador, direccion_viaje, capacidad_aproximada, estado_operativo) VALUES (11, 5, 'Plat A/C-S', 'Brooklyn', 1500, 'Operativa');
INSERT INTO PLATAFORMA (id_plataforma, estacion_id, identificador, direccion_viaje, capacidad_aproximada, estado_operativo) VALUES (12, 7, 'Plat B/Q-N', 'Manhattan Express', 1400, 'Operativa');
INSERT INTO PLATAFORMA (id_plataforma, estacion_id, identificador, direccion_viaje, capacidad_aproximada, estado_operativo) VALUES (13, 7, 'Plat B/Q-S', 'Brighton / Coney Island', 1400, 'Operativa');

-- 8. ESTACION_SERVICIO
PROMPT 8/33. Insertando ESTACION_SERVICIO...
INSERT INTO ESTACION_SERVICIO (id_estacion_servicio, estacion_id, tipo_servicio, disponible) VALUES (1, 1, 'Venta/Recarga Tarjetas', 'S');
INSERT INTO ESTACION_SERVICIO (id_estacion_servicio, estacion_id, tipo_servicio, disponible) VALUES (2, 1, 'Policía/Seguridad', 'S');
INSERT INTO ESTACION_SERVICIO (id_estacion_servicio, estacion_id, tipo_servicio, disponible) VALUES (3, 1, 'Servicios Sanitarios', 'S');
INSERT INTO ESTACION_SERVICIO (id_estacion_servicio, estacion_id, tipo_servicio, disponible) VALUES (4, 1, 'Atención al Pasajero', 'S');
INSERT INTO ESTACION_SERVICIO (id_estacion_servicio, estacion_id, tipo_servicio, disponible) VALUES (5, 2, 'Venta/Recarga Tarjetas', 'S');
INSERT INTO ESTACION_SERVICIO (id_estacion_servicio, estacion_id, tipo_servicio, disponible) VALUES (6, 2, 'Conexión Trenes Regionales', 'S');
INSERT INTO ESTACION_SERVICIO (id_estacion_servicio, estacion_id, tipo_servicio, disponible) VALUES (7, 5, 'Venta/Recarga Tarjetas', 'S');
INSERT INTO ESTACION_SERVICIO (id_estacion_servicio, estacion_id, tipo_servicio, disponible) VALUES (8, 7, 'Conexión Autobuses', 'S');
INSERT INTO ESTACION_SERVICIO (id_estacion_servicio, estacion_id, tipo_servicio, disponible) VALUES (9, 7, 'Conexión Trenes Regionales', 'S');

-- 9. LINEA
PROMPT 9/33. Insertando LINEA...
INSERT INTO LINEA (id_linea, codigo, nombre, color, estacion_origen_id, estacion_destino_id, estado_operativo, tipo_servicio_principal, fecha_inauguracion, longitud_km, operador_responsable) VALUES (1, '1', 'Broadway - 7th Avenue Local', 'Rojo', 12, 6, 'Activa', 'Local', TO_DATE('1904-10-27', 'YYYY-MM-DD'), 24.2, 'MTA New York City Transit');
INSERT INTO LINEA (id_linea, codigo, nombre, color, estacion_origen_id, estacion_destino_id, estado_operativo, tipo_servicio_principal, fecha_inauguracion, longitud_km, operador_responsable) VALUES (2, 'A', '8th Avenue Express', 'Azul', 1, 11, 'Activa', 'Expreso', TO_DATE('1932-09-10', 'YYYY-MM-DD'), 51.5, 'MTA New York City Transit');
INSERT INTO LINEA (id_linea, codigo, nombre, color, estacion_origen_id, estacion_destino_id, estado_operativo, tipo_servicio_principal, fecha_inauguracion, longitud_km, operador_responsable) VALUES (3, 'C', '8th Avenue Local', 'Azul', 1, 8, 'Activa', 'Local', TO_DATE('1933-07-01', 'YYYY-MM-DD'), 30.1, 'MTA New York City Transit');
INSERT INTO LINEA (id_linea, codigo, nombre, color, estacion_origen_id, estacion_destino_id, estado_operativo, tipo_servicio_principal, fecha_inauguracion, longitud_km, operador_responsable) VALUES (4, '7', 'Flushing Local and Express', 'Púrpura', 1, 10, 'Activa', 'Local', TO_DATE('1915-06-22', 'YYYY-MM-DD'), 14.6, 'MTA New York City Transit');
INSERT INTO LINEA (id_linea, codigo, nombre, color, estacion_origen_id, estacion_destino_id, estado_operativo, tipo_servicio_principal, fecha_inauguracion, longitud_km, operador_responsable) VALUES (5, 'L', '14th Street - Canarsie Local', 'Gris', 3, 7, 'Activa', 'Local', TO_DATE('1924-06-30', 'YYYY-MM-DD'), 16.5, 'MTA New York City Transit');

-- 10. LINEA_ESTACION
PROMPT 10/33. Insertando LINEA_ESTACION...
INSERT INTO LINEA_ESTACION (id_linea_estacion, linea_id, estacion_id, orden, distancia_km, tiempo_estimado_min) VALUES (1, 1, 12, 1, 0.0, 0);
INSERT INTO LINEA_ESTACION (id_linea_estacion, linea_id, estacion_id, orden, distancia_km, tiempo_estimado_min) VALUES (2, 1, 1, 2, 15.2, 28);
INSERT INTO LINEA_ESTACION (id_linea_estacion, linea_id, estacion_id, orden, distancia_km, tiempo_estimado_min) VALUES (3, 1, 3, 3, 2.5, 6);
INSERT INTO LINEA_ESTACION (id_linea_estacion, linea_id, estacion_id, orden, distancia_km, tiempo_estimado_min) VALUES (4, 1, 6, 4, 3.2, 7);

INSERT INTO LINEA_ESTACION (id_linea_estacion, linea_id, estacion_id, orden, distancia_km, tiempo_estimado_min) VALUES (5, 2, 1, 1, 0.0, 0);
INSERT INTO LINEA_ESTACION (id_linea_estacion, linea_id, estacion_id, orden, distancia_km, tiempo_estimado_min) VALUES (6, 2, 4, 2, 3.1, 5);
INSERT INTO LINEA_ESTACION (id_linea_estacion, linea_id, estacion_id, orden, distancia_km, tiempo_estimado_min) VALUES (7, 2, 5, 3, 2.8, 5);
INSERT INTO LINEA_ESTACION (id_linea_estacion, linea_id, estacion_id, orden, distancia_km, tiempo_estimado_min) VALUES (8, 2, 8, 4, 3.0, 6);
INSERT INTO LINEA_ESTACION (id_linea_estacion, linea_id, estacion_id, orden, distancia_km, tiempo_estimado_min) VALUES (9, 2, 11, 5, 18.5, 30);

INSERT INTO LINEA_ESTACION (id_linea_estacion, linea_id, estacion_id, orden, distancia_km, tiempo_estimado_min) VALUES (10, 4, 1, 1, 0.0, 0);
INSERT INTO LINEA_ESTACION (id_linea_estacion, linea_id, estacion_id, orden, distancia_km, tiempo_estimado_min) VALUES (11, 4, 2, 2, 1.2, 3);
INSERT INTO LINEA_ESTACION (id_linea_estacion, linea_id, estacion_id, orden, distancia_km, tiempo_estimado_min) VALUES (12, 4, 9, 3, 4.5, 8);
INSERT INTO LINEA_ESTACION (id_linea_estacion, linea_id, estacion_id, orden, distancia_km, tiempo_estimado_min) VALUES (13, 4, 10, 4, 8.9, 16);

-- 11. TRANSFERENCIA
PROMPT 11/33. Insertando TRANSFERENCIA...
INSERT INTO TRANSFERENCIA (id_transferencia, estacion_id, linea_origen_id, linea_destino_id, tiempo_estimado_min) VALUES (1, 1, 1, 2, 3);
INSERT INTO TRANSFERENCIA (id_transferencia, estacion_id, linea_origen_id, linea_destino_id, tiempo_estimado_min) VALUES (2, 1, 1, 4, 4);
INSERT INTO TRANSFERENCIA (id_transferencia, estacion_id, linea_origen_id, linea_destino_id, tiempo_estimado_min) VALUES (3, 1, 2, 4, 4);
INSERT INTO TRANSFERENCIA (id_transferencia, estacion_id, linea_origen_id, linea_destino_id, tiempo_estimado_min) VALUES (4, 3, 1, 5, 2);
INSERT INTO TRANSFERENCIA (id_transferencia, estacion_id, linea_origen_id, linea_destino_id, tiempo_estimado_min) VALUES (5, 5, 2, 3, 2);

-- 12. RUTA
PROMPT 12/33. Insertando RUTA...
INSERT INTO RUTA (id_ruta, codigo, linea_id, estacion_origen_id, estacion_destino_id, sentido, tipo_servicio, distancia_total_km, duracion_estimada_min, estado, fecha_vigencia_desde, fecha_vigencia_hasta) VALUES (1, 'RUT-1-SB', 1, 12, 6, 'Sur (Downtown)', 'Local', 24.2, 45, 'Activa', TO_DATE('2024-01-01', 'YYYY-MM-DD'), NULL);
INSERT INTO RUTA (id_ruta, codigo, linea_id, estacion_origen_id, estacion_destino_id, sentido, tipo_servicio, distancia_total_km, duracion_estimada_min, estado, fecha_vigencia_desde, fecha_vigencia_hasta) VALUES (2, 'RUT-1-NB', 1, 6, 12, 'Norte (Uptown)', 'Local', 24.2, 45, 'Activa', TO_DATE('2024-01-01', 'YYYY-MM-DD'), NULL);
INSERT INTO RUTA (id_ruta, codigo, linea_id, estacion_origen_id, estacion_destino_id, sentido, tipo_servicio, distancia_total_km, duracion_estimada_min, estado, fecha_vigencia_desde, fecha_vigencia_hasta) VALUES (3, 'RUT-A-EXP-SB', 2, 1, 11, 'Sur (Brooklyn)', 'Expreso', 27.4, 46, 'Activa', TO_DATE('2024-01-01', 'YYYY-MM-DD'), NULL);
INSERT INTO RUTA (id_ruta, codigo, linea_id, estacion_origen_id, estacion_destino_id, sentido, tipo_servicio, distancia_total_km, duracion_estimada_min, estado, fecha_vigencia_desde, fecha_vigencia_hasta) VALUES (4, 'RUT-7-EB', 4, 1, 10, 'Este (Flushing)', 'Local', 14.6, 27, 'Activa', TO_DATE('2024-01-01', 'YYYY-MM-DD'), NULL);

-- 13. RUTA_DETALLE
PROMPT 13/33. Insertando RUTA_DETALLE...
INSERT INTO RUTA_DETALLE (id_ruta_detalle, ruta_id, estacion_id, orden_llegada, se_detiene) VALUES (1, 1, 12, 1, 'S');
INSERT INTO RUTA_DETALLE (id_ruta_detalle, ruta_id, estacion_id, orden_llegada, se_detiene) VALUES (2, 1, 1, 2, 'S');
INSERT INTO RUTA_DETALLE (id_ruta_detalle, ruta_id, estacion_id, orden_llegada, se_detiene) VALUES (3, 1, 3, 3, 'S');
INSERT INTO RUTA_DETALLE (id_ruta_detalle, ruta_id, estacion_id, orden_llegada, se_detiene) VALUES (4, 1, 6, 4, 'S');

INSERT INTO RUTA_DETALLE (id_ruta_detalle, ruta_id, estacion_id, orden_llegada, se_detiene) VALUES (5, 3, 1, 1, 'S');
INSERT INTO RUTA_DETALLE (id_ruta_detalle, ruta_id, estacion_id, orden_llegada, se_detiene) VALUES (6, 3, 4, 2, 'S');
INSERT INTO RUTA_DETALLE (id_ruta_detalle, ruta_id, estacion_id, orden_llegada, se_detiene) VALUES (7, 3, 5, 3, 'S');
INSERT INTO RUTA_DETALLE (id_ruta_detalle, ruta_id, estacion_id, orden_llegada, se_detiene) VALUES (8, 3, 8, 4, 'S');
INSERT INTO RUTA_DETALLE (id_ruta_detalle, ruta_id, estacion_id, orden_llegada, se_detiene) VALUES (9, 3, 11, 5, 'S');

-- 14. HORARIO
PROMPT 14/33. Insertando HORARIO...
INSERT INTO HORARIO (id_horario, ruta_id, dia_semana, hora_inicio, hora_fin, frecuencia_minutos, tipo_servicio, fecha_vigencia_desde, fecha_vigencia_hasta) VALUES (1, 1, 'Lunes a Viernes', TO_DATE('06:00', 'HH24:MI'), TO_DATE('09:30', 'HH24:MI'), 4, 'Hora Pico Matutina', TO_DATE('2024-01-01', 'YYYY-MM-DD'), NULL);
INSERT INTO HORARIO (id_horario, ruta_id, dia_semana, hora_inicio, hora_fin, frecuencia_minutos, tipo_servicio, fecha_vigencia_desde, fecha_vigencia_hasta) VALUES (2, 1, 'Lunes a Viernes', TO_DATE('09:31', 'HH24:MI'), TO_DATE('16:00', 'HH24:MI'), 7, 'Valle / Regular', TO_DATE('2024-01-01', 'YYYY-MM-DD'), NULL);
INSERT INTO HORARIO (id_horario, ruta_id, dia_semana, hora_inicio, hora_fin, frecuencia_minutos, tipo_servicio, fecha_vigencia_desde, fecha_vigencia_hasta) VALUES (3, 3, 'Lunes a Viernes', TO_DATE('07:00', 'HH24:MI'), TO_DATE('10:00', 'HH24:MI'), 5, 'Expreso Matutino', TO_DATE('2024-01-01', 'YYYY-MM-DD'), NULL);
INSERT INTO HORARIO (id_horario, ruta_id, dia_semana, hora_inicio, hora_fin, frecuencia_minutos, tipo_servicio, fecha_vigencia_desde, fecha_vigencia_hasta) VALUES (4, 4, 'Lunes a Viernes', TO_DATE('06:30', 'HH24:MI'), TO_DATE('09:30', 'HH24:MI'), 3, 'Hora Pico', TO_DATE('2024-01-01', 'YYYY-MM-DD'), NULL);

-- 15. TREN
PROMPT 15/33. Insertando TREN...
INSERT INTO TREN (id_tren, codigo_interno, modelo_id, anio_fabricacion, capacidad_total, estado_operativo, kilometraje_acumulado, deposito_id, fecha_ultima_inspeccion, fecha_proxima_inspeccion) VALUES (1, 'TR-101', 1, 2018, 1200, 'Disponible', 145200.5, 4, TO_DATE('2026-08-15', 'YYYY-MM-DD'), TO_DATE('2026-11-15', 'YYYY-MM-DD'));
INSERT INTO TREN (id_tren, codigo_interno, modelo_id, anio_fabricacion, capacidad_total, estado_operativo, kilometraje_acumulado, deposito_id, fecha_ultima_inspeccion, fecha_proxima_inspeccion) VALUES (2, 'TR-102', 1, 2019, 1200, 'En Operación', 112400.0, 4, TO_DATE('2026-08-10', 'YYYY-MM-DD'), TO_DATE('2026-11-10', 'YYYY-MM-DD'));
INSERT INTO TREN (id_tren, codigo_interno, modelo_id, anio_fabricacion, capacidad_total, estado_operativo, kilometraje_acumulado, deposito_id, fecha_ultima_inspeccion, fecha_proxima_inspeccion) VALUES (3, 'TR-201', 2, 2020, 1400, 'En Operación', 98500.0, 1, TO_DATE('2026-07-20', 'YYYY-MM-DD'), TO_DATE('2026-10-20', 'YYYY-MM-DD'));
INSERT INTO TREN (id_tren, codigo_interno, modelo_id, anio_fabricacion, capacidad_total, estado_operativo, kilometraje_acumulado, deposito_id, fecha_ultima_inspeccion, fecha_proxima_inspeccion) VALUES (4, 'TR-202', 2, 2020, 1400, 'Disponible', 92100.0, 2, TO_DATE('2026-08-01', 'YYYY-MM-DD'), TO_DATE('2026-11-01', 'YYYY-MM-DD'));
INSERT INTO TREN (id_tren, codigo_interno, modelo_id, anio_fabricacion, capacidad_total, estado_operativo, kilometraje_acumulado, deposito_id, fecha_ultima_inspeccion, fecha_proxima_inspeccion) VALUES (5, 'TR-301', 3, 2021, 1350, 'En Mantenimiento', 74800.0, 3, TO_DATE('2026-05-10', 'YYYY-MM-DD'), TO_DATE('2026-08-10', 'YYYY-MM-DD'));
INSERT INTO TREN (id_tren, codigo_interno, modelo_id, anio_fabricacion, capacidad_total, estado_operativo, kilometraje_acumulado, deposito_id, fecha_ultima_inspeccion, fecha_proxima_inspeccion) VALUES (6, 'TR-401', 4, 2023, 1500, 'Disponible', 32400.0, 1, TO_DATE('2026-08-25', 'YYYY-MM-DD'), TO_DATE('2026-11-25', 'YYYY-MM-DD'));

-- 16. VAGON
PROMPT 16/33. Insertando VAGON...
INSERT INTO VAGON (id_vagon, numero_serie, tipo_vagon, capacidad_sentados, capacidad_de_pie, anio_fabricacion, estado, accesibilidad) VALUES (1, 'VG-1001', 'Pasajero Regular', 44, 110, 2019, 'En Uso', 'S');
INSERT INTO VAGON (id_vagon, numero_serie, tipo_vagon, capacidad_sentados, capacidad_de_pie, anio_fabricacion, estado, accesibilidad) VALUES (2, 'VG-1002', 'Pasajero Regular', 44, 110, 2019, 'En Uso', 'S');
INSERT INTO VAGON (id_vagon, numero_serie, tipo_vagon, capacidad_sentados, capacidad_de_pie, anio_fabricacion, estado, accesibilidad) VALUES (3, 'VG-1003', 'Pasajero Regular', 44, 110, 2019, 'En Uso', 'S');
INSERT INTO VAGON (id_vagon, numero_serie, tipo_vagon, capacidad_sentados, capacidad_de_pie, anio_fabricacion, estado, accesibilidad) VALUES (4, 'VG-1004', 'Pasajero Regular', 44, 110, 2019, 'En Uso', 'S');
INSERT INTO VAGON (id_vagon, numero_serie, tipo_vagon, capacidad_sentados, capacidad_de_pie, anio_fabricacion, estado, accesibilidad) VALUES (5, 'VG-1005', 'Pasajero Regular', 44, 110, 2019, 'En Uso', 'S');
INSERT INTO VAGON (id_vagon, numero_serie, tipo_vagon, capacidad_sentados, capacidad_de_pie, anio_fabricacion, estado, accesibilidad) VALUES (6, 'VG-1006', 'Pasajero Regular', 44, 110, 2019, 'En Uso', 'S');
INSERT INTO VAGON (id_vagon, numero_serie, tipo_vagon, capacidad_sentados, capacidad_de_pie, anio_fabricacion, estado, accesibilidad) VALUES (7, 'VG-1007', 'Pasajero Regular', 44, 110, 2020, 'En Uso', 'S');
INSERT INTO VAGON (id_vagon, numero_serie, tipo_vagon, capacidad_sentados, capacidad_de_pie, anio_fabricacion, estado, accesibilidad) VALUES (8, 'VG-1008', 'Pasajero Regular', 44, 110, 2020, 'En Uso', 'S');
INSERT INTO VAGON (id_vagon, numero_serie, tipo_vagon, capacidad_sentados, capacidad_de_pie, anio_fabricacion, estado, accesibilidad) VALUES (9, 'VG-1009', 'Pasajero Regular', 44, 110, 2020, 'En Uso', 'S');

-- 17. TREN_VAGON
PROMPT 17/33. Insertando TREN_VAGON...
INSERT INTO TREN_VAGON (id_tren_vagon, tren_id, vagon_id, posicion, fecha_inicio) VALUES (1, 1, 1, 1, TO_DATE('2026-01-01', 'YYYY-MM-DD'));
INSERT INTO TREN_VAGON (id_tren_vagon, tren_id, vagon_id, posicion, fecha_inicio) VALUES (2, 1, 2, 2, TO_DATE('2026-01-01', 'YYYY-MM-DD'));
INSERT INTO TREN_VAGON (id_tren_vagon, tren_id, vagon_id, posicion, fecha_inicio) VALUES (3, 1, 3, 3, TO_DATE('2026-01-01', 'YYYY-MM-DD'));
INSERT INTO TREN_VAGON (id_tren_vagon, tren_id, vagon_id, posicion, fecha_inicio) VALUES (4, 2, 4, 1, TO_DATE('2026-01-01', 'YYYY-MM-DD'));
INSERT INTO TREN_VAGON (id_tren_vagon, tren_id, vagon_id, posicion, fecha_inicio) VALUES (5, 2, 5, 2, TO_DATE('2026-01-01', 'YYYY-MM-DD'));
INSERT INTO TREN_VAGON (id_tren_vagon, tren_id, vagon_id, posicion, fecha_inicio) VALUES (6, 2, 6, 3, TO_DATE('2026-01-01', 'YYYY-MM-DD'));
INSERT INTO TREN_VAGON (id_tren_vagon, tren_id, vagon_id, posicion, fecha_inicio) VALUES (7, 3, 7, 1, TO_DATE('2026-01-01', 'YYYY-MM-DD'));
INSERT INTO TREN_VAGON (id_tren_vagon, tren_id, vagon_id, posicion, fecha_inicio) VALUES (8, 3, 8, 2, TO_DATE('2026-01-01', 'YYYY-MM-DD'));
INSERT INTO TREN_VAGON (id_tren_vagon, tren_id, vagon_id, posicion, fecha_inicio) VALUES (9, 3, 9, 3, TO_DATE('2026-01-01', 'YYYY-MM-DD'));

-- 18. EMPLEADO
PROMPT 18/33. Insertando EMPLEADO...
INSERT INTO EMPLEADO (id_empleado, numero_empleado, nombre_completo, fecha_nacimiento, direccion, telefono, correo_electronico, fecha_contratacion, cargo, salario, estado_laboral, supervisor_id) VALUES (1, 'EMP-1001', 'Carlos Roberto Morales', TO_DATE('1978-04-12', 'YYYY-MM-DD'), '742 Evergreen Terrace, Brooklyn', '212-555-0101', 'cmorales@nyct.com', TO_DATE('2010-03-15', 'YYYY-MM-DD'), 'Operador de Control', 85000.00, 'Activo', NULL);
INSERT INTO EMPLEADO (id_empleado, numero_empleado, nombre_completo, fecha_nacimiento, direccion, telefono, correo_electronico, fecha_contratacion, cargo, salario, estado_laboral, supervisor_id) VALUES (2, 'EMP-1002', 'Sarah Jessica Miller', TO_DATE('1983-09-22', 'YYYY-MM-DD'), '125 W 42nd St, Manhattan', '212-555-0102', 'smiller@nyct.com', TO_DATE('2015-06-01', 'YYYY-MM-DD'), 'Supervisor de Estación', 68000.00, 'Activo', 1);
INSERT INTO EMPLEADO (id_empleado, numero_empleado, nombre_completo, fecha_nacimiento, direccion, telefono, correo_electronico, fecha_contratacion, cargo, salario, estado_laboral, supervisor_id) VALUES (3, 'EMP-1003', 'Anthony David Rossi', TO_DATE('1985-11-04', 'YYYY-MM-DD'), '450 Grand Concourse, Bronx', '212-555-0103', 'arossi@nyct.com', TO_DATE('2016-09-12', 'YYYY-MM-DD'), 'Supervisor de Estación', 68000.00, 'Activo', 1);
INSERT INTO EMPLEADO (id_empleado, numero_empleado, nombre_completo, fecha_nacimiento, direccion, telefono, correo_electronico, fecha_contratacion, cargo, salario, estado_laboral, supervisor_id) VALUES (4, 'EMP-2001', 'Michael John Sullivan', TO_DATE('1988-02-18', 'YYYY-MM-DD'), '88 Atlantic Ave, Brooklyn', '212-555-0201', 'msullivan@nyct.com', TO_DATE('2018-01-10', 'YYYY-MM-DD'), 'Conductor', 62000.00, 'Activo', 1);
INSERT INTO EMPLEADO (id_empleado, numero_empleado, nombre_completo, fecha_nacimiento, direccion, telefono, correo_electronico, fecha_contratacion, cargo, salario, estado_laboral, supervisor_id) VALUES (5, 'EMP-2002', 'Elena Maria Rodriguez', TO_DATE('1991-07-30', 'YYYY-MM-DD'), '34 Roosevelt Ave, Queens', '212-555-0202', 'erodriguez@nyct.com', TO_DATE('2019-04-15', 'YYYY-MM-DD'), 'Conductor', 62000.00, 'Activo', 1);
INSERT INTO EMPLEADO (id_empleado, numero_empleado, nombre_completo, fecha_nacimiento, direccion, telefono, correo_electronico, fecha_contratacion, cargo, salario, estado_laboral, supervisor_id) VALUES (6, 'EMP-2003', 'James Patrick O Connor', TO_DATE('1986-12-14', 'YYYY-MM-DD'), '52 Court St, Brooklyn', '212-555-0203', 'joconnor@nyct.com', TO_DATE('2017-08-20', 'YYYY-MM-DD'), 'Conductor', 64000.00, 'Activo', 1);
INSERT INTO EMPLEADO (id_empleado, numero_empleado, nombre_completo, fecha_nacimiento, direccion, telefono, correo_electronico, fecha_contratacion, cargo, salario, estado_laboral, supervisor_id) VALUES (7, 'EMP-3001', 'David Lee Chen', TO_DATE('1990-05-19', 'YYYY-MM-DD'), '108 Main St, Queens', '212-555-0301', 'dchen@nyct.com', TO_DATE('2018-11-05', 'YYYY-MM-DD'), 'Técnico de Mantenimiento', 58000.00, 'Activo', 1);
INSERT INTO EMPLEADO (id_empleado, numero_empleado, nombre_completo, fecha_nacimiento, direccion, telefono, correo_electronico, fecha_contratacion, cargo, salario, estado_laboral, supervisor_id) VALUES (8, 'EMP-3002', 'Marcus Dwayne Washington', TO_DATE('1993-08-08', 'YYYY-MM-DD'), '78 Fulton St, Manhattan', '212-555-0302', 'mwashington@nyct.com', TO_DATE('2020-02-17', 'YYYY-MM-DD'), 'Técnico de Mantenimiento', 56000.00, 'Activo', 1);
INSERT INTO EMPLEADO (id_empleado, numero_empleado, nombre_completo, fecha_nacimiento, direccion, telefono, correo_electronico, fecha_contratacion, cargo, salario, estado_laboral, supervisor_id) VALUES (9, 'EMP-4001', 'Robert Walter Briggs', TO_DATE('1987-10-10', 'YYYY-MM-DD'), '210 Union Sq, Manhattan', '212-555-0401', 'rbriggs@nyct.com', TO_DATE('2016-03-01', 'YYYY-MM-DD'), 'Agente de Seguridad', 48000.00, 'Activo', 2);
INSERT INTO EMPLEADO (id_empleado, numero_empleado, nombre_completo, fecha_nacimiento, direccion, telefono, correo_electronico, fecha_contratacion, cargo, salario, estado_laboral, supervisor_id) VALUES (10, 'EMP-4002', 'Jessica Ann Taylor', TO_DATE('1995-03-25', 'YYYY-MM-DD'), '15 Jay St, Brooklyn', '212-555-0402', 'jtaylor@nyct.com', TO_DATE('2021-05-10', 'YYYY-MM-DD'), 'Personal de Atención al Pasajero', 45000.00, 'Activo', 3);

-- 19. CERTIFICACION
PROMPT 19/33. Insertando CERTIFICACION...
INSERT INTO CERTIFICACION (id_certificacion, empleado_id, tipo_certificacion, fecha_emision, fecha_vencimiento, institucion_emisora, estado) VALUES (1, 4, 'Licencia Conducción Clase A Subterráneo', TO_DATE('2024-01-10', 'YYYY-MM-DD'), TO_DATE('2027-01-10', 'YYYY-MM-DD'), 'Federal Railroad Administration', 'Vigente');
INSERT INTO CERTIFICACION (id_certificacion, empleado_id, tipo_certificacion, fecha_emision, fecha_vencimiento, institucion_emisora, estado) VALUES (2, 5, 'Licencia Conducción Clase A Subterráneo', TO_DATE('2023-05-15', 'YYYY-MM-DD'), TO_DATE('2026-05-15', 'YYYY-MM-DD'), 'Federal Railroad Administration', 'Vigente');
INSERT INTO CERTIFICACION (id_certificacion, empleado_id, tipo_certificacion, fecha_emision, fecha_vencimiento, institucion_emisora, estado) VALUES (3, 6, 'Licencia Conducción Clase B Subterráneo', TO_DATE('2022-02-01', 'YYYY-MM-DD'), TO_DATE('2025-02-01', 'YYYY-MM-DD'), 'Federal Railroad Administration', 'Vencida');
INSERT INTO CERTIFICACION (id_certificacion, empleado_id, tipo_certificacion, fecha_emision, fecha_vencimiento, institucion_emisora, estado) VALUES (4, 7, 'Especialista en Sistemas Neumáticos y Frenos', TO_DATE('2023-08-20', 'YYYY-MM-DD'), TO_DATE('2026-08-20', 'YYYY-MM-DD'), 'MTA Maintenance Training Academy', 'Vigente');
INSERT INTO CERTIFICACION (id_certificacion, empleado_id, tipo_certificacion, fecha_emision, fecha_vencimiento, institucion_emisora, estado) VALUES (5, 8, 'Certificación en Señalización Ferroviaria CBTC', TO_DATE('2024-03-12', 'YYYY-MM-DD'), TO_DATE('2027-03-12', 'YYYY-MM-DD'), 'MTA Maintenance Training Academy', 'Vigente');

-- 20. CERTIFICACION_MODELO
PROMPT 20/33. Insertando CERTIFICACION_MODELO...
INSERT INTO CERTIFICACION_MODELO (id_certificacion_modelo, certificacion_id, modelo_id) VALUES (1, 1, 1);
INSERT INTO CERTIFICACION_MODELO (id_certificacion_modelo, certificacion_id, modelo_id) VALUES (2, 1, 2);
INSERT INTO CERTIFICACION_MODELO (id_certificacion_modelo, certificacion_id, modelo_id) VALUES (3, 2, 2);
INSERT INTO CERTIFICACION_MODELO (id_certificacion_modelo, certificacion_id, modelo_id) VALUES (4, 2, 4);

-- 21. TURNO
PROMPT 21/33. Insertando TURNO...
INSERT INTO TURNO (id_turno, codigo_turno, empleado_id, fecha, hora_inicio, hora_fin, tipo_lugar, lugar_id, funcion, estado_asistencia) VALUES (1, 'TUR-20260901-01', 4, TO_DATE('2026-09-01', 'YYYY-MM-DD'), TO_TIMESTAMP('2026-09-01 06:00:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-09-01 14:00:00', 'YYYY-MM-DD HH24:MI:SS'), 'Tren', 1, 'Conducción Línea 1', 'Presente');
INSERT INTO TURNO (id_turno, codigo_turno, empleado_id, fecha, hora_inicio, hora_fin, tipo_lugar, lugar_id, funcion, estado_asistencia) VALUES (2, 'TUR-20260901-02', 5, TO_DATE('2026-09-01', 'YYYY-MM-DD'), TO_TIMESTAMP('2026-09-01 07:00:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-09-01 15:00:00', 'YYYY-MM-DD HH24:MI:SS'), 'Tren', 3, 'Conducción Línea A', 'Presente');
INSERT INTO TURNO (id_turno, codigo_turno, empleado_id, fecha, hora_inicio, hora_fin, tipo_lugar, lugar_id, funcion, estado_asistencia) VALUES (3, 'TUR-20260901-03', 2, TO_DATE('2026-09-01', 'YYYY-MM-DD'), TO_TIMESTAMP('2026-09-01 06:00:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-09-01 14:00:00', 'YYYY-MM-DD HH24:MI:SS'), 'Estación', 1, 'Supervisión Turnstile & Andenes', 'Presente');
INSERT INTO TURNO (id_turno, codigo_turno, empleado_id, fecha, hora_inicio, hora_fin, tipo_lugar, lugar_id, funcion, estado_asistencia) VALUES (4, 'TUR-20260901-04', 7, TO_DATE('2026-09-01', 'YYYY-MM-DD'), TO_TIMESTAMP('2026-09-01 08:00:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-09-01 16:30:00', 'YYYY-MM-DD HH24:MI:SS'), 'Depósito', 3, 'Mantenimiento Preventivo R179', 'Presente');

-- 22. PASAJERO
PROMPT 22/33. Insertando PASAJERO...
INSERT INTO PASAJERO (id_pasajero, identificador, nombre, fecha_nacimiento, correo_electronico, telefono, tipo_pasajero, fecha_registro, estado) VALUES (1, 'PAS-001', 'Liam Noah Smith', TO_DATE('1992-06-14', 'YYYY-MM-DD'), 'liam.smith@gmail.com', '646-555-1101', 'Regular', TO_DATE('2024-02-10', 'YYYY-MM-DD'), 'Activo');
INSERT INTO PASAJERO (id_pasajero, identificador, nombre, fecha_nacimiento, correo_electronico, telefono, tipo_pasajero, fecha_registro, estado) VALUES (2, 'PAS-002', 'Emma Olivia Johnson', TO_DATE('1998-11-23', 'YYYY-MM-DD'), 'emma.j@nyu.edu', '646-555-1102', 'Estudiante', TO_DATE('2024-03-01', 'YYYY-MM-DD'), 'Activo');
INSERT INTO PASAJERO (id_pasajero, identificador, nombre, fecha_nacimiento, correo_electronico, telefono, tipo_pasajero, fecha_registro, estado) VALUES (3, 'PAS-003', 'Arthur Robert Goldberg', TO_DATE('1954-03-12', 'YYYY-MM-DD'), 'artie.gold@verizon.net', '646-555-1103', 'Adulto Mayor', TO_DATE('2023-11-15', 'YYYY-MM-DD'), 'Activo');
INSERT INTO PASAJERO (id_pasajero, identificador, nombre, fecha_nacimiento, correo_electronico, telefono, tipo_pasajero, fecha_registro, estado) VALUES (4, 'PAS-004', 'Sophia Isabella Cruz', TO_DATE('2000-09-05', 'YYYY-MM-DD'), 'sophia.cruz@columbia.edu', '646-555-1104', 'Persona con Discapacidad', TO_DATE('2024-01-20', 'YYYY-MM-DD'), 'Activo');
INSERT INTO PASAJERO (id_pasajero, identificador, nombre, fecha_nacimiento, correo_electronico, telefono, tipo_pasajero, fecha_registro, estado) VALUES (5, 'PAS-005', 'Benjamin Thomas Wilson', TO_DATE('1985-08-17', 'YYYY-MM-DD'), 'bwilson@finance.ny.gov', '646-555-1105', 'Regular', TO_DATE('2023-10-05', 'YYYY-MM-DD'), 'Activo');

-- 23. TARJETA
PROMPT 23/33. Insertando TARJETA (nominales y anónimas)...
INSERT INTO TARJETA (id_tarjeta, numero_tarjeta, pasajero_id, fecha_emision, fecha_vencimiento, saldo_disponible, tarifa_id, estado) VALUES (1, 'OMNY-1001-0001', 1, TO_DATE('2024-02-10', 'YYYY-MM-DD'), TO_DATE('2029-02-10', 'YYYY-MM-DD'), 28.50, 1, 'Activa');
INSERT INTO TARJETA (id_tarjeta, numero_tarjeta, pasajero_id, fecha_emision, fecha_vencimiento, saldo_disponible, tarifa_id, estado) VALUES (2, 'OMNY-1001-0002', 2, TO_DATE('2024-03-01', 'YYYY-MM-DD'), TO_DATE('2025-06-30', 'YYYY-MM-DD'), 12.00, 6, 'Activa');
INSERT INTO TARJETA (id_tarjeta, numero_tarjeta, pasajero_id, fecha_emision, fecha_vencimiento, saldo_disponible, tarifa_id, estado) VALUES (3, 'OMNY-1001-0003', 3, TO_DATE('2023-11-15', 'YYYY-MM-DD'), TO_DATE('2028-11-15', 'YYYY-MM-DD'), 18.25, 2, 'Activa');
INSERT INTO TARJETA (id_tarjeta, numero_tarjeta, pasajero_id, fecha_emision, fecha_vencimiento, saldo_disponible, tarifa_id, estado) VALUES (4, 'OMNY-1001-0004', 4, TO_DATE('2024-01-20', 'YYYY-MM-DD'), TO_DATE('2027-01-20', 'YYYY-MM-DD'), 45.00, 3, 'Activa');
INSERT INTO TARJETA (id_tarjeta, numero_tarjeta, pasajero_id, fecha_emision, fecha_vencimiento, saldo_disponible, tarifa_id, estado) VALUES (5, 'OMNY-1001-0005', 5, TO_DATE('2023-10-05', 'YYYY-MM-DD'), TO_DATE('2028-10-05', 'YYYY-MM-DD'), 0.00, 5, 'Activa');
INSERT INTO TARJETA (id_tarjeta, numero_tarjeta, pasajero_id, fecha_emision, fecha_vencimiento, saldo_disponible, tarifa_id, estado) VALUES (6, 'OMNY-1001-0006', 1, TO_DATE('2022-01-10', 'YYYY-MM-DD'), TO_DATE('2024-01-10', 'YYYY-MM-DD'), 0.00, 1, 'Vencida');
INSERT INTO TARJETA (id_tarjeta, numero_tarjeta, pasajero_id, fecha_emision, fecha_vencimiento, saldo_disponible, tarifa_id, estado) VALUES (7, 'OMNY-1001-0007', 5, TO_DATE('2024-05-01', 'YYYY-MM-DD'), TO_DATE('2029-05-01', 'YYYY-MM-DD'), 5.50, 1, 'Bloqueada');
-- Tarjetas ANÓNIMAS (pasajero_id = NULL)
INSERT INTO TARJETA (id_tarjeta, numero_tarjeta, pasajero_id, fecha_emision, fecha_vencimiento, saldo_disponible, tarifa_id, estado) VALUES (8, 'MC-ANON-9001', NULL, TO_DATE('2026-08-01', 'YYYY-MM-DD'), TO_DATE('2027-08-01', 'YYYY-MM-DD'), 20.00, 1, 'Activa');
INSERT INTO TARJETA (id_tarjeta, numero_tarjeta, pasajero_id, fecha_emision, fecha_vencimiento, saldo_disponible, tarifa_id, estado) VALUES (9, 'MC-ANON-9002', NULL, TO_DATE('2026-08-15', 'YYYY-MM-DD'), TO_DATE('2027-08-15', 'YYYY-MM-DD'), 8.70, 1, 'Activa');
INSERT INTO TARJETA (id_tarjeta, numero_tarjeta, pasajero_id, fecha_emision, fecha_vencimiento, saldo_disponible, tarifa_id, estado) VALUES (10, 'MC-ANON-9003', NULL, TO_DATE('2026-09-01', 'YYYY-MM-DD'), TO_DATE('2027-09-01', 'YYYY-MM-DD'), 30.00, 1, 'Activa');

-- 24. RECARGA
PROMPT 24/33. Insertando RECARGA...
INSERT INTO RECARGA (id_recarga, numero_transaccion, tarjeta_id, fecha_hora, monto, medio_pago, estacion_canal, saldo_anterior, saldo_posterior) VALUES (1, 'REC-20260901-001', 1, TO_TIMESTAMP('2026-09-01 07:15:00', 'YYYY-MM-DD HH24:MI:SS'), 20.00, 'Tarjeta Débito', 'Times Sq - 42 St', 8.50, 28.50);
INSERT INTO RECARGA (id_recarga, numero_transaccion, tarjeta_id, fecha_hora, monto, medio_pago, estacion_canal, saldo_anterior, saldo_posterior) VALUES (2, 'REC-20260901-002', 3, TO_TIMESTAMP('2026-09-01 08:30:00', 'YYYY-MM-DD HH24:MI:SS'), 10.00, 'Efectivo', 'Grand Central - 42 St', 8.25, 18.25);
INSERT INTO RECARGA (id_recarga, numero_transaccion, tarjeta_id, fecha_hora, monto, medio_pago, estacion_canal, saldo_anterior, saldo_posterior) VALUES (3, 'REC-20260901-003', 8, TO_TIMESTAMP('2026-09-01 09:00:00', 'YYYY-MM-DD HH24:MI:SS'), 20.00, 'Efectivo', 'Fulton St', 0.00, 20.00);
INSERT INTO RECARGA (id_recarga, numero_transaccion, tarjeta_id, fecha_hora, monto, medio_pago, estacion_canal, saldo_anterior, saldo_posterior) VALUES (4, 'REC-20260901-004', 5, TO_TIMESTAMP('2026-09-01 10:15:00', 'YYYY-MM-DD HH24:MI:SS'), 132.00, 'Tarjeta Crédito', 'App Móvil OMNY', 0.00, 0.00);

-- 25. EQUIPO
PROMPT 25/33. Insertando EQUIPO...
INSERT INTO EQUIPO (id_equipo, codigo_equipo, tipo_equipo, tipo_referencia, referencia_id, ubicacion, fabricante, modelo, estado, fecha_instalacion) VALUES (1, 'EQ-TRK-101', 'Vía', 'ESTACION', 1, 'Vía 1 Norte - Times Sq', 'Bethlehem Steel', '115RE Rail', 'Disponible', TO_DATE('2020-04-10', 'YYYY-MM-DD'));
INSERT INTO EQUIPO (id_equipo, codigo_equipo, tipo_equipo, tipo_referencia, referencia_id, ubicacion, fabricante, modelo, estado, fecha_instalacion) VALUES (2, 'EQ-SIG-202', 'Señal', 'ESTACION', 1, 'Interlocking 42nd St', 'Siemens', 'Trainguard MT', 'Disponible', TO_DATE('2021-08-15', 'YYYY-MM-DD'));
INSERT INTO EQUIPO (id_equipo, codigo_equipo, tipo_equipo, tipo_referencia, referencia_id, ubicacion, fabricante, modelo, estado, fecha_instalacion) VALUES (3, 'EQ-ELV-301', 'Elevador', 'ESTACION', 2, 'Acceso Principal 42 St / Lexington', 'Otis', 'Gen2 Premier', 'Disponible', TO_DATE('2019-11-20', 'YYYY-MM-DD'));
INSERT INTO EQUIPO (id_equipo, codigo_equipo, tipo_equipo, tipo_referencia, referencia_id, ubicacion, fabricante, modelo, estado, fecha_instalacion) VALUES (4, 'EQ-ESC-401', 'Escalera Eléctrica', 'ESTACION', 5, 'Mezzanine Fulton Center Sur', 'Schindler', '9300 Advanced', 'En Mantenimiento', TO_DATE('2018-06-12', 'YYYY-MM-DD'));
INSERT INTO EQUIPO (id_equipo, codigo_equipo, tipo_equipo, tipo_referencia, referencia_id, ubicacion, fabricante, modelo, estado, fecha_instalacion) VALUES (5, 'EQ-TRN-101', 'Tren', 'TREN', 1, 'Rame TR-101 Línea 1', 'Bombardier', 'R142', 'Disponible', TO_DATE('2018-05-15', 'YYYY-MM-DD'));
INSERT INTO EQUIPO (id_equipo, codigo_equipo, tipo_equipo, tipo_referencia, referencia_id, ubicacion, fabricante, modelo, estado, fecha_instalacion) VALUES (6, 'EQ-TRN-301', 'Tren', 'TREN', 5, 'Rame TR-301 Corona Yard', 'Bombardier', 'R179', 'En Mantenimiento', TO_DATE('2021-02-10', 'YYYY-MM-DD'));

-- 26. VIAJE_PROGRAMADO (Incluye viajes retrasados >15 min para la Consulta 5)
PROMPT 26/33. Insertando VIAJE_PROGRAMADO...
INSERT INTO VIAJE_PROGRAMADO (id_viaje, numero_viaje, ruta_id, horario_id, fecha, hora_prog_salida, hora_real_salida, hora_prog_llegada, hora_real_llegada, tren_id, conductor_id, estado, cantidad_estimada_pasajeros) VALUES (1, 'VJ-20260901-001', 1, 1, TO_DATE('2026-09-01', 'YYYY-MM-DD'), TO_TIMESTAMP('2026-09-01 07:00:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-09-01 07:02:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-09-01 07:45:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-09-01 07:47:00', 'YYYY-MM-DD HH24:MI:SS'), 1, 4, 'Completado', 850);
INSERT INTO VIAJE_PROGRAMADO (id_viaje, numero_viaje, ruta_id, horario_id, fecha, hora_prog_salida, hora_real_salida, hora_prog_llegada, hora_real_llegada, tren_id, conductor_id, estado, cantidad_estimada_pasajeros) VALUES (2, 'VJ-20260901-002', 3, 3, TO_DATE('2026-09-01', 'YYYY-MM-DD'), TO_TIMESTAMP('2026-09-01 07:30:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-09-01 07:55:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-09-01 08:16:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-09-01 08:44:00', 'YYYY-MM-DD HH24:MI:SS'), 3, 5, 'Retrasado', 980);
INSERT INTO VIAJE_PROGRAMADO (id_viaje, numero_viaje, ruta_id, horario_id, fecha, hora_prog_salida, hora_real_salida, hora_prog_llegada, hora_real_llegada, tren_id, conductor_id, estado, cantidad_estimada_pasajeros) VALUES (3, 'VJ-20260901-003', 4, 4, TO_DATE('2026-09-01', 'YYYY-MM-DD'), TO_TIMESTAMP('2026-09-01 08:00:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-09-01 08:01:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-09-01 08:27:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-09-01 08:29:00', 'YYYY-MM-DD HH24:MI:SS'), 2, 6, 'Completado', 720);
INSERT INTO VIAJE_PROGRAMADO (id_viaje, numero_viaje, ruta_id, horario_id, fecha, hora_prog_salida, hora_real_salida, hora_prog_llegada, hora_real_llegada, tren_id, conductor_id, estado, cantidad_estimada_pasajeros) VALUES (4, 'VJ-20260901-004', 1, 2, TO_DATE('2026-09-01', 'YYYY-MM-DD'), TO_TIMESTAMP('2026-09-01 10:00:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-09-01 10:00:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-09-01 10:45:00', 'YYYY-MM-DD HH24:MI:SS'), NULL, 1, 4, 'En Curso', 650);
INSERT INTO VIAJE_PROGRAMADO (id_viaje, numero_viaje, ruta_id, horario_id, fecha, hora_prog_salida, hora_real_salida, hora_prog_llegada, hora_real_llegada, tren_id, conductor_id, estado, cantidad_estimada_pasajeros) VALUES (5, 'VJ-20260901-005', 3, 3, TO_DATE('2026-09-01', 'YYYY-MM-DD'), TO_TIMESTAMP('2026-09-01 08:30:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-09-01 08:52:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-09-01 09:16:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-09-01 09:41:00', 'YYYY-MM-DD HH24:MI:SS'), 4, 5, 'Retrasado', 890);

-- 27. VIAJE_PASAJERO
PROMPT 27/33. Insertando VIAJE_PASAJERO...
INSERT INTO VIAJE_PASAJERO (id_viaje_pasajero, numero_transaccion, tarjeta_id, estacion_ingreso_id, fecha_hora_ingreso, estacion_salida_id, fecha_hora_salida, tarifa_id, monto_cobrado, viaje_programado_id, estado_transaccion) VALUES (1, 'TRX-20260901-0001', 1, 1, TO_TIMESTAMP('2026-09-01 07:10:00', 'YYYY-MM-DD HH24:MI:SS'), 6, TO_TIMESTAMP('2026-09-01 07:42:00', 'YYYY-MM-DD HH24:MI:SS'), 1, 2.90, 1, 'Cerrada');
INSERT INTO VIAJE_PASAJERO (id_viaje_pasajero, numero_transaccion, tarjeta_id, estacion_ingreso_id, fecha_hora_ingreso, estacion_salida_id, fecha_hora_salida, tarifa_id, monto_cobrado, viaje_programado_id, estado_transaccion) VALUES (2, 'TRX-20260901-0002', 2, 1, TO_TIMESTAMP('2026-09-01 07:25:00', 'YYYY-MM-DD HH24:MI:SS'), 8, TO_TIMESTAMP('2026-09-01 08:05:00', 'YYYY-MM-DD HH24:MI:SS'), 6, 0.00, 2, 'Cerrada');
INSERT INTO VIAJE_PASAJERO (id_viaje_pasajero, numero_transaccion, tarjeta_id, estacion_ingreso_id, fecha_hora_ingreso, estacion_salida_id, fecha_hora_salida, tarifa_id, monto_cobrado, viaje_programado_id, estado_transaccion) VALUES (3, 'TRX-20260901-0003', 3, 2, TO_TIMESTAMP('2026-09-01 08:15:00', 'YYYY-MM-DD HH24:MI:SS'), 10, TO_TIMESTAMP('2026-09-01 08:40:00', 'YYYY-MM-DD HH24:MI:SS'), 2, 1.45, 3, 'Cerrada');
INSERT INTO VIAJE_PASAJERO (id_viaje_pasajero, numero_transaccion, tarjeta_id, estacion_ingreso_id, fecha_hora_ingreso, estacion_salida_id, fecha_hora_salida, tarifa_id, monto_cobrado, viaje_programado_id, estado_transaccion) VALUES (4, 'TRX-20260901-0004', 8, 5, TO_TIMESTAMP('2026-09-01 08:45:00', 'YYYY-MM-DD HH24:MI:SS'), 11, TO_TIMESTAMP('2026-09-01 09:20:00', 'YYYY-MM-DD HH24:MI:SS'), 1, 2.90, 2, 'Cerrada');
INSERT INTO VIAJE_PASAJERO (id_viaje_pasajero, numero_transaccion, tarjeta_id, estacion_ingreso_id, fecha_hora_ingreso, estacion_salida_id, fecha_hora_salida, tarifa_id, monto_cobrado, viaje_programado_id, estado_transaccion) VALUES (5, 'TRX-20260901-0005', 9, 3, TO_TIMESTAMP('2026-09-01 09:10:00', 'YYYY-MM-DD HH24:MI:SS'), NULL, NULL, 1, 2.90, NULL, 'Abierta');

-- 28. ORDEN_MANTENIMIENTO
PROMPT 28/33. Insertando ORDEN_MANTENIMIENTO...
INSERT INTO ORDEN_MANTENIMIENTO (id_orden, numero_orden, equipo_id, tipo_mantenimiento, descripcion_trabajo, fecha_solicitud, fecha_programada, fecha_inicio, fecha_finalizacion, prioridad, costo, estado) VALUES (1, 'ORD-2026-001', 6, 'Preventivo', 'Inspección de 75,000 km, recambio de zapatas y filtros HVAC', TO_DATE('2026-08-20', 'YYYY-MM-DD'), TO_DATE('2026-08-25', 'YYYY-MM-DD'), TO_DATE('2026-08-26', 'YYYY-MM-DD'), NULL, 'Media', 1200.00, 'En Ejecución');
INSERT INTO ORDEN_MANTENIMIENTO (id_orden, numero_orden, equipo_id, tipo_mantenimiento, descripcion_trabajo, fecha_solicitud, fecha_programada, fecha_inicio, fecha_finalizacion, prioridad, costo, estado) VALUES (2, 'ORD-2026-002', 4, 'Correctivo', 'Reparación de motor de tracción y alineación de peldaños', TO_DATE('2026-08-28', 'YYYY-MM-DD'), TO_DATE('2026-08-30', 'YYYY-MM-DD'), TO_DATE('2026-08-30', 'YYYY-MM-DD'), NULL, 'Alta', 2400.00, 'En Ejecución');
INSERT INTO ORDEN_MANTENIMIENTO (id_orden, numero_orden, equipo_id, tipo_mantenimiento, descripcion_trabajo, fecha_solicitud, fecha_programada, fecha_inicio, fecha_finalizacion, prioridad, costo, estado) VALUES (3, 'ORD-2026-003', 2, 'Inspección de Seguridad', 'Verificación semestral de transpondedores CBTC en vía 1', TO_DATE('2026-08-01', 'YYYY-MM-DD'), TO_DATE('2026-08-05', 'YYYY-MM-DD'), TO_DATE('2026-08-05', 'YYYY-MM-DD'), TO_DATE('2026-08-05', 'YYYY-MM-DD'), 'Baja', 450.00, 'Completada');

-- 29. ORDEN_TECNICO
PROMPT 29/33. Insertando ORDEN_TECNICO...
INSERT INTO ORDEN_TECNICO (id_orden_tecnico, orden_id, empleado_id, rol_en_orden) VALUES (1, 1, 7, 'Técnico Mecánico Principal');
INSERT INTO ORDEN_TECNICO (id_orden_tecnico, orden_id, empleado_id, rol_en_orden) VALUES (2, 2, 8, 'Técnico Especialista');
INSERT INTO ORDEN_TECNICO (id_orden_tecnico, orden_id, empleado_id, rol_en_orden) VALUES (3, 3, 7, 'Inspector de Vía y Señales');

-- 30. ORDEN_REPUESTO
PROMPT 30/33. Insertando ORDEN_REPUESTO...
INSERT INTO ORDEN_REPUESTO (id_orden_repuesto, orden_id, repuesto_id, cantidad, costo_total) VALUES (1, 1, 1, 8, 1164.00);
INSERT INTO ORDEN_REPUESTO (id_orden_repuesto, orden_id, repuesto_id, cantidad, costo_total) VALUES (2, 1, 5, 4, 260.00);
INSERT INTO ORDEN_REPUESTO (id_orden_repuesto, orden_id, repuesto_id, cantidad, costo_total) VALUES (3, 2, 8, 1, 1250.00);

-- 31. INCIDENTE
PROMPT 31/33. Insertando INCIDENTE...
INSERT INTO INCIDENTE (id_incidente, numero_incidente, tipo, descripcion, fecha_hora_inicio, fecha_hora_fin, nivel_severidad, reportado_por_id, estado, causa_identificada, acciones_realizadas, pasajeros_afectados_estimado) VALUES (1, 'INC-20260901-01', 'Falla de Señalización', 'Falla intermitente en circuito de vía en aproximación a Times Square', TO_TIMESTAMP('2026-09-01 07:20:00', 'YYYY-MM-DD HH24:MI:SS'), NULL, 'Alto', 5, 'Abierto', 'Sobrevoltaje en tablero de relé de señal', 'Cuadrilla técnica en sitio, operación a velocidad reducida', 2500);
INSERT INTO INCIDENTE (id_incidente, numero_incidente, tipo, descripcion, fecha_hora_inicio, fecha_hora_fin, nivel_severidad, reportado_por_id, estado, causa_identificada, acciones_realizadas, pasajeros_afectados_estimado) VALUES (2, 'INC-20260901-02', 'Falla Mecánica', 'Avería de compresor de frenos en tren TR-301', TO_TIMESTAMP('2026-09-01 08:15:00', 'YYYY-MM-DD HH24:MI:SS'), NULL, 'Medio', 4, 'En Atención', 'Fuga de aire en manguera flexible', 'Tren retirado a vía secundaria de servicio', 800);
INSERT INTO INCIDENTE (id_incidente, numero_incidente, tipo, descripcion, fecha_hora_inicio, fecha_hora_fin, nivel_severidad, reportado_por_id, estado, causa_identificada, acciones_realizadas, pasajeros_afectados_estimado) VALUES (3, 'INC-20260830-01', 'Objeto en la Vía', 'Basura metálica provocando arco en tercer riel', TO_TIMESTAMP('2026-08-30 14:10:00', 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP('2026-08-30 14:35:00', 'YYYY-MM-DD HH24:MI:SS'), 'Bajo', 2, 'Cerrado', 'Restos de andamio de construcción', 'Corte de energía por 15 min y retiro de escombros', 450);

-- 32. INCIDENTE_ELEMENTO_AFECTADO (Arco Exclusivo con FK real)
PROMPT 32/33. Insertando INCIDENTE_ELEMENTO_AFECTADO (Arco Exclusivo con FK)...
INSERT INTO INCIDENTE_ELEMENTO_AFECTADO (id_incidente_elemento, incidente_id, tipo_elemento, estacion_id, tren_id, ruta_id, equipo_id, viaje_id, linea_id, tipo_afectacion) VALUES (1, 1, 'ESTACION', 1, NULL, NULL, NULL, NULL, NULL, 'Retraso');
INSERT INTO INCIDENTE_ELEMENTO_AFECTADO (id_incidente_elemento, incidente_id, tipo_elemento, estacion_id, tren_id, ruta_id, equipo_id, viaje_id, linea_id, tipo_afectacion) VALUES (2, 1, 'RUTA', NULL, NULL, 3, NULL, NULL, NULL, 'Retraso');
INSERT INTO INCIDENTE_ELEMENTO_AFECTADO (id_incidente_elemento, incidente_id, tipo_elemento, estacion_id, tren_id, ruta_id, equipo_id, viaje_id, linea_id, tipo_afectacion) VALUES (3, 2, 'TREN', NULL, 5, NULL, NULL, NULL, NULL, 'Retiro de Tren');

-- 33. BITACORA
PROMPT 33/33. Insertando BITACORA...
INSERT INTO BITACORA (id_bitacora, fecha_hora, tabla_afectada, operacion, registro_id, usuario, descripcion) VALUES (1, TO_TIMESTAMP('2026-09-01 06:00:00', 'YYYY-MM-DD HH24:MI:SS'), 'VIAJE_PROGRAMADO', 'INSERT', 1, 'SISTEMA_METRO', 'Programación inicial de viaje VJ-20260901-001');
INSERT INTO BITACORA (id_bitacora, fecha_hora, tabla_afectada, operacion, registro_id, usuario, descripcion) VALUES (2, TO_TIMESTAMP('2026-09-01 07:20:00', 'YYYY-MM-DD HH24:MI:SS'), 'INCIDENTE', 'INSERT', 1, 'CCO_MORALES', 'Registro de falla de señalización INC-20260901-01');
INSERT INTO BITACORA (id_bitacora, fecha_hora, tabla_afectada, operacion, registro_id, usuario, descripcion) VALUES (3, TO_TIMESTAMP('2026-09-01 07:55:00', 'YYYY-MM-DD HH24:MI:SS'), 'VIAJE_PROGRAMADO', 'UPDATE', 2, 'SISTEMA_METRO', 'Cambio de estado a Retrasado (demora de 25 min)');

PROMPT ====================================================================
PROMPT Sincronizando secuencias para evitar colisiones en futuros inserts...
PROMPT ====================================================================
DECLARE
    v_val NUMBER;
    PROCEDURE avanzar_secuencia(p_seq VARCHAR2, p_veces NUMBER) IS
    BEGIN
        FOR i IN 1..p_veces LOOP
            EXECUTE IMMEDIATE 'SELECT ' || p_seq || '.NEXTVAL FROM DUAL' INTO v_val;
        END LOOP;
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
BEGIN
    avanzar_secuencia('SEQ_LINEA', 10);
    avanzar_secuencia('SEQ_ESTACION', 20);
    avanzar_secuencia('SEQ_HORARIO_ESTACION', 20);
    avanzar_secuencia('SEQ_PLATAFORMA', 20);
    avanzar_secuencia('SEQ_ESTACION_SERVICIO', 20);
    avanzar_secuencia('SEQ_TRANSFERENCIA', 10);
    avanzar_secuencia('SEQ_RUTA', 10);
    avanzar_secuencia('SEQ_RUTA_DETALLE', 20);
    avanzar_secuencia('SEQ_HORARIO', 10);
    avanzar_secuencia('SEQ_MODELO_TREN', 10);
    avanzar_secuencia('SEQ_DEPOSITO', 10);
    avanzar_secuencia('SEQ_TREN', 15);
    avanzar_secuencia('SEQ_VAGON', 30);
    avanzar_secuencia('SEQ_TREN_VAGON', 20);
    avanzar_secuencia('SEQ_EMPLEADO', 20);
    avanzar_secuencia('SEQ_CERTIFICACION', 10);
    avanzar_secuencia('SEQ_CERTIFICACION_MODELO', 10);
    avanzar_secuencia('SEQ_TURNO', 10);
    avanzar_secuencia('SEQ_PASAJERO', 20);
    avanzar_secuencia('SEQ_TARJETA', 20);
    avanzar_secuencia('SEQ_RECARGA', 10);
    avanzar_secuencia('SEQ_TARIFA', 10);
    avanzar_secuencia('SEQ_VIAJE_PROGRAMADO', 20);
    avanzar_secuencia('SEQ_VIAJE_PASAJERO', 20);
    avanzar_secuencia('SEQ_EQUIPO', 15);
    avanzar_secuencia('SEQ_ORDEN_MANTENIMIENTO', 10);
    avanzar_secuencia('SEQ_ORDEN_TECNICO', 10);
    avanzar_secuencia('SEQ_REPUESTO', 20);
    avanzar_secuencia('SEQ_ORDEN_REPUESTO', 10);
    avanzar_secuencia('SEQ_INCIDENTE', 10);
    avanzar_secuencia('SEQ_INCIDENTE_ELEMENTO_AF_F066', 10);
    avanzar_secuencia('SEQ_BITACORA', 10);
END;
/

COMMIT;

PROMPT ====================================================================
PROMPT ¡Carga de datos de prueba completada exitosamente! (33 tablas)
PROMPT Todos los cambios han sido confirmados con COMMIT.
PROMPT ====================================================================

EXIT;
