-- ======================================================================
-- SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]
-- Script de Enriquecimiento Masivo de Datos del Catalogo Real MTA
-- Archivo: database/scripts/mta_massive_enrichment.sql
-- Cobertura:
--   - 24+ Lineas: IRT 1-7, BMT/IND A, B, C, D, E, F, G, J, L, M, N, Q, R, W, Z,
--                 Shuttles (S-42nd, SF-Franklin, SR-Rockaway), SIR (Staten Island).
--   - 45 Estaciones representativas de los 5 distritos de Nueva York:
--     Manhattan (14), Brooklyn (11), Queens (9), The Bronx (7), Staten Island (4).
--     Con coordenadas GPS reales, plataformas, y conexiones intermodales.
--   - Flota de 24 trenes con modelos reales (R142, R160, R179, R188, R211, R68)
--     y depósitos reales (207th St, Coney Island, Corona, 239th St, Jamaica Yard).
--     Incluye tren 'TR-01' garantizado.
--   - Mapeo polimorfico 1:1 en EQUIPO para el 100% de la flota de trenes.
--   - Plantilla de 36 empleados con cargos oficiales MTA y certificaciones tecnicas vigentes.
--   - Sincronizacion dinamica de secuencias via SP_SINCRONIZAR_TODAS_SECUENCIAS.
-- ======================================================================

SET DEFINE OFF;
SET SERVEROUTPUT ON;
SET SQLBLANKLINES ON;
ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD';
ALTER SESSION SET NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS';

PROMPT ======================================================================
PROMPT INICIANDO ENRIQUECIMIENTO MASIVO DEL CATALOGO MTA NYCT...
PROMPT ======================================================================

-- ----------------------------------------------------------------------
-- 1. MODELOS DE TREN (MODELO_TREN)
-- ----------------------------------------------------------------------
PROMPT [1/10] Enriqueciendo MODELO_TREN...
MERGE INTO MODELO_TREN t
USING (
    SELECT 1 AS id_modelo, 'R142' AS nombre_modelo, 'Bombardier Transportation' AS fabricante FROM DUAL UNION ALL
    SELECT 2, 'R160', 'Alstom / Kawasaki Heavy Industries' FROM DUAL UNION ALL
    SELECT 3, 'R179', 'Bombardier Transportation' FROM DUAL UNION ALL
    SELECT 4, 'R211', 'Kawasaki Rail Car' FROM DUAL UNION ALL
    SELECT 5, 'R188', 'Kawasaki Heavy Industries' FROM DUAL UNION ALL
    SELECT 6, 'R68', 'Westinghouse / Amrail / Kawasaki' FROM DUAL
) s ON (t.nombre_modelo = s.nombre_modelo)
WHEN MATCHED THEN
    UPDATE SET t.fabricante = s.fabricante
WHEN NOT MATCHED THEN
    INSERT (id_modelo, nombre_modelo, fabricante)
    VALUES (s.id_modelo, s.nombre_modelo, s.fabricante);

-- ----------------------------------------------------------------------
-- 2. DEPOSITOS Y TALLERES (DEPOSITO)
-- ----------------------------------------------------------------------
PROMPT [2/10] Enriqueciendo DEPOSITO...
MERGE INTO DEPOSITO t
USING (
    SELECT 1 AS id_deposito, 'DEP-207' AS codigo, '207th Street Yard' AS nombre, 'Inwood, Manhattan (10th Ave & 207th St)' AS ubicacion, 35 AS capacidad FROM DUAL UNION ALL
    SELECT 2, 'DEP-CI', 'Coney Island Overhaul Yard', 'Avenue X, Brooklyn', 60 FROM DUAL UNION ALL
    SELECT 3, 'DEP-COR', 'Corona Yard', 'Flushing Meadows, Queens', 28 FROM DUAL UNION ALL
    SELECT 4, 'DEP-239', '239th Street Yard', 'Wakefield, The Bronx', 30 FROM DUAL UNION ALL
    SELECT 5, 'DEP-JAM', 'Jamaica Yard', 'Forest Hills / Kew Gardens, Queens', 45 FROM DUAL
) s ON (t.codigo = s.codigo)
WHEN MATCHED THEN
    UPDATE SET t.nombre = s.nombre, t.ubicacion = s.ubicacion, t.capacidad = s.capacidad
WHEN NOT MATCHED THEN
    INSERT (id_deposito, codigo, nombre, ubicacion, capacidad)
    VALUES (s.id_deposito, s.codigo, s.nombre, s.ubicacion, s.capacidad);

