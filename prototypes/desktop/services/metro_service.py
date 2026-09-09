"""
High-level Metro domain service functions.
Abstracts all SQL queries and data mapping away from the UI views.
"""
from typing import Dict, List, Tuple
from services.db import execute_query, ACTIVE_PDB
from config import DB_USER, DB_HOST, DB_PORT


def check_db_health() -> Dict[str, str]:
    """
    Validates database connectivity and active PDB.
    """
    res = execute_query("SELECT 1 FROM DUAL")
    return {
        "status": "online",
        "pdb": res.get("pdb", ACTIVE_PDB or "FREEPDB1"),
        "user": DB_USER,
        "host": f"{DB_HOST}:{DB_PORT}"
    }


def get_dashboard_kpis() -> Dict[str, str]:
    """
    Aggregates main operational KPIs across the system.
    """
    sql = """
        SELECT 
            (SELECT COUNT(*) FROM LINEA) AS TOTAL_LINEAS,
            (SELECT COUNT(*) FROM ESTACION) AS TOTAL_ESTACIONES,
            (SELECT COUNT(*) FROM TREN) AS TOTAL_TRENES,
            (SELECT COUNT(*) FROM EMPLEADO) AS TOTAL_EMPLEADOS,
            (SELECT COUNT(*) FROM TARJETA) AS TOTAL_TARJETAS,
            (SELECT COUNT(*) FROM INCIDENTE WHERE estado != 'Cerrado') AS INCIDENTES_ABIERTOS
        FROM DUAL
    """
    rows = execute_query(sql)["rows"]
    if rows:
        return rows[0]
    return {
        "TOTAL_LINEAS": "0", "TOTAL_ESTACIONES": "0", "TOTAL_TRENES": "0",
        "TOTAL_EMPLEADOS": "0", "TOTAL_TARJETAS": "0", "INCIDENTES_ABIERTOS": "0"
    }


def get_lines_summary() -> List[Dict]:
    """
    Retrieves all subway lines, color codes, operational status, and stop counts.
    """
    sql = """
        SELECT l.codigo, l.nombre, l.color, l.tipo_servicio_principal, l.estado_operativo,
               COUNT(le.estacion_id) AS estaciones
        FROM LINEA l
        LEFT JOIN LINEA_ESTACION le ON l.id_linea = le.linea_id
        GROUP BY l.codigo, l.nombre, l.color, l.tipo_servicio_principal, l.estado_operativo
        ORDER BY l.codigo
    """
    return execute_query(sql)["rows"]


def get_stations_summary() -> List[Dict]:
    """
    Retrieves all stations with platforms, ADA accessibility, and borough.
    """
    sql = """
        SELECT e.codigo, e.nombre, e.distrito, 
               NVL(e.cantidad_plataformas, 2) AS plataformas,
               e.accesible_discapacidad, e.elevadores_disponibles, e.estado_operativo
        FROM ESTACION e
        ORDER BY e.distrito, e.nombre
    """
    return execute_query(sql)["rows"]


def get_fleet_summary() -> List[Dict]:
    """
    Retrieves trains fleet with operational condition, model, and depots.
    """
    sql = """
        SELECT t.codigo_interno, m.nombre_modelo, m.fabricante, 
               NVL(d.nombre, 'Sin Depósito') AS deposito,
               t.kilometraje_acumulado,
               t.estado_operativo,
               TO_CHAR(t.fecha_ultima_inspeccion, 'YYYY-MM-DD') AS ultima_insp,
               TO_CHAR(t.fecha_proxima_inspeccion, 'YYYY-MM-DD') AS proxima_insp
        FROM TREN t
        JOIN MODELO_TREN m ON t.modelo_id = m.id_modelo
        LEFT JOIN DEPOSITO d ON t.deposito_id = d.id_deposito
        ORDER BY t.codigo_interno
    """
    return execute_query(sql)["rows"]


def get_staff_summary() -> List[Dict]:
    """
    Retrieves operational personnel, job roles, and supervisor links.
    """
    sql = """
        SELECT e.numero_empleado, e.nombre_completo, e.cargo, e.turno_habitual AS turno, e.estado_laboral,
               NVL(sup.nombre_completo, 'Jefatura General') AS supervisor,
               NVL(c.tipo_certificacion, 'General') AS certificacion
        FROM EMPLEADO e
        LEFT JOIN EMPLEADO sup ON e.supervisor_id = sup.id_empleado
        LEFT JOIN CERTIFICACION c ON e.id_empleado = c.empleado_id AND c.estado = 'Vigente'
        ORDER BY e.cargo, e.nombre_completo
    """
    return execute_query(sql)["rows"]


def get_incidents_summary() -> List[Dict]:
    """
    Retrieves open and recent incidents across the subway network.
    """
    sql = """
        SELECT i.numero_incidente, i.tipo, i.nivel_severidad,
               TO_CHAR(i.fecha_hora_inicio, 'YYYY-MM-DD HH24:MI') AS inicio,
               i.estado,
               NVL(e.nombre, NVL(t.codigo_interno, NVL(r.codigo, 'Red Metro'))) AS elemento_afectado,
               NVL(i.descripcion, 'Sin detalle') AS descripcion
        FROM INCIDENTE i
        LEFT JOIN INCIDENTE_ELEMENTO_AFECTADO a ON i.id_incidente = a.incidente_id
        LEFT JOIN ESTACION e ON a.estacion_id = e.id_estacion
        LEFT JOIN TREN t ON a.tren_id = t.id_tren
        LEFT JOIN RUTA r ON a.ruta_id = r.id_ruta
        ORDER BY i.fecha_hora_inicio DESC
    """
    return execute_query(sql)["rows"]


# --- Dynamic Lookup Helpers for UI Dropdowns ---

def get_stations_lookup() -> List[Tuple[str, str]]:
    """
    Returns list of (codigo, display_label) for stations dropdowns.
    """
    res = execute_query("SELECT codigo, nombre FROM ESTACION ORDER BY nombre")
    options = [("(Todas)", "(Todas las estaciones)")]
    for row in res["rows"]:
        options.append((row["CODIGO"], f"{row['NOMBRE']} ({row['CODIGO']})"))
    return options


def get_routes_lookup() -> List[Tuple[str, str]]:
    """
    Returns list of (codigo, display_label) for routes dropdowns.
    """
    res = execute_query("SELECT codigo, sentido FROM RUTA ORDER BY codigo")
    options = [("(Todas)", "(Todas las rutas)")]
    for row in res["rows"]:
        options.append((row["CODIGO"], f"{row['CODIGO']} - {row['SENTIDO']}"))
    return options


def get_orders_lookup() -> List[Tuple[str, str]]:
    """
    Returns list of (numero_orden, display_label) for maintenance orders dropdowns.
    """
    res = execute_query("SELECT numero_orden, tipo_mantenimiento FROM ORDEN_MANTENIMIENTO ORDER BY numero_orden")
    options = [("(Todas)", "(Todas las órdenes)")]
    for row in res["rows"]:
        options.append((row["NUMERO_ORDEN"], f"{row['NUMERO_ORDEN']} - {row['TIPO_MANTENIMIENTO']}"))
    return options

