"""
m7_incidents_service.py - Servicio backend para el Modulo 7: Incidentes Operativos y Contingencias.
Gestiona el registro de anomalías en la red, elementos afectados con restricción de Arco Exclusivo,
despacho y cancelación masiva de viajes (SP_CANCELAR_VIAJES_AFECTADOS), resolución técnica de incidentes,
consulta de la tabla de auditoría BITACORA y métricas estadísticas de la red.
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import oracledb

from services.db import get_connection, execute_query
from services.actions_service import (
    registrar_incidente as sp_registrar_incidente,
    cancelar_viajes_afectados as sp_cancelar_viajes_afectados,
    parse_oracle_error
)


# ==============================================================================
# 1. CATALOGO Y GESTION DE INCIDENTES (INCIDENTE)
# ==============================================================================

def get_incidentes(
    estado_filter: Optional[str] = None,
    severidad_filter: Optional[str] = None,
    tipo_filter: Optional[str] = None,
    search_text: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retorna la lista de incidentes operativos con reportero resuelto, elementos
    afectados concatenados y calculo de duracion del evento.
    """
    sql = """
        SELECT i.id_incidente,
               i.numero_incidente,
               i.tipo,
               i.descripcion,
               TO_CHAR(i.fecha_hora_inicio, 'YYYY-MM-DD HH24:MI') AS fecha_hora_inicio,
               TO_CHAR(i.fecha_hora_fin, 'YYYY-MM-DD HH24:MI') AS fecha_hora_fin,
               i.nivel_severidad,
               i.reportado_por_id,
               NVL(emp.nombre_completo, 'No asignado') AS reportado_por,
               i.estado,
               NVL(i.causa_identificada, 'En Investigación') AS causa_identificada,
               NVL(i.acciones_realizadas, 'En Evaluación') AS acciones_realizadas,
               NVL(i.pasajeros_afectados_estimado, 0) AS pasajeros_afectados_estimado,
               CASE
                   WHEN i.fecha_hora_fin IS NOT NULL THEN
                       ROUND((CAST(i.fecha_hora_fin AS DATE) - CAST(i.fecha_hora_inicio AS DATE)) * 24 * 60)
                   ELSE
                       ROUND((SYSDATE - CAST(i.fecha_hora_inicio AS DATE)) * 24 * 60)
               END AS duracion_minutos,
               (
                   SELECT LISTAGG(
                       a.tipo_elemento || ': ' || 
                       NVL(e.nombre, NVL(t.codigo_interno, NVL(r.codigo, NVL(lin.codigo, NVL(eq.codigo_equipo, NVL(vp.numero_viaje, 'General')))))),
                       ' | '
                   ) WITHIN GROUP (ORDER BY a.id_incidente_elemento)
                   FROM INCIDENTE_ELEMENTO_AFECTADO a
                   LEFT JOIN ESTACION e ON a.estacion_id = e.id_estacion
                   LEFT JOIN TREN t ON a.tren_id = t.id_tren
                   LEFT JOIN RUTA r ON a.ruta_id = r.id_ruta
                   LEFT JOIN LINEA lin ON a.linea_id = lin.id_linea
                   LEFT JOIN EQUIPO eq ON a.equipo_id = eq.id_equipo
                   LEFT JOIN VIAJE_PROGRAMADO vp ON a.viaje_id = vp.id_viaje
                   WHERE a.incidente_id = i.id_incidente
               ) AS elementos_afectados_str,
               (SELECT COUNT(*) FROM INCIDENTE_ELEMENTO_AFECTADO a WHERE a.incidente_id = i.id_incidente) AS total_elementos_afectados
        FROM INCIDENTE i
        LEFT JOIN EMPLEADO emp ON i.reportado_por_id = emp.id_empleado
        WHERE 1 = 1
    """
    params: Dict[str, Any] = {}

    if estado_filter and estado_filter != "(Todos)":
        sql += " AND i.estado = :estado"
        params["estado"] = estado_filter

    if severidad_filter and severidad_filter != "(Todas)":
        sql += " AND i.nivel_severidad = :sev"
        params["sev"] = severidad_filter

    if tipo_filter and tipo_filter != "(Todos)":
        sql += " AND i.tipo = :tipo"
        params["tipo"] = tipo_filter

    if search_text and search_text.strip():
        sql += """ AND (
            UPPER(i.numero_incidente) LIKE UPPER(:st) OR
            UPPER(i.descripcion) LIKE UPPER(:st) OR
            UPPER(i.causa_identificada) LIKE UPPER(:st) OR
            UPPER(i.acciones_realizadas) LIKE UPPER(:st)
        )"""
        params["st"] = f"%{search_text.strip()}%"

    sql += " ORDER BY i.id_incidente DESC"
    return execute_query(sql, params)["rows"]