-- ----------------------------------------------------------------------
-- 3. ESTACIONES EMBLEMATICAS (ESTACION - 45 ESTACIONES EN 5 DISTRITOS)
-- ----------------------------------------------------------------------
PROMPT [3/10] Enriqueciendo ESTACION (5 Distritos)...
MERGE INTO ESTACION t
USING (
    -- Manhattan (Existentes + Nuevas)
    SELECT 1 AS id_estacion, 'TSQ42' AS codigo, 'Times Sq - 42 St' AS nombre, 'Broadway & 42nd St' AS direccion, 'Manhattan' AS distrito, 40.7559 AS latitud, -73.9871 AS longitud, TO_DATE('1904-10-27','YYYY-MM-DD') AS fecha_inauguracion, 14 AS accesos, 4 AS plat, 'Operativa' AS estado, '24 horas' AS horario, 'S' AS elev, 'S' AS esc, 'S' AS acc, 'Transferencia' AS tipo FROM DUAL UNION ALL
    SELECT 2, 'GCT42', 'Grand Central - 42 St', 'Park Ave & 42nd St', 'Manhattan', 40.7517, -73.9768, TO_DATE('1904-10-27','YYYY-MM-DD'), 12, 4, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 3, '14USQ', '14 St - Union Sq', 'Broadway & 14th St', 'Manhattan', 40.7359, -73.9906, TO_DATE('1904-10-27','YYYY-MM-DD'), 10, 4, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 4, 'W4ST', 'W 4 St - Washington Sq', '6th Ave & W 4th St', 'Manhattan', 40.7310, -74.0003, TO_DATE('1932-09-10','YYYY-MM-DD'), 8, 4, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 5, 'FLTN', 'Fulton St', 'Fulton St & Broadway', 'Manhattan', 40.7103, -74.0076, TO_DATE('1905-01-16','YYYY-MM-DD'), 16, 6, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 6, 'BCH', 'Brooklyn Bridge - City Hall', 'Centre St & Chambers St', 'Manhattan', 40.7130, -74.0041, TO_DATE('1904-10-27','YYYY-MM-DD'), 6, 2, 'Operativa', '24 horas', 'S', 'N', 'S', 'Terminal' FROM DUAL UNION ALL
    SELECT 13, 'PENN34', '34 St - Penn Station', '7th Ave & 34th St', 'Manhattan', 40.7506, -73.9935, TO_DATE('1910-11-27','YYYY-MM-DD'), 18, 4, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 14, '59COL', '59 St - Columbus Circle', 'Broadway & 59th St', 'Manhattan', 40.7683, -73.9819, TO_DATE('1904-10-27','YYYY-MM-DD'), 12, 4, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 15, '125HAR', '125 St - Harlem', 'Lenox Ave & 125th St', 'Manhattan', 40.8041, -73.9376, TO_DATE('1904-11-23','YYYY-MM-DD'), 8, 2, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 16, 'WALL', 'Wall St', 'Broadway & Wall St', 'Manhattan', 40.7076, -74.0090, TO_DATE('1905-06-12','YYYY-MM-DD'), 6, 2, 'Operativa', '24 horas', 'S', 'N', 'S', 'Expresa' FROM DUAL UNION ALL
    SELECT 17, 'CANAL', 'Canal St', 'Broadway & Canal St', 'Manhattan', 40.7188, -74.0018, TO_DATE('1904-10-27','YYYY-MM-DD'), 10, 4, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 18, 'SFERRY', 'South Ferry - Whitehall St', 'State St & Whitehall St', 'Manhattan', 40.7014, -74.0130, TO_DATE('1905-07-10','YYYY-MM-DD'), 8, 2, 'Operativa', '24 horas', 'S', 'S', 'S', 'Terminal' FROM DUAL UNION ALL
    SELECT 19, '72ND2', '72 St - 2nd Av', '2nd Ave & 72nd St', 'Manhattan', 40.7688, -73.9584, TO_DATE('2017-01-01','YYYY-MM-DD'), 6, 2, 'Operativa', '24 horas', 'S', 'S', 'S', 'Expresa' FROM DUAL UNION ALL
    SELECT 20, 'INW207', 'Inwood - 207 St', 'Broadway & 207th St', 'Manhattan', 40.8681, -73.9199, TO_DATE('1932-09-10','YYYY-MM-DD'), 6, 2, 'Operativa', '24 horas', 'S', 'N', 'S', 'Terminal' FROM DUAL UNION ALL

    -- Brooklyn (Existentes + Nuevas)
    SELECT 7, 'ATL', 'Atlantic Av - Barclays Ctr', 'Flatbush Ave & Atlantic Ave', 'Brooklyn', 40.6844, -73.9786, TO_DATE('1908-05-01','YYYY-MM-DD'), 11, 6, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 8, 'JAY', 'Jay St - MetroTech', 'Jay St & Willoughby St', 'Brooklyn', 40.6923, -73.9873, TO_DATE('1933-02-01','YYYY-MM-DD'), 7, 3, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 11, 'CONEY', 'Coney Island - Stillwell Av', 'Surf Ave & Stillwell Ave', 'Brooklyn', 40.5771, -73.9812, TO_DATE('1919-05-30','YYYY-MM-DD'), 6, 8, 'Operativa', '24 horas', 'S', 'N', 'S', 'Terminal' FROM DUAL UNION ALL
    SELECT 21, 'BOHALL', 'Court St - Borough Hall', 'Court St & Joralemon St', 'Brooklyn', 40.6934, -73.9903, TO_DATE('1908-01-09','YYYY-MM-DD'), 8, 4, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 22, 'DEKALB', 'DeKalb Av', 'Flatbush Ave Ext & DeKalb Ave', 'Brooklyn', 40.6906, -73.9818, TO_DATE('1920-08-01','YYYY-MM-DD'), 8, 6, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 23, 'BEDNOST', 'Bedford - Nostrand Avs', 'Lafayette Ave & Bedford Ave', 'Brooklyn', 40.6896, -73.9535, TO_DATE('1937-07-01','YYYY-MM-DD'), 4, 2, 'Operativa', '24 horas', 'N', 'N', 'N', 'Local' FROM DUAL UNION ALL
    SELECT 24, 'FRKFULT', 'Franklin Av - Fulton St', 'Franklin Ave & Fulton St', 'Brooklyn', 40.6806, -73.9559, TO_DATE('1936-04-09','YYYY-MM-DD'), 6, 4, 'Operativa', '24 horas', 'S', 'N', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 25, 'CRWNUT', 'Crown Hts - Utica Av', 'Eastern Pkwy & Utica Ave', 'Brooklyn', 40.6689, -73.9321, TO_DATE('1920-08-23','YYYY-MM-DD'), 8, 4, 'Operativa', '24 horas', 'S', 'S', 'S', 'Terminal' FROM DUAL UNION ALL
    SELECT 26, 'CHURAV', 'Church Av', 'Nostrand Ave & Church Ave', 'Brooklyn', 40.6508, -73.9496, TO_DATE('1920-08-23','YYYY-MM-DD'), 6, 2, 'Operativa', '24 horas', 'S', 'N', 'S', 'Expresa' FROM DUAL UNION ALL
    SELECT 27, 'BRIGHT', 'Brighton Beach', 'Brighton Beach Ave & Brighton 6th St', 'Brooklyn', 40.5776, -73.9614, TO_DATE('1917-04-22','YYYY-MM-DD'), 6, 4, 'Operativa', '24 horas', 'S', 'N', 'S', 'Expresa' FROM DUAL UNION ALL
    SELECT 28, 'CANROC', 'Canarsie - Rockaway Pkwy', 'Rockaway Pkwy & Glenwood Rd', 'Brooklyn', 40.6467, -73.9019, TO_DATE('1906-12-28','YYYY-MM-DD'), 4, 2, 'Operativa', '24 horas', 'S', 'N', 'S', 'Terminal' FROM DUAL UNION ALL

    -- Queens (Existentes + Nuevas)
    SELECT 9, 'QBORO', 'Queensboro Plaza', 'Queens Plaza & 27th St', 'Queens', 40.7506, -73.9402, TO_DATE('1916-11-05','YYYY-MM-DD'), 5, 2, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 10, 'FLSH', 'Flushing - Main St', 'Main St & Roosevelt Ave', 'Queens', 40.7596, -73.8300, TO_DATE('1928-01-21','YYYY-MM-DD'), 8, 2, 'Operativa', '24 horas', 'S', 'S', 'S', 'Terminal' FROM DUAL UNION ALL
    SELECT 29, 'JKSNRV', 'Jackson Hts - Roosevelt Av', 'Roosevelt Ave & 74th St', 'Queens', 40.7466, -73.8913, TO_DATE('1933-08-19','YYYY-MM-DD'), 10, 4, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 30, 'CRTSQ', 'Court Sq - 23 St', 'Jackson Ave & 23rd St', 'Queens', 40.7471, -73.9453, TO_DATE('1933-08-19','YYYY-MM-DD'), 8, 4, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 31, 'FORH71', 'Forest Hills - 71 Av', 'Queens Blvd & 71st Ave', 'Queens', 40.7214, -73.8445, TO_DATE('1936-12-31','YYYY-MM-DD'), 8, 4, 'Operativa', '24 horas', 'S', 'S', 'S', 'Expresa' FROM DUAL UNION ALL
    SELECT 32, 'JAMCTR', 'Jamaica Center - Parsons/Archer', 'Parsons Blvd & Archer Ave', 'Queens', 40.7021, -73.7997, TO_DATE('1988-12-11','YYYY-MM-DD'), 8, 2, 'Operativa', '24 horas', 'S', 'S', 'S', 'Terminal' FROM DUAL UNION ALL
    SELECT 33, 'ASTDIT', 'Astoria - Ditmars Blvd', '31st St & Ditmars Blvd', 'Queens', 40.7750, -73.9120, TO_DATE('1917-02-01','YYYY-MM-DD'), 6, 2, 'Operativa', '24 horas', 'S', 'N', 'S', 'Terminal' FROM DUAL UNION ALL
    SELECT 34, 'HOWJFK', 'Howard Beach - JFK Airport', 'Coleman Sq & 159th Ave', 'Queens', 40.6605, -73.8306, TO_DATE('1956-06-28','YYYY-MM-DD'), 6, 2, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 35, 'RCKB116', 'Rockaway Park - Beach 116 St', 'Beach 116th St & Newport Ave', 'Queens', 40.5809, -73.8373, TO_DATE('1956-06-28','YYYY-MM-DD'), 4, 2, 'Operativa', '24 horas', 'S', 'N', 'S', 'Terminal' FROM DUAL UNION ALL

    -- The Bronx (Existentes + Nuevas)
    SELECT 12, 'VDCRT', 'Van Cortlandt Park - 242 St', 'Broadway & 242nd St', 'The Bronx', 40.8892, -73.8986, TO_DATE('1908-08-01','YYYY-MM-DD'), 4, 2, 'Operativa', '24 horas', 'N', 'N', 'N', 'Terminal' FROM DUAL UNION ALL
    SELECT 36, 'YANK161', '161 St - Yankee Stadium', 'River Ave & 161st St', 'The Bronx', 40.8279, -73.9257, TO_DATE('1917-06-02','YYYY-MM-DD'), 10, 4, 'Operativa', '24 horas', 'S', 'S', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 37, 'PELPK', 'Pelham Bay Park', 'Bruckner Blvd & Westchester Ave', 'The Bronx', 40.8525, -73.8275, TO_DATE('1920-12-20','YYYY-MM-DD'), 6, 2, 'Operativa', '24 horas', 'S', 'S', 'S', 'Terminal' FROM DUAL UNION ALL
    SELECT 38, 'WAKE241', 'Wakefield - 241 St', 'White Plains Rd & 241st St', 'The Bronx', 40.9031, -73.8506, TO_DATE('1920-12-13','YYYY-MM-DD'), 6, 2, 'Operativa', '24 horas', 'S', 'N', 'S', 'Terminal' FROM DUAL UNION ALL
    SELECT 39, 'FORDRD', 'Fordham Rd', 'Grand Concourse & Fordham Rd', 'The Bronx', 40.8613, -73.8977, TO_DATE('1933-07-01','YYYY-MM-DD'), 8, 4, 'Operativa', '24 horas', 'S', 'S', 'S', 'Expresa' FROM DUAL UNION ALL
    SELECT 40, 'THRD149', 'Third Av - 149 St', '3rd Ave & 149th St', 'The Bronx', 40.8161, -73.9178, TO_DATE('1905-07-10','YYYY-MM-DD'), 6, 2, 'Operativa', '24 horas', 'S', 'N', 'S', 'Transferencia' FROM DUAL UNION ALL
    SELECT 41, 'NORW205', 'Norwood - 205 St', 'Bainbridge Ave & 206th St', 'The Bronx', 40.8749, -73.8789, TO_DATE('1933-10-28','YYYY-MM-DD'), 4, 2, 'Operativa', '24 horas', 'N', 'N', 'N', 'Terminal' FROM DUAL UNION ALL

    -- Staten Island (MANDATORIO: St. George, Tompkinsville, Clifton, Tottenville)
    SELECT 42, 'STGEO', 'St. George', '1 Ferry Terminal', 'Staten Island', 40.6437, -74.0736, TO_DATE('1886-03-07','YYYY-MM-DD'), 8, 4, 'Operativa', '24 horas', 'S', 'S', 'S', 'Terminal' FROM DUAL UNION ALL
    SELECT 43, 'TOMPK', 'Tompkinsville', 'Victory Blvd & Bay St', 'Staten Island', 40.6358, -74.0748, TO_DATE('1884-07-31','YYYY-MM-DD'), 4, 2, 'Operativa', '24 horas', 'S', 'N', 'S', 'Local' FROM DUAL UNION ALL
    SELECT 44, 'CLIFT', 'Clifton', 'Bay St & Townsend Ave', 'Staten Island', 40.6213, -74.0714, TO_DATE('1860-04-23','YYYY-MM-DD'), 4, 2, 'Operativa', '24 horas', 'N', 'N', 'N', 'Local' FROM DUAL UNION ALL
    SELECT 45, 'TOTTEN', 'Tottenville', 'Main St & Arthur Kill Rd', 'Staten Island', 40.5128, -74.2520, TO_DATE('1860-06-02','YYYY-MM-DD'), 4, 2, 'Operativa', '24 horas', 'S', 'N', 'S', 'Terminal' FROM DUAL
) s ON (t.codigo = s.codigo)
WHEN MATCHED THEN
    UPDATE SET t.nombre = s.nombre, t.direccion = s.direccion, t.distrito = s.distrito,
               t.latitud = s.latitud, t.longitud = s.longitud, t.cantidad_accesos = s.accesos,
               t.cantidad_plataformas = s.plat, t.estado_operativo = s.estado,
               t.horario_funcionamiento = s.horario, t.elevadores_disponibles = s.elev,
               t.escaleras_electricas_disponibles = s.esc, t.accesible_discapacidad = s.acc,
               t.tipo_estacion = s.tipo
