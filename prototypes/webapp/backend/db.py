"""
Módulo de Acceso a Datos (Oracle Database) para el Sistema Metro NY.
Maneja la conexión con detección automática de PDB (FREEPDB1 / XEPDB1).
"""
import os
import oracledb

# Configuración por defecto
DB_USER = os.getenv("ORACLE_USER", "METRO_NY")
DB_PASSWORD = os.getenv("ORACLE_PASSWORD", "MetroPass123")
DB_HOST = os.getenv("ORACLE_HOST", "localhost")
DB_PORT = int(os.getenv("ORACLE_PORT", "1521"))
ACTIVE_PDB = None

CANDIDATE_PDBS = ["FREEPDB1", "XEPDB1", "ORCLPDB"]

def get_connection():
    """
    Obtiene una conexión activa a Oracle.
    Intenta primero con el PDB cacheado o prueba la lista de candidatos.
    """
    global ACTIVE_PDB

    # Si se especificó un PDB por variable de entorno, usarlo
    env_pdb = os.getenv("ORACLE_PDB")
    candidates = [env_pdb] if env_pdb else ([ACTIVE_PDB] if ACTIVE_PDB else CANDIDATE_PDBS)

    last_error = None
    for pdb in candidates:
        if not pdb:
            continue
        try:
            dsn = f"{DB_HOST}:{DB_PORT}/{pdb}"
            conn = oracledb.connect(
                user=DB_USER,
                password=DB_PASSWORD,
                dsn=dsn
            )
            ACTIVE_PDB = pdb
            return conn
        except Exception as e:
            last_error = e

    # Si ninguno conectó directamente, intentar con todos los candidatos
    for pdb in CANDIDATE_PDBS:
        if pdb in candidates:
            continue
        try:
            dsn = f"{DB_HOST}:{DB_PORT}/{pdb}"
            conn = oracledb.connect(
                user=DB_USER,
                password=DB_PASSWORD,
                dsn=dsn
            )
            ACTIVE_PDB = pdb
            return conn
        except Exception as e:
            last_error = e

    raise RuntimeError(f"No se pudo conectar a Oracle en {DB_HOST}:{DB_PORT}. Error: {last_error}")


