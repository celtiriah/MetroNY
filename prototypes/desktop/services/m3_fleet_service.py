"""
m3_fleet_service.py - Servicio especializado para el Módulo 3: Flota, Trenes y Material Rodante.
Proporciona lógica de negocio y operaciones transaccionales para:
1. Catálogos maestros de apoyo (Modelos de tren, Depósitos / Patios).
2. Gestión integral de Trenes (TREN), estados operativos y auditoría.
3. Gestión de Vagones (VAGON), capacidades y accesibilidad PMR.
4. Formación y Composición de Trenes (TREN_VAGON), acoplamiento y desacoplamiento con
   preservación histórica (Regla de negocio 25) y recálculo dinámico de capacidad total.
5. Verificación de disponibilidad operativa en tiempo real (FN_TREN_DISPONIBLE, inspecciones).
6. Asignación de material rodante a viajes programados (VIAJE_PROGRAMADO), impidiendo
   asignaciones simultáneas solapadas (Regla de negocio 8) y trenes en mantenimiento (Regla 11).
"""
import re
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import oracledb

from services.db import get_connection, execute_query
from services.actions_service import parse_oracle_error


def _query_rows(sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Ejecuta una consulta SQL y retorna la lista de diccionarios de filas."""
    res = execute_query(sql, params)
    return res.get("rows", [])


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
# 1. CATALOGOS AUXILIARES: MODELOS Y DEPOSITOS
# ==============================================================================

def get_modelos_combo() -> List[Dict[str, Any]]:
    """
    Retorna los modelos de tren registrados (R142, R160, R179, R211, etc.)
    con sus fabricantes.
    """
    sql = """
        SELECT id_modelo, nombre_modelo, fabricante
        FROM MODELO_TREN
        ORDER BY nombre_modelo
    """
    return _query_rows(sql)


def get_depositos_combo() -> List[Dict[str, Any]]:
    """
    Retorna los patios y depósitos de almacenamiento y mantenimiento.
    """
    sql = """
        SELECT id_deposito, codigo, nombre, ubicacion, capacidad
        FROM DEPOSITO
        ORDER BY nombre
    """
    return _query_rows(sql)


# ==============================================================================
# 2. GESTION DE TRENES (TREN)
# ==============================================================================

def get_trenes(
    estado_filter: Optional[str] = None,
    deposito_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Retorna el catálogo completo de trenes con modelo, fabricante, depósito base,
    capacidad total, kilometraje acumulado, fechas de inspección técnica,
    evaluación de la función FN_TREN_DISPONIBLE y conteo de vagones activos.
    """
    sql = """
        SELECT t.id_tren, t.codigo_interno,
               t.modelo_id, m.nombre_modelo, m.fabricante,
               t.deposito_id, NVL(d.nombre, 'Sin Depósito') AS nombre_deposito,
               d.codigo AS codigo_deposito,
               t.anio_fabricacion,
               t.capacidad_total,
               t.estado_operativo,
               t.kilometraje_acumulado,
               TO_CHAR(t.fecha_ultima_inspeccion, 'YYYY-MM-DD') AS fecha_ultima_inspeccion,
               TO_CHAR(t.fecha_proxima_inspeccion, 'YYYY-MM-DD') AS fecha_proxima_inspeccion,
               FN_TREN_DISPONIBLE(t.id_tren) AS disponible_fn,
               CASE 
                   WHEN t.fecha_proxima_inspeccion IS NOT NULL AND t.fecha_proxima_inspeccion < TRUNC(SYSDATE) THEN 1
                   ELSE 0
               END AS inspeccion_vencida,
               (SELECT COUNT(*) FROM TREN_VAGON tv WHERE tv.tren_id = t.id_tren AND tv.fecha_fin IS NULL) AS total_vagones_activos
        FROM TREN t
        JOIN MODELO_TREN m ON t.modelo_id = m.id_modelo
        LEFT JOIN DEPOSITO d ON t.deposito_id = d.id_deposito
        WHERE 1=1
    """
    params: Dict[str, Any] = {}
    if estado_filter and estado_filter != "(Todos)":
        sql += " AND t.estado_operativo = :estado_filter"
        params["estado_filter"] = estado_filter

    if deposito_id is not None:
        sql += " AND t.deposito_id = :deposito_id"
        params["deposito_id"] = deposito_id

    sql += " ORDER BY t.codigo_interno"
    return _query_rows(sql, params)


def get_tren_by_id(id_tren: int) -> Optional[Dict[str, Any]]:
    """Retorna los datos detallados de un tren específico."""
    sql = """
        SELECT t.id_tren, t.codigo_interno,
               t.modelo_id, m.nombre_modelo, m.fabricante,
               t.deposito_id, NVL(d.nombre, 'Sin Depósito') AS nombre_deposito,
               t.anio_fabricacion,
               t.capacidad_total,
               t.estado_operativo,
               t.kilometraje_acumulado,
               TO_CHAR(t.fecha_ultima_inspeccion, 'YYYY-MM-DD') AS fecha_ultima_inspeccion,
               TO_CHAR(t.fecha_proxima_inspeccion, 'YYYY-MM-DD') AS fecha_proxima_inspeccion,
               FN_TREN_DISPONIBLE(t.id_tren) AS disponible_fn
        FROM TREN t
        JOIN MODELO_TREN m ON t.modelo_id = m.id_modelo
        LEFT JOIN DEPOSITO d ON t.deposito_id = d.id_deposito
        WHERE t.id_tren = :id_tren
    """
    rows = _query_rows(sql, {"id_tren": id_tren})
    return rows[0] if rows else None


def _validar_datos_tren(datos: Dict[str, Any], id_tren_existente: Optional[int] = None) -> Optional[str]:
    """Valida reglas de dominio técnico y restricciones relacionales para un tren."""
    codigo = str(datos.get("codigo_interno") or "").strip().upper()
    if not codigo:
        return "El código interno del tren es obligatorio."
    if len(codigo) > 15:
        return "El código interno no puede exceder 15 caracteres."

    modelo_id = datos.get("modelo_id")
    if modelo_id is None:
        return "Debe seleccionar un modelo de tren válido."
    try:
        if int(modelo_id) <= 0:
            return "Debe seleccionar un modelo de tren válido."
    except (ValueError, TypeError):
        return "El identificador del modelo de tren es inválido."

    anio = datos.get("anio_fabricacion")
    if anio is not None and str(anio).strip() != "":
        try:
            anio_int = int(anio)
            max_anio = datetime.now().year + 1
            if anio_int < 1950 or anio_int > max_anio:
                return f"El año de fabricación debe estar comprendido entre 1950 y {max_anio}."
        except (ValueError, TypeError):
            return "El año de fabricación debe ser un número entero válido."

    km = datos.get("kilometraje_acumulado")
    if km is not None and str(km).strip() != "":
        try:
            km_flt = float(km)
            if km_flt < 0:
                return "El kilometraje acumulado no puede ser un valor negativo."
        except (ValueError, TypeError):
            return "El kilometraje debe ser un valor numérico válido."

    f_ult = datos.get("fecha_ultima_inspeccion")
    f_prox = datos.get("fecha_proxima_inspeccion")
    if f_ult and f_prox and str(f_ult).strip() and str(f_prox).strip():
        try:
            d_ult = datetime.strptime(str(f_ult).strip()[:10], "%Y-%m-%d").date()
            d_prox = datetime.strptime(str(f_prox).strip()[:10], "%Y-%m-%d").date()
            if d_prox < d_ult:
                return "La fecha de próxima inspección técnica no puede ser anterior a la fecha de última inspección."
        except ValueError:
            return "El formato de las fechas de inspección debe ser estrictamente YYYY-MM-DD."

    return None


def crear_tren(datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inserta un nuevo tren en la tabla TREN usando SEQ_TREN.NEXTVAL.
    Valida preventivamente formato, modelo, año, kilometraje y fechas de inspección.
    """
    err_val = _validar_datos_tren(datos)
    if err_val:
        return {"success": False, "error": err_val}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT SEQ_TREN.NEXTVAL FROM DUAL")
        seq_row = cursor.fetchone()
        new_id = int(seq_row[0]) if seq_row else 1

        sql = """
            INSERT INTO TREN (
                id_tren, codigo_interno, modelo_id, anio_fabricacion,
                capacidad_total, estado_operativo, kilometraje_acumulado,
                deposito_id, fecha_ultima_inspeccion, fecha_proxima_inspeccion
            ) VALUES (
                :id_tren, :codigo_interno, :modelo_id, :anio_fabricacion,
                0, :estado_operativo, :kilometraje_acumulado,
                :deposito_id,
                CASE WHEN :fecha_ult IS NOT NULL THEN TO_DATE(:fecha_ult, 'YYYY-MM-DD') ELSE NULL END,
                CASE WHEN :fecha_prox IS NOT NULL THEN TO_DATE(:fecha_prox, 'YYYY-MM-DD') ELSE NULL END
            )
        """
        params = {
            "id_tren": new_id,
            "codigo_interno": datos["codigo_interno"].strip().upper(),
            "modelo_id": int(datos["modelo_id"]),
            "anio_fabricacion": datos.get("anio_fabricacion"),
            "estado_operativo": datos.get("estado_operativo", "Disponible"),
            "kilometraje_acumulado": _safe_float(datos.get("kilometraje_acumulado")),
            "deposito_id": datos.get("deposito_id"),
            "fecha_ult": datos.get("fecha_ultima_inspeccion") or None,
            "fecha_prox": datos.get("fecha_proxima_inspeccion") or None,
        }
        cursor.execute(sql, params)

        # Crear automáticamente activo correspondiente en EQUIPO para módulo de mantenimiento
        sql_equipo = """
            INSERT INTO EQUIPO (
                id_equipo, codigo_equipo, tipo_equipo, tipo_referencia,
                referencia_id, ubicacion, fabricante, modelo, estado,
                fecha_instalacion, fecha_ultima_revision, fecha_proxima_revision
            ) VALUES (
                SEQ_EQUIPO.NEXTVAL, 'EQ-' || :codigo_interno, 'Tren', 'TREN',
                :id_tren, 'Patio Base', 
                (SELECT fabricante FROM MODELO_TREN WHERE id_modelo = :modelo_id),
                (SELECT nombre_modelo FROM MODELO_TREN WHERE id_modelo = :modelo_id),
                :estado_operativo,
                SYSDATE,
                CASE WHEN :fecha_ult IS NOT NULL THEN TO_DATE(:fecha_ult, 'YYYY-MM-DD') ELSE NULL END,
                CASE WHEN :fecha_prox IS NOT NULL THEN TO_DATE(:fecha_prox, 'YYYY-MM-DD') ELSE NULL END
            )
        """
        cursor.execute(sql_equipo, {
            "codigo_interno": datos["codigo_interno"].strip().upper(),
            "id_tren": new_id,
            "modelo_id": int(datos["modelo_id"]),
            "estado_operativo": datos.get("estado_operativo", "Disponible"),
            "fecha_ult": datos.get("fecha_ultima_inspeccion") or None,
            "fecha_prox": datos.get("fecha_proxima_inspeccion") or None,
        })

        conn.commit()
        return {"success": True, "id_tren": new_id, "codigo_interno": datos["codigo_interno"]}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def modificar_tren(id_tren: int, datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Actualiza datos técnicos y administrativos de un tren existente.
    Verifica integridad de odómetro impidiendo reducción fraudulenta.
    """
    err_val = _validar_datos_tren(datos, id_tren_existente=id_tren)
    if err_val:
        return {"success": False, "error": err_val}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Validar protección de odómetro a nivel servicio
        cursor.execute("SELECT kilometraje_acumulado FROM TREN WHERE id_tren = :id_tren", {"id_tren": id_tren})
        row_km = cursor.fetchone()
        if row_km and row_km[0] is not None:
            km_actual = _safe_float(row_km[0])
            km_nuevo = _safe_float(datos.get("kilometraje_acumulado"))
            if km_nuevo < km_actual:
                return {
                    "success": False,
                    "error": f"Intento de manipulación de odómetro: El kilometraje acumulado no puede reducirse (Valor actual: {km_actual:.1f} km, Nuevo: {km_nuevo:.1f} km)."
                }

        sql = """
            UPDATE TREN
            SET codigo_interno = :codigo_interno,
                modelo_id = :modelo_id,
                anio_fabricacion = :anio_fabricacion,
                deposito_id = :deposito_id,
                kilometraje_acumulado = :kilometraje_acumulado,
                fecha_ultima_inspeccion = CASE WHEN :fecha_ult IS NOT NULL THEN TO_DATE(:fecha_ult, 'YYYY-MM-DD') ELSE NULL END,
                fecha_proxima_inspeccion = CASE WHEN :fecha_prox IS NOT NULL THEN TO_DATE(:fecha_prox, 'YYYY-MM-DD') ELSE NULL END
            WHERE id_tren = :id_tren
        """
        params = {
            "id_tren": id_tren,
            "codigo_interno": datos["codigo_interno"].strip().upper(),
            "modelo_id": int(datos["modelo_id"]),
            "anio_fabricacion": datos.get("anio_fabricacion"),
            "deposito_id": datos.get("deposito_id"),
            "kilometraje_acumulado": _safe_float(datos.get("kilometraje_acumulado")),
            "fecha_ult": datos.get("fecha_ultima_inspeccion") or None,
            "fecha_prox": datos.get("fecha_proxima_inspeccion") or None,
        }
        cursor.execute(sql, params)

        # Actualizar equipo asociado en EQUIPO
        sql_eq = """
            UPDATE EQUIPO
            SET codigo_equipo = 'EQ-' || :codigo_interno,
                modelo = (SELECT nombre_modelo FROM MODELO_TREN WHERE id_modelo = :modelo_id),
                fabricante = (SELECT fabricante FROM MODELO_TREN WHERE id_modelo = :modelo_id),
                fecha_ultima_revision = CASE WHEN :fecha_ult IS NOT NULL THEN TO_DATE(:fecha_ult, 'YYYY-MM-DD') ELSE NULL END,
                fecha_proxima_revision = CASE WHEN :fecha_prox IS NOT NULL THEN TO_DATE(:fecha_prox, 'YYYY-MM-DD') ELSE NULL END
            WHERE tipo_referencia = 'TREN' AND referencia_id = :id_tren
        """
        cursor.execute(sql_eq, {
            "codigo_interno": datos["codigo_interno"].strip().upper(),
            "modelo_id": int(datos["modelo_id"]),
            "fecha_ult": datos.get("fecha_ultima_inspeccion") or None,
            "fecha_prox": datos.get("fecha_proxima_inspeccion") or None,
            "id_tren": id_tren
        })

        conn.commit()
        return {"success": True}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def cambiar_estado_tren(id_tren: int, nuevo_estado: str) -> Dict[str, Any]:
    """
    Modifica el estado operativo de un tren ('Disponible', 'En Operación',
    'En Mantenimiento', 'Fuera de Servicio', 'Retirado').
    Esta operación dispara automáticamente el trigger TRG_TREN_CAMBIO_ESTADO
    que registra el cambio en la tabla BITACORA.
    """
    estados_validos = ["Disponible", "En Operación", "En Mantenimiento", "Fuera de Servicio", "Retirado"]
    if nuevo_estado not in estados_validos:
        return {"success": False, "error": f"Estado inválido. Opciones permitidas: {', '.join(estados_validos)}"}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = "UPDATE TREN SET estado_operativo = :nuevo_estado WHERE id_tren = :id_tren"
        cursor.execute(sql, {"nuevo_estado": nuevo_estado, "id_tren": id_tren})

        # Sincronizar estado en EQUIPO
        cursor.execute("""
            UPDATE EQUIPO
            SET estado = :nuevo_estado
            WHERE tipo_referencia = 'TREN' AND referencia_id = :id_tren
        """, {"nuevo_estado": nuevo_estado, "id_tren": id_tren})

        conn.commit()
        return {"success": True, "nuevo_estado": nuevo_estado}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def verificar_dependencias_tren(id_tren: int) -> Dict[str, Any]:
    """
    Audita exhaustivamente las relaciones operativas de un tren antes de permitir
    su eliminación física o baja lógica en el sistema:
    - Viajes asignados (históricos o futuros en VIAJE_PROGRAMADO)
    - Vagones actualmente acoplados (TREN_VAGON con fecha_fin IS NULL)
    - Vagones históricamente asignados (TREN_VAGON con fecha_fin IS NOT NULL)
    - Órdenes de mantenimiento registradas (ORDEN_MANTENIMIENTO vía EQUIPO)
    - Incidentes reportados (INCIDENTE_ELEMENTO_AFECTADO)
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT codigo_interno, estado_operativo FROM TREN WHERE id_tren = :id_tren", {"id_tren": id_tren})
        row = cursor.fetchone()
        if not row:
            return {"success": False, "error": "El tren especificado no existe en la base de datos."}
        cod_interno, est_operativo = str(row[0]), str(row[1])

        # 1. Viajes
        cursor.execute("SELECT COUNT(*) FROM VIAJE_PROGRAMADO WHERE tren_id = :id_tren", {"id_tren": id_tren})
        viajes_cnt = int(cursor.fetchone()[0])

        # 2. Vagones acoplados activos
        cursor.execute("SELECT COUNT(*) FROM TREN_VAGON WHERE tren_id = :id_tren AND fecha_fin IS NULL", {"id_tren": id_tren})
        vagones_activos_cnt = int(cursor.fetchone()[0])

        # 3. Vagones históricos
        cursor.execute("SELECT COUNT(*) FROM TREN_VAGON WHERE tren_id = :id_tren AND fecha_fin IS NOT NULL", {"id_tren": id_tren})
        vagones_hist_cnt = int(cursor.fetchone()[0])

        # 4. Órdenes de taller
        cursor.execute("""
            SELECT COUNT(*) FROM ORDEN_MANTENIMIENTO om
            JOIN EQUIPO eq ON om.equipo_id = eq.id_equipo
            WHERE eq.tipo_referencia = 'TREN' AND eq.referencia_id = :id_tren
        """, {"id_tren": id_tren})
        ordenes_cnt = int(cursor.fetchone()[0])

        # 5. Incidentes
        cursor.execute("SELECT COUNT(*) FROM INCIDENTE_ELEMENTO_AFECTADO WHERE tren_id = :id_tren", {"id_tren": id_tren})
        incidentes_cnt = int(cursor.fetchone()[0])

        resumen_partes = []
        if viajes_cnt > 0:
            resumen_partes.append(f"{viajes_cnt} viaje(s) programado(s)")
        if vagones_activos_cnt > 0:
            resumen_partes.append(f"{vagones_activos_cnt} vagón(es) acoplado(s) actualmente")
        if vagones_hist_cnt > 0:
            resumen_partes.append(f"{vagones_hist_cnt} registro(s) de formación previa")
        if ordenes_cnt > 0:
            resumen_partes.append(f"{ordenes_cnt} orden(es) de mantenimiento")
        if incidentes_cnt > 0:
            resumen_partes.append(f"{incidentes_cnt} reporte(s) de incidente")

        resumen_texto = ", ".join(resumen_partes) if resumen_partes else "Sin dependencias operativas registradas"
        tiene_dependencias = (viajes_cnt > 0 or ordenes_cnt > 0 or vagones_hist_cnt > 0 or incidentes_cnt > 0)
        puede_eliminar_fisico = (not tiene_dependencias and vagones_activos_cnt == 0)

        return {
            "success": True,
            "id_tren": id_tren,
            "codigo_interno": cod_interno,
            "estado_operativo": est_operativo,
            "viajes_cnt": viajes_cnt,
            "vagones_activos_cnt": vagones_activos_cnt,
            "vagones_hist_cnt": vagones_hist_cnt,
            "ordenes_cnt": ordenes_cnt,
            "incidentes_cnt": incidentes_cnt,
            "tiene_dependencias": tiene_dependencias,
            "puede_eliminar_fisico": puede_eliminar_fisico,
            "resumen": resumen_texto
        }
    except Exception as exc:
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def dar_de_baja_tren(id_tren: int) -> Dict[str, Any]:
    """
    Aplica baja lógica (Soft-Delete) a un tren, marcando su estado como 'Retirado'
    e impidiendo su eliminación física para salvaguardar la integridad referencial
    del histórico de viajes, composiciones y órdenes de mantenimiento.
    """
    dep = verificar_dependencias_tren(id_tren)
    if not dep.get("success"):
        return dep

    if dep.get("vagones_activos_cnt", 0) > 0:
        return {
            "success": False,
            "error": f"No se puede retirar el tren {dep.get('codigo_interno')}: tiene {dep.get('vagones_activos_cnt')} vagón(es) acoplado(s) activamente. Desacóplelos primero en la pestaña de Composición."
        }

    return cambiar_estado_tren(id_tren, "Retirado")


def eliminar_tren(id_tren: int) -> Dict[str, Any]:
    """
    Elimina un tren del sistema si no posee historial operativo alguno.
    Si posee historial de viajes, acoplamientos u órdenes de mantenimiento,
    la eliminación física es rechazada por regla de integridad DBA,
    instruyendo al operador a utilizar la baja lógica (Retirado).
    """
    dep = verificar_dependencias_tren(id_tren)
    if not dep.get("success"):
        return dep

    if dep.get("vagones_activos_cnt", 0) > 0:
        return {
            "success": False,
            "error": f"No se puede eliminar el tren: tiene {dep.get('vagones_activos_cnt')} vagón(es) acoplado(s) actualmente. Desacóplelos primero."
        }

    if dep.get("tiene_dependencias", False):
        return {
            "success": False,
            "requiere_baja_logica": True,
            "resumen": dep.get("resumen"),
            "error": (
                f"No se permite la eliminación física del tren {dep.get('codigo_interno')} "
                f"debido a que posee historial operativo registrado ({dep.get('resumen')}). "
                f"Por integridad relacional, se debe aplicar baja lógica (estado Retirado)."
            )
        }

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Eliminar equipo asociado
        cursor.execute("DELETE FROM EQUIPO WHERE tipo_referencia = 'TREN' AND referencia_id = :id_tren", {"id_tren": id_tren})
        # Eliminar tren
        cursor.execute("DELETE FROM TREN WHERE id_tren = :id_tren", {"id_tren": id_tren})
        conn.commit()
        return {"success": True}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def recalcular_capacidad_tren(id_tren: int) -> int:
    """
    Calcula la suma de capacidades de los vagones acoplados activamente al tren
    (fecha_fin IS NULL) y actualiza el campo CAPACIDAD_TOTAL en TREN.
    Retorna la nueva capacidad total calculada.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql_sum = """
            SELECT NVL(SUM(NVL(v.capacidad_sentados, 0) + NVL(v.capacidad_de_pie, 0)), 0)
            FROM VAGON v
            JOIN TREN_VAGON tv ON v.id_vagon = tv.vagon_id
            WHERE tv.tren_id = :id_tren AND tv.fecha_fin IS NULL
        """
        cursor.execute(sql_sum, {"id_tren": id_tren})
        row = cursor.fetchone()
        nueva_capacidad = int(row[0]) if row else 0

        cursor.execute(
            "UPDATE TREN SET capacidad_total = :cap WHERE id_tren = :id_tren",
            {"cap": nueva_capacidad, "id_tren": id_tren}
        )
        conn.commit()
        return nueva_capacidad
    except Exception:
        conn.rollback()
        return 0
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 3. GESTION DE VAGONES (VAGON)
# ==============================================================================

def get_vagones(
    estado_filter: Optional[str] = None,
    tipo_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retorna el inventario completo de vagones del sistema, con capacidades,
    año de fabricación, estado operativo, accesibilidad y datos del tren al que
    está actualmente acoplado (si aplica).
    """
    sql = """
        SELECT v.id_vagon, v.numero_serie, v.tipo_vagon,
               v.capacidad_sentados, v.capacidad_de_pie,
               (NVL(v.capacidad_sentados, 0) + NVL(v.capacidad_de_pie, 0)) AS capacidad_total,
               v.anio_fabricacion, v.estado, v.accesibilidad,
               t.codigo_interno AS tren_acoplado,
               t.id_tren AS tren_acoplado_id,
               tv.posicion AS posicion_en_tren,
               tv.id_tren_vagon AS activo_tv_id
        FROM VAGON v
        LEFT JOIN TREN_VAGON tv ON v.id_vagon = tv.vagon_id AND tv.fecha_fin IS NULL
        LEFT JOIN TREN t ON tv.tren_id = t.id_tren
        WHERE 1=1
    """
    params: Dict[str, Any] = {}
    if estado_filter and estado_filter != "(Todos)":
        sql += " AND v.estado = :estado_filter"
        params["estado_filter"] = estado_filter

    if tipo_filter and tipo_filter != "(Todos)":
        sql += " AND v.tipo_vagon = :tipo_filter"
        params["tipo_filter"] = tipo_filter

    sql += " ORDER BY v.numero_serie"
    return _query_rows(sql, params)


def get_vagones_disponibles_combo() -> List[Dict[str, Any]]:
    """
    Retorna los vagones que están libres y listos para ser acoplados a un tren
    (estado = 'Disponible' y sin acoplamiento activo en TREN_VAGON).
    Cumple con la Regla de Negocio 12.
    """
    sql = """
        SELECT v.id_vagon, v.numero_serie, v.tipo_vagon,
               v.capacidad_sentados, v.capacidad_de_pie,
               (NVL(v.capacidad_sentados, 0) + NVL(v.capacidad_de_pie, 0)) AS capacidad_total,
               v.accesibilidad
        FROM VAGON v
        WHERE v.estado = 'Disponible'
          AND NOT EXISTS (
              SELECT 1 FROM TREN_VAGON tv
              WHERE tv.vagon_id = v.id_vagon AND tv.fecha_fin IS NULL
          )
        ORDER BY v.numero_serie
    """
    return _query_rows(sql)


def _validar_datos_vagon(datos: Dict[str, Any]) -> Optional[str]:
    """Valida reglas de dominio y límites de capacidad física para un vagón."""
    serie = str(datos.get("numero_serie") or "").strip().upper()
    if not serie:
        return "El número de serie del vagón es obligatorio."
    if len(serie) > 20:
        return "El número de serie no puede exceder 20 caracteres."

    sentados = datos.get("capacidad_sentados")
    if sentados is not None and str(sentados).strip() != "":
        try:
            s_int = int(sentados)
            if s_int < 0 or s_int > 200:
                return "La capacidad de pasajeros sentados debe estar comprendida entre 0 y 200."
        except (ValueError, TypeError):
            return "La capacidad de sentados debe ser un número entero válido."

    pie = datos.get("capacidad_de_pie")
    if pie is not None and str(pie).strip() != "":
        try:
            p_int = int(pie)
            if p_int < 0 or p_int > 400:
                return "La capacidad de pasajeros de pie debe estar comprendida entre 0 y 400."
        except (ValueError, TypeError):
            return "La capacidad de pie debe ser un número entero válido."

    anio = datos.get("anio_fabricacion")
    if anio is not None and str(anio).strip() != "":
        try:
            anio_int = int(anio)
            max_anio = datetime.now().year + 1
            if anio_int < 1950 or anio_int > max_anio:
                return f"El año de fabricación del vagón debe estar comprendido entre 1950 y {max_anio}."
        except (ValueError, TypeError):
            return "El año de fabricación debe ser un número entero válido."

    return None


def crear_vagon(datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Registra un nuevo vagón en la tabla VAGON usando SEQ_VAGON.NEXTVAL.
    Valida preventivamente formato de serie, capacidades y año de fabricación.
    """
    err_val = _validar_datos_vagon(datos)
    if err_val:
        return {"success": False, "error": err_val}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT SEQ_VAGON.NEXTVAL FROM DUAL")
        seq_row = cursor.fetchone()
        new_id = int(seq_row[0]) if seq_row else 1

        sql = """
            INSERT INTO VAGON (
                id_vagon, numero_serie, tipo_vagon,
                capacidad_sentados, capacidad_de_pie,
                anio_fabricacion, estado, accesibilidad
            ) VALUES (
                :id_vagon, :numero_serie, :tipo_vagon,
                :cap_sentados, :cap_pie,
                :anio_fab, :estado, :accesibilidad
            )
        """
        params = {
            "id_vagon": new_id,
            "numero_serie": datos["numero_serie"].strip().upper(),
            "tipo_vagon": datos.get("tipo_vagon", "Pasajero Regular"),
            "cap_sentados": _safe_int(datos.get("capacidad_sentados"), 40),
            "cap_pie": _safe_int(datos.get("capacidad_de_pie"), 160),
            "anio_fab": datos.get("anio_fabricacion"),
            "estado": datos.get("estado", "Disponible"),
            "accesibilidad": datos.get("accesibilidad", "S")
        }
        cursor.execute(sql, params)
        conn.commit()
        return {"success": True, "id_vagon": new_id, "numero_serie": datos["numero_serie"]}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def modificar_vagon(id_vagon: int, datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Actualiza datos de un vagón y recomputa la capacidad del tren si está acoplado.
    """
    err_val = _validar_datos_vagon(datos)
    if err_val:
        return {"success": False, "error": err_val}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE VAGON
            SET numero_serie = :numero_serie,
                tipo_vagon = :tipo_vagon,
                capacidad_sentados = :cap_sentados,
                capacidad_de_pie = :cap_pie,
                anio_fabricacion = :anio_fab,
                accesibilidad = :accesibilidad
            WHERE id_vagon = :id_vagon
        """
        params = {
            "id_vagon": id_vagon,
            "numero_serie": datos["numero_serie"].strip().upper(),
            "tipo_vagon": datos.get("tipo_vagon", "Pasajero Regular"),
            "cap_sentados": _safe_int(datos.get("capacidad_sentados"), 40),
            "cap_pie": _safe_int(datos.get("capacidad_de_pie"), 160),
            "anio_fab": datos.get("anio_fabricacion"),
            "accesibilidad": datos.get("accesibilidad", "S")
        }
        cursor.execute(sql, params)

        # Si el vagón está acoplado a un tren, identificar el tren para recalcular capacidad
        cursor.execute("""
            SELECT tren_id FROM TREN_VAGON WHERE vagon_id = :id_vagon AND fecha_fin IS NULL
        """, {"id_vagon": id_vagon})
        tren_row = cursor.fetchone()
        tren_id_asociado = int(tren_row[0]) if tren_row else None

        conn.commit()

        if tren_id_asociado:
            recalcular_capacidad_tren(tren_id_asociado)

        return {"success": True}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def cambiar_estado_vagon(id_vagon: int, nuevo_estado: str) -> Dict[str, Any]:
    """
    Permite cambiar el estado de un vagón ('Disponible', 'Mantenimiento', 'Fuera de Servicio').
    Impide marcar en mantenimiento o fuera de servicio si actualmente está acoplado a un tren.
    """
    estados_permitidos = ["Disponible", "En Uso", "Fuera de Servicio", "Mantenimiento"]
    if nuevo_estado not in estados_permitidos:
        return {"success": False, "error": f"Estado inválido. Opciones: {', '.join(estados_permitidos)}"}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Validar si está acoplado actualmente
        cursor.execute("""
            SELECT tv.tren_id, t.codigo_interno
            FROM TREN_VAGON tv
            JOIN TREN t ON tv.tren_id = t.id_tren
            WHERE tv.vagon_id = :id_vagon AND tv.fecha_fin IS NULL
        """, {"id_vagon": id_vagon})
        acoplado = cursor.fetchone()

        if acoplado and nuevo_estado in ("Fuera de Servicio", "Mantenimiento", "Disponible"):
            return {
                "success": False,
                "error": f"No se puede cambiar el estado a '{nuevo_estado}': el vagón está acoplado activamente al tren {acoplado[1]}. Desacóplelo primero."
            }

        cursor.execute("UPDATE VAGON SET estado = :nuevo_estado WHERE id_vagon = :id_vagon", {
            "nuevo_estado": nuevo_estado,
            "id_vagon": id_vagon
        })
        conn.commit()
        return {"success": True, "nuevo_estado": nuevo_estado}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def verificar_dependencias_vagon(id_vagon: int) -> Dict[str, Any]:
    """
    Audita acoplamientos activos e históricos de un vagón en la flota.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT numero_serie, estado FROM VAGON WHERE id_vagon = :id_vagon", {"id_vagon": id_vagon})
        row = cursor.fetchone()
        if not row:
            return {"success": False, "error": "El vagón no existe en la base de datos."}
        num_serie, est = str(row[0]), str(row[1])

        # Acoplamiento activo
        cursor.execute("""
            SELECT t.codigo_interno
            FROM TREN_VAGON tv
            JOIN TREN t ON tv.tren_id = t.id_tren
            WHERE tv.vagon_id = :id_vagon AND tv.fecha_fin IS NULL
        """, {"id_vagon": id_vagon})
        activo_row = cursor.fetchone()
        tren_acoplado = str(activo_row[0]) if activo_row else None

        # Historial de acoplamiento
        cursor.execute("""
            SELECT COUNT(*) FROM TREN_VAGON WHERE vagon_id = :id_vagon AND fecha_fin IS NOT NULL
        """, {"id_vagon": id_vagon})
        hist_count = int(cursor.fetchone()[0])

        tiene_historial = hist_count > 0
        esta_acoplado = tren_acoplado is not None

        return {
            "success": True,
            "id_vagon": id_vagon,
            "numero_serie": num_serie,
            "estado": est,
            "esta_acoplado": esta_acoplado,
            "tren_acoplado": tren_acoplado,
            "hist_count": hist_count,
            "tiene_historial": tiene_historial,
            "puede_eliminar_fisico": not esta_acoplado and not tiene_historial
        }
    except Exception as exc:
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def dar_de_baja_vagon(id_vagon: int) -> Dict[str, Any]:
    """
    Aplica baja lógica (Soft-Delete) al vagón marcándolo como 'Fuera de Servicio',
    preservando el historial de acoplamientos (Regla 25).
    """
    dep = verificar_dependencias_vagon(id_vagon)
    if not dep.get("success"):
        return dep

    if dep.get("esta_acoplado"):
        return {
            "success": False,
            "error": f"No se puede dar de baja el vagón {dep.get('numero_serie')}: está acoplado activamente al tren {dep.get('tren_acoplado')}. Desacóplelo primero."
        }

    return cambiar_estado_vagon(id_vagon, "Fuera de Servicio")


def eliminar_vagon(id_vagon: int) -> Dict[str, Any]:
    """
    Elimina un vagón si no está acoplado ni posee historial de formaciones previas.
    Si posee historial, instruye a aplicar la baja lógica (Fuera de Servicio - Regla 25).
    """
    dep = verificar_dependencias_vagon(id_vagon)
    if not dep.get("success"):
        return dep

    if dep.get("esta_acoplado"):
        return {
            "success": False,
            "error": f"No se puede eliminar el vagón: está acoplado activamente al tren {dep.get('tren_acoplado')}. Desacóplelo primero."
        }

    if dep.get("tiene_historial"):
        return {
            "success": False,
            "requiere_baja_logica": True,
            "error": (
                f"No se permite la eliminación física del vagón {dep.get('numero_serie')} "
                f"debido a que posee {dep.get('hist_count')} registro(s) en el historial de formaciones (Regla 25). "
                f"Por integridad relacional, aplique la baja lógica (marcar como Fuera de Servicio)."
            )
        }

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM VAGON WHERE id_vagon = :id_vagon", {"id_vagon": id_vagon})
        conn.commit()
        return {"success": True}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 4. COMPOSICION DE TRENES (TREN_VAGON) Y REGLAS 12 Y 25
# ==============================================================================

def get_composicion_activa(id_tren: int) -> List[Dict[str, Any]]:
    """
    Retorna la formación actual de vagones acoplados al tren (fecha_fin IS NULL),
    ordenados estrictamente por su POSICION (1, 2, 3...).
    """
    sql = """
        SELECT tv.id_tren_vagon, tv.tren_id, tv.vagon_id, tv.posicion,
               TO_CHAR(tv.fecha_inicio, 'YYYY-MM-DD HH24:MI:SS') AS fecha_inicio,
               v.numero_serie, v.tipo_vagon,
               v.capacidad_sentados, v.capacidad_de_pie,
               (NVL(v.capacidad_sentados, 0) + NVL(v.capacidad_de_pie, 0)) AS capacidad_total,
               v.accesibilidad, v.estado AS estado_vagon
        FROM TREN_VAGON tv
        JOIN VAGON v ON tv.vagon_id = v.id_vagon
        WHERE tv.tren_id = :id_tren AND tv.fecha_fin IS NULL
        ORDER BY tv.posicion ASC
    """
    return _query_rows(sql, {"id_tren": id_tren})


def acoplar_vagon(id_tren: int, id_vagon: int, posicion: Optional[int] = None) -> Dict[str, Any]:
    """
    Acopla un vagón a un tren.
    Valida:
    - Regla de Negocio 12: Un vagón no puede pertenecer simultáneamente a dos trenes.
    - El vagón debe estar en estado 'Disponible'.
    - Si no se provee posición, se asigna automáticamente al final de la formación.
    Efectos:
    - Inserta en TREN_VAGON con FECHA_INICIO = SYSDATE y FECHA_FIN = NULL.
    - Actualiza VAGON.estado = 'En Uso'.
    - Recalcula TREN.capacidad_total sumando las capacidades de los vagones acoplados.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Validar que el tren exista
        cursor.execute("SELECT codigo_interno, estado_operativo FROM TREN WHERE id_tren = :id_tren", {"id_tren": id_tren})
        tren_row = cursor.fetchone()
        if not tren_row:
            return {"success": False, "error": "El tren especificado no existe."}

        # 2. Validar que el vagón exista y esté disponible (Regla 12)
        cursor.execute("SELECT numero_serie, estado FROM VAGON WHERE id_vagon = :id_vagon", {"id_vagon": id_vagon})
        vag_row = cursor.fetchone()
        if not vag_row:
            return {"success": False, "error": "El vagón especificado no existe."}

        num_serie, est_vag = vag_row[0], vag_row[1]

        # Verificar si ya está acoplado activamente a cualquier tren
        cursor.execute("""
            SELECT t.codigo_interno
            FROM TREN_VAGON tv
            JOIN TREN t ON tv.tren_id = t.id_tren
            WHERE tv.vagon_id = :id_vagon AND tv.fecha_fin IS NULL
        """, {"id_vagon": id_vagon})
        acop_activo = cursor.fetchone()
        if acop_activo:
            return {
                "success": False,
                "error": f"Conflicto de acoplamiento: El vagón {num_serie} ya está acoplado al tren {acop_activo[0]} (Regla de negocio 12)."
            }

        if est_vag != "Disponible":
            return {
                "success": False,
                "error": f"El vagón {num_serie} no está disponible (Estado actual: {est_vag})."
            }

        # 3. Determinar posición
        if posicion is None or posicion <= 0:
            cursor.execute("""
                SELECT NVL(MAX(posicion), 0) + 1
                FROM TREN_VAGON
                WHERE tren_id = :id_tren AND fecha_fin IS NULL
            """, {"id_tren": id_tren})
            posicion = int(cursor.fetchone()[0])

        # 4. Insertar en TREN_VAGON
        cursor.execute("SELECT SEQ_TREN_VAGON.NEXTVAL FROM DUAL")
        new_tv_id = int(cursor.fetchone()[0])

        sql_insert = """
            INSERT INTO TREN_VAGON (
                id_tren_vagon, tren_id, vagon_id, posicion, fecha_inicio, fecha_fin
            ) VALUES (
                :id_tv, :id_tren, :id_vagon, :posicion, SYSDATE, NULL
            )
        """
        cursor.execute(sql_insert, {
            "id_tv": new_tv_id,
            "id_tren": id_tren,
            "id_vagon": id_vagon,
            "posicion": posicion
        })

        # 5. Actualizar estado del vagón a 'En Uso'
        cursor.execute("UPDATE VAGON SET estado = 'En Uso' WHERE id_vagon = :id_vagon", {"id_vagon": id_vagon})

        conn.commit()

        # 6. Recalcular capacidad total del tren
        nueva_capacidad = recalcular_capacidad_tren(id_tren)

        return {
            "success": True,
            "id_tren_vagon": new_tv_id,
            "posicion": posicion,
            "nueva_capacidad": nueva_capacidad,
            "mensaje": f"Vagón {num_serie} acoplado exitosamente al tren en posición {posicion}."
        }
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def desacoplar_vagon(id_tren_vagon: int) -> Dict[str, Any]:
    """
    Desacopla un vagón de una formación.
    Cumplimiento estricto de la Regla de Negocio 25:
    - NO elimina físicamente el registro de TREN_VAGON.
    - Establece FECHA_FIN = SYSDATE, marcando el fin de la asociación activa.
    - Restablece el estado del vagón a 'Disponible'.
    - Renormaliza las posiciones de los vagones restantes en el tren.
    - Recalcula y actualiza la capacidad total del tren en Oracle.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Obtener datos del acoplamiento activo
        cursor.execute("""
            SELECT tv.tren_id, tv.vagon_id, v.numero_serie, t.codigo_interno
            FROM TREN_VAGON tv
            JOIN VAGON v ON tv.vagon_id = v.id_vagon
            JOIN TREN t ON tv.tren_id = t.id_tren
            WHERE tv.id_tren_vagon = :id_tv AND tv.fecha_fin IS NULL
        """, {"id_tv": id_tren_vagon})
        row = cursor.fetchone()
        if not row:
            return {"success": False, "error": "El registro de acoplamiento no existe o ya fue desacoplado previamente."}

        tren_id, vagon_id, num_serie, cod_tren = int(row[0]), int(row[1]), row[2], row[3]

        # 2. Cerrar asociación histórica (Regla 25)
        cursor.execute("""
            UPDATE TREN_VAGON
            SET fecha_fin = SYSDATE
            WHERE id_tren_vagon = :id_tv
        """, {"id_tv": id_tren_vagon})

        # 3. Liberar vagón a 'Disponible'
        cursor.execute("UPDATE VAGON SET estado = 'Disponible' WHERE id_vagon = :vagon_id", {"vagon_id": vagon_id})

        # 4. Renormalizar posiciones de los vagones restantes
        cursor.execute("""
            SELECT id_tren_vagon
            FROM TREN_VAGON
            WHERE tren_id = :tren_id AND fecha_fin IS NULL
            ORDER BY posicion ASC
        """, {"tren_id": tren_id})
        restantes = cursor.fetchall()
        for idx, r in enumerate(restantes, start=1):
            cursor.execute("""
                UPDATE TREN_VAGON SET posicion = :pos WHERE id_tren_vagon = :tv_id
            """, {"pos": idx, "tv_id": r[0]})

        conn.commit()

        # 5. Recalcular capacidad total del tren
        nueva_capacidad = recalcular_capacidad_tren(tren_id)

        return {
            "success": True,
            "tren_id": tren_id,
            "vagon_id": vagon_id,
            "nueva_capacidad": nueva_capacidad,
            "mensaje": f"Vagón {num_serie} desacoplado del tren {cod_tren}. Registro histórico conservado."
        }
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def reordenar_posicion(id_tren_vagon: int, nueva_posicion: int) -> Dict[str, Any]:
    """
    Cambia la posición ordenada de un vagón dentro de la formación activa de su tren.
    """
    if nueva_posicion < 1:
        return {"success": False, "error": "La posición debe ser un número entero mayor o igual a 1."}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT tren_id, posicion FROM TREN_VAGON WHERE id_tren_vagon = :id_tv AND fecha_fin IS NULL
        """, {"id_tv": id_tren_vagon})
        row = cursor.fetchone()
        if not row:
            return {"success": False, "error": "El registro de composición no está activo."}

        tren_id, pos_actual = int(row[0]), int(row[1])
        if pos_actual == nueva_posicion:
            return {"success": True}

        # Intercambiar o desplazar
        cursor.execute("""
            SELECT id_tren_vagon FROM TREN_VAGON
            WHERE tren_id = :tren_id AND posicion = :nueva_pos AND fecha_fin IS NULL
        """, {"tren_id": tren_id, "nueva_pos": nueva_posicion})
        otro = cursor.fetchone()
        if otro:
            # Intercambiar posiciones
            otro_id = int(otro[0])
            cursor.execute("UPDATE TREN_VAGON SET posicion = -1 WHERE id_tren_vagon = :id_tv", {"id_tv": id_tren_vagon})
            cursor.execute("UPDATE TREN_VAGON SET posicion = :pos_actual WHERE id_tren_vagon = :otro_id", {
                "pos_actual": pos_actual, "otro_id": otro_id
            })
            cursor.execute("UPDATE TREN_VAGON SET posicion = :nueva_pos WHERE id_tren_vagon = :id_tv", {
                "nueva_pos": nueva_posicion, "id_tv": id_tren_vagon
            })
        else:
            cursor.execute("UPDATE TREN_VAGON SET posicion = :nueva_pos WHERE id_tren_vagon = :id_tv", {
                "nueva_pos": nueva_posicion, "id_tv": id_tren_vagon
            })

        conn.commit()
        return {"success": True}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def get_historial_composicion(
    tren_id: Optional[int] = None,
    vagon_id: Optional[int] = None,
    estado_filtro: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retorna la auditoría completa de asociaciones históricas y activas entre
    trenes y vagones (TREN_VAGON). Cumple con el requerimiento:
    "Conservar el historial de vagones asignados" y la Regla 25.
    """
    sql = """
        SELECT tv.id_tren_vagon,
               tv.tren_id, t.codigo_interno AS codigo_tren,
               tv.vagon_id, v.numero_serie AS numero_vagon, v.tipo_vagon,
               tv.posicion,
               TO_CHAR(tv.fecha_inicio, 'YYYY-MM-DD HH24:MI:SS') AS fecha_inicio,
               TO_CHAR(tv.fecha_fin, 'YYYY-MM-DD HH24:MI:SS') AS fecha_fin,
               CASE WHEN tv.fecha_fin IS NULL THEN 'Activo' ELSE 'Histórico' END AS estado_asociacion,
               (NVL(v.capacidad_sentados, 0) + NVL(v.capacidad_de_pie, 0)) AS capacidad_vagon
        FROM TREN_VAGON tv
        JOIN TREN t ON tv.tren_id = t.id_tren
        JOIN VAGON v ON tv.vagon_id = v.id_vagon
        WHERE 1=1
    """
    params: Dict[str, Any] = {}
    if tren_id is not None:
        sql += " AND tv.tren_id = :tren_id"
        params["tren_id"] = tren_id

    if vagon_id is not None:
        sql += " AND tv.vagon_id = :vagon_id"
        params["vagon_id"] = vagon_id

    if estado_filtro == "Activos":
        sql += " AND tv.fecha_fin IS NULL"
    elif estado_filtro == "Históricos":
        sql += " AND tv.fecha_fin IS NOT NULL"

    sql += " ORDER BY tv.fecha_inicio DESC, tv.posicion ASC"
    return _query_rows(sql, params)


# ==============================================================================
# 5. DISPONIBILIDAD OPERATIVA Y ASIGNACION A VIAJES (REGLAS 8 Y 11)
# ==============================================================================

def verificar_disponibilidad_tren(id_tren: int) -> Dict[str, Any]:
    """
    Evalúa la disponibilidad operativa del tren en tiempo real:
    1. Invoca la función PL/SQL FN_TREN_DISPONIBLE.
    2. Comprueba si la fecha próxima de inspección técnica está vencida.
    3. Comprueba si tiene órdenes de mantenimiento abiertas.
    4. Comprueba si actualmente tiene un viaje en curso.
    """
    sql = """
        SELECT t.id_tren, t.codigo_interno, t.estado_operativo,
               t.capacidad_total,
               TO_CHAR(t.fecha_proxima_inspeccion, 'YYYY-MM-DD') AS fecha_proxima_inspeccion,
               FN_TREN_DISPONIBLE(t.id_tren) AS disponible_fn,
               CASE 
                   WHEN t.fecha_proxima_inspeccion IS NOT NULL AND t.fecha_proxima_inspeccion < TRUNC(SYSDATE) THEN 1
                   ELSE 0
               END AS inspeccion_vencida,
               TRUNC(t.fecha_proxima_inspeccion) - TRUNC(SYSDATE) AS dias_para_inspeccion,
               (
                   SELECT COUNT(*)
                   FROM EQUIPO eq
                   JOIN ORDEN_MANTENIMIENTO om ON eq.id_equipo = om.equipo_id
                   WHERE eq.tipo_referencia = 'TREN'
                     AND eq.referencia_id = t.id_tren
                     AND om.estado IN ('Solicitada', 'Programada', 'En Ejecución', 'En Ejecucion')
               ) AS ordenes_mantenimiento_activas,
               (
                   SELECT COUNT(*)
                   FROM VIAJE_PROGRAMADO vp
                   WHERE vp.tren_id = t.id_tren AND vp.estado = 'En Curso'
               ) AS viajes_en_curso
        FROM TREN t
        WHERE t.id_tren = :id_tren
    """
    rows = _query_rows(sql, {"id_tren": id_tren})
    if not rows:
        return {"success": False, "error": "Tren no encontrado"}

    row = rows[0]
    disponible_fn = _safe_int(row.get("DISPONIBLE_FN")) == 1
    inspeccion_vencida = _safe_int(row.get("INSPECCION_VENCIDA")) == 1
    ordenes_activas = _safe_int(row.get("ORDENES_MANTENIMIENTO_ACTIVAS"))
    viajes_curso = _safe_int(row.get("VIAJES_EN_CURSO"))
    estado_op = str(row.get("ESTADO_OPERATIVO", ""))

    motivos = []
    if estado_op != "Disponible":
        motivos.append(f"Estado operativo es '{estado_op}'")
    if ordenes_activas > 0:
        motivos.append(f"Tiene {ordenes_activas} orden(es) de mantenimiento activa(s)")
    if inspeccion_vencida:
        motivos.append("Inspección técnica de seguridad vencida")
    if viajes_curso > 0:
        motivos.append("Tiene un viaje activo en curso")

    apto = disponible_fn and not inspeccion_vencida and viajes_curso == 0

    return {
        "success": True,
        "id_tren": id_tren,
        "codigo_interno": row["CODIGO_INTERNO"],
        "estado_operativo": estado_op,
        "capacidad_total": _safe_int(row.get("CAPACIDAD_TOTAL")),
        "fecha_proxima_inspeccion": row.get("FECHA_PROXIMA_INSPECCION", "-"),
        "dias_para_inspeccion": row.get("DIAS_PARA_INSPECCION"),
        "disponible_fn": disponible_fn,
        "inspeccion_vencida": inspeccion_vencida,
        "ordenes_mantenimiento_activas": ordenes_activas,
        "viajes_en_curso": viajes_curso,
        "apto_para_servicio": apto,
        "motivos": motivos
    }


def get_kpis_flota() -> Dict[str, int]:
    """
    Retorna los contadores clave de la flota para los cuadros de mando:
    - Total de trenes
    - Trenes disponibles
    - Trenes en operación
    - Trenes en mantenimiento
    - Trenes con inspección vencida
    - Total de vagones
    - Vagones en uso vs disponibles
    """
    sql = """
        SELECT
            (SELECT COUNT(*) FROM TREN) AS total_trenes,
            (SELECT COUNT(*) FROM TREN WHERE estado_operativo = 'Disponible') AS disponibles,
            (SELECT COUNT(*) FROM TREN WHERE estado_operativo = 'En Operación' OR estado_operativo LIKE 'En Operac%') AS en_operacion,
            (SELECT COUNT(*) FROM TREN WHERE estado_operativo = 'En Mantenimiento') AS en_mantenimiento,
            (SELECT COUNT(*) FROM TREN WHERE fecha_proxima_inspeccion < TRUNC(SYSDATE)) AS inspecciones_vencidas,
            (SELECT COUNT(*) FROM VAGON) AS total_vagones,
            (SELECT COUNT(*) FROM VAGON WHERE estado = 'En Uso') AS vagones_en_uso,
            (SELECT COUNT(*) FROM VAGON WHERE estado = 'Disponible') AS vagones_libres
        FROM DUAL
    """
    rows = _query_rows(sql)
    if rows:
        r = rows[0]
        return {
            "total_trenes": _safe_int(r.get("TOTAL_TRENES")),
            "disponibles": _safe_int(r.get("DISPONIBLES")),
            "en_operacion": _safe_int(r.get("EN_OPERACION")),
            "en_mantenimiento": _safe_int(r.get("EN_MANTENIMIENTO")),
            "inspecciones_vencidas": _safe_int(r.get("INSPECCIONES_VENCIDAS")),
            "total_vagones": _safe_int(r.get("TOTAL_VAGONES")),
            "vagones_en_uso": _safe_int(r.get("VAGONES_EN_USO")),
            "vagones_libres": _safe_int(r.get("VAGONES_LIBRES")),
        }
    return {
        "total_trenes": 0, "disponibles": 0, "en_operacion": 0,
        "en_mantenimiento": 0, "inspecciones_vencidas": 0,
        "total_vagones": 0, "vagones_en_uso": 0, "vagones_libres": 0
    }


def get_viajes_asignados_tren(
    id_tren: Optional[int] = None,
    fecha_filtro: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retorna la lista de viajes programados asociados a un tren (o todos los viajes
    para facilitar la asignación de trenes pendientes).
    """
    sql = """
        SELECT vp.id_viaje, vp.numero_viaje,
               vp.ruta_id, r.codigo AS codigo_ruta,
               l.codigo AS codigo_linea, l.color AS color_linea,
               TO_CHAR(vp.fecha, 'YYYY-MM-DD') AS fecha,
               TO_CHAR(vp.hora_prog_salida, 'YYYY-MM-DD HH24:MI:SS') AS salida_prog,
               TO_CHAR(vp.hora_prog_llegada, 'YYYY-MM-DD HH24:MI:SS') AS llegada_prog,
               vp.tren_id, t.codigo_interno AS codigo_tren,
               vp.conductor_id, e.nombre_completo AS conductor,
               vp.estado AS estado_viaje,
               vp.cantidad_estimada_pasajeros
        FROM VIAJE_PROGRAMADO vp
        JOIN RUTA r ON vp.ruta_id = r.id_ruta
        JOIN LINEA l ON r.linea_id = l.id_linea
        LEFT JOIN TREN t ON vp.tren_id = t.id_tren
        LEFT JOIN EMPLEADO e ON vp.conductor_id = e.id_empleado
        WHERE 1=1
    """
    params: Dict[str, Any] = {}
    if id_tren is not None:
        sql += " AND vp.tren_id = :id_tren"
        params["id_tren"] = id_tren

    if fecha_filtro:
        sql += " AND vp.fecha = TO_DATE(:fecha_filtro, 'YYYY-MM-DD')"
        params["fecha_filtro"] = fecha_filtro

    sql += " ORDER BY vp.fecha DESC, vp.hora_prog_salida DESC"
    return _query_rows(sql, params)


def asignar_tren_a_viaje(id_viaje: int, id_tren: int) -> Dict[str, Any]:
    """
    Asigna un tren a un viaje programado, garantizando el cumplimiento estricto de:
    - Regla de Negocio 11: Un tren en mantenimiento o fuera de servicio no puede asignarse.
      (Validado también por el trigger TRG_TREN_MANTENIMIENTO_NO_ASIGNAR).
    - Regla de Negocio 8: Un tren no puede estar asignado a dos viajes simultáneos.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Obtener datos del viaje a asignar
        cursor.execute("""
            SELECT id_viaje, numero_viaje, fecha,
                   hora_prog_salida, hora_prog_llegada, estado
            FROM VIAJE_PROGRAMADO
            WHERE id_viaje = :id_viaje
        """, {"id_viaje": id_viaje})
        viaje = cursor.fetchone()
        if not viaje:
            return {"success": False, "error": "El viaje programado no existe."}

        num_viaje = viaje[1]
        fecha_viaje = viaje[2]
        salida_viaje = viaje[3]
        llegada_viaje = viaje[4]
        estado_viaje = viaje[5]

        if estado_viaje in ("Cancelado", "Completado"):
            return {
                "success": False,
                "error": f"No se puede asignar tren al viaje {num_viaje} porque su estado es '{estado_viaje}'."
            }

        # 2. Validar estado del tren (Regla 11)
        cursor.execute("""
            SELECT codigo_interno, estado_operativo, fecha_proxima_inspeccion
            FROM TREN
            WHERE id_tren = :id_tren
        """, {"id_tren": id_tren})
        tren = cursor.fetchone()
        if not tren:
            return {"success": False, "error": "El tren seleccionado no existe."}

        cod_tren, estado_tren, prox_insp = tren[0], tren[1], tren[2]

        if estado_tren == "En Mantenimiento":
            return {
                "success": False,
                "error": f"Operación rechazada (Regla 11): El tren {cod_tren} se encuentra en taller de mantenimiento."
            }
        if estado_tren in ("Fuera de Servicio", "Retirado"):
            return {
                "success": False,
                "error": f"Operación rechazada: El tren {cod_tren} está fuera de servicio o retirado."
            }

        # 3. Validar solapamiento horario de este tren con otros viajes (Regla de Negocio 8)
        sql_solapamiento = """
            SELECT vp.numero_viaje,
                   TO_CHAR(vp.hora_prog_salida, 'HH24:MI') AS sal,
                   TO_CHAR(vp.hora_prog_llegada, 'HH24:MI') AS lleg
            FROM VIAJE_PROGRAMADO vp
            WHERE vp.tren_id = :id_tren
              AND vp.fecha = :fecha_viaje
              AND vp.id_viaje != :id_viaje
              AND vp.estado NOT IN ('Cancelado', 'Completado')
              AND (
                  (vp.hora_prog_salida < :llegada_viaje AND vp.hora_prog_llegada > :salida_viaje)
              )
        """
        cursor.execute(sql_solapamiento, {
            "id_tren": id_tren,
            "fecha_viaje": fecha_viaje,
            "id_viaje": id_viaje,
            "llegada_viaje": llegada_viaje,
            "salida_viaje": salida_viaje
        })
        conflicto = cursor.fetchone()
        if conflicto:
            return {
                "success": False,
                "error": f"Conflicto de asignación (Regla 8): El tren {cod_tren} ya está asignado al viaje {conflicto[0]} ({conflicto[1]} - {conflicto[2]}) en ese mismo intervalo horario."
            }

        # 4. Actualizar asignación
        cursor.execute("""
            UPDATE VIAJE_PROGRAMADO
            SET tren_id = :id_tren
            WHERE id_viaje = :id_viaje
        """, {"id_tren": id_tren, "id_viaje": id_viaje})

        conn.commit()
        return {
            "success": True,
            "mensaje": f"Tren {cod_tren} asignado exitosamente al viaje {num_viaje}."
        }
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def desasignar_tren_de_viaje(id_viaje: int) -> Dict[str, Any]:
    """
    Desvincula el tren asignado a un viaje, siempre que el viaje esté en estado 'Programado'.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT numero_viaje, estado, tren_id FROM VIAJE_PROGRAMADO WHERE id_viaje = :id_viaje
        """, {"id_viaje": id_viaje})
        row = cursor.fetchone()
        if not row:
            return {"success": False, "error": "El viaje no existe."}

        num_viaje, estado_viaje, tren_id = row[0], row[1], row[2]
        if not tren_id:
            return {"success": False, "error": "El viaje no tiene ningún tren asignado."}

        if estado_viaje != "Programado":
            return {
                "success": False,
                "error": f"No se puede desasignar el tren: el viaje {num_viaje} se encuentra en estado '{estado_viaje}'."
            }

        cursor.execute("UPDATE VIAJE_PROGRAMADO SET tren_id = NULL WHERE id_viaje = :id_viaje", {"id_viaje": id_viaje})
        conn.commit()
        return {"success": True, "mensaje": f"Tren desasignado del viaje {num_viaje}."}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()
