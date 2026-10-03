"""
m6_maintenance_service.py - Servicio backend para el Modulo 6: Mantenimiento.
Gestiona el catalogo de equipos e infraestructura, ordenes de trabajo preventivas y correctivas,
asignacion de cuadrillas tecnicas, consumo de repuestos y calculo de costos consolidados.
Cumple con los 9 requerimientos oficiales y las Reglas de Negocio 19 y 25.
"""
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date
import oracledb

from services.db import get_connection, execute_query
from services.actions_service import parse_oracle_error, crear_orden_mantenimiento as sp_crear_orden_mantenimiento


def _safe_int(val: Any, default: int = 0) -> int:
    try:
        if val is None or val == "-" or val == "":
            return default
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        if val is None or val == "-" or val == "":
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


# ==============================================================================
# VALIDACIONES DE NEGOCIO Y DOMINIO
# ==============================================================================

def _validar_datos_repuesto(
    codigo: str,
    nombre: str,
    costo_unitario: float,
    stock_disponible: int = 0
) -> Optional[str]:
    """Valida los datos de una pieza de repuesto antes de persistir."""
    if not codigo or not codigo.strip():
        return "El código de la pieza es obligatorio."
    cod = codigo.strip().upper()
    if not re.match(r"^REP-[A-Z0-9]{2,8}(-[A-Z0-9]{1,4})?$", cod):
        return "El código debe cumplir con el formato estándar de inventario (ej. REP-1001 o REP-BRK-01)."
    if not nombre or len(nombre.strip()) < 3:
        return "La denominación de la pieza debe contener al menos 3 caracteres."
    if len(nombre.strip()) > 100:
        return "La denominación de la pieza no puede exceder 100 caracteres."
    if costo_unitario < 0:
        return "El costo unitario no puede ser negativo."
    if stock_disponible < 0:
        return "El stock inicial disponible no puede ser negativo."
    return None


def _validar_datos_orden(
    equipo_id: int,
    tipo_mantenimiento: str,
    descripcion: str,
    prioridad: str
) -> Optional[str]:
    """Valida los datos principales para apertura de orden de mantenimiento."""
    if equipo_id <= 0:
        return "Debe seleccionar un activo o equipo válido."
    tipos_validos = ("Preventivo", "Correctivo", "Predictivo", "Inspección de Seguridad")
    if tipo_mantenimiento not in tipos_validos:
        return f"Tipo de mantenimiento inválido. Permitidos: {', '.join(tipos_validos)}."
    if not descripcion or len(descripcion.strip()) < 3:
        return "La descripción del trabajo debe contener al menos 3 caracteres."
    if len(descripcion.strip()) > 500:
        return "La descripción del trabajo no puede exceder 500 caracteres."
    prioridades_validas = ("Baja", "Media", "Alta", "Urgente")
    if prioridad not in prioridades_validas:
        return f"Prioridad inválida. Permitidas: {', '.join(prioridades_validas)}."
    return None



# ==============================================================================
# 1. CATALOGO DE EQUIPOS Y ACTIVOS (EQUIPO)
# ==============================================================================