WHEN NOT MATCHED THEN
    INSERT (id_estacion, codigo, nombre, direccion, distrito, latitud, longitud, fecha_inauguracion, cantidad_accesos, cantidad_plataformas, estado_operativo, horario_funcionamiento, elevadores_disponibles, escaleras_electricas_disponibles, accesible_discapacidad, tipo_estacion)
    VALUES (s.id_estacion, s.codigo, s.nombre, s.direccion, s.distrito, s.latitud, s.longitud, s.fecha_inauguracion, s.accesos, s.plat, s.estado, s.horario, s.elev, s.esc, s.acc, s.tipo);

-- ----------------------------------------------------------------------
-- 4. PLATAFORMAS (PLATAFORMA - 2 POR CADA NUEVA ESTACION)
-- ----------------------------------------------------------------------
PROMPT [4/10] Enriqueciendo PLATAFORMA...
BEGIN
    FOR e IN (SELECT id_estacion, codigo, nombre, distrito FROM ESTACION WHERE id_estacion NOT IN (SELECT DISTINCT estacion_id FROM PLATAFORMA) ORDER BY id_estacion) LOOP
        -- Plataforma Norte / Salida
        MERGE INTO PLATAFORMA p
        USING (SELECT e.id_estacion AS est_id, 'Plat ' || e.codigo || '-N' AS ident FROM DUAL) s
        ON (p.estacion_id = s.est_id AND p.identificador = s.ident)
        WHEN MATCHED THEN
            UPDATE SET p.direccion_viaje = 'Uptown / Northbound', p.capacidad_aproximada = 1400, p.estado_operativo = 'Operativa'
        WHEN NOT MATCHED THEN
            INSERT (id_plataforma, estacion_id, identificador, direccion_viaje, capacidad_aproximada, estado_operativo)
            VALUES (SEQ_PLATAFORMA.NEXTVAL, s.est_id, s.ident, 'Uptown / Northbound', 1400, 'Operativa');

        -- Plataforma Sur / Retorno
        MERGE INTO PLATAFORMA p
        USING (SELECT e.id_estacion AS est_id, 'Plat ' || e.codigo || '-S' AS ident FROM DUAL) s
        ON (p.estacion_id = s.est_id AND p.identificador = s.ident)
        WHEN MATCHED THEN
            UPDATE SET p.direccion_viaje = 'Downtown / Southbound', p.capacidad_aproximada = 1400, p.estado_operativo = 'Operativa'
        WHEN NOT MATCHED THEN
            INSERT (id_plataforma, estacion_id, identificador, direccion_viaje, capacidad_aproximada, estado_operativo)
            VALUES (SEQ_PLATAFORMA.NEXTVAL, s.est_id, s.ident, 'Downtown / Southbound', 1400, 'Operativa');
    END LOOP;
END;
/

-- ----------------------------------------------------------------------
-- 5. LINEAS CANONICAS MTA (LINEA - 26 RUTAS TOTALES: IRT 1-7, BMT/IND A-Z, SHUTTLES, SIR)
-- ----------------------------------------------------------------------
PROMPT [5/10] Enriqueciendo LINEA (26 rutas oficiales MTA)...
MERGE INTO LINEA t
USING (
    -- IRT Division A (1 a 7)
    SELECT 1 AS id_linea, '1' AS codigo, 'Broadway - 7th Avenue Local' AS nombre, '#EE352E' AS color, 12 AS orig, 6 AS dest, 'Activa' AS estado, 'Local' AS tipo, TO_DATE('1904-10-27','YYYY-MM-DD') AS fecha, 24.2 AS len, 'Carlos Roberto Morales (Operador de Control)' AS op FROM DUAL UNION ALL
    SELECT 6, '2', '7th Avenue Express', '#EE352E', 38, 21, 'Activa', 'Expreso', TO_DATE('1904-11-23','YYYY-MM-DD'), 38.5, 'Raymond Francis Burke (Operador de Control)' FROM DUAL UNION ALL
    SELECT 7, '3', '7th Avenue Express', '#EE352E', 15, 25, 'Activa', 'Expreso', TO_DATE('1904-11-23','YYYY-MM-DD'), 23.4, 'Raymond Francis Burke (Operador de Control)' FROM DUAL UNION ALL
    SELECT 8, '4', 'Lexington Avenue Express', '#00933C', 36, 25, 'Activa', 'Expreso', TO_DATE('1904-10-27','YYYY-MM-DD'), 25.1, 'Diane Evelyn Foster (Operador de Control)' FROM DUAL UNION ALL
    SELECT 9, '5', 'Lexington Avenue Express', '#00933C', 38, 21, 'Activa', 'Expreso', TO_DATE('1905-07-10','YYYY-MM-DD'), 36.2, 'Diane Evelyn Foster (Operador de Control)' FROM DUAL UNION ALL
    SELECT 10, '6', 'Lexington Avenue Local', '#00933C', 37, 6, 'Activa', 'Local', TO_DATE('1904-10-27','YYYY-MM-DD'), 29.8, 'Diane Evelyn Foster (Operador de Control)' FROM DUAL UNION ALL
    SELECT 4, '7', 'Flushing Local and Express', '#B933AD', 1, 10, 'Activa', 'Local', TO_DATE('1915-06-22','YYYY-MM-DD'), 14.6, 'Carlos Roberto Morales (Operador de Control)' FROM DUAL UNION ALL

    -- BMT/IND Division B (A-Z)
    SELECT 2, 'A', '8th Avenue Express', '#0039A6', 20, 11, 'Activa', 'Expreso', TO_DATE('1932-09-10','YYYY-MM-DD'), 51.5, 'Jonathan Edward Hayes (Operador de Control)' FROM DUAL UNION ALL
    SELECT 11, 'B', '6th Avenue Express', '#FF6319', 39, 27, 'Activa', 'Expreso', TO_DATE('1940-12-15','YYYY-MM-DD'), 32.1, 'Hector Manuel Cruz (Operador de Control)' FROM DUAL UNION ALL
    SELECT 3, 'C', '8th Avenue Local', '#0039A6', 15, 24, 'Activa', 'Local', TO_DATE('1933-07-01','YYYY-MM-DD'), 30.1, 'Patricia Lynn Gomez (Operador de Control)' FROM DUAL UNION ALL
    SELECT 12, 'D', '6th Avenue Express', '#FF6319', 41, 11, 'Activa', 'Expreso', TO_DATE('1940-12-15','YYYY-MM-DD'), 41.2, 'Hector Manuel Cruz (Operador de Control)' FROM DUAL UNION ALL
    SELECT 13, 'E', '8th Avenue Local', '#0039A6', 32, 18, 'Activa', 'Local', TO_DATE('1933-08-19','YYYY-MM-DD'), 24.5, 'Patricia Lynn Gomez (Operador de Control)' FROM DUAL UNION ALL
    SELECT 14, 'F', '6th Avenue Local', '#FF6319', 32, 11, 'Activa', 'Local', TO_DATE('1940-12-15','YYYY-MM-DD'), 42.8, 'Hector Manuel Cruz (Operador de Control)' FROM DUAL UNION ALL
    SELECT 15, 'G', 'Brooklyn-Queens Crosstown Local', '#6CBE45', 30, 26, 'Activa', 'Local', TO_DATE('1933-08-19','YYYY-MM-DD'), 18.2, 'Patricia Lynn Gomez (Operador de Control)' FROM DUAL UNION ALL
    SELECT 16, 'J', 'Nassau Street Express', '#996633', 32, 5, 'Activa', 'Expreso', TO_DATE('1908-06-30','YYYY-MM-DD'), 20.6, 'Raymond Francis Burke (Operador de Control)' FROM DUAL UNION ALL
    SELECT 5, 'L', '14th Street - Canarsie Local', '#A7A9AC', 4, 28, 'Activa', 'Local', TO_DATE('1924-06-30','YYYY-MM-DD'), 16.5, 'Jonathan Edward Hayes (Operador de Control)' FROM DUAL UNION ALL
    SELECT 17, 'M', 'Queens Boulevard / 6th Avenue Local', '#FF6319', 31, 23, 'Activa', 'Local', TO_DATE('1914-02-22','YYYY-MM-DD'), 22.8, 'Hector Manuel Cruz (Operador de Control)' FROM DUAL UNION ALL
    SELECT 18, 'N', 'Broadway Express', '#FCCC0A', 33, 11, 'Activa', 'Expreso', TO_DATE('1915-06-22','YYYY-MM-DD'), 31.7, 'Jonathan Edward Hayes (Operador de Control)' FROM DUAL UNION ALL
    SELECT 19, 'Q', 'Second Avenue / Broadway Express', '#FCCC0A', 19, 11, 'Activa', 'Expreso', TO_DATE('1920-08-01','YYYY-MM-DD'), 26.5, 'Jonathan Edward Hayes (Operador de Control)' FROM DUAL UNION ALL
    SELECT 20, 'R', 'Broadway Local', '#FCCC0A', 31, 21, 'Activa', 'Local', TO_DATE('1916-01-15','YYYY-MM-DD'), 25.3, 'Carlos Roberto Morales (Operador de Control)' FROM DUAL UNION ALL
    SELECT 21, 'W', 'Broadway Local', '#FCCC0A', 33, 18, 'Activa', 'Local', TO_DATE('2001-07-22','YYYY-MM-DD'), 18.0, 'Carlos Roberto Morales (Operador de Control)' FROM DUAL UNION ALL
    SELECT 22, 'Z', 'Nassau Street Express', '#996633', 32, 5, 'Activa', 'Expreso', TO_DATE('1988-12-11','YYYY-MM-DD'), 20.6, 'Raymond Francis Burke (Operador de Control)' FROM DUAL UNION ALL

    -- Shuttles y Staten Island
    SELECT 23, 'S', '42nd Street Shuttle', '#808183', 1, 2, 'Activa', 'Local', TO_DATE('1904-10-27','YYYY-MM-DD'), 1.3, 'Carlos Roberto Morales (Operador de Control)' FROM DUAL UNION ALL
    SELECT 24, 'SF', 'Franklin Avenue Shuttle', '#808183', 24, 26, 'Activa', 'Local', TO_DATE('1920-08-01','YYYY-MM-DD'), 3.2, 'Diane Evelyn Foster (Operador de Control)' FROM DUAL UNION ALL
    SELECT 25, 'SR', 'Rockaway Park Shuttle', '#808183', 34, 35, 'Activa', 'Local', TO_DATE('1956-06-28','YYYY-MM-DD'), 7.8, 'Hector Manuel Cruz (Operador de Control)' FROM DUAL UNION ALL
    SELECT 26, 'SIR', 'Staten Island Railway', '#0039A6', 42, 45, 'Activa', 'Local', TO_DATE('1860-04-23','YYYY-MM-DD'), 23.0, 'Diane Evelyn Foster (Operador de Control)' FROM DUAL
) s ON (t.codigo = s.codigo)
WHEN MATCHED THEN
    UPDATE SET t.nombre = s.nombre, t.color = s.color, t.estacion_origen_id = s.orig,
               t.estacion_destino_id = s.dest, t.estado_operativo = s.estado,
               t.tipo_servicio_principal = s.tipo, t.longitud_km = s.len,
               t.operador_responsable = s.op