def execute_query(sql, params=None):
    """
    Ejecuta una consulta SQL y retorna las columnas y filas serializables en JSON.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or {})
        columns = [col[0] for col in cursor.description]
        rows = []
        for row in cursor.fetchall():
            row_dict = {}
            for col_name, val in zip(columns, row):
                # Conversión segura de tipos de Oracle para JSON
                if val is None:
                    row_dict[col_name] = "-"
                elif hasattr(val, "strftime"):
                    row_dict[col_name] = val.strftime("%Y-%m-%d %H:%M") if hasattr(val, "hour") and val.hour != 0 else val.strftime("%Y-%m-%d")
                elif isinstance(val, (int, float)):
                    row_dict[col_name] = val
                else:
                    row_dict[col_name] = str(val)
            rows.append(row_dict)
        return {"columns": columns, "rows": rows, "total": len(rows), "pdb": ACTIVE_PDB}
    finally:
        cursor.close()
        conn.close()


# Las 15 consultas mínimas oficiales del enunciado
CONSULTAS_CATALOGO = {
    1: {
        "titulo": "1. Líneas que pasan por una estación determinada",
        "descripcion": "¿Qué líneas pasan por Times Sq - 42 St? (Relación N:M entre Línea y Estación)",
        "sql": """
            SELECT e.nombre AS "Estación",
                   l.codigo AS "Línea",
                   l.nombre AS "Nombre de Línea",
                   l.color  AS "Color Dist.",
                   le.orden AS "Orden Secuencia"
            FROM ESTACION e
            JOIN LINEA_ESTACION le ON e.id_estacion = le.estacion_id
            JOIN LINEA l           ON le.linea_id = l.id_linea
            WHERE e.codigo = 'TSQ42'
            ORDER BY le.orden
        """
    },
    2: {
        "titulo": "2. Paradas secuenciales de una ruta",
        "descripcion": "¿Cuáles son las estaciones de la ruta RUT-1-SB y en qué orden se visitan?",
        "sql": """
            SELECT r.codigo         AS "Código Ruta",
                   r.sentido        AS "Sentido",
                   rd.orden_llegada AS "Secuencia",
                   e.nombre         AS "Estación",
                   CASE rd.se_detiene WHEN 'S' THEN 'Sí (Parada)' ELSE 'Pasa Expreso' END AS "Detención"
            FROM RUTA r
            JOIN RUTA_DETALLE rd ON r.id_ruta = rd.ruta_id
            JOIN ESTACION e      ON rd.estacion_id = e.id_estacion
            WHERE r.codigo = 'RUT-1-SB'
            ORDER BY rd.orden_llegada
        """
    },
    3: {
        "titulo": "3. Estaciones de transferencia entre líneas",
        "descripcion": "¿Qué estaciones permiten transbordo entre líneas y cuál es el tiempo de caminata?",
        "sql": """
            SELECT e.nombre AS "Estación de Conexión",
                   e.distrito AS "Distrito",
                   lo.codigo || ' (' || lo.color || ')' AS "Línea Origen",
                   ld.codigo || ' (' || ld.color || ')' AS "Línea Destino",
                   t.tiempo_estimado_min AS "Min. Caminata"
            FROM TRANSFERENCIA t
            JOIN ESTACION e  ON t.estacion_id = e.id_estacion
            JOIN LINEA lo    ON t.linea_origen_id = lo.id_linea
            JOIN LINEA ld    ON t.linea_destino_id = ld.id_linea
            ORDER BY e.nombre, t.tiempo_estimado_min
        """
    },
    4: {
        "titulo": "4. Viajes programados para una fecha",
        "descripcion": "¿Qué viajes están asignados para el 2026-09-01 con su tren y conductor?",
        "sql": """
            SELECT vp.numero_viaje AS "Número Viaje",
                   r.codigo        AS "Ruta",
                   TO_CHAR(vp.hora_prog_salida, 'HH24:MI') AS "Hora Prog.",
                   t.codigo_interno AS "Tren Asignado",
                   e.nombre_completo AS "Conductor",
                   vp.estado       AS "Estado"
            FROM VIAJE_PROGRAMADO vp
            JOIN RUTA r     ON vp.ruta_id = r.id_ruta
            JOIN TREN t     ON vp.tren_id = t.id_tren
            JOIN EMPLEADO e ON vp.conductor_id = e.id_empleado
            WHERE vp.fecha = TO_DATE('2026-09-01', 'YYYY-MM-DD')
            ORDER BY vp.hora_prog_salida
        """
    },
    5: {
        "titulo": "5. Viajes con retrasos mayores a 15 minutos",
        "descripcion": "¿Qué viajes salieron con más de 15 minutos de demora según el horario programado?",
        "sql": """
            SELECT vp.numero_viaje  AS "Número Viaje",
                   r.codigo         AS "Ruta",
                   TO_CHAR(vp.hora_prog_salida, 'HH24:MI') AS "Salida Prog.",
                   TO_CHAR(vp.hora_real_salida, 'HH24:MI') AS "Salida Real",
                   ROUND((CAST(vp.hora_real_salida AS DATE) - CAST(vp.hora_prog_salida AS DATE)) * 24 * 60) AS "Min. Demora",
                   vp.estado        AS "Estado"
            FROM VIAJE_PROGRAMADO vp
            JOIN RUTA r ON vp.ruta_id = r.id_ruta
            WHERE vp.hora_real_salida IS NOT NULL
              AND (CAST(vp.hora_real_salida AS DATE) - CAST(vp.hora_prog_salida AS DATE)) * 24 * 60 > 15
            ORDER BY "Min. Demora" DESC
        """
    },
    6: {
        "titulo": "6. Trenes disponibles en el sistema",
        "descripcion": "¿Qué unidades de material rodante están operativas y listas para el servicio?",
        "sql": """
            SELECT t.codigo_interno  AS "Código Tren",
                   m.nombre_modelo   AS "Modelo",
                   m.fabricante      AS "Fabricante",
                   NVL(d.nombre, 'Sin Depósito') AS "Depósito Base",
                   t.estado_operativo AS "Estado"
            FROM TREN t
            JOIN MODELO_TREN m  ON t.modelo_id = m.id_modelo
            LEFT JOIN DEPOSITO d ON t.deposito_id = d.id_deposito
            WHERE t.estado_operativo = 'Disponible'
            ORDER BY t.codigo_interno
        """
    },
    7: {
        "titulo": "7. Trenes con inspección vencida o en taller",
        "descripcion": "¿Qué trenes requieren mantenimiento preventivo inmediato o están en reparación?",
        "sql": """
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
            ORDER BY t.fecha_proxima_inspeccion
        """
    },
    8: {
        "titulo": "8. Asignación de conductor y certificación por viaje",
        "descripcion": "¿Qué conductor operó cada viaje y cuál es su licencia de conducción MTA?",
        "sql": """
            SELECT vp.numero_viaje   AS "Viaje",
                   r.codigo          AS "Ruta",
                   emp.numero_empleado AS "Num. Empleado",
                   emp.nombre_completo AS "Nombre Conductor",
                   NVL(c.tipo_certificacion, 'Sin Certificar') AS "Licencia MTA",
                   TO_CHAR(vp.fecha, 'YYYY-MM-DD') AS "Fecha"
            FROM VIAJE_PROGRAMADO vp
            JOIN RUTA r     ON vp.ruta_id = r.id_ruta
            JOIN EMPLEADO emp ON vp.conductor_id = emp.id_empleado
            LEFT JOIN CERTIFICACION c ON emp.id_empleado = c.empleado_id AND c.estado = 'Vigente'
            ORDER BY vp.fecha, vp.hora_prog_salida
        """
    },
    9: {
        "titulo": "9. Pasajeros transportados por línea",
        "descripcion": "¿Cuántos pasajeros utilizaron cada una de las 5 líneas durante el período?",
        "sql": """
            SELECT l.codigo          AS "Línea",
                   l.nombre          AS "Nombre de la Línea",
                   COUNT(vp.id_viaje_pasajero) AS "Total Pasajeros"
            FROM LINEA l
            LEFT JOIN RUTA r             ON l.id_linea = r.linea_id
            LEFT JOIN VIAJE_PROGRAMADO vprog ON r.id_ruta = vprog.ruta_id
            LEFT JOIN VIAJE_PASAJERO vp  ON vprog.id_viaje = vp.viaje_programado_id
            GROUP BY l.codigo, l.nombre
            ORDER BY "Total Pasajeros" DESC
        """
    },
    10: {
        "titulo": "10. Recaudación por fecha, estación y tarifa",
        "descripcion": "¿Cuánto dinero ingresó al sistema desglosado por torniquete y perfil de tarjeta?",
        "sql": """
            SELECT TO_CHAR(CAST(vp.fecha_hora_ingreso AS DATE), 'YYYY-MM-DD') AS "Fecha",
                   e.nombre  AS "Estación de Ingreso",
                   t.nombre  AS "Perfil Tarifa",
                   COUNT(vp.id_viaje_pasajero) AS "Pasajes Validados",
                   SUM(vp.monto_cobrado)       AS "Total Recaudado ($)"
            FROM VIAJE_PASAJERO vp
            JOIN ESTACION e ON vp.estacion_ingreso_id = e.id_estacion
            JOIN TARIFA t   ON vp.tarifa_id = t.id_tarifa
            GROUP BY TO_CHAR(CAST(vp.fecha_hora_ingreso AS DATE), 'YYYY-MM-DD'), e.nombre, t.nombre
            ORDER BY "Fecha", "Estación de Ingreso", "Total Recaudado ($)" DESC
        """
    },
    11: {
        "titulo": "11. Estaciones con mayor afluencia de pasajeros",
        "descripcion": "Ranking de estaciones con más ingresos de pasajeros registrados en torniquete",
        "sql": """
            SELECT e.nombre   AS "Estación",
                   e.distrito AS "Distrito",
                   COUNT(vp.id_viaje_pasajero) AS "Total Pasajeros Validados"
            FROM ESTACION e
            JOIN VIAJE_PASAJERO vp ON e.id_estacion = vp.estacion_ingreso_id
            GROUP BY e.nombre, e.distrito
            ORDER BY "Total Pasajeros Validados" DESC
        """
    },
    12: {
        "titulo": "12. Incidentes abiertos en la red",
        "descripcion": "Incidentes no resueltos con resolución de Arco Exclusivo (estación, tren o vía)",
        "sql": """
            SELECT i.numero_incidente AS "Incidente",
                   i.tipo             AS "Tipo Incidente",
                   i.nivel_severidad  AS "Severidad",
                   TO_CHAR(i.fecha_hora_inicio, 'YYYY-MM-DD HH24:MI') AS "Fecha Inicio",
                   i.estado           AS "Estado",
                   NVL(e.nombre, NVL(t.codigo_interno, NVL(r.codigo, 'General de Red'))) AS "Elemento Afectado"
            FROM INCIDENTE i
            LEFT JOIN INCIDENTE_ELEMENTO_AFECTADO a ON i.id_incidente = a.incidente_id
            LEFT JOIN ESTACION e ON a.estacion_id = e.id_estacion
            LEFT JOIN TREN t     ON a.tren_id = t.id_tren
            LEFT JOIN RUTA r     ON a.ruta_id = r.id_ruta
            WHERE i.estado != 'Cerrado'
            ORDER BY i.fecha_hora_inicio DESC
        """
    },
    13: {
        "titulo": "13. Líneas con más minutos de retraso acumulados",
        "descripcion": "Total de minutos perdidos por demoras operativas agrupados por línea",
        "sql": """
            SELECT l.codigo AS "Línea",
                   l.nombre AS "Nombre Línea",
                   l.color  AS "Color",
                   COUNT(vp.id_viaje) AS "Viajes Demorados",
                   NVL(SUM(ROUND((CAST(vp.hora_real_salida AS DATE) - CAST(vp.hora_prog_salida AS DATE)) * 24 * 60)), 0) AS "Minutos Demora"
            FROM LINEA l
            JOIN RUTA r ON l.id_linea = r.linea_id
            JOIN VIAJE_PROGRAMADO vp ON r.id_ruta = vp.ruta_id
            WHERE vp.hora_real_salida > vp.hora_prog_salida
            GROUP BY l.codigo, l.nombre, l.color
            ORDER BY "Minutos Demora" DESC
        """
    },
    14: {
        "titulo": "14. Tarjetas OMNY bloqueadas o vencidas",
        "descripcion": "Tarjetas fuera de servicio o con fecha de vigencia anterior a hoy",
        "sql": """
            SELECT t.numero_tarjeta        AS "Número Tarjeta",
                   tar.nombre              AS "Perfil Tarifa",
                   NVL(p.nombre, '(Anónima)') AS "Pasajero Titular",
                   t.saldo_disponible      AS "Saldo ($)",
                   TO_CHAR(t.fecha_vencimiento, 'YYYY-MM-DD') AS "Vencimiento",
                   t.estado                AS "Estado Tarjeta"
            FROM TARJETA t
            JOIN TARIFA tar ON t.tarifa_id = tar.id_tarifa
            LEFT JOIN PASAJERO p ON t.pasajero_id = p.id_pasajero
            WHERE t.estado IN ('Bloqueada', 'Vencida')
               OR t.fecha_vencimiento < SYSDATE
            ORDER BY t.estado, t.fecha_vencimiento
        """
    },
    15: {
        "titulo": "15. Técnicos asignados a órdenes de mantenimiento",
        "descripcion": "Detalle de personal asignado y rol desempeñado en cada reparación o inspección",
        "sql": """
            SELECT om.numero_orden       AS "Orden Mantenimiento",
                   om.tipo_mantenimiento AS "Tipo",
                   eq.codigo_equipo      AS "Equipo",
                   e.nombre_completo     AS "Técnico Especialista",
                   ot.rol_en_orden       AS "Rol Desempeñado",
                   om.estado             AS "Estado Orden"
            FROM ORDEN_MANTENIMIENTO om
            JOIN EQUIPO eq        ON om.equipo_id = eq.id_equipo
            JOIN ORDEN_TECNICO ot ON om.id_orden = ot.orden_id
            JOIN EMPLEADO e       ON ot.empleado_id = e.id_empleado
            ORDER BY om.numero_orden, e.nombre_completo
        """
    }
}

