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
import re
from typing import List, Dict, Any, Optional, Tuple
import oracledb

from services.db import get_connection, execute_query
from services.actions_service import parse_oracle_error


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


def _validar_datos_pasajero(datos: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Valida los campos obligatorios y formatos de un pasajero frecuente."""
    nombre = (datos.get("nombre") or "").strip()
    if not nombre or len(nombre) < 3:
        return False, "El nombre del pasajero es obligatorio y debe tener al menos 3 caracteres."

    tipo_pas = datos.get("tipo_pasajero", "Regular")
    tipos_validos = ["Adulto Mayor", "Empleado Autorizado", "Estudiante", "Persona con Discapacidad", "Regular"]
    if tipo_pas not in tipos_validos:
        return False, f"Tipo de pasajero invalido ('{tipo_pas}'). Permitidos: {', '.join(tipos_validos)}."

    f_nac = datos.get("fecha_nacimiento")
    if f_nac:
        try:
            d_nac = datetime.strptime(str(f_nac)[:10], "%Y-%m-%d").date()
            today = date.today()
            if d_nac > today:
                return False, "La fecha de nacimiento no puede ser futura."
            edad = today.year - d_nac.year - ((today.month, today.day) < (d_nac.month, d_nac.day))
            if edad < 0 or edad > 125:
                return False, f"Fecha de nacimiento invalida (edad calculada: {edad} anios)."
        except ValueError:
            return False, "Formato de fecha de nacimiento invalido. Debe ser AAAA-MM-DD."

    correo = (datos.get("correo_electronico") or "").strip()
    if correo and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", correo):
        return False, "El formato del correo electronico no es valido."

    tel = (datos.get("telefono") or "").strip()
    if tel and not re.match(r"^[\d\+\-\(\)\s]{7,25}$", tel):
        return False, "El formato del telefono no es valido."

    estado = datos.get("estado", "Activo")
    if estado not in ("Activo", "Inactivo"):
        return False, "El estado del pasajero debe ser 'Activo' o 'Inactivo'."

    return True, None


def _validar_datos_tarjeta(datos: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Valida los parametros para emision o modificacion de tarjetas OMNY."""
    saldo = float(datos.get("saldo_disponible") or 0.0)
    if saldo < 0:
        return False, "El saldo disponible no puede ser negativo (minimo $0.00)."

    f_emi = datos.get("fecha_emision")
    today = date.today()
    d_emi = today
    if f_emi:
        try:
            d_emi = datetime.strptime(str(f_emi)[:10], "%Y-%m-%d").date()
            if d_emi > today:
                return False, "La fecha de emision no puede ser futura."
        except ValueError:
            return False, "Formato de fecha de emision invalido. Debe ser AAAA-MM-DD."

    f_venc = datos.get("fecha_vencimiento")
    if f_venc:
        try:
            d_venc = datetime.strptime(str(f_venc)[:10], "%Y-%m-%d").date()
            if d_venc < d_emi:
                return False, "La fecha de vencimiento no puede ser anterior a la fecha de emision."
        except ValueError:
            return False, "Formato de fecha de vencimiento invalido. Debe ser AAAA-MM-DD."

    estado = datos.get("estado", "Activa")
    estados_validos = ["Activa", "Bloqueada", "Cancelada", "Reportada Perdida", "Vencida"]
    if estado not in estados_validos:
        return False, f"Estado de tarjeta invalido ('{estado}'). Opciones: {', '.join(estados_validos)}."

    # Validar coherencia de prefijo si se especifica un número de tarjeta explícito
    num_tarjeta = (datos.get("numero_tarjeta") or "").strip().upper()
    tipo_soporte = str(datos.get("tipo_soporte") or "Tarjeta").strip()
    pasajero_id = datos.get("pasajero_id")

    if num_tarjeta:
        if tipo_soporte == "Boleto":
            if not num_tarjeta.startswith("BOL-"):
                return False, "Los boletos de uso único deben comenzar con el prefijo BOL- (p.ej. BOL-2026-0001)."
        elif pasajero_id is None:
            # Tarjeta Al Portador / Anónima
            if num_tarjeta.startswith("OMNY-") and not num_tarjeta.startswith("OMNY-ANON-"):
                return False, (
                    "Las tarjetas al portador no pueden usar el prefijo de tarjetas registradas (OMNY-). "
                    "Debe utilizar el prefijo MC-ANON- (p.ej. MC-ANON-2026-0001) o dejar el campo vacío para autogenerarlo."
                )
            valid_bearer = (
                num_tarjeta.startswith("MC-ANON-") or
                num_tarjeta.startswith("MC-") or
                num_tarjeta.startswith("ANON-") or
                num_tarjeta.startswith("OMNY-ANON-")
            )
            if not valid_bearer:
                return False, "Las tarjetas al portador deben comenzar con el prefijo MC-ANON- (p.ej. MC-ANON-2026-0001)."
        else:
            # Tarjeta Nominada / Registrada a nombre de un pasajero
            if num_tarjeta.startswith("BOL-") or num_tarjeta.startswith("MC-ANON-") or num_tarjeta.startswith("ANON-"):
                return False, "Las tarjetas registradas deben comenzar con el prefijo OMNY- (p.ej. OMNY-2026-0001)."
            if not num_tarjeta.startswith("OMNY-"):
                return False, "Las tarjetas registradas deben comenzar con el prefijo OMNY- (p.ej. OMNY-2026-0001)."

    return True, None


def _validar_recarga(numero_tarjeta: str, monto: float, medio_pago: str) -> Tuple[bool, Optional[str]]:
    """Valida los parametros de recarga antes de la llamada a base de datos."""
    if not (numero_tarjeta or "").strip():
        return False, "Debe especificar el numero de tarjeta a recargar."

    if monto <= 0:
        return False, f"El monto de recarga (${monto:.2f}) debe ser estrictamente positivo (> 0)."

    if monto > 1000:
        return False, f"El monto maximo de recarga permitido por transaccion es $1,000.00 (recibido: ${monto:.2f})."

    medios_validos = ["App Móvil", "Efectivo", "Tarjeta Crédito", "Tarjeta Débito", "Transferencia"]
    if medio_pago not in medios_validos:
        return False, f"Medio de pago no reconocido. Permitidos: {', '.join(medios_validos)}."

    return True, None


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
    valido, err = _validar_datos_pasajero(datos)
    if not valido:
        return {"success": False, "error": err or "Datos de pasajero inválidos."}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT SEQ_PASAJERO.NEXTVAL FROM DUAL")
        new_id = int(cursor.fetchone()[0])

        ident = datos.get("identificador", "").strip().upper()
        if not ident:
            ident = f"PAS-{new_id:03d}"

        tipo_pas = datos.get("tipo_pasajero", "Regular")

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
    valido, err = _validar_datos_pasajero(datos)
    if not valido:
        return {"success": False, "error": err or "Datos de pasajero inválidos."}

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


def verificar_dependencias_pasajero(id_pasajero: int) -> Dict[str, Any]:
    """
    Verifica si el pasajero tiene tarjetas vinculadas y el saldo total de las mismas.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT nombre, estado FROM PASAJERO WHERE id_pasajero = :id", {"id": id_pasajero})
        row_p = cursor.fetchone()
        if not row_p:
            return {"existe": False, "total_tarjetas": 0, "saldo_total": 0.0, "puede_eliminar": False}

        cursor.execute("SELECT COUNT(*), NVL(SUM(saldo_disponible), 0) FROM TARJETA WHERE pasajero_id = :id", {"id": id_pasajero})
        row = cursor.fetchone()
        count_tar = int(row[0] or 0)
        saldo_tot = float(row[1] or 0.0)
        return {
            "existe": True,
            "nombre": str(row_p[0] or ""),
            "estado": str(row_p[1] or ""),
            "total_tarjetas": count_tar,
            "saldo_total": saldo_tot,
            "puede_eliminar": (count_tar == 0)
        }
    finally:
        cursor.close()
        conn.close()


def dar_de_baja_pasajero(id_pasajero: int) -> Dict[str, Any]:
    """Baja logica (soft-delete): Pasa el pasajero a estado 'Inactivo'."""
    return cambiar_estado_pasajero(id_pasajero, "Inactivo")


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
                "error": f"No se puede eliminar físicamente: el pasajero tiene {tarjetas_count} tarjeta(s) vinculada(s). Desvincúlelas primero o desactívelo."
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
               TO_CHAR(t.pase_fecha_inicio, 'YYYY-MM-DD') AS pase_fecha_inicio,
               TO_CHAR(t.pase_fecha_fin, 'YYYY-MM-DD') AS pase_fecha_fin,
               t.saldo_disponible,
               t.tarifa_id,
               tar.codigo AS tarifa_codigo,
               tar.nombre AS tarifa_nombre,
               tar.monto AS tarifa_monto,
               tar.duracion_beneficio_dias,
               CASE 
                   WHEN tar.duracion_beneficio_dias IS NOT NULL AND tar.duracion_beneficio_dias > 0 THEN 1
                   ELSE 0
               END AS es_pase_ilimitado,
               CASE
                   WHEN tar.duracion_beneficio_dias IS NOT NULL AND tar.duracion_beneficio_dias > 0 
                        AND t.pase_fecha_fin IS NOT NULL 
                        AND t.pase_fecha_fin >= TRUNC(SYSDATE)
                        AND (t.pase_fecha_inicio IS NULL OR t.pase_fecha_inicio <= TRUNC(SYSDATE))
                        AND EXISTS (
                            SELECT 1 FROM RECARGA r 
                            WHERE r.tarjeta_id = t.id_tarjeta 
                              AND r.monto >= tar.monto
                        )
                   THEN 1
                   ELSE 0
               END AS pase_vigente,
               CASE
                   WHEN t.pase_fecha_fin IS NOT NULL THEN TRUNC(t.pase_fecha_fin) - TRUNC(SYSDATE)
                   ELSE NULL
               END AS pase_dias_restantes,
               t.estado,
               NVL(t.tipo_soporte, 'Tarjeta') AS tipo_soporte,
               CASE WHEN NVL(t.tipo_soporte, 'Tarjeta') = 'Boleto' THEN 1 ELSE 0 END AS es_boleto,
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
    try:
        return _query_rows(sql, params)
    except Exception as exc:
        err_msg = str(exc)
        if "ORA-00904" in err_msg or "PASE_FECHA" in err_msg or "TIPO_SOPORTE" in err_msg:
            legacy_sql = """
                SELECT t.id_tarjeta, t.numero_tarjeta, t.pasajero_id,
                       NVL(p.nombre, 'Anónima / Al Portador') AS pasajero,
                       NVL(p.identificador, '-') AS identificador_pasajero,
                       NVL(p.tipo_pasajero, 'No Registrado') AS tipo_pasajero,
                       TO_CHAR(t.fecha_emision, 'YYYY-MM-DD') AS fecha_emision,
                       TO_CHAR(t.fecha_vencimiento, 'YYYY-MM-DD') AS fecha_vencimiento,
                       NULL AS pase_fecha_inicio,
                       NULL AS pase_fecha_fin,
                       t.saldo_disponible,
                       t.tarifa_id,
                       tar.codigo AS tarifa_codigo,
                       tar.nombre AS tarifa_nombre,
                       tar.monto AS tarifa_monto,
                       tar.duracion_beneficio_dias,
                       0 AS es_pase_ilimitado,
                       0 AS pase_vigente,
                       NULL AS pase_dias_restantes,
                       t.estado,
                       'Tarjeta' AS tipo_soporte,
                       0 AS es_boleto,
                       CASE 
                           WHEN t.fecha_vencimiento IS NOT NULL AND t.fecha_vencimiento < TRUNC(SYSDATE) THEN 1
                           ELSE 0
                       END AS esta_vencida,
                       TRUNC(NVL(t.fecha_vencimiento, SYSDATE)) - TRUNC(SYSDATE) AS dias_restantes,
                       (SELECT COUNT(*) FROM VIAJE_PASAJERO vp WHERE vp.tarjeta_id = t.id_tarjeta) AS total_viajes,
                       (SELECT COUNT(*) FROM RECARGA r WHERE r.tarjeta_id = t.id_tarjeta) AS total_recargas
                FROM TARJETA t
                LEFT JOIN PASAJERO p ON t.pasajero_id = p.id_pasajero
                LEFT JOIN TARIFA tar ON t.tarifa_id = tar.id_tarifa
                WHERE 1=1
            """
            if estado_filter and estado_filter != "(Todos)":
                legacy_sql += " AND t.estado = :estado_filter"
            if pasajero_id is not None:
                legacy_sql += " AND t.pasajero_id = :p_id"
            if search_text:
                legacy_sql += """ AND (
                    LOWER(t.numero_tarjeta) LIKE :st
                    OR LOWER(NVL(p.nombre, '')) LIKE :st
                    OR LOWER(NVL(tar.nombre, '')) LIKE :st
                )"""
            legacy_sql += " ORDER BY t.id_tarjeta ASC"
            try:
                return _query_rows(legacy_sql, params)
            except Exception:
                return []
        return []


def get_tarjeta_by_id(id_tarjeta: int) -> Optional[Dict[str, Any]]:
    """Retorna la información completa de una tarjeta por ID."""
    sql = """
        SELECT t.id_tarjeta, t.numero_tarjeta, t.pasajero_id,
               NVL(p.nombre, 'Anónima / Al Portador') AS pasajero,
               TO_CHAR(t.fecha_emision, 'YYYY-MM-DD') AS fecha_emision,
               TO_CHAR(t.fecha_vencimiento, 'YYYY-MM-DD') AS fecha_vencimiento,
               TO_CHAR(t.pase_fecha_inicio, 'YYYY-MM-DD') AS pase_fecha_inicio,
               TO_CHAR(t.pase_fecha_fin, 'YYYY-MM-DD') AS pase_fecha_fin,
               t.saldo_disponible, t.tarifa_id, tar.nombre AS tarifa_nombre,
               tar.monto AS tarifa_monto, tar.duracion_beneficio_dias,
               CASE 
                   WHEN tar.duracion_beneficio_dias IS NOT NULL AND tar.duracion_beneficio_dias > 0 THEN 1
                   ELSE 0
               END AS es_pase_ilimitado,
               CASE
                   WHEN tar.duracion_beneficio_dias IS NOT NULL AND tar.duracion_beneficio_dias > 0 
                        AND t.pase_fecha_fin IS NOT NULL 
                        AND t.pase_fecha_fin >= TRUNC(SYSDATE)
                        AND (t.pase_fecha_inicio IS NULL OR t.pase_fecha_inicio <= TRUNC(SYSDATE))
                        AND EXISTS (
                            SELECT 1 FROM RECARGA r 
                            WHERE r.tarjeta_id = t.id_tarjeta 
                              AND r.monto >= tar.monto
                        )
                   THEN 1
                   ELSE 0
               END AS pase_vigente,
               CASE
                   WHEN t.pase_fecha_fin IS NOT NULL THEN TRUNC(t.pase_fecha_fin) - TRUNC(SYSDATE)
                   ELSE NULL
               END AS pase_dias_restantes,
               t.estado,
               NVL(t.tipo_soporte, 'Tarjeta') AS tipo_soporte,
               CASE WHEN NVL(t.tipo_soporte, 'Tarjeta') = 'Boleto' THEN 1 ELSE 0 END AS es_boleto
        FROM TARJETA t
        LEFT JOIN PASAJERO p ON t.pasajero_id = p.id_pasajero
        LEFT JOIN TARIFA tar ON t.tarifa_id = tar.id_tarifa
        WHERE t.id_tarjeta = :id
    """
    rows = _query_rows(sql, {"id": id_tarjeta})
    return rows[0] if rows else None


def get_tarjeta_by_numero(numero_tarjeta: str) -> Optional[Dict[str, Any]]:
    """Retorna la tarjeta a partir de su número OMNY con validaciones de pase."""
    sql = """
        SELECT t.id_tarjeta, t.numero_tarjeta, t.pasajero_id,
               NVL(p.nombre, 'Anónima / Al Portador') AS pasajero,
               t.saldo_disponible, t.tarifa_id, tar.nombre AS tarifa_nombre,
               tar.monto AS tarifa_monto, tar.duracion_beneficio_dias,
               TO_CHAR(t.fecha_vencimiento, 'YYYY-MM-DD') AS fecha_vencimiento,
               TO_CHAR(t.pase_fecha_inicio, 'YYYY-MM-DD') AS pase_fecha_inicio,
               TO_CHAR(t.pase_fecha_fin, 'YYYY-MM-DD') AS pase_fecha_fin,
               CASE 
                   WHEN tar.duracion_beneficio_dias IS NOT NULL AND tar.duracion_beneficio_dias > 0 THEN 1
                   ELSE 0
               END AS es_pase_ilimitado,
               CASE
                   WHEN tar.duracion_beneficio_dias IS NOT NULL AND tar.duracion_beneficio_dias > 0 
                        AND t.pase_fecha_fin IS NOT NULL 
                        AND t.pase_fecha_fin >= TRUNC(SYSDATE)
                        AND (t.pase_fecha_inicio IS NULL OR t.pase_fecha_inicio <= TRUNC(SYSDATE))
                        AND EXISTS (
                            SELECT 1 FROM RECARGA r 
                            WHERE r.tarjeta_id = t.id_tarjeta 
                              AND r.monto >= tar.monto
                        )
                   THEN 1
                   ELSE 0
               END AS pase_vigente,
               CASE
                   WHEN t.pase_fecha_fin IS NOT NULL THEN TRUNC(t.pase_fecha_fin) - TRUNC(SYSDATE)
                   ELSE NULL
               END AS pase_dias_restantes,
               t.estado,
               NVL(t.tipo_soporte, 'Tarjeta') AS tipo_soporte,
               CASE WHEN NVL(t.tipo_soporte, 'Tarjeta') = 'Boleto' THEN 1 ELSE 0 END AS es_boleto
        FROM TARJETA t
        LEFT JOIN PASAJERO p ON t.pasajero_id = p.id_pasajero
        LEFT JOIN TARIFA tar ON t.tarifa_id = tar.id_tarifa
        WHERE t.numero_tarjeta = :num
    """
    try:
        rows = _query_rows(sql, {"num": numero_tarjeta.strip()})
        return rows[0] if rows else None
    except Exception as exc:
        err_msg = str(exc)
        if "ORA-00904" in err_msg or "PASE_FECHA" in err_msg or "TIPO_SOPORTE" in err_msg:
            legacy_sql = """
                SELECT t.id_tarjeta, t.numero_tarjeta, t.pasajero_id,
                       NVL(p.nombre, 'Anónima / Al Portador') AS pasajero,
                       t.saldo_disponible, t.tarifa_id, tar.nombre AS tarifa_nombre,
                       tar.monto AS tarifa_monto, tar.duracion_beneficio_dias,
                       TO_CHAR(t.fecha_vencimiento, 'YYYY-MM-DD') AS fecha_vencimiento,
                       NULL AS pase_fecha_inicio,
                       NULL AS pase_fecha_fin,
                       0 AS es_pase_ilimitado,
                       0 AS pase_vigente,
                       NULL AS pase_dias_restantes,
                       t.estado,
                       'Tarjeta' AS tipo_soporte,
                       0 AS es_boleto
                FROM TARJETA t
                LEFT JOIN PASAJERO p ON t.pasajero_id = p.id_pasajero
                LEFT JOIN TARIFA tar ON t.tarifa_id = tar.id_tarifa
                WHERE t.numero_tarjeta = :num
            """
            try:
                rows = _query_rows(legacy_sql, {"num": numero_tarjeta.strip()})
                return rows[0] if rows else None
            except Exception:
                return None
        return None


def pagar_o_renovar_pase(
    numero_tarjeta: str,
    medio_pago: str = "Tarjeta Débito",
    estacion_canal: str = "Taquilla OMNY"
) -> Dict[str, Any]:
    """
    Registra el pago de un Pase Semanal o Mensual Ilimitado:
    - Obtiene la tarifa asociada y su duración (7 o 30 días).
    - Inserta la transacción de pago en RECARGA por el monto del pase (ej. $132 o $34).
    - Actualiza TARJETA estableciendo pase_fecha_inicio = TRUNC(SYSDATE) y pase_fecha_fin = TRUNC(SYSDATE) + duracion.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT t.id_tarjeta, t.saldo_disponible, tar.id_tarifa, tar.nombre, tar.monto, tar.duracion_beneficio_dias
            FROM TARJETA t
            JOIN TARIFA tar ON t.tarifa_id = tar.id_tarifa
            WHERE t.numero_tarjeta = :num
        """, {"num": numero_tarjeta.strip()})
        row = cursor.fetchone()
        if not row:
            return {"success": False, "error": "Tarjeta no encontrada."}

        tar_id, saldo, _, tarifa_nombre, monto_pase, duracion = row
        if not duracion or int(duracion) <= 0:
            return {"success": False, "error": f"La tarifa actual ({tarifa_nombre}) no es un pase ilimitado periódico."}

        duracion_dias = int(duracion)
        monto_float = float(monto_pase)
        saldo_float = float(saldo or 0.0)

        # Generar número de transacción para RECARGA / PAGO
        cursor.execute("SELECT TO_CHAR(SYSDATE, 'YYYYMMDD') FROM DUAL")
        f_str = cursor.fetchone()[0]
        cursor.execute("SELECT SEQ_RECARGA.NEXTVAL FROM DUAL")
        seq_val = int(cursor.fetchone()[0])
        tx_num = f"PASE-{f_str}-{seq_val:04d}"

        # Insertar registro contable de pago
        cursor.execute("""
            INSERT INTO RECARGA (
                id_recarga, numero_transaccion, tarjeta_id, fecha_hora,
                monto, medio_pago, estacion_canal, saldo_anterior, saldo_posterior
            ) VALUES (
                :id_rec, :tx_num, :t_id, SYSTIMESTAMP,
                :monto, :medio, :canal, :sal_ant, :sal_post
            )
        """, {
            "id_rec": seq_val,
            "tx_num": tx_num,
            "t_id": tar_id,
            "monto": monto_float,
            "medio": medio_pago[:20],
            "canal": f"Pago {tarifa_nombre}"[:50],
            "sal_ant": saldo_float,
            "sal_post": saldo_float
        })

        # Actualizar vigencia del pase en TARJETA
        cursor.execute("""
            UPDATE TARJETA
            SET pase_fecha_inicio = TRUNC(SYSDATE),
                pase_fecha_fin    = TRUNC(SYSDATE) + :dur
            WHERE id_tarjeta = :t_id
        """, {"dur": duracion_dias, "t_id": tar_id})

        conn.commit()

        cursor.execute("""
            SELECT TO_CHAR(pase_fecha_inicio, 'YYYY-MM-DD'), TO_CHAR(pase_fecha_fin, 'YYYY-MM-DD')
            FROM TARJETA WHERE id_tarjeta = :t_id
        """, {"t_id": tar_id})
        f_row = cursor.fetchone()

        return {
            "success": True,
            "mensaje": f"Pago registrado exitosamente. {tarifa_nombre} activado desde {f_row[0]} hasta {f_row[1]}.",
            "fecha_inicio": f_row[0],
            "fecha_fin": f_row[1],
            "monto_pagado": monto_float,
            "transaccion": tx_num
        }
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def emitir_tarjeta(datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Emite una nueva tarjeta OMNY (nominal o anónima) en Oracle.
    Regla 13: Una tarjeta puede pertenecer a un pasajero o ser anónima.
    Regla 15: El saldo inicial no puede ser negativo.
    """
    valido, err = _validar_datos_tarjeta(datos)
    if not valido:
        return {"success": False, "error": err or "Datos de tarjeta inválidos."}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT SEQ_TARJETA.NEXTVAL FROM DUAL")
        new_id = int(cursor.fetchone()[0])

        tipo_soporte = str(datos.get("tipo_soporte") or "Tarjeta").strip()
        if tipo_soporte not in ("Tarjeta", "Boleto"):
            tipo_soporte = "Tarjeta"

        pasajero_id = datos.get("pasajero_id")
        if tipo_soporte == "Boleto":
            pasajero_id = None  # Boletos son siempre al portador / anonimos
        elif pasajero_id:
            pasajero_id = int(pasajero_id)

        num_tarjeta = datos.get("numero_tarjeta", "").strip().upper()
        if not num_tarjeta:
            if tipo_soporte == "Boleto":
                num_tarjeta = f"BOL-2026-{new_id:04d}"
            elif pasajero_id is None:
                # Al Portador / Anónima: asigna el prefijo correspondiente a tarjetas al portador
                num_tarjeta = f"MC-ANON-2026-{new_id:04d}"
            else:
                # Registrada / Nominada: asigna el prefijo de tarjetas registradas OMNY
                num_tarjeta = f"OMNY-2026-{new_id:04d}"

        # Obtener tarifa predeterminada si no se indica
        tarifa_id = datos.get("tarifa_id")
        if not tarifa_id:
            cursor.execute("SELECT id_tarifa FROM TARIFA WHERE codigo = 'TAR-REG' AND ROWNUM = 1")
            row_tar = cursor.fetchone()
            tarifa_id = row_tar[0] if row_tar else 1

        val_saldo = datos.get("saldo_disponible")
        if val_saldo is not None:
            saldo_ini = float(val_saldo)
        else:
            saldo_ini = 2.90 if tipo_soporte == "Boleto" else 0.0

        # Fechas de emisión y vencimiento (5 años para tarjetas, 24 horas para boletos)
        f_emi = datos.get("fecha_emision")
        f_venc = datos.get("fecha_vencimiento")

        sql = """
            INSERT INTO TARJETA (
                id_tarjeta, numero_tarjeta, uid_nfc, pasajero_id,
                fecha_emision, fecha_vencimiento,
                saldo_disponible, tarifa_id, estado, tipo_soporte
            ) VALUES (
                :id_tar, :num_tar, :uid_nfc, :pas_id,
                CASE WHEN :f_emi IS NOT NULL THEN TO_DATE(:f_emi, 'YYYY-MM-DD') ELSE SYSDATE END,
                CASE 
                    WHEN :f_venc IS NOT NULL THEN TO_DATE(:f_venc, 'YYYY-MM-DD')
                    WHEN :tipo_soporte = 'Boleto' THEN TRUNC(SYSDATE) + 1
                    ELSE ADD_MONTHS(SYSDATE, 60)
                END,
                :saldo, :tarifa_id, :estado, :tipo_soporte
            )
        """
        params = {
            "id_tar": new_id,
            "num_tar": num_tarjeta[:20],
            "uid_nfc": num_tarjeta[:50],
            "pas_id": pasajero_id,
            "f_emi": f_emi or None,
            "f_venc": f_venc or None,
            "saldo": saldo_ini,
            "tarifa_id": int(tarifa_id),
            "estado": datos.get("estado", "Activa")[:20],
            "tipo_soporte": tipo_soporte
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
    valido, err = _validar_datos_tarjeta(datos)
    if not valido:
        return {"success": False, "error": err or "Datos de tarjeta inválidos."}

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
    Cambia el estado de una tarjeta ('Activa', 'Bloqueada', 'Cancelada', 'Reportada Perdida', 'Vencida', 'Usado').
    """
    estados_validos = ["Activa", "Bloqueada", "Cancelada", "Reportada Perdida", "Vencida", "Usado"]
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


def verificar_dependencias_tarjeta(id_tarjeta: int) -> Dict[str, Any]:
    """
    Verifica las dependencias operativas de una tarjeta:
    - Viajes registrados en torniquetes (VIAJE_PASAJERO)
    - Recargas efectuadas (RECARGA)
    - Saldo remanente
    - Tipo de soporte (Tarjeta o Boleto)
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT saldo_disponible, estado, numero_tarjeta, NVL(tipo_soporte, 'Tarjeta') FROM TARJETA WHERE id_tarjeta = :id", {"id": id_tarjeta})
        row_tar = cursor.fetchone()
        if not row_tar:
            return {"existe": False, "total_viajes": 0, "total_recargas": 0, "saldo": 0.0, "puede_eliminar": False, "es_boleto": False, "tipo_soporte": "Tarjeta"}

        saldo = float(row_tar[0] or 0.0)
        estado = str(row_tar[1] or "")
        num_tar = str(row_tar[2] or "")
        tipo_soporte = str(row_tar[3] or "Tarjeta")
        es_boleto = (tipo_soporte == "Boleto")

        cursor.execute("SELECT COUNT(*) FROM VIAJE_PASAJERO WHERE tarjeta_id = :id", {"id": id_tarjeta})
        total_viajes = int(cursor.fetchone()[0])

        cursor.execute("SELECT COUNT(*) FROM RECARGA WHERE tarjeta_id = :id", {"id": id_tarjeta})
        total_recargas = int(cursor.fetchone()[0])

        # Para tarjetas convencionales: Regla 25 (cero viajes y cero recargas)
        # Para boletos de uso único: se permite eliminación física completa
        puede_eliminar = es_boleto or (total_viajes == 0 and total_recargas == 0)

        return {
            "existe": True,
            "numero_tarjeta": num_tar,
            "saldo": saldo,
            "estado": estado,
            "tipo_soporte": tipo_soporte,
            "es_boleto": es_boleto,
            "total_viajes": total_viajes,
            "total_recargas": total_recargas,
            "puede_eliminar": puede_eliminar
        }
    finally:
        cursor.close()
        conn.close()


def dar_de_baja_tarjeta(id_tarjeta: int) -> Dict[str, Any]:
    """
    Baja logica (soft-delete): Cambia el estado a 'Cancelada'.
    Preserva intacto el historial en VIAJE_PASAJERO y RECARGA.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT estado, numero_tarjeta FROM TARJETA WHERE id_tarjeta = :id", {"id": id_tarjeta})
        row = cursor.fetchone()
        if not row:
            return {"success": False, "error": "Tarjeta no encontrada."}

        cursor.execute("UPDATE TARJETA SET estado = 'Cancelada' WHERE id_tarjeta = :id", {"id": id_tarjeta})
        conn.commit()
        return {"success": True, "numero_tarjeta": row[1], "estado": "Cancelada"}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def eliminar_tarjeta(id_tarjeta: int) -> Dict[str, Any]:
    """
    Elimina físicamente una tarjeta o boleto.
    - Boletos de uso único (Single-Ride tickets): Se permite eliminación física completa,
      limpiando transacciones de viaje y recarga registradas para el boleto.
    - Tarjetas OMNY convencionales: Elimina si no tiene viajes ni recargas registradas (Regla 25).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT NVL(tipo_soporte, 'Tarjeta'), numero_tarjeta FROM TARJETA WHERE id_tarjeta = :id", {"id": id_tarjeta})
        row_t = cursor.fetchone()
        if not row_t:
            return {"success": False, "error": "Tarjeta o boleto no encontrado."}

        tipo_soporte = str(row_t[0] or "Tarjeta")
        num_tar = str(row_t[1] or "")
        es_boleto = (tipo_soporte == "Boleto")

        if es_boleto:
            cursor.execute("DELETE FROM VIAJE_PASAJERO WHERE tarjeta_id = :id", {"id": id_tarjeta})
            cursor.execute("DELETE FROM RECARGA WHERE tarjeta_id = :id", {"id": id_tarjeta})
            cursor.execute("DELETE FROM TARJETA WHERE id_tarjeta = :id", {"id": id_tarjeta})
            conn.commit()
            return {"success": True, "es_boleto": True, "numero_tarjeta": num_tar}

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
                "error": f"No se puede eliminar físicamente: tiene {rec_count} recarga(s) registrada(s)."
            }

        cursor.execute("DELETE FROM TARJETA WHERE id_tarjeta = :id", {"id": id_tarjeta})
        conn.commit()
        return {"success": True, "es_boleto": False, "numero_tarjeta": num_tar}
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



def emitir_y_validar_boleto_inmediato(estacion_id: int) -> Dict[str, Any]:
    """
    Emite un boleto de uso único (Single-Ride Ticket de $2.90)
    y valida inmediatamente el paso por el torniquete de la estación indicada.
    Al pasar, el boleto queda automáticamente consumido y marcado como 'Usado'.
    """
    res_emit = emitir_tarjeta({
        "tipo_soporte": "Boleto",
        "saldo_disponible": 2.90,
        "estado": "Activa"
    })
    if not res_emit.get("success"):
        return {
            "success": False,
            "resultado": "ERROR",
            "mensaje": res_emit.get("error", "No se pudo emitir el boleto de uso único."),
            "monto_cobrado": 0.0,
            "nuevo_saldo": 0.0
        }

    num_boleto = str(res_emit.get("numero_tarjeta"))
    res_tap = validar_ingreso_torniquete(num_boleto, estacion_id)
    res_tap["numero_tarjeta"] = num_boleto
    res_tap["tipo_soporte"] = "Boleto"
    return res_tap




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
    valido, err = _validar_recarga(numero_tarjeta, monto, medio_pago)
    if not valido:
        return {"success": False, "error": err or "Parámetros de recarga inválidos."}

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
        monto_val = float(datos.get("monto") or 0.0)
        if monto_val < 0:
            return {"success": False, "error": "El monto de la tarifa no puede ser negativo (CHK_TARIFA_MONTO)."}

        params = {
            "id": new_id,
            "cod": cod[:15],
            "nombre": datos["nombre"].strip()[:60],
            "descrip": (datos.get("descripcion") or "").strip()[:200] or None,
            "monto": monto_val,
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
    monto_val = float(datos.get("monto") or 0.0)
    if monto_val < 0:
        return {"success": False, "error": "El monto de la tarifa no puede ser negativo (CHK_TARIFA_MONTO)."}

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
            "monto": monto_val,
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
            "total_tarjetas": _safe_int(r.get("TOTAL_TARJETAS")),
            "tarjetas_activas": _safe_int(r.get("TARJETAS_ACTIVAS")),
            "tarjetas_bloqueadas": _safe_int(r.get("TARJETAS_BLOQUEADAS")),
            "saldo_total_circulacion": _safe_float(r.get("SALDO_TOTAL_CIRCULACION")),
            "total_pasajeros": _safe_int(r.get("TOTAL_PASAJEROS")),
            "viajes_hoy": _safe_int(r.get("VIAJES_HOY")),
            "recaudacion_hoy": _safe_float(r.get("RECAUDACION_HOY")),
        }
    return {
        "total_tarjetas": 0, "tarjetas_activas": 0, "tarjetas_bloqueadas": 0,
        "saldo_total_circulacion": 0.0, "total_pasajeros": 0,
        "viajes_hoy": 0, "recaudacion_hoy": 0.0
    }