WHEN NOT MATCHED THEN
    INSERT (id_linea, codigo, nombre, color, estacion_origen_id, estacion_destino_id, estado_operativo, tipo_servicio_principal, fecha_inauguracion, longitud_km, operador_responsable)
    VALUES (s.id_linea, s.codigo, s.nombre, s.color, s.orig, s.dest, s.estado, s.tipo, s.fecha, s.len, s.op);

-- ----------------------------------------------------------------------
-- 6. LINEA_ESTACION (CONEXIONES Y TRAMOS DE LA RED)
-- ----------------------------------------------------------------------
PROMPT [6/10] Enriqueciendo LINEA_ESTACION...
BEGIN
    -- Mapeo de estaciones por linea para las nuevas lineas
    FOR rec IN (
        SELECT l.id_linea, l.codigo, l.estacion_origen_id, l.estacion_destino_id
        FROM LINEA l
        WHERE l.id_linea NOT IN (SELECT DISTINCT linea_id FROM LINEA_ESTACION)
    ) LOOP
        -- Origen
        INSERT INTO LINEA_ESTACION (id_linea_estacion, linea_id, estacion_id, orden, distancia_km, tiempo_estimado_min)
        VALUES (SEQ_LINEA_ESTACION.NEXTVAL, rec.id_linea, rec.estacion_origen_id, 1, 0.0, 0);

        -- Destino
        INSERT INTO LINEA_ESTACION (id_linea_estacion, linea_id, estacion_id, orden, distancia_km, tiempo_estimado_min)
        VALUES (SEQ_LINEA_ESTACION.NEXTVAL, rec.id_linea, rec.estacion_destino_id, 2, 15.0, 25);
    END LOOP;
END;
/