def get_equipos(
    tipo_filter: Optional[str] = None,
    estado_filter: Optional[str] = None,
    search_text: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retorna la lista de activos de infraestructura registrados en EQUIPO,
    resolviendo la referencia polimorfica a estacion, plataforma o tren.
    """
    sql = """
        SELECT eq.id_equipo,
               eq.codigo_equipo,
               eq.tipo_equipo,
               eq.tipo_referencia,
               eq.referencia_id,
               eq.ubicacion,
               eq.fabricante,
               eq.modelo,
               eq.numero_serie,
               TO_CHAR(eq.fecha_instalacion, 'YYYY-MM-DD') AS fecha_instalacion,
               eq.estado,
               TO_CHAR(eq.fecha_ultima_revision, 'YYYY-MM-DD HH24:MI') AS fecha_ultima_revision,
               TO_CHAR(eq.fecha_proxima_revision, 'YYYY-MM-DD') AS fecha_proxima_revision,
               CASE
                   WHEN eq.fecha_proxima_revision IS NULL THEN 'Sin Programar'
                   WHEN TRUNC(eq.fecha_proxima_revision) < TRUNC(SYSDATE) THEN 'Inspeccion Vencida'
                   WHEN TRUNC(eq.fecha_proxima_revision) <= TRUNC(SYSDATE + 7) THEN 'Proxima a Vencer'
                   ELSE 'Al Dia'
               END AS alerta_inspeccion,
               CASE
                   WHEN eq.tipo_referencia = 'ESTACION' THEN (SELECT e.nombre FROM ESTACION e WHERE e.id_estacion = eq.referencia_id)
                   WHEN eq.tipo_referencia = 'TREN' THEN (SELECT t.codigo_interno FROM TREN t WHERE t.id_tren = eq.referencia_id)
                   WHEN eq.tipo_referencia = 'PLATAFORMA' THEN (SELECT p.identificador FROM PLATAFORMA p WHERE p.id_plataforma = eq.referencia_id)
                   WHEN eq.tipo_referencia = 'VAGON' THEN (SELECT v.numero_serie FROM VAGON v WHERE v.id_vagon = eq.referencia_id)
                   ELSE 'General'
               END AS referencia_nombre
        FROM EQUIPO eq
        WHERE 1 = 1
    """
    params: Dict[str, Any] = {}

    if tipo_filter and tipo_filter != "(Todos)":
        sql += " AND eq.tipo_equipo = :tipo"
        params["tipo"] = tipo_filter

    if estado_filter and estado_filter != "(Todos)":
        sql += " AND eq.estado = :estado"
        params["estado"] = estado_filter

    if search_text and search_text.strip():
        sql += """ AND (
            UPPER(eq.codigo_equipo) LIKE UPPER(:st) OR
            UPPER(eq.ubicacion) LIKE UPPER(:st) OR
            UPPER(eq.fabricante) LIKE UPPER(:st) OR
            UPPER(eq.modelo) LIKE UPPER(:st)
        )"""
        params["st"] = f"%{search_text.strip()}%"

    sql += " ORDER BY eq.id_equipo DESC"
    return execute_query(sql, params)["rows"]


def get_equipo_by_id(id_equipo: int) -> Optional[Dict[str, Any]]:
    """Obtiene el detalle completo de un equipo."""
    sql = """
        SELECT eq.id_equipo,
               eq.codigo_equipo,
               eq.tipo_equipo,
               eq.tipo_referencia,
               eq.referencia_id,
               eq.ubicacion,
               eq.fabricante,
               eq.modelo,
               eq.numero_serie,
               TO_CHAR(eq.fecha_instalacion, 'YYYY-MM-DD') AS fecha_instalacion,
               eq.estado,
               TO_CHAR(eq.fecha_ultima_revision, 'YYYY-MM-DD') AS fecha_ultima_revision,
               TO_CHAR(eq.fecha_proxima_revision, 'YYYY-MM-DD') AS fecha_proxima_revision
        FROM EQUIPO eq
        WHERE eq.id_equipo = :id_eq
    """
    rows = execute_query(sql, {"id_eq": int(id_equipo)})["rows"]
    return rows[0] if rows else None


def crear_equipo(
    codigo_equipo: str,
    tipo_equipo: str,
    tipo_referencia: str = "NINGUNO",
    referencia_id: Optional[int] = None,
    ubicacion: Optional[str] = None,
    fabricante: Optional[str] = None,
    modelo: Optional[str] = None,
    numero_serie: Optional[str] = None,
    fecha_instalacion: Optional[str] = None,
    estado: str = "Disponible",
    fecha_proxima_revision: Optional[str] = None
) -> Dict[str, Any]:
    """Registra un nuevo activo de infraestructura en EQUIPO."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        v_id = cursor.var(oracledb.NUMBER)
        sql = """
            INSERT INTO EQUIPO (
                id_equipo, codigo_equipo, tipo_equipo, tipo_referencia,
                referencia_id, ubicacion, fabricante, modelo, numero_serie,
                fecha_instalacion, estado, fecha_proxima_revision
            ) VALUES (
                SEQ_EQUIPO.NEXTVAL, :codigo, :tipo, :tipo_ref,
                :ref_id, :ubicacion, :fab, :modelo, :serie,
                TO_DATE(:f_inst, 'YYYY-MM-DD'), :estado, TO_DATE(:f_prox, 'YYYY-MM-DD')
            ) RETURNING id_equipo INTO :v_id
        """
        cursor.execute(sql, {
            "codigo": codigo_equipo.strip(),
            "tipo": tipo_equipo,
            "tipo_ref": tipo_referencia,
            "ref_id": referencia_id,
            "ubicacion": ubicacion.strip() if ubicacion else None,
            "fab": fabricante.strip() if fabricante else None,
            "modelo": modelo.strip() if modelo else None,
            "serie": numero_serie.strip() if numero_serie else None,
            "f_inst": fecha_instalacion if fecha_instalacion else None,
            "estado": estado,
            "f_prox": fecha_proxima_revision if fecha_proxima_revision else None,
            "v_id": v_id
        })
        conn.commit()
        id_gen = int(v_id.getvalue()[0])
        return {
            "success": True,
            "id_equipo": id_gen,
            "mensaje": f"Equipo {codigo_equipo} registrado exitosamente con ID {id_gen}."
        }
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def modificar_equipo(
    id_equipo: int,
    codigo_equipo: str,
    tipo_equipo: str,
    tipo_referencia: str,
    referencia_id: Optional[int],
    ubicacion: Optional[str],
    fabricante: Optional[str],
    modelo: Optional[str],
    numero_serie: Optional[str],
    estado: str,
    fecha_proxima_revision: Optional[str]
) -> Dict[str, Any]:
    """Modifica los atributos tecnicos y administrativos de un equipo existente."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE EQUIPO
            SET codigo_equipo = :codigo,
                tipo_equipo = :tipo,
                tipo_referencia = :tipo_ref,
                referencia_id = :ref_id,
                ubicacion = :ubicacion,
                fabricante = :fab,
                modelo = :modelo,
                numero_serie = :serie,
                estado = :estado,
                fecha_proxima_revision = TO_DATE(:f_prox, 'YYYY-MM-DD')
            WHERE id_equipo = :id_eq
        """
        cursor.execute(sql, {
            "codigo": codigo_equipo.strip(),
            "tipo": tipo_equipo,
            "tipo_ref": tipo_referencia,
            "ref_id": referencia_id,
            "ubicacion": ubicacion.strip() if ubicacion else None,
            "fab": fabricante.strip() if fabricante else None,
            "modelo": modelo.strip() if modelo else None,
            "serie": numero_serie.strip() if numero_serie else None,
            "estado": estado,
            "f_prox": fecha_proxima_revision if fecha_proxima_revision else None,
            "id_eq": int(id_equipo)
        })
        conn.commit()
        return {
            "success": True,
            "mensaje": f"Equipo {codigo_equipo} actualizado exitosamente."
        }
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def actualizar_fechas_inspeccion(
    id_equipo: int,
    fecha_ultima: Optional[str] = None,
    fecha_proxima: Optional[str] = None
) -> Dict[str, Any]:
    """Actualiza las fechas de revision tecnica de un equipo."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE EQUIPO
            SET fecha_ultima_revision = NVL(TO_DATE(:f_ult, 'YYYY-MM-DD'), SYSDATE),
                fecha_proxima_revision = TO_DATE(:f_prox, 'YYYY-MM-DD')
            WHERE id_equipo = :id_eq
        """
        cursor.execute(sql, {
            "f_ult": fecha_ultima,
            "f_prox": fecha_proxima,
            "id_eq": int(id_equipo)
        })
        conn.commit()
        return {"success": True, "mensaje": "Fechas de inspeccion actualizadas correctamente."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def verificar_dependencias_equipo(id_equipo: int) -> Dict[str, Any]:
    """Verifica si el equipo posee ordenes activas o historicas asociadas."""
    sql = """
        SELECT 
            (SELECT COUNT(*) FROM ORDEN_MANTENIMIENTO WHERE equipo_id = :id_eq) AS total_ordenes,
            (SELECT COUNT(*) FROM ORDEN_MANTENIMIENTO WHERE equipo_id = :id_eq AND estado IN ('En Ejecución', 'En Ejecucion', 'Programada', 'Solicitada')) AS ordenes_activas
        FROM DUAL
    """
    rows = execute_query(sql, {"id_eq": int(id_equipo)})["rows"]
    if rows:
        r = rows[0]
        tot = _safe_int(r.get("TOTAL_ORDENES"))
        act = _safe_int(r.get("ORDENES_ACTIVAS"))
        return {"total_ordenes": tot, "ordenes_activas": act, "tiene_dependencias": tot > 0}
    return {"total_ordenes": 0, "ordenes_activas": 0, "tiene_dependencias": False}


def dar_de_baja_equipo(id_equipo: int) -> Dict[str, Any]:
    """Da de baja un equipo de forma segura cambiando su estado a 'Retirado'."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM ORDEN_MANTENIMIENTO 
            WHERE equipo_id = :id_eq AND estado IN ('En Ejecución', 'En Ejecucion', 'Programada', 'Solicitada')
        """, {"id_eq": int(id_equipo)})
        count_act = int(cursor.fetchone()[0])
        if count_act > 0:
            return {
                "success": False,
                "error": f"No se puede dar de baja el activo {id_equipo} porque tiene {count_act} orden(es) activa(s) en ejecución. Finalícelas o cancélelas primero."
            }

        cursor.execute("UPDATE EQUIPO SET estado = 'Retirado' WHERE id_equipo = :id_eq", {"id_eq": int(id_equipo)})
        conn.commit()
        return {"success": True, "mensaje": f"Activo {id_equipo} dado de baja exitosamente (Estado: 'Retirado')."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def eliminar_equipo(id_equipo: int) -> Dict[str, Any]:
    """
    Elimina un equipo si no posee ordenes de mantenimiento o incidentes historicos
    asociados (Regla 25: integridad referencial).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Verificar ordenes activas o historicas
        cursor.execute(
            "SELECT COUNT(*) FROM ORDEN_MANTENIMIENTO WHERE equipo_id = :id_eq",
            {"id_eq": int(id_equipo)}
        )
        row = cursor.fetchone()
        count_ordenes = int(row[0]) if row else 0
        if count_ordenes > 0:
            return {
                "success": False,
                "error": f"No se puede eliminar el equipo {id_equipo} porque registra {count_ordenes} orden(es) de mantenimiento historica(s). Modifique su estado a 'Fuera de Servicio' o 'Retirado'."
            }

        cursor.execute("DELETE FROM EQUIPO WHERE id_equipo = :id_eq", {"id_eq": int(id_equipo)})
        conn.commit()
        return {"success": True, "mensaje": f"Equipo {id_equipo} eliminado del sistema."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 2. ORDENES DE MANTENIMIENTO (ORDEN_MANTENIMIENTO)
# ==============================================================================

def get_ordenes(
    estado_filter: Optional[str] = None,
    tipo_filter: Optional[str] = None,
    prioridad_filter: Optional[str] = None,
    search_text: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retorna la lista completa de ordenes de mantenimiento con datos de equipo,
    tecnico lider asignado y costo total acumulado.
    """
    sql = """
        SELECT om.id_orden,
               om.numero_orden,
               om.equipo_id,
               eq.codigo_equipo,
               eq.tipo_equipo,
               eq.ubicacion AS ubicacion_equipo,
               om.tipo_mantenimiento,
               om.descripcion_trabajo,
               TO_CHAR(om.fecha_solicitud, 'YYYY-MM-DD HH24:MI') AS fecha_solicitud,
               TO_CHAR(om.fecha_programada, 'YYYY-MM-DD') AS fecha_programada,
               TO_CHAR(om.fecha_inicio, 'YYYY-MM-DD HH24:MI') AS fecha_inicio,
               TO_CHAR(om.fecha_finalizacion, 'YYYY-MM-DD HH24:MI') AS fecha_finalizacion,
               om.prioridad,
               om.costo AS costo_base,
               NVL((SELECT SUM(r.costo_total) FROM ORDEN_REPUESTO r WHERE r.orden_id = om.id_orden), 0) AS costo_repuestos,
               (NVL(om.costo, 0) + NVL((SELECT SUM(r.costo_total) FROM ORDEN_REPUESTO r WHERE r.orden_id = om.id_orden), 0)) AS costo_total_calculado,
               om.estado,
               NVL(
                   (SELECT emp.nombre_completo 
                    FROM ORDEN_TECNICO ot 
                    JOIN EMPLEADO emp ON ot.empleado_id = emp.id_empleado 
                    WHERE ot.orden_id = om.id_orden AND ROWNUM = 1),
                   'Sin Tecnico Asignado'
               ) AS tecnico_lider,
               (SELECT COUNT(*) FROM ORDEN_TECNICO ot WHERE ot.orden_id = om.id_orden) AS total_tecnicos,
               (SELECT COUNT(*) FROM ORDEN_REPUESTO r WHERE r.orden_id = om.id_orden) AS total_repuestos
        FROM ORDEN_MANTENIMIENTO om
        JOIN EQUIPO eq ON om.equipo_id = eq.id_equipo
        WHERE 1 = 1
    """
    params: Dict[str, Any] = {}

    if estado_filter and estado_filter != "(Todos)":
        sql += " AND om.estado = :estado"
        params["estado"] = estado_filter

    if tipo_filter and tipo_filter != "(Todos)":
        sql += " AND om.tipo_mantenimiento = :tipo"
        params["tipo"] = tipo_filter

    if prioridad_filter and prioridad_filter != "(Todos)":
        sql += " AND om.prioridad = :prioridad"
        params["prioridad"] = prioridad_filter

    if search_text and search_text.strip():
        sql += """ AND (
            UPPER(om.numero_orden) LIKE UPPER(:st) OR
            UPPER(eq.codigo_equipo) LIKE UPPER(:st) OR
            UPPER(om.descripcion_trabajo) LIKE UPPER(:st) OR
            UPPER(eq.ubicacion) LIKE UPPER(:st)
        )"""
        params["st"] = f"%{search_text.strip()}%"

    sql += " ORDER BY om.id_orden DESC"
    return execute_query(sql, params)["rows"]


def get_orden_detalle(id_orden: int) -> Optional[Dict[str, Any]]:
    """Obtiene informacion detallada de una orden de mantenimiento."""
    sql = """
        SELECT om.id_orden,
               om.numero_orden,
               om.equipo_id,
               eq.codigo_equipo,
               eq.tipo_equipo,
               eq.tipo_referencia,
               eq.referencia_id,
               eq.ubicacion,
               om.tipo_mantenimiento,
               om.descripcion_trabajo,
               TO_CHAR(om.fecha_solicitud, 'YYYY-MM-DD HH24:MI') AS fecha_solicitud,
               TO_CHAR(om.fecha_programada, 'YYYY-MM-DD') AS fecha_programada,
               TO_CHAR(om.fecha_inicio, 'YYYY-MM-DD HH24:MI') AS fecha_inicio,
               TO_CHAR(om.fecha_finalizacion, 'YYYY-MM-DD HH24:MI') AS fecha_finalizacion,
               om.prioridad,
               om.costo AS costo_base,
               om.estado
        FROM ORDEN_MANTENIMIENTO om
        JOIN EQUIPO eq ON om.equipo_id = eq.id_equipo
        WHERE om.id_orden = :id_ord
    """
    rows = execute_query(sql, {"id_ord": int(id_orden)})["rows"]
    if not rows:
        return None
    data = rows[0]
    data["tecnicos"] = get_tecnicos_por_orden(id_orden)
    data["repuestos"] = get_repuestos_por_orden(id_orden)
    data["costo_total"] = calcular_costo_total_orden(id_orden)
    return data


def crear_orden(
    equipo_id: int,
    tipo_mantenimiento: str,
    descripcion: str,
    prioridad: str = "Media",
    tecnico_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Crea una nueva orden de mantenimiento invocando el procedimiento canonico
    SP_CREAR_ORDEN_MANTENIMIENTO.
    Actualiza automaticamente el estado del equipo y tren a 'En Mantenimiento'.
    """
    err = _validar_datos_orden(equipo_id, tipo_mantenimiento, descripcion, prioridad)
    if err:
        return {"success": False, "error": err}

    return sp_crear_orden_mantenimiento(
        equipo_id=int(equipo_id),
        tipo_mantenimiento=tipo_mantenimiento,
        descripcion=descripcion.strip(),
        prioridad=prioridad,
        tecnico_id=int(tecnico_id) if tecnico_id else None
    )


def cambiar_estado_orden(id_orden: int, nuevo_estado: str) -> Dict[str, Any]:
    """Actualiza el estado de una orden de trabajo."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = "UPDATE ORDEN_MANTENIMIENTO SET estado = :est WHERE id_orden = :id_ord"
        cursor.execute(sql, {"est": nuevo_estado, "id_ord": int(id_orden)})
        conn.commit()
        return {"success": True, "mensaje": f"Estado de la orden actualizado a '{nuevo_estado}'."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def completar_orden(
    id_orden: int,
    costo_final: Optional[float] = None,
    fecha_fin: Optional[str] = None,
    dias_proxima_revision: int = 90
) -> Dict[str, Any]:
    """
    Finaliza formalmente una orden de mantenimiento invocando el procedimiento
    canonico SP_CERRAR_ORDEN_MANTENIMIENTO:
    1. Valida cuadrilla de tecnicos asignada (TRG_ORDEN_MANT_VALIDAR_CIERRE).
    2. Establece estado = 'Completada' y fecha_finalizacion auditada.
    3. Actualiza el costo acumulado con FN_COSTO_ORDEN_MANTENIMIENTO o el valor auditado.
    4. Restaura el estado del equipo y tren a 'Disponible' y programa proxima inspeccion.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        v_msg = cursor.var(oracledb.STRING)
        f_date = None
        if fecha_fin and fecha_fin.strip():
            try:
                f_date = datetime.strptime(fecha_fin.strip(), "%Y-%m-%d %H:%M")
            except ValueError:
                try:
                    f_date = datetime.strptime(fecha_fin.strip(), "%Y-%m-%d")
                except ValueError:
                    f_date = None

        cursor.callproc("SP_CERRAR_ORDEN_MANTENIMIENTO", [
            int(id_orden),
            float(costo_final) if costo_final is not None else None,
            f_date,
            int(dias_proxima_revision),
            v_msg
        ])
        conn.commit()
        msg_val = v_msg.getvalue()
        return {
            "success": True,
            "mensaje": str(msg_val or f"Orden {id_orden} completada exitosamente.")
        }
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def cancelar_orden(id_orden: int) -> Dict[str, Any]:
    """
    Cancela una orden de mantenimiento de forma segura (Regla 25).
    Restaura el equipo y tren si no existen otras ordenes activas en ejecucion.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT om.equipo_id, eq.tipo_referencia, eq.referencia_id
            FROM ORDEN_MANTENIMIENTO om
            JOIN EQUIPO eq ON om.equipo_id = eq.id_equipo
            WHERE om.id_orden = :id_ord
        """, {"id_ord": int(id_orden)})
        row = cursor.fetchone()
        if not row:
            return {"success": False, "error": f"Orden {id_orden} no encontrada."}

        equipo_id = int(row[0])
        tipo_ref = str(row[1] or "NINGUNO")
        ref_id = int(row[2]) if row[2] is not None else None

        cursor.execute("UPDATE ORDEN_MANTENIMIENTO SET estado = 'Cancelada' WHERE id_orden = :id_ord", {"id_ord": int(id_orden)})

        # Verificar si hay otras ordenes activas sobre el mismo equipo
        cursor.execute("""
            SELECT COUNT(*) 
            FROM ORDEN_MANTENIMIENTO 
            WHERE equipo_id = :id_eq AND estado IN ('En Ejecución', 'Programada', 'Solicitada')
        """, {"id_eq": equipo_id})
        count_activas = int(cursor.fetchone()[0])

        if count_activas == 0:
            cursor.execute("UPDATE EQUIPO SET estado = 'Disponible' WHERE id_equipo = :id_eq", {"id_eq": equipo_id})
            if tipo_ref == "TREN" and ref_id is not None:
                cursor.execute("UPDATE TREN SET estado_operativo = 'Disponible' WHERE id_tren = :id_tren", {"id_tren": ref_id})

        conn.commit()
        return {"success": True, "mensaje": f"Orden {id_orden} cancelada exitosamente."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 3. ASIGNACION DE TECNICOS Y CUADRILLAS (ORDEN_TECNICO)
# ==============================================================================

def get_tecnicos_disponibles() -> List[Dict[str, Any]]:
    """
    Retorna la lista de empleados capacitados con cargo 'Técnico de Mantenimiento'
    y estado laboral 'Activo'.
    """
    sql = """
        SELECT e.id_empleado,
               e.numero_empleado,
               e.nombre_completo,
               e.cargo,
               e.telefono,
               e.correo_electronico,
               (SELECT COUNT(*) FROM ORDEN_TECNICO ot 
                JOIN ORDEN_MANTENIMIENTO om ON ot.orden_id = om.id_orden 
                WHERE ot.empleado_id = e.id_empleado AND om.estado IN ('En Ejecución', 'Programada')) AS ordenes_activas
        FROM EMPLEADO e
        WHERE (e.cargo LIKE '%T%cnico%' OR e.cargo = 'Técnico de Mantenimiento')
          AND e.estado_laboral = 'Activo'
        ORDER BY e.nombre_completo
    """
    return execute_query(sql)["rows"]


def get_tecnicos_por_orden(orden_id: int) -> List[Dict[str, Any]]:
    """Retorna los tecnicos asignados a una orden especifica."""
    sql = """
        SELECT ot.id_orden_tecnico,
               ot.orden_id,
               ot.empleado_id,
               e.numero_empleado,
               e.nombre_completo,
               e.cargo,
               e.telefono,
               ot.rol_en_orden
        FROM ORDEN_TECNICO ot
        JOIN EMPLEADO e ON ot.empleado_id = e.id_empleado
        WHERE ot.orden_id = :ord_id
        ORDER BY ot.id_orden_tecnico
    """
    return execute_query(sql, {"ord_id": int(orden_id)})["rows"]


def asignar_tecnico_a_orden(
    orden_id: int,
    empleado_id: int,
    rol_en_orden: str = "Técnico Especialista"
) -> Dict[str, Any]:
    """Asigna un tecnico a una orden de mantenimiento."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        v_id = cursor.var(oracledb.NUMBER)
        sql = """
            INSERT INTO ORDEN_TECNICO (
                id_orden_tecnico, orden_id, empleado_id, rol_en_orden
            ) VALUES (
                SEQ_ORDEN_TECNICO.NEXTVAL, :ord_id, :emp_id, :rol
            ) RETURNING id_orden_tecnico INTO :v_id
        """
        cursor.execute(sql, {
            "ord_id": int(orden_id),
            "emp_id": int(empleado_id),
            "rol": rol_en_orden.strip(),
            "v_id": v_id
        })
        conn.commit()
        id_gen = int(v_id.getvalue()[0])
        return {
            "success": True,
            "id_orden_tecnico": id_gen,
            "mensaje": f"Técnico asignado a la orden {orden_id} con rol '{rol_en_orden}'."
        }
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def modificar_rol_tecnico(id_orden_tecnico: int, nuevo_rol: str) -> Dict[str, Any]:
    """Modifica el rol de un tecnico en la orden de trabajo."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = "UPDATE ORDEN_TECNICO SET rol_en_orden = :rol WHERE id_orden_tecnico = :id_ot"
        cursor.execute(sql, {"rol": nuevo_rol.strip(), "id_ot": int(id_orden_tecnico)})
        conn.commit()
        return {"success": True, "mensaje": "Rol de técnico actualizado correctamente."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def desasignar_tecnico(id_orden_tecnico: int) -> Dict[str, Any]:
    """Remueve un tecnico de una orden de trabajo."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = "DELETE FROM ORDEN_TECNICO WHERE id_orden_tecnico = :id_ot"
        cursor.execute(sql, {"id_ot": int(id_orden_tecnico)})
        conn.commit()
        return {"success": True, "mensaje": "Técnico removido de la orden de trabajo."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 4. REPUESTOS Y COSTOS (REPUESTO y ORDEN_REPUESTO)
# ==============================================================================

def get_catalogo_repuestos(search_text: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retorna el catalogo de repuestos utilizables en intervenciones con stock disponible."""
    sql = """
        SELECT r.id_repuesto,
               r.codigo,
               r.nombre,
               r.costo_unitario,
               r.stock_disponible,
               NVL((SELECT SUM(orp.cantidad) FROM ORDEN_REPUESTO orp WHERE orp.repuesto_id = r.id_repuesto), 0) AS total_consumido
        FROM REPUESTO r
        WHERE 1 = 1
    """
    params: Dict[str, Any] = {}
    if search_text and search_text.strip():
        sql += " AND (UPPER(r.codigo) LIKE UPPER(:st) OR UPPER(r.nombre) LIKE UPPER(:st))"
        params["st"] = f"%{search_text.strip()}%"

    sql += " ORDER BY r.codigo"
    try:
        return execute_query(sql, params)["rows"]
    except Exception as exc:
        err_msg = str(exc)
        if "ORA-00904" in err_msg or "STOCK_DISPONIBLE" in err_msg:
            legacy_sql = """
                SELECT r.id_repuesto,
                       r.codigo,
                       r.nombre,
                       r.costo_unitario,
                       50 AS stock_disponible,
                       NVL((SELECT SUM(orp.cantidad) FROM ORDEN_REPUESTO orp WHERE orp.repuesto_id = r.id_repuesto), 0) AS total_consumido
                FROM REPUESTO r
                WHERE 1 = 1
            """
            if search_text and search_text.strip():
                legacy_sql += " AND (UPPER(r.codigo) LIKE UPPER(:st) OR UPPER(r.nombre) LIKE UPPER(:st))"
            legacy_sql += " ORDER BY r.codigo"
            try:
                return execute_query(legacy_sql, params)["rows"]
            except Exception:
                return []
        return []


def crear_repuesto(
    codigo: str,
    nombre: str,
    costo_unitario: float,
    stock_disponible: int = 50
) -> Dict[str, Any]:
    """Registra una nueva pieza en el catalogo de REPUESTO."""
    err = _validar_datos_repuesto(codigo, nombre, costo_unitario, stock_disponible)
    if err:
        return {"success": False, "error": err}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        v_id = cursor.var(oracledb.NUMBER)
        sql = """
            INSERT INTO REPUESTO (id_repuesto, codigo, nombre, costo_unitario, stock_disponible)
            VALUES (SEQ_REPUESTO.NEXTVAL, :cod, :nom, :costo, :stock)
            RETURNING id_repuesto INTO :v_id
        """
        cursor.execute(sql, {
            "cod": codigo.strip().upper(),
            "nom": nombre.strip(),
            "costo": float(costo_unitario),
            "stock": int(stock_disponible),
            "v_id": v_id
        })
        conn.commit()
        id_gen = int(v_id.getvalue()[0])
        return {
            "success": True,
            "id_repuesto": id_gen,
            "mensaje": f"Repuesto {codigo.strip().upper()} registrado con ID {id_gen}."
        }
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def modificar_repuesto(
    id_repuesto: int,
    codigo: str,
    nombre: str,
    costo_unitario: float,
    stock_disponible: int = 50
) -> Dict[str, Any]:
    """Modifica el codigo, descripcion, costo unitario o stock de un repuesto."""
    err = _validar_datos_repuesto(codigo, nombre, costo_unitario, stock_disponible)
    if err:
        return {"success": False, "error": err}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE REPUESTO
            SET codigo = :cod,
                nombre = :nom,
                costo_unitario = :costo,
                stock_disponible = :stock
            WHERE id_repuesto = :id_rep
        """
        cursor.execute(sql, {
            "cod": codigo.strip().upper(),
            "nom": nombre.strip(),
            "costo": float(costo_unitario),
            "stock": int(stock_disponible),
            "id_rep": int(id_repuesto)
        })
        conn.commit()
        return {"success": True, "mensaje": f"Repuesto {codigo.strip().upper()} actualizado exitosamente."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def verificar_dependencias_repuesto(id_repuesto: int) -> Dict[str, Any]:
    """Verifica consumos historicos de un repuesto en ordenes de mantenimiento."""
    sql = "SELECT COUNT(*) AS total_consumos FROM ORDEN_REPUESTO WHERE repuesto_id = :id_rep"
    rows = execute_query(sql, {"id_rep": int(id_repuesto)})["rows"]
    tot = _safe_int(rows[0].get("TOTAL_CONSUMOS")) if rows else 0
    return {"total_consumos": tot, "tiene_dependencias": tot > 0}


def eliminar_repuesto(id_repuesto: int) -> Dict[str, Any]:
    """Elimina un repuesto si no tiene consumos historicos en ORDEN_REPUESTO."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM ORDEN_REPUESTO WHERE repuesto_id = :id_rep", {"id_rep": int(id_repuesto)})
        count_uso = int(cursor.fetchone()[0])
        if count_uso > 0:
            return {
                "success": False,
                "error": f"No se puede eliminar el repuesto {id_repuesto} porque registra {count_uso} consumo(s) en ordenes historicas."
            }

        cursor.execute("DELETE FROM REPUESTO WHERE id_repuesto = :id_rep", {"id_rep": int(id_repuesto)})
        conn.commit()
        return {"success": True, "mensaje": f"Repuesto {id_repuesto} eliminado del catalogo."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def get_repuestos_por_orden(orden_id: int) -> List[Dict[str, Any]]:
    """Retorna los repuestos consumidos en una orden con sus subtotales."""
    sql = """
        SELECT orp.id_orden_repuesto,
               orp.orden_id,
               orp.repuesto_id,
               r.codigo AS codigo_repuesto,
               r.nombre AS nombre_repuesto,
               r.costo_unitario,
               orp.cantidad,
               orp.costo_total
        FROM ORDEN_REPUESTO orp
        JOIN REPUESTO r ON orp.repuesto_id = r.id_repuesto
        WHERE orp.orden_id = :ord_id
        ORDER BY orp.id_orden_repuesto
    """
    return execute_query(sql, {"ord_id": int(orden_id)})["rows"]


def registrar_consumo_repuesto(
    orden_id: int,
    repuesto_id: int,
    cantidad: int
) -> Dict[str, Any]:
    """
    Registra el uso de un repuesto en una orden de mantenimiento.
    Calcula el costo total = cantidad * costo_unitario y descuenta del stock.
    """
    if cantidad <= 0:
        return {"success": False, "error": "La cantidad de repuestos debe ser mayor a cero."}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT costo_unitario, stock_disponible FROM REPUESTO WHERE id_repuesto = :id_rep", {"id_rep": int(repuesto_id)})
        row = cursor.fetchone()
        if not row:
            return {"success": False, "error": f"Repuesto ID {repuesto_id} no encontrado."}

        costo_unitario = _safe_float(row[0])
        stock_disp = _safe_int(row[1])

        if cantidad > stock_disp:
            return {
                "success": False,
                "error": f"Stock insuficiente en almacén ({stock_disp} disponible(s), solicitado: {cantidad})."
            }

        costo_total = round(cantidad * costo_unitario, 2)

        v_id = cursor.var(oracledb.NUMBER)
        sql = """
            INSERT INTO ORDEN_REPUESTO (
                id_orden_repuesto, orden_id, repuesto_id, cantidad, costo_total
            ) VALUES (
                SEQ_ORDEN_REPUESTO.NEXTVAL, :ord_id, :rep_id, :cant, :costo
            ) RETURNING id_orden_repuesto INTO :v_id
        """
        cursor.execute(sql, {
            "ord_id": int(orden_id),
            "rep_id": int(repuesto_id),
            "cant": int(cantidad),
            "costo": costo_total,
            "v_id": v_id
        })
        conn.commit()
        id_gen = int(v_id.getvalue()[0])
        return {
            "success": True,
            "id_orden_repuesto": id_gen,
            "costo_total": costo_total,
            "mensaje": f"Consumo registrado: {cantidad} unidad(es) (${costo_total:.2f})."
        }
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def eliminar_consumo_repuesto(id_orden_repuesto: int) -> Dict[str, Any]:
    """Elimina una partida de repuesto consumido en una orden."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = "DELETE FROM ORDEN_REPUESTO WHERE id_orden_repuesto = :id_orp"
        cursor.execute(sql, {"id_orp": int(id_orden_repuesto)})
        conn.commit()
        return {"success": True, "mensaje": "Partida de repuesto eliminada de la orden."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def calcular_costo_total_orden(orden_id: int) -> float:
    """Invoca la funcion canonica FN_COSTO_ORDEN_MANTENIMIENTO."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        res = cursor.callfunc("FN_COSTO_ORDEN_MANTENIMIENTO", oracledb.NUMBER, [int(orden_id)])
        return float(res if res is not None else 0.0)
    except Exception:
        return 0.0
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 5. AUDITORIA, ALERTAS Y TRENES EN TALLER
# ==============================================================================

def get_kpis_mantenimiento() -> Dict[str, Any]:
    """Retorna los indicadores clave de rendimiento del modulo de mantenimiento."""
    sql = """
        SELECT 
            (SELECT COUNT(*) FROM ORDEN_MANTENIMIENTO) AS total_ordenes,
            (SELECT COUNT(*) FROM ORDEN_MANTENIMIENTO WHERE estado = 'En Ejecución') AS ordenes_en_ejecucion,
            (SELECT COUNT(*) FROM ORDEN_MANTENIMIENTO WHERE estado IN ('Solicitada', 'Programada')) AS ordenes_programadas,
            (SELECT COUNT(*) FROM ORDEN_MANTENIMIENTO WHERE estado = 'Completada') AS ordenes_completadas,
            (SELECT COUNT(*) FROM EQUIPO WHERE estado IN ('Fuera de Servicio', 'En Mantenimiento')) AS equipos_fuera_servicio,
            (SELECT COUNT(*) FROM EQUIPO WHERE fecha_proxima_revision IS NOT NULL AND TRUNC(fecha_proxima_revision) < TRUNC(SYSDATE)) AS inspecciones_vencidas,
            (SELECT COUNT(*) FROM TREN WHERE estado_operativo = 'En Mantenimiento') AS trenes_en_taller,
            (SELECT NVL(SUM(costo), 0) FROM ORDEN_MANTENIMIENTO) + 
            (SELECT NVL(SUM(costo_total), 0) FROM ORDEN_REPUESTO) AS inversion_total
        FROM DUAL
    """
    rows = execute_query(sql)["rows"]
    if rows:
        r = rows[0]
        return {
            "total_ordenes": _safe_int(r.get("TOTAL_ORDENES")),
            "en_ejecucion": _safe_int(r.get("ORDENES_EN_EJECUCION")),
            "programadas": _safe_int(r.get("ORDENES_PROGRAMADAS")),
            "completadas": _safe_int(r.get("ORDENES_COMPLETADAS")),
            "equipos_fuera_servicio": _safe_int(r.get("EQUIPOS_FUERA_SERVICIO")),
            "inspecciones_vencidas": _safe_int(r.get("INSPECCIONES_VENCIDAS")),
            "trenes_en_taller": _safe_int(r.get("TRENES_EN_TALLER")),
            "inversion_total": _safe_float(r.get("INVERSION_TOTAL"))
        }
    return {
        "total_ordenes": 0, "en_ejecucion": 0, "programadas": 0,
        "completadas": 0, "equipos_fuera_servicio": 0,
        "inspecciones_vencidas": 0, "trenes_en_taller": 0, "inversion_total": 0.0
    }


def get_equipos_inspeccion_vencida() -> List[Dict[str, Any]]:
    """Retorna los activos que tienen la fecha de proxima inspeccion vencida o proxima."""
    sql = """
        SELECT eq.id_equipo,
               eq.codigo_equipo,
               eq.tipo_equipo,
               eq.ubicacion,
               eq.estado,
               TO_CHAR(eq.fecha_ultima_revision, 'YYYY-MM-DD') AS fecha_ultima_revision,
               TO_CHAR(eq.fecha_proxima_revision, 'YYYY-MM-DD') AS fecha_proxima_revision,
               ROUND(TRUNC(eq.fecha_proxima_revision) - TRUNC(SYSDATE)) AS dias_restantes
        FROM EQUIPO eq
        WHERE eq.fecha_proxima_revision IS NULL
           OR TRUNC(eq.fecha_proxima_revision) <= TRUNC(SYSDATE + 15)
        ORDER BY eq.fecha_proxima_revision ASC NULLS FIRST
    """
    return execute_query(sql)["rows"]


def get_equipos_fuera_servicio() -> List[Dict[str, Any]]:
    """Retorna los equipos actualmente fuera de servicio o en mantenimiento."""
    sql = """
        SELECT eq.id_equipo,
               eq.codigo_equipo,
               eq.tipo_equipo,
               eq.ubicacion,
               eq.estado,
               (SELECT om.numero_orden 
                FROM ORDEN_MANTENIMIENTO om 
                WHERE om.equipo_id = eq.id_equipo AND om.estado IN ('En Ejecución', 'Programada') AND ROWNUM = 1) AS orden_activa,
               (SELECT om.tipo_mantenimiento 
                FROM ORDEN_MANTENIMIENTO om 
                WHERE om.equipo_id = eq.id_equipo AND om.estado IN ('En Ejecución', 'Programada') AND ROWNUM = 1) AS tipo_mantenimiento
        FROM EQUIPO eq
        WHERE eq.estado IN ('Fuera de Servicio', 'En Mantenimiento')
        ORDER BY eq.tipo_equipo, eq.codigo_equipo
    """
    return execute_query(sql)["rows"]


def get_trenes_en_taller() -> List[Dict[str, Any]]:
    """Consulta la vista oficial VW_TRENES_MANTENIMIENTO."""
    sql = """
        SELECT id_tren,
               codigo_tren,
               nombre_modelo,
               deposito,
               kilometraje_acumulado,
               numero_orden,
               tipo_mantenimiento,
               descripcion_trabajo,
               prioridad,
               costo_orden,
               estado_orden,
               tecnico_responsable,
               fecha_ingreso_taller
        FROM VW_TRENES_MANTENIMIENTO
        ORDER BY codigo_tren
    """
    return execute_query(sql)["rows"]