def get_incidente_by_id(id_incidente: int) -> Optional[Dict[str, Any]]:
    """Obtiene el detalle estructurado de un incidente especifico."""
    sql = """
        SELECT i.id_incidente,
               i.numero_incidente,
               i.tipo,
               i.descripcion,
               TO_CHAR(i.fecha_hora_inicio, 'YYYY-MM-DD HH24:MI') AS fecha_hora_inicio,
               TO_CHAR(i.fecha_hora_fin, 'YYYY-MM-DD HH24:MI') AS fecha_hora_fin,
               i.nivel_severidad,
               i.reportado_por_id,
               NVL(emp.nombre_completo, 'No asignado') AS reportado_por,
               i.estado,
               i.causa_identificada,
               i.acciones_realizadas,
               i.pasajeros_afectados_estimado
        FROM INCIDENTE i
        LEFT JOIN EMPLEADO emp ON i.reportado_por_id = emp.id_empleado
        WHERE i.id_incidente = :id_inc
    """
    rows = execute_query(sql, {"id_inc": int(id_incidente)})["rows"]
    if not rows:
        return None
    data = rows[0]
    data["elementos"] = get_elementos_afectados(id_incidente)
    return data


def registrar_incidente(
    tipo: str,
    descripcion: str,
    nivel_severidad: str,
    reportado_por_id: int,
    tipo_elemento: Optional[str] = None,
    elemento_id: Optional[int] = None,
    tipo_afectacion: str = "Retraso"
) -> Dict[str, Any]:
    """
    Registra un incidente invocando el procedimiento canonico SP_REGISTRAR_INCIDENTE.
    El trigger TRG_INCIDENTE_AUDITORIA inserta automaticamente la operacion en BITACORA.
    """
    return sp_registrar_incidente(
        tipo=tipo,
        descripcion=descripcion.strip(),
        nivel_severidad=nivel_severidad,
        reportado_por_id=int(reportado_por_id),
        tipo_elemento=tipo_elemento,
        elemento_id=int(elemento_id) if elemento_id else None,
        tipo_afectacion=tipo_afectacion
    )


def cambiar_estado(id_incidente: int, nuevo_estado: str) -> Dict[str, Any]:
    """Actualiza el estado de un incidente ('Abierto', 'En Atención', 'Cerrado')."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = "UPDATE INCIDENTE SET estado = :est WHERE id_incidente = :id_inc"
        cursor.execute(sql, {"est": nuevo_estado, "id_inc": int(id_incidente)})
        conn.commit()
        return {"success": True, "mensaje": f"Estado del incidente actualizado a '{nuevo_estado}'."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def cerrar_incidente(
    id_incidente: int,
    causa_identificada: str,
    acciones_realizadas: str,
    pasajeros_afectados: int,
    fecha_fin: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cierra formalmente un incidente operativo registrando la causa raiz,
    acciones correctivas, estimacion de pasajeros y fecha de finalizacion.
    El trigger TRG_INCIDENTE_AUDITORIA registra la actualizacion en BITACORA.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE INCIDENTE
            SET estado = 'Cerrado',
                causa_identificada = :causa,
                acciones_realizadas = :acciones,
                pasajeros_afectados_estimado = :pasajeros,
                fecha_hora_fin = NVL(TO_TIMESTAMP(:f_fin, 'YYYY-MM-DD HH24:MI'), SYSTIMESTAMP)
            WHERE id_incidente = :id_inc
        """
        cursor.execute(sql, {
            "causa": causa_identificada.strip(),
            "acciones": acciones_realizadas.strip(),
            "pasajeros": int(pasajeros_afectados),
            "f_fin": fecha_fin if fecha_fin else None,
            "id_inc": int(id_incidente)
        })
        conn.commit()
        return {
            "success": True,
            "mensaje": f"Incidente {id_incidente} cerrado exitosamente. Auditoría registrada en BITACORA."
        }
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 2. ELEMENTOS AFECTADOS Y ARCO EXCLUSIVO (INCIDENTE_ELEMENTO_AFECTADO)
# ==============================================================================