-- ----------------------------------------------------------------------
-- 6B. RUTAS OPERATIVAS (RUTA - 44 RUTAS CANONICAS PARA LAS 26 LINEAS)
-- ----------------------------------------------------------------------
PROMPT [6B/10] Enriqueciendo RUTA (44 rutas para las 26 lineas MTA)...
MERGE INTO RUTA t
USING (
    -- Linea 1 (id: 1)
    SELECT 1 AS id_ruta, 'RUT-1-SB' AS cod, 1 AS lin, 12 AS orig, 18 AS dest, 'Sur (Downtown)' AS sent, 'Local' AS tipo, 24.2 AS dist, 50 AS dur, 'Activa' AS est FROM DUAL UNION ALL
    SELECT 2, 'RUT-1-NB', 1, 18, 12, 'Norte (Uptown)', 'Local', 24.2, 50, 'Activa' FROM DUAL UNION ALL
    -- Linea A (id: 2)
    SELECT 3, 'RUT-A-EXP-SB', 2, 20, 34, 'Sur (Queens)', 'Expreso', 31.8, 60, 'Activa' FROM DUAL UNION ALL
    SELECT 5, 'RUT-A-EXP-NB', 2, 34, 20, 'Norte (Manhattan)', 'Expreso', 31.8, 60, 'Activa' FROM DUAL UNION ALL
    -- Linea C (id: 3)
    SELECT 6, 'RUT-C-SB', 3, 14, 24, 'Sur (Brooklyn)', 'Local', 18.0, 40, 'Activa' FROM DUAL UNION ALL
    SELECT 7, 'RUT-C-NB', 3, 24, 14, 'Norte (Manhattan)', 'Local', 18.0, 40, 'Activa' FROM DUAL UNION ALL
    -- Linea 7 (id: 4)
    SELECT 4, 'RUT-7-EB', 4, 1, 10, 'Este (Flushing)', 'Local', 15.2, 32, 'Activa' FROM DUAL UNION ALL
    SELECT 8, 'RUT-7-WB', 4, 10, 1, 'Oeste (Manhattan)', 'Expreso', 15.2, 28, 'Activa' FROM DUAL UNION ALL
    -- Linea L (id: 5)
    SELECT 9, 'RUT-L-EB', 5, 3, 28, 'Este (Canarsie)', 'Local', 16.0, 34, 'Activa' FROM DUAL UNION ALL
    SELECT 10, 'RUT-L-WB', 5, 28, 3, 'Oeste (Manhattan)', 'Local', 16.0, 34, 'Activa' FROM DUAL UNION ALL
    -- Linea 2 (id: 6)
    SELECT 11, 'RUT-2-SB', 6, 38, 25, 'Sur (Brooklyn)', 'Expreso', 26.5, 52, 'Activa' FROM DUAL UNION ALL
    SELECT 12, 'RUT-2-NB', 6, 25, 38, 'Norte (Bronx)', 'Expreso', 26.5, 52, 'Activa' FROM DUAL UNION ALL
    -- Linea 3 (id: 7)
    SELECT 13, 'RUT-3-SB', 7, 15, 16, 'Sur (Downtown)', 'Expreso', 16.8, 35, 'Activa' FROM DUAL UNION ALL
    SELECT 14, 'RUT-3-NB', 7, 16, 15, 'Norte (Harlem)', 'Expreso', 16.8, 35, 'Activa' FROM DUAL UNION ALL
    -- Linea 4 (id: 8)
    SELECT 15, 'RUT-4-SB', 8, 36, 7, 'Sur (Brooklyn)', 'Expreso', 21.0, 42, 'Activa' FROM DUAL UNION ALL
    SELECT 16, 'RUT-4-NB', 8, 7, 36, 'Norte (Bronx)', 'Expreso', 21.0, 42, 'Activa' FROM DUAL UNION ALL
    -- Linea 5 (id: 9)
    SELECT 17, 'RUT-5-SB', 9, 40, 7, 'Sur (Brooklyn)', 'Expreso', 19.5, 40, 'Activa' FROM DUAL UNION ALL
    SELECT 18, 'RUT-5-NB', 9, 7, 40, 'Norte (Bronx)', 'Expreso', 19.5, 40, 'Activa' FROM DUAL UNION ALL
    -- Linea 6 (id: 10)
    SELECT 19, 'RUT-6-SB', 10, 37, 6, 'Sur (Downtown)', 'Local', 22.4, 48, 'Activa' FROM DUAL UNION ALL
    SELECT 20, 'RUT-6-NB', 10, 6, 37, 'Norte (Bronx)', 'Local', 22.4, 48, 'Activa' FROM DUAL UNION ALL
    -- Linea B (id: 11)
    SELECT 21, 'RUT-B-SB', 11, 36, 27, 'Sur (Brooklyn)', 'Expreso', 28.0, 55, 'Activa' FROM DUAL UNION ALL
    SELECT 22, 'RUT-B-NB', 11, 27, 36, 'Norte (Bronx)', 'Expreso', 28.0, 55, 'Activa' FROM DUAL UNION ALL
    -- Linea D (id: 12)
    SELECT 23, 'RUT-D-SB', 12, 41, 11, 'Sur (Coney Island)', 'Expreso', 33.5, 65, 'Activa' FROM DUAL UNION ALL
    SELECT 24, 'RUT-D-NB', 12, 11, 41, 'Norte (Bronx)', 'Expreso', 33.5, 65, 'Activa' FROM DUAL UNION ALL
    -- Linea E (id: 13)
    SELECT 25, 'RUT-E-SB', 13, 32, 5, 'Sur (Downtown)', 'Local', 22.5, 45, 'Activa' FROM DUAL UNION ALL
    SELECT 26, 'RUT-E-NB', 13, 5, 32, 'Norte (Queens)', 'Local', 22.5, 45, 'Activa' FROM DUAL UNION ALL
    -- Linea F (id: 14)
    SELECT 27, 'RUT-F-SB', 14, 31, 11, 'Sur (Coney Island)', 'Local', 30.2, 62, 'Activa' FROM DUAL UNION ALL
    SELECT 28, 'RUT-F-NB', 14, 11, 31, 'Norte (Queens)', 'Local', 30.2, 62, 'Activa' FROM DUAL UNION ALL
    -- Linea G (id: 15)
    SELECT 29, 'RUT-G-SB', 15, 30, 26, 'Sur (Brooklyn)', 'Local', 16.5, 36, 'Activa' FROM DUAL UNION ALL
    SELECT 30, 'RUT-G-NB', 15, 26, 30, 'Norte (Queens)', 'Local', 16.5, 36, 'Activa' FROM DUAL UNION ALL
    -- Linea J (id: 16)
    SELECT 31, 'RUT-J-WB', 16, 32, 16, 'Oeste (Manhattan)', 'Expreso', 19.8, 42, 'Activa' FROM DUAL UNION ALL
    SELECT 32, 'RUT-J-EB', 16, 16, 32, 'Este (Queens)', 'Expreso', 19.8, 42, 'Activa' FROM DUAL UNION ALL
    -- Linea M (id: 17)
    SELECT 33, 'RUT-M-EB', 17, 31, 4, 'Sur (Downtown)', 'Local', 17.5, 38, 'Activa' FROM DUAL UNION ALL
    SELECT 34, 'RUT-M-WB', 17, 4, 31, 'Norte (Queens)', 'Local', 17.5, 38, 'Activa' FROM DUAL UNION ALL
    -- Linea N (id: 18)
    SELECT 35, 'RUT-N-SB', 18, 33, 11, 'Sur (Coney Island)', 'Expreso', 31.0, 58, 'Activa' FROM DUAL UNION ALL
    SELECT 36, 'RUT-N-NB', 18, 11, 33, 'Norte (Astoria)', 'Expreso', 31.0, 58, 'Activa' FROM DUAL UNION ALL
    -- Linea Q (id: 19)
    SELECT 37, 'RUT-Q-SB', 19, 19, 11, 'Sur (Coney Island)', 'Expreso', 26.5, 52, 'Activa' FROM DUAL UNION ALL
    SELECT 38, 'RUT-Q-NB', 19, 11, 19, 'Norte (2nd Ave)', 'Expreso', 26.5, 52, 'Activa' FROM DUAL UNION ALL
    -- Linea R (id: 20)
    SELECT 39, 'RUT-R-SB', 20, 31, 21, 'Sur (Brooklyn)', 'Local', 22.0, 48, 'Activa' FROM DUAL UNION ALL
    SELECT 40, 'RUT-R-NB', 20, 21, 31, 'Norte (Queens)', 'Local', 22.0, 48, 'Activa' FROM DUAL UNION ALL
    -- Linea W (id: 21)
    SELECT 41, 'RUT-W-SB', 21, 33, 18, 'Sur (Whitehall)', 'Local', 17.5, 38, 'Activa' FROM DUAL UNION ALL
    SELECT 42, 'RUT-W-NB', 21, 18, 33, 'Norte (Astoria)', 'Local', 17.5, 38, 'Activa' FROM DUAL UNION ALL
    -- Linea Z (id: 22)
    SELECT 43, 'RUT-Z-WB', 22, 32, 5, 'Oeste (Hora Pico)', 'Expreso', 19.8, 39, 'Activa' FROM DUAL UNION ALL
    -- Linea S (id: 23)
    SELECT 44, 'RUT-S-42', 23, 1, 2, 'Este (Grand Central)', 'Especial', 1.2, 4, 'Activa' FROM DUAL UNION ALL
    -- Linea SF (id: 24)
    SELECT 45, 'RUT-SF-SB', 24, 24, 25, 'Sur (Franklin)', 'Local', 2.5, 7, 'Activa' FROM DUAL UNION ALL
    -- Linea SR (id: 25)
    SELECT 46, 'RUT-SR-SB', 25, 34, 35, 'Sur (Rockaways)', 'Local', 7.8, 16, 'Activa' FROM DUAL UNION ALL
    -- Linea SIR (id: 26)
    SELECT 47, 'RUT-SIR-SB', 26, 42, 45, 'Sur (Tottenville)', 'Local', 22.5, 44, 'Activa' FROM DUAL UNION ALL
    SELECT 48, 'RUT-SIR-NB', 26, 45, 42, 'Norte (St. George)', 'Local', 22.5, 44, 'Activa' FROM DUAL
) s ON (t.codigo = s.cod)
WHEN MATCHED THEN
    UPDATE SET t.linea_id = s.lin, t.estacion_origen_id = s.orig, t.estacion_destino_id = s.dest,
               t.sentido = s.sent, t.tipo_servicio = s.tipo, t.distancia_total_km = s.dist,
               t.duracion_estimada_min = s.dur, t.estado = s.est
WHEN NOT MATCHED THEN
    INSERT (id_ruta, codigo, linea_id, estacion_origen_id, estacion_destino_id, sentido, tipo_servicio, distancia_total_km, duracion_estimada_min, estado, fecha_vigencia_desde, fecha_vigencia_hasta)
    VALUES (s.id_ruta, s.cod, s.lin, s.orig, s.dest, s.sent, s.tipo, s.dist, s.dur, s.est, TO_DATE('2024-01-01','YYYY-MM-DD'), NULL);

PROMPT [6C/10] Sincronizando RUTA_DETALLE para todas las rutas...
BEGIN
    FOR r IN (
        SELECT id_ruta, estacion_origen_id, estacion_destino_id, distancia_total_km, duracion_estimada_min 
        FROM RUTA 
        WHERE id_ruta NOT IN (SELECT DISTINCT ruta_id FROM RUTA_DETALLE)
    ) LOOP
        -- Parada Origen (orden 1)
        INSERT INTO RUTA_DETALLE (id_ruta_detalle, ruta_id, estacion_id, orden_llegada, distancia_desde_anterior_km, tiempo_desde_anterior_min, se_detiene)
        VALUES (SEQ_RUTA_DETALLE.NEXTVAL, r.id_ruta, r.estacion_origen_id, 1, 0.0, 0, 'S');

        -- Parada Destino (orden 2)
        INSERT INTO RUTA_DETALLE (id_ruta_detalle, ruta_id, estacion_id, orden_llegada, distancia_desde_anterior_km, tiempo_desde_anterior_min, se_detiene)
        VALUES (SEQ_RUTA_DETALLE.NEXTVAL, r.id_ruta, r.estacion_destino_id, 2, r.distancia_total_km, r.duracion_estimada_min, 'S');
    END LOOP;
END;
/

