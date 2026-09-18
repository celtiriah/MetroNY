"""
m5_cards_service.py - Servicio especializado para el Módulo 5: Pasajeros y Tarifas OMNY.
Proporciona lógica de negocio y operaciones transaccionales para:
1. Gestión de Pasajeros Frecuentes (PASAJERO) y categorización de perfiles.
2. Emisión y ciclo de vida de Tarjetas OMNY / MetroCard (TARJETA), nominales y anónimas.
3. Validación y simulación de paso por torniquetes (SP_REGISTRAR_INGRESO, VIAJE_PASAJERO).
4. Recarga de saldo en estaciones y canales digitales (SP_RECARGAR_TARJETA, RECARGA).
5. Catálogo de Tarifas vigentes (TARIFA) y reglas de Fare Capping de la MTA.
6. Métricas y KPIs de recaudación y afluencia de pasajeros.
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import oracledb

from services.db import get_connection, execute_query
from services.actions_service import parse_oracle_error


def _query_rows(sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Ejecuta una consulta SQL y retorna la lista de diccionarios de filas."""
    res = execute_query(sql, params)
    return res.get("rows", [])


# ==============================================================================
# 1. GESTION DE PASAJEROS FRECUENTES (PASAJERO)
# ==============================================================================

def get_pasajeros(
    tipo_filter: Optional[str] = None,
    estado_filter: Optional[str] = None,
    search_text: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retorna el padrón de pasajeros registrados con conteo de tarjetas asociadas.
    """
    sql = """
        SELECT p.id_pasajero, p.identificador, p.nombre,
               TO_CHAR(p.fecha_nacimiento, 'YYYY-MM-DD') AS fecha_nacimiento,
               p.correo_electronico, p.telefono, p.tipo_pasajero,
               TO_CHAR(p.fecha_registro, 'YYYY-MM-DD') AS fecha_registro,
               p.estado,
               (
                   SELECT COUNT(*)
                   FROM TARJETA t
                   WHERE t.pasajero_id = p.id_pasajero
               ) AS total_tarjetas,
               (
                   SELECT NVL(SUM(t.saldo_disponible), 0)
                   FROM TARJETA t
                   WHERE t.pasajero_id = p.id_pasajero
               ) AS saldo_total_acumulado
        FROM PASAJERO p
        WHERE 1=1
    """
    params: Dict[str, Any] = {}
    if tipo_filter and tipo_filter != "(Todos)":
        sql += " AND p.tipo_pasajero = :tipo_filter"
        params["tipo_filter"] = tipo_filter

    if estado_filter and estado_filter != "(Todos)":
        sql += " AND p.estado = :estado_filter"
        params["estado_filter"] = estado_filter

    if search_text:
        sql += """ AND (
            LOWER(p.nombre) LIKE :st
            OR LOWER(p.identificador) LIKE :st
            OR LOWER(NVL(p.correo_electronico, '')) LIKE :st
            OR LOWER(NVL(p.telefono, '')) LIKE :st
        )"""
        params["st"] = f"%{search_text.strip().lower()}%"

    sql += " ORDER BY p.nombre ASC"
    return _query_rows(sql, params)


def get_pasajero_by_id(id_pasajero: int) -> Optional[Dict[str, Any]]:
    """Retorna la ficha de un pasajero específico."""
    sql = """
        SELECT p.id_pasajero, p.identificador, p.nombre,
               TO_CHAR(p.fecha_nacimiento, 'YYYY-MM-DD') AS fecha_nacimiento,
               p.correo_electronico, p.telefono, p.tipo_pasajero,
               TO_CHAR(p.fecha_registro, 'YYYY-MM-DD') AS fecha_registro,
               p.estado
        FROM PASAJERO p
        WHERE p.id_pasajero = :id
    """
    rows = _query_rows(sql, {"id": id_pasajero})
    return rows[0] if rows else None


def crear_pasajero(datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Registra un nuevo pasajero frecuente en la tabla PASAJERO usando SEQ_PASAJERO.NEXTVAL.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT SEQ_PASAJERO.NEXTVAL FROM DUAL")
        new_id = int(cursor.fetchone()[0])

        ident = datos.get("identificador", "").strip().upper()
        if not ident:
            ident = f"PAS-{new_id:03d}"

        # Validar tipo de pasajero permitido
        tipo_pas = datos.get("tipo_pasajero", "Regular")
        tipos_validos = ["Adulto Mayor", "Empleado Autorizado", "Estudiante", "Persona con Discapacidad", "Regular"]
        if tipo_pas not in tipos_validos:
            tipo_pas = "Regular"

        sql = """
            INSERT INTO PASAJERO (
                id_pasajero, identificador, nombre, fecha_nacimiento,
                correo_electronico, telefono, tipo_pasajero, fecha_registro, estado
            ) VALUES (
                :id_pas, :ident, :nombre,
                CASE WHEN :f_nac IS NOT NULL THEN TO_DATE(:f_nac, 'YYYY-MM-DD') ELSE NULL END,
                :correo, :tel, :tipo,
                CASE WHEN :f_reg IS NOT NULL THEN TO_DATE(:f_reg, 'YYYY-MM-DD') ELSE SYSDATE END,
                :estado
            )
        """
        params = {
            "id_pas": new_id,
            "ident": ident[:20],
            "nombre": datos["nombre"].strip()[:150],
            "f_nac": datos.get("fecha_nacimiento") or None,
            "correo": (datos.get("correo_electronico") or "").strip().lower()[:100] or None,
            "tel": (datos.get("telefono") or "").strip()[:20] or None,
            "tipo": tipo_pas[:25],
            "f_reg": datos.get("fecha_registro") or None,
            "estado": datos.get("estado", "Activo")[:15]
        }
        cursor.execute(sql, params)
        conn.commit()
        return {"success": True, "id_pasajero": new_id, "identificador": ident}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def modificar_pasajero(id_pasajero: int, datos: Dict[str, Any]) -> Dict[str, Any]:
    """Actualiza datos personales o categoría de un pasajero."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE PASAJERO
            SET identificador = :ident,
                nombre = :nombre,
                fecha_nacimiento = CASE WHEN :f_nac IS NOT NULL THEN TO_DATE(:f_nac, 'YYYY-MM-DD') ELSE NULL END,
                correo_electronico = :correo,
                telefono = :tel,
                tipo_pasajero = :tipo,
                estado = :estado
            WHERE id_pasajero = :id
        """
        params = {
            "id": id_pasajero,
            "ident": datos.get("identificador", "").strip().upper()[:20],
            "nombre": datos["nombre"].strip()[:150],
            "f_nac": datos.get("fecha_nacimiento") or None,
            "correo": (datos.get("correo_electronico") or "").strip().lower()[:100] or None,
            "tel": (datos.get("telefono") or "").strip()[:20] or None,
            "tipo": datos.get("tipo_pasajero", "Regular")[:25],
            "estado": datos.get("estado", "Activo")[:15]
        }
        cursor.execute(sql, params)
        conn.commit()
        return {"success": True}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def cambiar_estado_pasajero(id_pasajero: int, nuevo_estado: str) -> Dict[str, Any]:
    """Cambia el estado del pasajero ('Activo', 'Inactivo')."""
    if nuevo_estado not in ("Activo", "Inactivo"):
        return {"success": False, "error": "Estado inválido. Opciones: Activo, Inactivo"}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE PASAJERO SET estado = :est WHERE id_pasajero = :id", {"est": nuevo_estado, "id": id_pasajero})
        conn.commit()
        return {"success": True, "nuevo_estado": nuevo_estado}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def eliminar_pasajero(id_pasajero: int) -> Dict[str, Any]:
    """
    Elimina un pasajero si no tiene tarjetas con saldo o transacciones registradas.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM TARJETA WHERE pasajero_id = :id", {"id": id_pasajero})
        tarjetas_count = cursor.fetchone()[0]
        if tarjetas_count > 0:
            return {
                "success": False,
                "error": f"No se puede eliminar: el pasajero tiene {tarjetas_count} tarjeta(s) vinculada(s). Desvincúlelas primero."
            }

        cursor.execute("DELETE FROM PASAJERO WHERE id_pasajero = :id", {"id": id_pasajero})
        conn.commit()
        return {"success": True}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 2. GESTION DE TARJETAS (TARJETA) - NOMINALES Y ANONIMAS
# ==============================================================================

def get_tarjetas(
    estado_filter: Optional[str] = None,
    search_text: Optional[str] = None,
    pasajero_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Retorna el catálogo de tarjetas con su titular, tarifa asignada, saldo y estado.
    """
    sql = """
        SELECT t.id_tarjeta, t.numero_tarjeta, t.pasajero_id,
               NVL(p.nombre, 'Anónima / Al Portador') AS pasajero,
               NVL(p.identificador, '-') AS identificador_pasajero,
               NVL(p.tipo_pasajero, 'No Registrado') AS tipo_pasajero,
               TO_CHAR(t.fecha_emision, 'YYYY-MM-DD') AS fecha_emision,
               TO_CHAR(t.fecha_vencimiento, 'YYYY-MM-DD') AS fecha_vencimiento,
               t.saldo_disponible,
               t.tarifa_id,
               tar.codigo AS tarifa_codigo,
               tar.nombre AS tarifa_nombre,
               tar.monto AS tarifa_monto,
               t.estado,
               CASE 
                   WHEN t.fecha_vencimiento IS NOT NULL AND t.fecha_vencimiento < TRUNC(SYSDATE) THEN 1
                   ELSE 0
               END AS esta_vencida,
               TRUNC(NVL(t.fecha_vencimiento, SYSDATE)) - TRUNC(SYSDATE) AS dias_restantes,
               (
                   SELECT COUNT(*)
                   FROM VIAJE_PASAJERO vp
                   WHERE vp.tarjeta_id = t.id_tarjeta
               ) AS total_viajes,
               (
                   SELECT COUNT(*)
                   FROM RECARGA r
                   WHERE r.tarjeta_id = t.id_tarjeta
               ) AS total_recargas
        FROM TARJETA t
        LEFT JOIN PASAJERO p ON t.pasajero_id = p.id_pasajero
        LEFT JOIN TARIFA tar ON t.tarifa_id = tar.id_tarifa
        WHERE 1=1
    """
    params: Dict[str, Any] = {}
    if estado_filter and estado_filter != "(Todos)":
        sql += " AND t.estado = :estado_filter"
        params["estado_filter"] = estado_filter

    if pasajero_id is not None:
        sql += " AND t.pasajero_id = :p_id"
        params["p_id"] = pasajero_id

    if search_text:
        sql += """ AND (
            LOWER(t.numero_tarjeta) LIKE :st
            OR LOWER(NVL(p.nombre, '')) LIKE :st
            OR LOWER(NVL(tar.nombre, '')) LIKE :st
        )"""
        params["st"] = f"%{search_text.strip().lower()}%"

    sql += " ORDER BY t.id_tarjeta ASC"
    return _query_rows(sql, params)


def get_tarjeta_by_id(id_tarjeta: int) -> Optional[Dict[str, Any]]:
    """Retorna la información completa de una tarjeta por ID."""
    sql = """
        SELECT t.id_tarjeta, t.numero_tarjeta, t.pasajero_id,
               NVL(p.nombre, 'Anónima / Al Portador') AS pasajero,
               TO_CHAR(t.fecha_emision, 'YYYY-MM-DD') AS fecha_emision,
               TO_CHAR(t.fecha_vencimiento, 'YYYY-MM-DD') AS fecha_vencimiento,
               t.saldo_disponible, t.tarifa_id, tar.nombre AS tarifa_nombre,
               tar.monto AS tarifa_monto, t.estado
        FROM TARJETA t
        LEFT JOIN PASAJERO p ON t.pasajero_id = p.id_pasajero
        LEFT JOIN TARIFA tar ON t.tarifa_id = tar.id_tarifa
        WHERE t.id_tarjeta = :id
    """
    rows = _query_rows(sql, {"id": id_tarjeta})
    return rows[0] if rows else None


def get_tarjeta_by_numero(numero_tarjeta: str) -> Optional[Dict[str, Any]]:
    """Retorna la tarjeta a partir de su número OMNY."""
    sql = """
        SELECT t.id_tarjeta, t.numero_tarjeta, t.pasajero_id,
               NVL(p.nombre, 'Anónima / Al Portador') AS pasajero,
               t.saldo_disponible, t.tarifa_id, tar.nombre AS tarifa_nombre,
               tar.monto AS tarifa_monto, t.estado,
               TO_CHAR(t.fecha_vencimiento, 'YYYY-MM-DD') AS fecha_vencimiento
        FROM TARJETA t
        LEFT JOIN PASAJERO p ON t.pasajero_id = p.id_pasajero
        LEFT JOIN TARIFA tar ON t.tarifa_id = tar.id_tarifa
        WHERE t.numero_tarjeta = :num
    """
    rows = _query_rows(sql, {"num": numero_tarjeta.strip()})
    return rows[0] if rows else None


def emitir_tarjeta(datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Emite una nueva tarjeta OMNY (nominal o anónima) en Oracle.
    Regla 13: Una tarjeta puede pertenecer a un pasajero o ser anónima.
    Regla 15: El saldo inicial no puede ser negativo.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT SEQ_TARJETA.NEXTVAL FROM DUAL")
        new_id = int(cursor.fetchone()[0])

        num_tarjeta = datos.get("numero_tarjeta", "").strip().upper()
        if not num_tarjeta:
            num_tarjeta = f"OMNY-2026-{new_id:04d}"

        # Obtener tarifa predeterminada si no se indica
        tarifa_id = datos.get("tarifa_id")
        if not tarifa_id:
            cursor.execute("SELECT id_tarifa FROM TARIFA WHERE codigo = 'TAR-REG' AND ROWNUM = 1")
            row_tar = cursor.fetchone()
            tarifa_id = row_tar[0] if row_tar else 1

        saldo_ini = float(datos.get("saldo_disponible") or 0.0)
        if saldo_ini < 0:
            return {"success": False, "error": "El saldo inicial no puede ser negativo (Regla de negocio 15)."}

        # Fechas de emisión y vencimiento (5 años estándar)
        f_emi = datos.get("fecha_emision")
        f_venc = datos.get("fecha_vencimiento")

        pasajero_id = datos.get("pasajero_id")
        if pasajero_id:
            pasajero_id = int(pasajero_id)

        sql = """
            INSERT INTO TARJETA (
                id_tarjeta, numero_tarjeta, pasajero_id,
                fecha_emision, fecha_vencimiento,
                saldo_disponible, tarifa_id, estado
            ) VALUES (
                :id_tar, :num_tar, :pas_id,
                CASE WHEN :f_emi IS NOT NULL THEN TO_DATE(:f_emi, 'YYYY-MM-DD') ELSE SYSDATE END,
                CASE WHEN :f_venc IS NOT NULL THEN TO_DATE(:f_venc, 'YYYY-MM-DD') ELSE ADD_MONTHS(SYSDATE, 60) END,
                :saldo, :tarifa_id, :estado
            )
        """
        params = {
            "id_tar": new_id,
            "num_tar": num_tarjeta[:20],
            "pas_id": pasajero_id,
            "f_emi": f_emi or None,
            "f_venc": f_venc or None,
            "saldo": saldo_ini,
            "tarifa_id": int(tarifa_id),
            "estado": datos.get("estado", "Activa")[:20]
        }
        cursor.execute(sql, params)
        conn.commit()
        return {"success": True, "id_tarjeta": new_id, "numero_tarjeta": num_tarjeta}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def modificar_tarjeta(id_tarjeta: int, datos: Dict[str, Any]) -> Dict[str, Any]:
    """Actualiza la tarifa, fecha de vencimiento o titular de la tarjeta."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        pas_id = datos.get("pasajero_id")
        if pas_id:
            pas_id = int(pas_id)

        sql = """
            UPDATE TARJETA
            SET pasajero_id = :pas_id,
                tarifa_id = :tar_id,
                fecha_vencimiento = CASE WHEN :f_venc IS NOT NULL THEN TO_DATE(:f_venc, 'YYYY-MM-DD') ELSE fecha_vencimiento END,
                estado = :estado
            WHERE id_tarjeta = :id
        """
        params = {
            "id": id_tarjeta,
            "pas_id": pas_id,
            "tar_id": int(datos["tarifa_id"]),
            "f_venc": datos.get("fecha_vencimiento") or None,
            "estado": datos.get("estado", "Activa")[:20]
        }
        cursor.execute(sql, params)
        conn.commit()
        return {"success": True}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def cambiar_estado_tarjeta(id_tarjeta: int, nuevo_estado: str) -> Dict[str, Any]:
    """
    Cambia el estado de una tarjeta ('Activa', 'Bloqueada', 'Cancelada', 'Reportada Perdida', 'Vencida').
    """
    estados_validos = ["Activa", "Bloqueada", "Cancelada", "Reportada Perdida", "Vencida"]
    if nuevo_estado not in estados_validos:
        return {"success": False, "error": f"Estado inválido. Opciones: {', '.join(estados_validos)}"}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE TARJETA SET estado = :est WHERE id_tarjeta = :id",
            {"est": nuevo_estado, "id": id_tarjeta}
        )
        conn.commit()
        return {"success": True, "nuevo_estado": nuevo_estado}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def eliminar_tarjeta(id_tarjeta: int) -> Dict[str, Any]:
    """
    Elimina una tarjeta si no tiene viajes ni recargas registradas (Regla 25).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM VIAJE_PASAJERO WHERE tarjeta_id = :id", {"id": id_tarjeta})
        viajes_count = cursor.fetchone()[0]
        if viajes_count > 0:
            return {
                "success": False,
                "error": f"No se puede eliminar físicamente: tiene {viajes_count} viaje(s) histórico(s) (Regla de negocio 25)."
            }

        cursor.execute("SELECT COUNT(*) FROM RECARGA WHERE tarjeta_id = :id", {"id": id_tarjeta})
        rec_count = cursor.fetchone()[0]
        if rec_count > 0:
            return {
                "success": False,
                "error": f"No se puede eliminar: tiene {rec_count} recarga(s) registrada(s)."
            }

        cursor.execute("DELETE FROM TARJETA WHERE id_tarjeta = :id", {"id": id_tarjeta})
        conn.commit()
        return {"success": True}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 3. OPERACIONES DE TORNIQUETE, RECARGAS Y VIAJES
# ==============================================================================

def validar_ingreso_torniquete(
    numero_tarjeta: str,
    estacion_id: int,
    viaje_programado_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Ejecuta el procedimiento almacenado canónico SP_REGISTRAR_INGRESO:
    - Verifica si la estación está operativa (Regla 21).
    - Verifica si la tarjeta está activa y vigente (Regla 16).
    - Verifica si el saldo cubre la tarifa (Regla 15).
    - Descuenta la tarifa y registra la transacción en VIAJE_PASAJERO (Regla 18).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        v_resultado = cursor.var(str)
        v_mensaje = cursor.var(str)
        v_cobrado = cursor.var(oracledb.NUMBER)
        v_saldo = cursor.var(oracledb.NUMBER)

        cursor.callproc(
            "SP_REGISTRAR_INGRESO",
            [
                numero_tarjeta.strip().upper(),
                int(estacion_id),
                viaje_programado_id,
                v_resultado,
                v_mensaje,
                v_cobrado,
                v_saldo
            ]
        )
        conn.commit()

        res = str(v_resultado.getvalue() or "ERROR")
        msg = str(v_mensaje.getvalue() or "")
        cobrado = float(v_cobrado.getvalue() or 0.0)
        nuevo_saldo = float(v_saldo.getvalue() or 0.0)

        return {
            "success": (res == "AUTORIZADO"),
            "resultado": res,
            "mensaje": msg,
            "monto_cobrado": cobrado,
            "nuevo_saldo": nuevo_saldo
        }
    except Exception as exc:
        conn.rollback()
        return {
            "success": False,
            "resultado": "ERROR",
            "mensaje": parse_oracle_error(exc),
            "monto_cobrado": 0.0,
            "nuevo_saldo": 0.0
        }
    finally:
        cursor.close()
        conn.close()


def registrar_viaje_anonimo(estacion_id: int) -> Dict[str, Any]:
    """
    Registra un viaje de pasajero anónimo (Regla 13).
    Selecciona una tarjeta anónima activa con saldo o emite una transacción de pase rápido.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Buscar una tarjeta anónima con saldo suficiente
        cursor.execute("""
            SELECT numero_tarjeta
            FROM TARJETA
            WHERE pasajero_id IS NULL
              AND estado = 'Activa'
              AND saldo_disponible >= 2.90
            FETCH FIRST 1 ROWS ONLY
        """)
        row = cursor.fetchone()
        if row:
            num_anon = row[0]
        else:
            # Si no hay anónima con saldo, buscar cualquier anónima y recargarle $10
            cursor.execute("""
                SELECT numero_tarjeta
                FROM TARJETA
                WHERE pasajero_id IS NULL AND estado = 'Activa'
                FETCH FIRST 1 ROWS ONLY
            """)
            row2 = cursor.fetchone()
            if row2:
                num_anon = row2[0]
                recargar_tarjeta(num_anon, 10.0, "Efectivo", "Torniquete Rápido")
            else:
                # Emitir nueva tarjeta anónima
                res_emit = emitir_tarjeta({"saldo_disponible": 10.0})
                num_anon = res_emit.get("numero_tarjeta", "MC-ANON-9001")

        # Proceder con la validación de ingreso
        return validar_ingreso_torniquete(num_anon, estacion_id)
    except Exception as exc:
        return {"success": False, "resultado": "ERROR", "mensaje": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def recargar_tarjeta(
    numero_tarjeta: str,
    monto: float,
    medio_pago: str = "Efectivo",
    estacion_canal: str = "Torniquete Estacion"
) -> Dict[str, Any]:
    """
    Ejecuta el procedimiento canónico SP_RECARGAR_TARJETA.
    Regla 14: Una tarjeta puede registrar muchas recargas y muchos viajes.
    """
    if monto <= 0:
        return {"success": False, "error": "El monto a recargar debe ser estrictamente positivo."}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        v_nuevo_saldo = cursor.var(oracledb.NUMBER)
        v_num_tx = cursor.var(str)

        cursor.callproc(
            "SP_RECARGAR_TARJETA",
            [
                numero_tarjeta.strip().upper(),
                float(monto),
                medio_pago,
                estacion_canal[:50],
                v_nuevo_saldo,
                v_num_tx
            ]
        )
        conn.commit()

        saldo = float(v_nuevo_saldo.getvalue() or 0.0)
        num_tx = str(v_num_tx.getvalue() or "")

        return {
            "success": True,
            "nuevo_saldo": saldo,
            "numero_transaccion": num_tx,
            "mensaje": f"Recarga exitosa por ${monto:.2f}. Nuevo saldo disponible: ${saldo:.2f}."
        }
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def registrar_salida_torniquete(
    id_viaje_pasajero: int,
    estacion_salida_id: int
) -> Dict[str, Any]:
    """
    Registra la salida física del pasajero por el torniquete de destino,
    cerrando la transacción en VIAJE_PASAJERO.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE VIAJE_PASAJERO
            SET estacion_salida_id = :est_sal,
                fecha_hora_salida = SYSTIMESTAMP,
                estado_transaccion = 'Cerrada'
            WHERE id_viaje_pasajero = :id
        """
        cursor.execute(sql, {"est_sal": estacion_salida_id, "id": id_viaje_pasajero})
        conn.commit()
        return {"success": True}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 4. HISTORIALES Y AUDITORIA (VIAJE_PASAJERO / RECARGA)
# ==============================================================================

def get_historial_viajes(
    numero_tarjeta: Optional[str] = None,
    tarjeta_id: Optional[int] = None,
    estacion_id: Optional[int] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Retorna el historial pormenorizado de pasos por torniquete.
    """
    sql = """
        SELECT vp.id_viaje_pasajero, vp.numero_transaccion,
               t.numero_tarjeta,
               NVL(p.nombre, 'Anónima') AS pasajero,
               e_in.nombre AS estacion_ingreso,
               NVL(e_out.nombre, '-') AS estacion_salida,
               TO_CHAR(vp.fecha_hora_ingreso, 'YYYY-MM-DD HH24:MI:SS') AS fecha_hora_ingreso,
               TO_CHAR(vp.fecha_hora_ingreso, 'HH24:MI') AS hora_corta,
               vp.monto_cobrado,
               tar.nombre AS tarifa_aplicada,
               vp.estado_transaccion
        FROM VIAJE_PASAJERO vp
        JOIN TARJETA t ON vp.tarjeta_id = t.id_tarjeta
        LEFT JOIN PASAJERO p ON t.pasajero_id = p.id_pasajero
        JOIN ESTACION e_in ON vp.estacion_ingreso_id = e_in.id_estacion
        LEFT JOIN ESTACION e_out ON vp.estacion_salida_id = e_out.id_estacion
        JOIN TARIFA tar ON vp.tarifa_id = tar.id_tarifa
        WHERE 1=1
    """
    params: Dict[str, Any] = {}
    if numero_tarjeta:
        sql += " AND t.numero_tarjeta = :num_tar"
        params["num_tar"] = numero_tarjeta.strip()

    if tarjeta_id is not None:
        sql += " AND vp.tarjeta_id = :t_id"
        params["t_id"] = tarjeta_id

    if estacion_id is not None:
        sql += " AND vp.estacion_ingreso_id = :est_id"
        params["est_id"] = estacion_id

    sql += f" ORDER BY vp.fecha_hora_ingreso DESC FETCH FIRST {int(limit)} ROWS ONLY"
    return _query_rows(sql, params)


def get_historial_recargas(
    numero_tarjeta: Optional[str] = None,
    tarjeta_id: Optional[int] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Retorna el registro de abonos y recargas de saldo efectuadas.
    """
    sql = """
        SELECT r.id_recarga, r.numero_transaccion,
               t.numero_tarjeta,
               NVL(p.nombre, 'Anónima') AS pasajero,
               r.monto, r.medio_pago, r.estacion_canal,
               r.saldo_anterior, r.saldo_posterior,
               TO_CHAR(r.fecha_hora, 'YYYY-MM-DD HH24:MI:SS') AS fecha_hora,
               TO_CHAR(r.fecha_hora, 'HH24:MI') AS hora_corta
        FROM RECARGA r
        JOIN TARJETA t ON r.tarjeta_id = t.id_tarjeta
        LEFT JOIN PASAJERO p ON t.pasajero_id = p.id_pasajero
        WHERE 1=1
    """
    params: Dict[str, Any] = {}
    if numero_tarjeta:
        sql += " AND t.numero_tarjeta = :num_tar"
        params["num_tar"] = numero_tarjeta.strip()

    if tarjeta_id is not None:
        sql += " AND r.tarjeta_id = :t_id"
        params["t_id"] = tarjeta_id

    sql += f" ORDER BY r.fecha_hora DESC FETCH FIRST {int(limit)} ROWS ONLY"
    return _query_rows(sql, params)


# ==============================================================================
# 5. CATALOGO DE TARIFAS (TARIFA) Y FARE CAPPING
# ==============================================================================

def get_tarifas(estado_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retorna la lista de tarifas oficiales de la MTA, sus montos y vigencias.
    """
    sql = """
        SELECT id_tarifa, codigo, nombre, descripcion, monto,
               tipo_pasajero,
               TO_CHAR(fecha_inicio_vigencia, 'YYYY-MM-DD') AS fecha_inicio,
               TO_CHAR(fecha_fin_vigencia, 'YYYY-MM-DD') AS fecha_fin,
               cantidad_maxima_viajes, duracion_beneficio_dias, estado
        FROM TARIFA
        WHERE 1=1
    """
    params: Dict[str, Any] = {}
    if estado_filter and estado_filter != "(Todos)":
        sql += " AND estado = :est"
        params["est"] = estado_filter

    sql += " ORDER BY monto ASC"
    return _query_rows(sql, params)


def get_tarifas_combo() -> List[Dict[str, Any]]:
    """Retorna las tarifas vigentes para selectores en combobox."""
    sql = """
        SELECT id_tarifa, codigo, nombre, monto, tipo_pasajero
        FROM TARIFA
        WHERE estado = 'Vigente'
        ORDER BY monto ASC
    """
    return _query_rows(sql)


def get_estaciones_combo() -> List[Tuple[int, str]]:
    """Retorna las estaciones de metro para el simulador de torniquete."""
    sql = """
        SELECT id_estacion, codigo || ' - ' || nombre AS etiqueta, distrito
        FROM ESTACION
        WHERE estado_operativo = 'Operativa'
        ORDER BY nombre
    """
    rows = _query_rows(sql)
    return [(int(r["ID_ESTACION"]), f"{r['ETIQUETA']} ({r.get('DISTRITO', '')})") for r in rows]


def crear_tarifa(datos: Dict[str, Any]) -> Dict[str, Any]:
    """Registra una nueva tarifa en el sistema."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT SEQ_TARIFA.NEXTVAL FROM DUAL")
        new_id = int(cursor.fetchone()[0])

        cod = datos.get("codigo", "").strip().upper()
        if not cod:
            cod = f"TAR-{new_id:03d}"

        sql = """
            INSERT INTO TARIFA (
                id_tarifa, codigo, nombre, descripcion, monto,
                tipo_pasajero, fecha_inicio_vigencia, fecha_fin_vigencia,
                cantidad_maxima_viajes, duracion_beneficio_dias, estado
            ) VALUES (
                :id, :cod, :nombre, :descrip, :monto,
                :tipo_pas,
                CASE WHEN :f_ini IS NOT NULL THEN TO_DATE(:f_ini, 'YYYY-MM-DD') ELSE SYSDATE END,
                CASE WHEN :f_fin IS NOT NULL THEN TO_DATE(:f_fin, 'YYYY-MM-DD') ELSE NULL END,
                :max_viajes, :dur_dias, :estado
            )
        """
        params = {
            "id": new_id,
            "cod": cod[:15],
            "nombre": datos["nombre"].strip()[:60],
            "descrip": (datos.get("descripcion") or "").strip()[:200] or None,
            "monto": float(datos.get("monto") or 2.90),
            "tipo_pas": (datos.get("tipo_pasajero") or "Regular")[:25],
            "f_ini": datos.get("fecha_inicio_vigencia") or None,
            "f_fin": datos.get("fecha_fin_vigencia") or None,
            "max_viajes": datos.get("cantidad_maxima_viajes") or None,
            "dur_dias": datos.get("duracion_beneficio_dias") or None,
            "estado": datos.get("estado", "Vigente")[:15]
        }
        cursor.execute(sql, params)
        conn.commit()
        return {"success": True, "id_tarifa": new_id, "codigo": cod}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def modificar_tarifa(id_tarifa: int, datos: Dict[str, Any]) -> Dict[str, Any]:
    """Modifica el costo, descripción o vigencia de una tarifa."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE TARIFA
            SET nombre = :nombre,
                descripcion = :descrip,
                monto = :monto,
                tipo_pasajero = :tipo_pas,
                fecha_inicio_vigencia = CASE WHEN :f_ini IS NOT NULL THEN TO_DATE(:f_ini, 'YYYY-MM-DD') ELSE fecha_inicio_vigencia END,
                fecha_fin_vigencia = CASE WHEN :f_fin IS NOT NULL THEN TO_DATE(:f_fin, 'YYYY-MM-DD') ELSE NULL END,
                cantidad_maxima_viajes = :max_viajes,
                duracion_beneficio_dias = :dur_dias,
                estado = :estado
            WHERE id_tarifa = :id
        """
        params = {
            "id": id_tarifa,
            "nombre": datos["nombre"].strip()[:60],
            "descrip": (datos.get("descripcion") or "").strip()[:200] or None,
            "monto": float(datos.get("monto") or 2.90),
            "tipo_pas": (datos.get("tipo_pasajero") or "Regular")[:25],
            "f_ini": datos.get("fecha_inicio_vigencia") or None,
            "f_fin": datos.get("fecha_fin_vigencia") or None,
            "max_viajes": datos.get("cantidad_maxima_viajes") or None,
            "dur_dias": datos.get("duracion_beneficio_dias") or None,
            "estado": datos.get("estado", "Vigente")[:15]
        }
        cursor.execute(sql, params)
        conn.commit()
        return {"success": True}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 6. METRICAS EJECUTIVAS Y KPIS (OMNY / METROCARD)
# ==============================================================================

def get_kpis_omny() -> Dict[str, Any]:
    """
    Retorna las métricas clave de recaudación y usuarios OMNY:
    - Total de tarjetas registradas
    - Tarjetas activas
    - Saldo total disponible en circulación (USD)
    - Total de pasajeros registrados
    - Viajes validados hoy
    - Recaudación total de hoy
    """
    sql = """
        SELECT
            (SELECT COUNT(*) FROM TARJETA) AS total_tarjetas,
            (SELECT COUNT(*) FROM TARJETA WHERE estado = 'Activa') AS tarjetas_activas,
            (SELECT COUNT(*) FROM TARJETA WHERE estado = 'Bloqueada') AS tarjetas_bloqueadas,
            (SELECT NVL(SUM(saldo_disponible), 0) FROM TARJETA) AS saldo_total_circulacion,
            (SELECT COUNT(*) FROM PASAJERO) AS total_pasajeros,
            (SELECT COUNT(*) FROM VIAJE_PASAJERO WHERE TRUNC(fecha_hora_ingreso) = TRUNC(SYSDATE)) AS viajes_hoy,
            (SELECT NVL(SUM(monto_cobrado), 0) FROM VIAJE_PASAJERO WHERE TRUNC(fecha_hora_ingreso) = TRUNC(SYSDATE)) AS recaudacion_hoy
        FROM DUAL
    """
    rows = _query_rows(sql)
    if rows:
        r = rows[0]
        return {
            "total_tarjetas": int(r.get("TOTAL_TARJETAS") or 0),
            "tarjetas_activas": int(r.get("TARJETAS_ACTIVAS") or 0),
            "tarjetas_bloqueadas": int(r.get("TARJETAS_BLOQUEADAS") or 0),
            "saldo_total_circulacion": float(r.get("SALDO_TOTAL_CIRCULACION") or 0.0),
            "total_pasajeros": int(r.get("TOTAL_PASAJEROS") or 0),
            "viajes_hoy": int(r.get("VIAJES_HOY") or 0),
            "recaudacion_hoy": float(r.get("RECAUDACION_HOY") or 0.0),
        }
    return {
        "total_tarjetas": 0, "tarjetas_activas": 0, "tarjetas_bloqueadas": 0,
        "saldo_total_circulacion": 0.0, "total_pasajeros": 0,
        "viajes_hoy": 0, "recaudacion_hoy": 0.0
    }