def get_elementos_afectados(incidente_id: int) -> List[Dict[str, Any]]:
    """
    Retorna los elementos de la red asociados a un incidente, resolviendo nombres
    e identificadores segun el tipo de elemento.
    """
    sql = """
        SELECT a.id_incidente_elemento,
               a.incidente_id,
               a.tipo_elemento,
               a.tipo_afectacion,
               a.estacion_id,
               a.tren_id,
               a.ruta_id,
               a.linea_id,
               a.equipo_id,
               a.viaje_id,
               CASE
                   WHEN a.tipo_elemento = 'ESTACION' THEN (SELECT e.nombre || ' (' || e.codigo || ')' FROM ESTACION e WHERE e.id_estacion = a.estacion_id)
                   WHEN a.tipo_elemento = 'TREN' THEN (SELECT t.codigo_interno || ' [' || m.nombre_modelo || ']' FROM TREN t JOIN MODELO_TREN m ON t.modelo_id = m.id_modelo WHERE t.id_tren = a.tren_id)
                   WHEN a.tipo_elemento = 'RUTA' THEN (SELECT 'Ruta ' || r.codigo || ' (' || r.sentido || ')' FROM RUTA r WHERE r.id_ruta = a.ruta_id)
                   WHEN a.tipo_elemento = 'LINEA' THEN (SELECT 'Línea ' || lin.codigo || ' - ' || lin.nombre FROM LINEA lin WHERE lin.id_linea = a.linea_id)
                   WHEN a.tipo_elemento = 'EQUIPO' THEN (SELECT eq.codigo_equipo || ' (' || eq.tipo_equipo || ')' FROM EQUIPO eq WHERE eq.id_equipo = a.equipo_id)
                   WHEN a.tipo_elemento = 'VIAJE_PROGRAMADO' THEN (SELECT 'Viaje ' || vp.numero_viaje FROM VIAJE_PROGRAMADO vp WHERE vp.id_viaje = a.viaje_id)
                   ELSE 'Elemento Desconocido'
               END AS elemento_nombre
        FROM INCIDENTE_ELEMENTO_AFECTADO a
        WHERE a.incidente_id = :inc_id
        ORDER BY a.id_incidente_elemento
    """
    return execute_query(sql, {"inc_id": int(incidente_id)})["rows"]