-- ----------------------------------------------------------------------
-- 7. TRENES REALES (TREN - 24 TRENES INCLUYENDO 'TR-01' Y TODOS LOS MODELOS)
-- ----------------------------------------------------------------------
PROMPT [7/10] Enriqueciendo TREN (24 unidades de flota)...
MERGE INTO TREN t
USING (
    -- Tren garantizado para pruebas de mantenimiento (R142, 207th St Yard)
    SELECT 7 AS id_tren, 'TR-01' AS codigo_interno, 1 AS modelo_id, 2021 AS anio, 1300 AS cap, 'Disponible' AS estado, 42150.00 AS km, 1 AS dep_id, TO_DATE('2026-08-15','YYYY-MM-DD') AS u_insp, TO_DATE('2026-11-15','YYYY-MM-DD') AS p_insp FROM DUAL UNION ALL

    -- R142 Bombardier (239th St Yard)
    SELECT 8, 'TR-103', 1, 2020, 1200, 'Disponible', 78200.00, 4, TO_DATE('2026-07-10','YYYY-MM-DD'), TO_DATE('2026-10-10','YYYY-MM-DD') FROM DUAL UNION ALL
    SELECT 9, 'TR-104', 1, 2019, 1200, 'Disponible', 95400.00, 4, TO_DATE('2026-06-15','YYYY-MM-DD'), TO_DATE('2026-09-15','YYYY-MM-DD') FROM DUAL UNION ALL

    -- R160 Alstom/Kawasaki (Coney Island & Jamaica Yard)
    SELECT 10, 'TR-203', 2, 2020, 1400, 'Disponible', 84300.00, 2, TO_DATE('2026-08-01','YYYY-MM-DD'), TO_DATE('2026-11-01','YYYY-MM-DD') FROM DUAL UNION ALL
    SELECT 11, 'TR-204', 2, 2021, 1400, 'Disponible', 62100.00, 5, TO_DATE('2026-07-25','YYYY-MM-DD'), TO_DATE('2026-10-25','YYYY-MM-DD') FROM DUAL UNION ALL
    SELECT 12, 'TR-205', 2, 2022, 1400, 'Disponible', 51200.00, 5, TO_DATE('2026-08-12','YYYY-MM-DD'), TO_DATE('2026-11-12','YYYY-MM-DD') FROM DUAL UNION ALL

    -- R179 Bombardier (Coney Island & 207th St)
    SELECT 13, 'TR-302', 3, 2020, 1250, 'Disponible', 71000.00, 2, TO_DATE('2026-07-18','YYYY-MM-DD'), TO_DATE('2026-10-18','YYYY-MM-DD') FROM DUAL UNION ALL
    SELECT 14, 'TR-303', 3, 2021, 1250, 'Disponible', 48900.00, 1, TO_DATE('2026-08-05','YYYY-MM-DD'), TO_DATE('2026-11-05','YYYY-MM-DD') FROM DUAL UNION ALL

    -- R211 Kawasaki (207th St & Coney Island)
    SELECT 15, 'TR-402', 4, 2023, 1450, 'Disponible', 28400.00, 1, TO_DATE('2026-08-20','YYYY-MM-DD'), TO_DATE('2026-11-20','YYYY-MM-DD') FROM DUAL UNION ALL
    SELECT 16, 'TR-403', 4, 2023, 1450, 'Disponible', 24100.00, 2, TO_DATE('2026-08-10','YYYY-MM-DD'), TO_DATE('2026-11-10','YYYY-MM-DD') FROM DUAL UNION ALL
    SELECT 17, 'TR-404', 4, 2024, 1450, 'Disponible', 15300.00, 1, TO_DATE('2026-09-01','YYYY-MM-DD'), TO_DATE('2026-12-01','YYYY-MM-DD') FROM DUAL UNION ALL

    -- R188 Kawasaki (Corona Yard - Linea 7)
    SELECT 18, 'TR-501', 5, 2018, 1200, 'Disponible', 110200.00, 3, TO_DATE('2026-06-20','YYYY-MM-DD'), TO_DATE('2026-09-20','YYYY-MM-DD') FROM DUAL UNION ALL
    SELECT 19, 'TR-502', 5, 2019, 1200, 'Disponible', 98400.00, 3, TO_DATE('2026-07-15','YYYY-MM-DD'), TO_DATE('2026-10-15','YYYY-MM-DD') FROM DUAL UNION ALL
    SELECT 20, 'TR-503', 5, 2020, 1200, 'Disponible', 82100.00, 3, TO_DATE('2026-08-01','YYYY-MM-DD'), TO_DATE('2026-11-01','YYYY-MM-DD') FROM DUAL UNION ALL
    SELECT 21, 'TR-504', 5, 2021, 1200, 'Disponible', 63500.00, 3, TO_DATE('2026-08-22','YYYY-MM-DD'), TO_DATE('2026-11-22','YYYY-MM-DD') FROM DUAL UNION ALL

    -- R68 Westinghouse/Kawasaki (Coney Island & Jamaica Yard)
    SELECT 22, 'TR-601', 6, 1988, 1350, 'Disponible', 312000.00, 2, TO_DATE('2026-05-10','YYYY-MM-DD'), TO_DATE('2026-08-10','YYYY-MM-DD') FROM DUAL UNION ALL
    SELECT 23, 'TR-602', 6, 1989, 1350, 'Disponible', 298400.00, 2, TO_DATE('2026-06-01','YYYY-MM-DD'), TO_DATE('2026-09-01','YYYY-MM-DD') FROM DUAL UNION ALL
    SELECT 24, 'TR-603', 6, 1989, 1350, 'Disponible', 305100.00, 5, TO_DATE('2026-07-01','YYYY-MM-DD'), TO_DATE('2026-10-01','YYYY-MM-DD') FROM DUAL
) s ON (t.codigo_interno = s.codigo_interno)
WHEN MATCHED THEN
    UPDATE SET t.modelo_id = s.modelo_id, t.anio_fabricacion = s.anio, t.capacidad_total = s.cap,
               t.estado_operativo = s.estado, t.deposito_id = s.dep_id,
               t.fecha_ultima_inspeccion = s.u_insp, t.fecha_proxima_inspeccion = s.p_insp
WHEN NOT MATCHED THEN
    INSERT (id_tren, codigo_interno, modelo_id, anio_fabricacion, capacidad_total, estado_operativo, kilometraje_acumulado, deposito_id, fecha_ultima_inspeccion, fecha_proxima_inspeccion)
    VALUES (s.id_tren, s.codigo_interno, s.modelo_id, s.anio, s.cap, s.estado, s.km, s.dep_id, s.u_insp, s.p_insp);

-- ----------------------------------------------------------------------
-- 7B. VAGONES Y COMPOSICIONES DE FLOTA (VAGON Y TREN_VAGON)
-- ----------------------------------------------------------------------
PROMPT [7B/10] Enriqueciendo VAGON y acoplamientos TREN_VAGON...
MERGE INTO VAGON t
USING (
    -- Vagones acoplados para TR-01 (id_tren = 7)
    SELECT 10 AS id_vagon, 'VG-2001' AS num, 'Pasajero Regular' AS tipo, 44 AS sent, 110 AS pie, 2021 AS anio, 'En Uso' AS est, 'S' AS acc FROM DUAL UNION ALL
    SELECT 11, 'VG-2002', 'Pasajero Regular', 44, 110, 2021, 'En Uso', 'S' FROM DUAL UNION ALL
    SELECT 12, 'VG-2003', 'Pasajero Regular', 44, 110, 2021, 'En Uso', 'S' FROM DUAL UNION ALL
    -- Vagones de reserva / disponibles para operacion y talleres
    SELECT 13, 'VG-2004', 'Pasajero Regular', 44, 110, 2022, 'Disponible', 'S' FROM DUAL UNION ALL
    SELECT 14, 'VG-2005', 'Pasajero Regular', 44, 110, 2022, 'Disponible', 'S' FROM DUAL UNION ALL
    SELECT 15, 'VG-2006', 'Pasajero Regular', 44, 110, 2022, 'Disponible', 'S' FROM DUAL UNION ALL
    SELECT 16, 'VG-2007', 'Pasajero Regular', 44, 110, 2023, 'Disponible', 'S' FROM DUAL UNION ALL
    SELECT 17, 'VG-2008', 'Pasajero Regular', 44, 110, 2023, 'Disponible', 'S' FROM DUAL UNION ALL
    SELECT 18, 'VG-2009', 'Pasajero Regular', 44, 110, 2023, 'Disponible', 'S' FROM DUAL UNION ALL
    SELECT 19, 'VG-2010', 'Pasajero Regular', 44, 110, 2024, 'Disponible', 'S' FROM DUAL
) s ON (t.numero_serie = s.num)
WHEN MATCHED THEN
    UPDATE SET t.tipo_vagon = s.tipo, t.capacidad_sentados = s.sent, t.capacidad_de_pie = s.pie,
               t.anio_fabricacion = s.anio, t.estado = s.est, t.accesibilidad = s.acc
WHEN NOT MATCHED THEN
    INSERT (id_vagon, numero_serie, tipo_vagon, capacidad_sentados, capacidad_de_pie, anio_fabricacion, estado, accesibilidad)
    VALUES (s.id_vagon, s.num, s.tipo, s.sent, s.pie, s.anio, s.est, s.acc);

BEGIN
    -- Acoplamiento de vagones para TR-01 (id_tren = 7)
    FOR c IN (
        SELECT 7 AS t_id, 10 AS v_id, 1 AS pos FROM DUAL UNION ALL
        SELECT 7, 11, 2 FROM DUAL UNION ALL
        SELECT 7, 12, 3 FROM DUAL
    ) LOOP
        MERGE INTO TREN_VAGON tv
        USING (SELECT c.t_id AS trn, c.v_id AS vag, c.pos AS p FROM DUAL) s
        ON (tv.tren_id = s.trn AND tv.vagon_id = s.vag)
        WHEN MATCHED THEN
            UPDATE SET tv.posicion = s.p, tv.fecha_fin = NULL
        WHEN NOT MATCHED THEN
            INSERT (id_tren_vagon, tren_id, vagon_id, posicion, fecha_inicio)
            VALUES (SEQ_TREN_VAGON.NEXTVAL, s.trn, s.vag, s.p, TO_DATE('2026-01-01', 'YYYY-MM-DD'));
    END LOOP;
END;
/

-- ----------------------------------------------------------------------
-- 8. MAPEO POLIMORFICO EN EQUIPO (1:1 PARA EL 100% DE TRENES)
-- ----------------------------------------------------------------------
PROMPT [8/10] Sincronizando EQUIPO para mantenimiento polimorfico de trenes...
BEGIN
    -- Limpiar registros duplicados redundantes de ejecuciones anteriores
    DELETE FROM EQUIPO eq_dup
    WHERE eq_dup.tipo_referencia = 'TREN'
      AND eq_dup.codigo_equipo IN ('EQ-TR-101', 'EQ-TR-301')
      AND EXISTS (
          SELECT 1 FROM EQUIPO eq_orig
          WHERE eq_orig.tipo_referencia = 'TREN'
            AND eq_orig.referencia_id = eq_dup.referencia_id
            AND eq_orig.codigo_equipo IN ('EQ-TRN-101', 'EQ-TRN-301')
      );

    -- Renombrar los codigos heredados de datos_prueba a la nomenclatura estandar EQ-TR-
    UPDATE EQUIPO SET codigo_equipo = 'EQ-TR-101' WHERE codigo_equipo = 'EQ-TRN-101';
    UPDATE EQUIPO SET codigo_equipo = 'EQ-TR-301' WHERE codigo_equipo = 'EQ-TRN-301';

    FOR trn IN (
        SELECT t.id_tren, t.codigo_interno, t.estado_operativo, t.anio_fabricacion,
               m.nombre_modelo, m.fabricante, d.nombre as nombre_deposito
        FROM TREN t
        JOIN MODELO_TREN m ON t.modelo_id = m.id_modelo
        LEFT JOIN DEPOSITO d ON t.deposito_id = d.id_deposito
        ORDER BY t.id_tren
    ) LOOP
        MERGE INTO EQUIPO eq
        USING (SELECT 'EQ-' || trn.codigo_interno AS cod_eq FROM DUAL) s
        ON ((eq.tipo_referencia = 'TREN' AND eq.referencia_id = trn.id_tren) OR eq.codigo_equipo = s.cod_eq)
        WHEN MATCHED THEN
            UPDATE SET eq.tipo_equipo = 'Tren',
                       eq.ubicacion = NVL(trn.nombre_deposito, 'Patio de Maniobras MTA'),
                       eq.fabricante = trn.fabricante,
                       eq.modelo = trn.nombre_modelo,
                       eq.estado = CASE WHEN trn.estado_operativo = 'En Mantenimiento' THEN 'En Mantenimiento' ELSE 'Disponible' END
        WHEN NOT MATCHED THEN
            INSERT (id_equipo, codigo_equipo, tipo_equipo, tipo_referencia, referencia_id, ubicacion, fabricante, modelo, estado, fecha_instalacion)
            VALUES (SEQ_EQUIPO.NEXTVAL, s.cod_eq, 'Tren', 'TREN', trn.id_tren, NVL(trn.nombre_deposito, 'Patio de Maniobras MTA'), trn.fabricante, trn.nombre_modelo, CASE WHEN trn.estado_operativo = 'En Mantenimiento' THEN 'En Mantenimiento' ELSE 'Disponible' END, TO_DATE(NVL(trn.anio_fabricacion, 2020) || '-01-01', 'YYYY-MM-DD'));
    END LOOP;
END;
/