def asociar_elemento_afectado(
    incidente_id: int,
    tipo_elemento: str,
    elemento_id: int,
    tipo_afectacion: str = "Retraso"
) -> Dict[str, Any]:
    """
    Inserta un elemento afectado en INCIDENTE_ELEMENTO_AFECTADO garantizando el
    cumplimiento estricto del Arco Exclusivo (CK_INCIDENTE_ELEMENTO_ARCO):
    exactamente una sola columna de FK debe poblarse segun tipo_elemento.
    """
    tipos_validos = ["ESTACION", "TREN", "RUTA", "LINEA", "EQUIPO", "VIAJE_PROGRAMADO"]
    if tipo_elemento not in tipos_validos:
        return {"success": False, "error": f"Tipo de elemento no válido: {tipo_elemento}"}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        v_est_id: Optional[int] = None
        v_tren_id: Optional[int] = None
        v_ruta_id: Optional[int] = None
        v_linea_id: Optional[int] = None
        v_equipo_id: Optional[int] = None
        v_viaje_id: Optional[int] = None

        if tipo_elemento == "ESTACION":
            v_est_id = int(elemento_id)
        elif tipo_elemento == "TREN":
            v_tren_id = int(elemento_id)
        elif tipo_elemento == "RUTA":
            v_ruta_id = int(elemento_id)
        elif tipo_elemento == "LINEA":
            v_linea_id = int(elemento_id)
        elif tipo_elemento == "EQUIPO":
            v_equipo_id = int(elemento_id)
        elif tipo_elemento == "VIAJE_PROGRAMADO":
            v_viaje_id = int(elemento_id)

        v_id = cursor.var(oracledb.NUMBER)
        sql = """
            INSERT INTO INCIDENTE_ELEMENTO_AFECTADO (
                id_incidente_elemento, incidente_id, tipo_elemento,
                estacion_id, tren_id, ruta_id, linea_id, equipo_id, viaje_id,
                tipo_afectacion
            ) VALUES (
                SEQ_INCIDENTE_ELEMENTO_AF_F066.NEXTVAL, :inc_id, :tipo_elem,
                :est_id, :tren_id, :ruta_id, :linea_id, :eq_id, :viaje_id,
                :tipo_af
            ) RETURNING id_incidente_elemento INTO :v_id
        """
        cursor.execute(sql, {
            "inc_id": int(incidente_id),
            "tipo_elem": tipo_elemento,
            "est_id": v_est_id,
            "tren_id": v_tren_id,
            "ruta_id": v_ruta_id,
            "linea_id": v_linea_id,
            "eq_id": v_equipo_id,
            "viaje_id": v_viaje_id,
            "tipo_af": tipo_afectacion,
            "v_id": v_id
        })
        conn.commit()
        id_gen = int(v_id.getvalue()[0])
        return {
            "success": True,
            "id_incidente_elemento": id_gen,
            "mensaje": f"Elemento {tipo_elemento} asociado exitosamente con afectación '{tipo_afectacion}'."
        }
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def modificar_afectacion_elemento(id_incidente_elemento: int, nuevo_tipo_afectacion: str) -> Dict[str, Any]:
    """Modifica el tipo de afectacion operativa de un elemento de red."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = "UPDATE INCIDENTE_ELEMENTO_AFECTADO SET tipo_afectacion = :af WHERE id_incidente_elemento = :id_ie"
        cursor.execute(sql, {"af": nuevo_tipo_afectacion, "id_ie": int(id_incidente_elemento)})
        conn.commit()
        return {"success": True, "mensaje": "Tipo de afectación actualizado correctamente."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def desvincular_elemento(id_incidente_elemento: int) -> Dict[str, Any]:
    """Desvincula un elemento de red del incidente."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = "DELETE FROM INCIDENTE_ELEMENTO_AFECTADO WHERE id_incidente_elemento = :id_ie"
        cursor.execute(sql, {"id_ie": int(id_incidente_elemento)})
        conn.commit()
        return {"success": True, "mensaje": "Elemento desvinculado del incidente."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 3. DESPACHO Y CANCELACION MASIVA DE VIAJES
# ==============================================================================

def get_viajes_potencialmente_afectados(incidente_id: int) -> List[Dict[str, Any]]:
    """
    Retorna la lista de viajes programados que intersectan con los elementos de red
    afectados por el incidente (estacion, ruta, linea).
    """
    sql = """
        SELECT vp.id_viaje,
               vp.numero_viaje,
               r.codigo AS ruta_codigo,
               l.codigo AS linea_codigo,
               l.nombre AS linea_nombre,
               t.codigo_interno AS tren_codigo,
               emp.nombre_completo AS conductor,
               TO_CHAR(vp.fecha, 'YYYY-MM-DD') AS fecha,
               TO_CHAR(vp.hora_prog_salida, 'HH24:MI') AS salida,
               TO_CHAR(vp.hora_prog_llegada, 'HH24:MI') AS llegada,
               vp.estado
        FROM VIAJE_PROGRAMADO vp
        JOIN RUTA r ON vp.ruta_id = r.id_ruta
        JOIN LINEA l ON r.linea_id = l.id_linea
        JOIN TREN t ON vp.tren_id = t.id_tren
        LEFT JOIN EMPLEADO emp ON vp.conductor_id = emp.id_empleado
        WHERE vp.estado IN ('Programado', 'En Abordaje')
          AND (
              vp.ruta_id IN (
                  SELECT a.ruta_id FROM INCIDENTE_ELEMENTO_AFECTADO a
                  WHERE a.incidente_id = :inc_id AND a.ruta_id IS NOT NULL
              )
              OR r.linea_id IN (
                  SELECT a.linea_id FROM INCIDENTE_ELEMENTO_AFECTADO a
                  WHERE a.incidente_id = :inc_id AND a.linea_id IS NOT NULL
              )
              OR vp.ruta_id IN (
                  SELECT rd.ruta_id FROM RUTA_DETALLE rd
                  JOIN INCIDENTE_ELEMENTO_AFECTADO a ON rd.estacion_id = a.estacion_id
                  WHERE a.incidente_id = :inc_id
              )
              OR vp.tren_id IN (
                  SELECT a.tren_id FROM INCIDENTE_ELEMENTO_AFECTADO a
                  WHERE a.incidente_id = :inc_id AND a.tren_id IS NOT NULL
              )
          )
        ORDER BY vp.fecha, vp.hora_prog_salida
    """
    return execute_query(sql, {"inc_id": int(incidente_id)})["rows"]


def despachar_cancelacion_viajes(incidente_id: int) -> Dict[str, Any]:
    """
    Ejecuta el procedimiento canonico SP_CANCELAR_VIAJES_AFECTADOS para cancelar
    de forma atómica todos los viajes programados impactados por el incidente.
    """
    return sp_cancelar_viajes_afectados(int(incidente_id))


# ==============================================================================
# 4. BITACORA DE AUDITORIA EN TIEMPO REAL (BITACORA)
# ==============================================================================

def get_bitacora_incidentes(search_text: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Consulta la bitacora de auditoria del sistema generada automaticamente por
    el trigger TRG_INCIDENTE_AUDITORIA ante eventos sobre la tabla INCIDENTE.
    """
    sql = f"""
        SELECT b.id_bitacora,
               TO_CHAR(b.fecha_hora, 'YYYY-MM-DD HH24:MI:SS') AS fecha_hora,
               b.tabla_afectada,
               b.operacion,
               b.registro_id,
               b.usuario,
               b.descripcion
        FROM BITACORA b
        WHERE b.tabla_afectada = 'INCIDENTE'
    """
    params: Dict[str, Any] = {}
    if search_text and search_text.strip():
        sql += " AND (UPPER(b.descripcion) LIKE UPPER(:st) OR UPPER(b.usuario) LIKE UPPER(:st))"
        params["st"] = f"%{search_text.strip()}%"

    sql += f" ORDER BY b.id_bitacora DESC FETCH FIRST {int(limit)} ROWS ONLY"
    return execute_query(sql, params)["rows"]


# ==============================================================================
# 5. KPIS Y ESTADISTICAS ANALITICAS DE RED
# ==============================================================================

def get_kpis_incidentes() -> Dict[str, Any]:
    """Retorna los indicadores de monitoreo en vivo para la cabecera del modulo."""
    sql = """
        SELECT
            (SELECT COUNT(*) FROM INCIDENTE WHERE estado != 'Cerrado') AS incidentes_activos,
            (SELECT COUNT(*) FROM INCIDENTE WHERE estado = 'En Atención') AS en_atencion,
            (SELECT COUNT(*) FROM INCIDENTE WHERE estado = 'Abierto') AS abiertos,
            (SELECT COUNT(*) FROM INCIDENTE WHERE estado != 'Cerrado' AND nivel_severidad IN ('Alto', 'Crítico')) AS criticos_altos,
            (SELECT NVL(SUM(pasajeros_afectados_estimado), 0) FROM INCIDENTE WHERE estado != 'Cerrado') AS pasajeros_afectados_activos,
            (SELECT COUNT(*) FROM VIAJE_PROGRAMADO WHERE estado = 'Cancelado') AS viajes_cancelados_total
        FROM DUAL
    """
    rows = execute_query(sql)["rows"]
    if rows:
        r = rows[0]
        return {
            "activos": int(r.get("INCIDENTES_ACTIVOS") or 0),
            "en_atencion": int(r.get("EN_ATENCION") or 0),
            "abiertos": int(r.get("ABIERTOS") or 0),
            "criticos_altos": int(r.get("CRITICOS_ALTOS") or 0),
            "pasajeros_afectados": int(r.get("PASAJEROS_AFECTADOS_ACTIVOS") or 0),
            "viajes_cancelados": int(r.get("VIAJES_CANCELADOS_TOTAL") or 0)
        }
    return {"activos": 0, "en_atencion": 0, "abiertos": 0, "criticos_altos": 0, "pasajeros_afectados": 0, "viajes_cancelados": 0}


def get_estadisticas_incidentes() -> Dict[str, Any]:
    """Retorna agregaciones estadisticas para la pestana de analiticas."""
    sql_sev = """
        SELECT nivel_severidad, COUNT(*) AS total
        FROM INCIDENTE
        GROUP BY nivel_severidad
        ORDER BY total DESC
    """
    sql_tipo = """
        SELECT tipo, COUNT(*) AS total
        FROM INCIDENTE
        GROUP BY tipo
        ORDER BY total DESC
    """
    sql_estado = """
        SELECT estado, COUNT(*) AS total
        FROM INCIDENTE
        GROUP BY estado
        ORDER BY total DESC
    """
    return {
        "por_severidad": execute_query(sql_sev)["rows"],
        "por_tipo": execute_query(sql_tipo)["rows"],
        "por_estado": execute_query(sql_estado)["rows"]
    }