-- ----------------------------------------------------------------------
-- 9. PLANTILLA DE PERSONAL (EMPLEADO - 36 EMPLEADOS CON CARGOS MTA)
-- ----------------------------------------------------------------------
PROMPT [9/10] Enriqueciendo EMPLEADO (36 empleados en 6 cargos MTA)...
MERGE INTO EMPLEADO t
USING (
    -- Maquinistas / Conductores
    SELECT 13 AS id_emp, 'EMP-2004' AS num, 'Brandon James Miller' AS nom, TO_DATE('1989-05-12','YYYY-MM-DD') AS fnac, '145 Flatbush Ave, Brooklyn' AS dir, '212-555-0204' AS tel, 'bmiller@nyct.com' AS mail, TO_DATE('2019-01-10','YYYY-MM-DD') AS fcont, 'Conductor' AS cargo, 63000.00 AS sal, 'Activo' AS est, 1 AS sup FROM DUAL UNION ALL
    SELECT 14, 'EMP-2005', 'Kimberly Ann Scott', TO_DATE('1992-08-23','YYYY-MM-DD'), '210 Fordham Rd, Bronx', '212-555-0205', 'kscott@nyct.com', TO_DATE('2019-06-15','YYYY-MM-DD'), 'Conductor', 62500.00, 'Activo', 1 FROM DUAL UNION ALL
    SELECT 15, 'EMP-2006', 'Tyrone Marcus Davis', TO_DATE('1987-03-17','YYYY-MM-DD'), '88 Queens Blvd, Queens', '212-555-0206', 'tdavis@nyct.com', TO_DATE('2018-09-01','YYYY-MM-DD'), 'Conductor', 64500.00, 'Activo', 1 FROM DUAL UNION ALL
    SELECT 16, 'EMP-2007', 'Maria Santos Gomez', TO_DATE('1990-11-04','YYYY-MM-DD'), '312 St. George Term, Staten Island', '212-555-0207', 'mgomez@nyct.com', TO_DATE('2020-02-15','YYYY-MM-DD'), 'Conductor', 62000.00, 'Activo', 1 FROM DUAL UNION ALL
    SELECT 17, 'EMP-2008', 'Sean Patrick Murphy', TO_DATE('1985-06-29','YYYY-MM-DD'), '75 Inwood Ave, Manhattan', '212-555-0208', 'smurphy@nyct.com', TO_DATE('2017-04-10','YYYY-MM-DD'), 'Conductor', 65000.00, 'Activo', 1 FROM DUAL UNION ALL
    SELECT 18, 'EMP-2009', 'Angela Christine Lee', TO_DATE('1993-01-15','YYYY-MM-DD'), '440 Roosevelt Ave, Queens', '212-555-0209', 'alee@nyct.com', TO_DATE('2021-03-20','YYYY-MM-DD'), 'Conductor', 61500.00, 'Activo', 1 FROM DUAL UNION ALL
    SELECT 19, 'EMP-2010', 'Derek Raymond Washington', TO_DATE('1988-10-08','YYYY-MM-DD'), '92 Fulton St, Manhattan', '212-555-0210', 'dwashington@nyct.com', TO_DATE('2018-11-12','YYYY-MM-DD'), 'Conductor', 63500.00, 'Activo', 1 FROM DUAL UNION ALL
    SELECT 20, 'EMP-2011', 'Rosa Linda Hernandez', TO_DATE('1991-04-19','YYYY-MM-DD'), '521 Nostrand Ave, Brooklyn', '212-555-0211', 'rhernandez@nyct.com', TO_DATE('2020-08-01','YYYY-MM-DD'), 'Conductor', 62000.00, 'Activo', 1 FROM DUAL UNION ALL
    SELECT 21, 'EMP-2012', 'Kevin Brian O Reilly', TO_DATE('1986-09-02','YYYY-MM-DD'), '18 Surf Ave, Brooklyn', '212-555-0212', 'koreilly@nyct.com', TO_DATE('2017-07-15','YYYY-MM-DD'), 'Conductor', 64000.00, 'Activo', 1 FROM DUAL UNION ALL
    SELECT 22, 'EMP-2013', 'Jasmine Nicole Jackson', TO_DATE('1994-07-25','YYYY-MM-DD'), '65 Main St, Queens', '212-555-0213', 'jjackson@nyct.com', TO_DATE('2022-01-10','YYYY-MM-DD'), 'Conductor', 61000.00, 'Activo', 1 FROM DUAL UNION ALL

    -- Operadores de Control de Tráfico Ferroviario
    SELECT 23, 'EMP-1006', 'Raymond Francis Burke', TO_DATE('1981-02-14','YYYY-MM-DD'), '120 Broadway, Manhattan', '212-555-0106', 'rburke@nyct.com', TO_DATE('2011-05-15','YYYY-MM-DD'), 'Operador de Control', 86500.00, 'Activo', 1 FROM DUAL UNION ALL
    SELECT 24, 'EMP-1007', 'Diane Evelyn Foster', TO_DATE('1983-12-05','YYYY-MM-DD'), '350 Grand Concourse, Bronx', '212-555-0107', 'dfoster@nyct.com', TO_DATE('2013-09-20','YYYY-MM-DD'), 'Operador de Control', 87000.00, 'Activo', 1 FROM DUAL UNION ALL
    SELECT 25, 'EMP-1008', 'Hector Manuel Cruz', TO_DATE('1979-08-30','YYYY-MM-DD'), '82 Court St, Brooklyn', '212-555-0108', 'hcruz@nyct.com', TO_DATE('2009-03-01','YYYY-MM-DD'), 'Operador de Control', 88000.00, 'Activo', 1 FROM DUAL UNION ALL

    -- Tecnicos de Mantenimiento de Material Rodante e Instalaciones
    SELECT 26, 'EMP-3003', 'Anthony Paul Marino', TO_DATE('1988-04-18','YYYY-MM-DD'), '10th Ave & 207th St, Manhattan', '212-555-0303', 'amarino@nyct.com', TO_DATE('2018-05-10','YYYY-MM-DD'), 'Técnico de Mantenimiento', 59000.00, 'Activo', 1 FROM DUAL UNION ALL
    SELECT 27, 'EMP-3004', 'Brian Keith Kowalski', TO_DATE('1991-10-22','YYYY-MM-DD'), 'Avenue X & Shell Rd, Brooklyn', '212-555-0304', 'bkowalski@nyct.com', TO_DATE('2019-11-15','YYYY-MM-DD'), 'Técnico de Mantenimiento', 57500.00, 'Activo', 1 FROM DUAL UNION ALL
    SELECT 28, 'EMP-3005', 'Luis Alberto Vega', TO_DATE('1986-01-30','YYYY-MM-DD'), 'Corona Yard, 126th St, Queens', '212-555-0305', 'lvega@nyct.com', TO_DATE('2017-02-20','YYYY-MM-DD'), 'Técnico de Mantenimiento', 60500.00, 'Activo', 1 FROM DUAL UNION ALL
    SELECT 29, 'EMP-3006', 'Jamal Antwon Jefferson', TO_DATE('1992-06-11','YYYY-MM-DD'), 'Jamaica Yard, Forest Hills, Queens', '212-555-0306', 'jjefferson@nyct.com', TO_DATE('2020-04-01','YYYY-MM-DD'), 'Técnico de Mantenimiento', 58000.00, 'Activo', 1 FROM DUAL UNION ALL
    SELECT 30, 'EMP-3007', 'Gary Steven Newman', TO_DATE('1984-09-14','YYYY-MM-DD'), '239th St Yard, Wakefield, Bronx', '212-555-0307', 'gnewman@nyct.com', TO_DATE('2016-08-15','YYYY-MM-DD'), 'Técnico de Mantenimiento', 61000.00, 'Activo', 1 FROM DUAL UNION ALL

    -- Supervisores de Estacion
    SELECT 31, 'EMP-1009', 'Michelle Denise Clark', TO_DATE('1982-05-20','YYYY-MM-DD'), '34th St & 7th Ave, Manhattan', '212-555-0109', 'mclark@nyct.com', TO_DATE('2014-06-01','YYYY-MM-DD'), 'Supervisor de Estación', 69000.00, 'Activo', 1 FROM DUAL UNION ALL
    SELECT 32, 'EMP-1010', 'Gregory Allen Brooks', TO_DATE('1980-11-11','YYYY-MM-DD'), 'Atlantic Ave & Flatbush, Brooklyn', '212-555-0110', 'gbrooks@nyct.com', TO_DATE('2012-10-15','YYYY-MM-DD'), 'Supervisor de Estación', 70000.00, 'Activo', 1 FROM DUAL UNION ALL

    -- Agentes de Seguridad
    SELECT 33, 'EMP-4003', 'Terrence Vance Mitchell', TO_DATE('1990-03-08','YYYY-MM-DD'), 'Times Sq & 42nd St, Manhattan', '212-555-0403', 'tmitchell@nyct.com', TO_DATE('2019-03-15','YYYY-MM-DD'), 'Agente de Seguridad', 49000.00, 'Activo', 2 FROM DUAL UNION ALL
    SELECT 34, 'EMP-4004', 'Victor Daniel Ramos', TO_DATE('1993-12-19','YYYY-MM-DD'), 'Jay St & MetroTech, Brooklyn', '212-555-0404', 'vramos@nyct.com', TO_DATE('2021-08-10','YYYY-MM-DD'), 'Agente de Seguridad', 48500.00, 'Activo', 2 FROM DUAL UNION ALL

    -- Personal de Atencion al Pasajero
    SELECT 35, 'EMP-4005', 'Stephanie Marie Ortiz', TO_DATE('1996-02-28','YYYY-MM-DD'), 'Grand Central 42nd St, Manhattan', '212-555-0405', 'sortiz@nyct.com', TO_DATE('2022-04-15','YYYY-MM-DD'), 'Personal de Atención al Pasajero', 46000.00, 'Activo', 3 FROM DUAL UNION ALL
    SELECT 36, 'EMP-4006', 'Natasha Renee Williams', TO_DATE('1995-07-04','YYYY-MM-DD'), 'Fulton St Subway Hub, Manhattan', '212-555-0406', 'nwilliams@nyct.com', TO_DATE('2022-09-01','YYYY-MM-DD'), 'Personal de Atención al Pasajero', 46500.00, 'Activo', 3 FROM DUAL
) s ON (t.numero_empleado = s.num)
WHEN MATCHED THEN
    UPDATE SET t.nombre_completo = s.nom, t.fecha_nacimiento = s.fnac, t.direccion = s.dir,
               t.telefono = s.tel, t.correo_electronico = s.mail, t.fecha_contratacion = s.fcont,
               t.cargo = s.cargo, t.salario = s.sal, t.estado_laboral = s.est, t.supervisor_id = s.sup
WHEN NOT MATCHED THEN
    INSERT (id_empleado, numero_empleado, nombre_completo, fecha_nacimiento, direccion, telefono, correo_electronico, fecha_contratacion, cargo, salario, estado_laboral, supervisor_id)
    VALUES (s.id_emp, s.num, s.nom, s.fnac, s.dir, s.tel, s.mail, s.fcont, s.cargo, s.sal, s.est, s.sup);

-- ----------------------------------------------------------------------
-- 10. CERTIFICACIONES TECNICAS (CERTIFICACION - VIGENTES 2027/2028)
-- ----------------------------------------------------------------------
PROMPT [10/10] Enriqueciendo CERTIFICACION y CERTIFICACION_MODELO...
BEGIN
    -- Licencias para Conductores
    FOR cond IN (
        SELECT id_empleado, nombre_completo FROM EMPLEADO
        WHERE cargo = 'Conductor'
          AND id_empleado NOT IN (SELECT empleado_id FROM CERTIFICACION WHERE tipo_certificacion LIKE '%Conducci%')
    ) LOOP
        INSERT INTO CERTIFICACION (
            id_certificacion, empleado_id, tipo_certificacion, fecha_emision, fecha_vencimiento, institucion_emisora, estado
        ) VALUES (
            SEQ_CERTIFICACION.NEXTVAL, cond.id_empleado, 'Licencia Conducción Clase A Subterráneo',
            TO_DATE('2024-01-15', 'YYYY-MM-DD'), TO_DATE('2028-01-15', 'YYYY-MM-DD'), 'Federal Railroad Administration', 'Vigente'
        );
    END LOOP;

    -- Certificaciones para Tecnicos de Mantenimiento
    FOR tec IN (
        SELECT id_empleado, nombre_completo FROM EMPLEADO
        WHERE cargo = 'Técnico de Mantenimiento'
          AND id_empleado NOT IN (SELECT empleado_id FROM CERTIFICACION)
    ) LOOP
        INSERT INTO CERTIFICACION (
            id_certificacion, empleado_id, tipo_certificacion, fecha_emision, fecha_vencimiento, institucion_emisora, estado
        ) VALUES (
            SEQ_CERTIFICACION.NEXTVAL, tec.id_empleado, 'Especialista en Sistemas Neumáticos y Frenos',
            TO_DATE('2024-03-01', 'YYYY-MM-DD'), TO_DATE('2027-03-01', 'YYYY-MM-DD'), 'MTA Maintenance Training Academy', 'Vigente'
        );
    END LOOP;

    -- Sincronizar modelos habilitados para certificaciones
    FOR c IN (SELECT id_certificacion FROM CERTIFICACION WHERE id_certificacion NOT IN (SELECT DISTINCT certificacion_id FROM CERTIFICACION_MODELO)) LOOP
        INSERT INTO CERTIFICACION_MODELO (id_certificacion_modelo, certificacion_id, modelo_id)
        VALUES (SEQ_CERTIFICACION_MODELO.NEXTVAL, c.id_certificacion, 1);
        INSERT INTO CERTIFICACION_MODELO (id_certificacion_modelo, certificacion_id, modelo_id)
        VALUES (SEQ_CERTIFICACION_MODELO.NEXTVAL, c.id_certificacion, 2);
    END LOOP;
END;
/

-- ----------------------------------------------------------------------
-- SINCRONIZACION FINAL DE TODAS LAS SECUENCIAS
-- ----------------------------------------------------------------------
PROMPT Sincronizando secuencias del sistema...
BEGIN
    SP_SINCRONIZAR_TODAS_SECUENCIAS;
END;
/

COMMIT;

PROMPT ======================================================================
PROMPT ENRIQUECIMIENTO MASIVO MTA COMPLETADO EXITOSAMENTE.
PROMPT ======================================================================
