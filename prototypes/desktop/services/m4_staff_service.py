"""
m4_staff_service.py - Servicio especializado para el Módulo 4: Personal y Turnos.
Proporciona lógica de negocio y operaciones transaccionales para:
1. Gestión integral de Empleados (EMPLEADO), cargos, salarios y supervisión jerárquica.
2. Gestión de Certificaciones Técnicas (CERTIFICACION y CERTIFICACION_MODELO), modelos de tren
   habilitados y auditoría de vencimientos de licencias.
3. Programación de Turnos Laborales (TURNO) con detección automática de traslapes y prevención
   de conflictos de horarios para un mismo empleado.
4. Control de Asistencia, registro de Ausencias y sustituciones de personal operativo.
5. Asignación de Conductores a Viajes Programados (VIAJE_PROGRAMADO), impidiendo solapamientos
   simultáneos (Regla de negocio 9) y garantizando licencia técnica vigente (Regla 10).
6. Resumen de KPIs y métricas del personal de la MTA.
"""
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import oracledb

from services.db import get_connection, execute_query
from services.actions_service import parse_oracle_error


def _query_rows(sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Ejecuta una consulta SQL y retorna la lista de diccionarios de filas."""
    res = execute_query(sql, params)
    return res.get("rows", [])


# ==============================================================================
# 1. GESTION DE EMPLEADOS (EMPLEADO)
# ==============================================================================

def get_empleados(
    cargo_filter: Optional[str] = None,
    estado_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retorna el catálogo completo de empleados con supervisor, cargo, salario,
    estado laboral y conteo de certificaciones activas.
    """
    sql = """
        SELECT e.id_empleado, e.numero_empleado, e.nombre_completo,
               e.cargo, e.turno_habitual, e.salario, e.estado_laboral,
               e.telefono, e.correo_electronico, e.direccion,
               TO_CHAR(e.fecha_nacimiento, 'YYYY-MM-DD') AS fecha_nacimiento,
               TO_CHAR(e.fecha_contratacion, 'YYYY-MM-DD') AS fecha_contratacion,
               e.supervisor_id,
               NVL(sup.nombre_completo, 'Jefatura General') AS nombre_supervisor,
               (
                   SELECT COUNT(*) 
                   FROM CERTIFICACION c 
                   WHERE c.empleado_id = e.id_empleado AND c.estado = 'Vigente'
               ) AS total_certificaciones_vigentes,
               (
                   SELECT c.tipo_certificacion
                   FROM CERTIFICACION c
                   WHERE c.empleado_id = e.id_empleado AND c.estado = 'Vigente'
                   FETCH FIRST 1 ROWS ONLY
               ) AS certificacion_principal,
               (
                   SELECT COUNT(*)
                   FROM EMPLEADO sub
                   WHERE sub.supervisor_id = e.id_empleado
               ) AS total_subordinados
        FROM EMPLEADO e
        LEFT JOIN EMPLEADO sup ON e.supervisor_id = sup.id_empleado
        WHERE 1=1
    """
    params: Dict[str, Any] = {}
    if cargo_filter and cargo_filter != "(Todos)":
        sql += " AND e.cargo = :cargo_filter"
        params["cargo_filter"] = cargo_filter

    if estado_filter and estado_filter != "(Todos)":
        sql += " AND e.estado_laboral = :estado_filter"
        params["estado_filter"] = estado_filter

    sql += " ORDER BY e.nombre_completo"
    return _query_rows(sql, params)


def get_empleado_by_id(id_empleado: int) -> Optional[Dict[str, Any]]:
    """Retorna la ficha técnica detallada de un empleado."""
    sql = """
        SELECT e.id_empleado, e.numero_empleado, e.nombre_completo,
               e.cargo, e.turno_habitual, e.salario, e.estado_laboral,
               e.telefono, e.correo_electronico, e.direccion,
               TO_CHAR(e.fecha_nacimiento, 'YYYY-MM-DD') AS fecha_nacimiento,
               TO_CHAR(e.fecha_contratacion, 'YYYY-MM-DD') AS fecha_contratacion,
               e.supervisor_id,
               NVL(sup.nombre_completo, 'Jefatura General') AS nombre_supervisor
        FROM EMPLEADO e
        LEFT JOIN EMPLEADO sup ON e.supervisor_id = sup.id_empleado
        WHERE e.id_empleado = :id_emp
    """
    rows = _query_rows(sql, {"id_emp": id_empleado})
    return rows[0] if rows else None


def get_subordinados(supervisor_id: int) -> List[Dict[str, Any]]:
    """Retorna los empleados bajo la supervisión directa del empleado dado."""
    sql = """
        SELECT id_empleado, numero_empleado, nombre_completo, cargo, estado_laboral
        FROM EMPLEADO
        WHERE supervisor_id = :sup_id
        ORDER BY nombre_completo
    """
    return _query_rows(sql, {"sup_id": supervisor_id})


def get_supervisores_combo() -> List[Dict[str, Any]]:
    """
    Retorna la lista de empleados que pueden fungir como supervisores.
    """
    sql = """
        SELECT id_empleado, numero_empleado, nombre_completo, cargo
        FROM EMPLEADO
        WHERE estado_laboral = 'Activo'
        ORDER BY nombre_completo
    """
    return _query_rows(sql)


def crear_empleado(datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Registra un nuevo empleado en la tabla EMPLEADO usando SEQ_EMPLEADO.NEXTVAL.
    Parámetros requeridos:
      - nombre_completo (str)
      - cargo (str)
    Opcionales:
      - numero_empleado (str)
      - fecha_nacimiento (YYYY-MM-DD)
      - direccion (str)
      - telefono (str)
      - correo_electronico (str)
      - fecha_contratacion (YYYY-MM-DD)
      - turno_habitual (str)
      - salario (float)
      - estado_laboral (str, default 'Activo')
      - supervisor_id (int)
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT SEQ_EMPLEADO.NEXTVAL FROM DUAL")
        seq_row = cursor.fetchone()
        new_id = int(seq_row[0]) if seq_row else 1

        num_emp = datos.get("numero_empleado", "").strip().upper()
        if not num_emp:
            num_emp = f"EMP-{new_id:04d}"

        correo = datos.get("correo_electronico", "").strip().lower()
        if not correo:
            correo = f"empleado.{new_id}@mta.info"

        sql = """
            INSERT INTO EMPLEADO (
                id_empleado, numero_empleado, nombre_completo,
                fecha_nacimiento, direccion, telefono, correo_electronico,
                fecha_contratacion, cargo, turno_habitual, salario,
                estado_laboral, supervisor_id
            ) VALUES (
                :id_emp, :num_emp, :nombre,
                CASE WHEN :f_nac IS NOT NULL THEN TO_DATE(:f_nac, 'YYYY-MM-DD') ELSE NULL END,
                :direccion, :tel, :correo,
                CASE WHEN :f_cont IS NOT NULL THEN TO_DATE(:f_cont, 'YYYY-MM-DD') ELSE SYSDATE END,
                :cargo, :turno, :salario,
                :estado, :sup_id
            )
        """
        params = {
            "id_emp": new_id,
            "num_emp": num_emp,
            "nombre": datos["nombre_completo"].strip(),
            "f_nac": datos.get("fecha_nacimiento") or None,
            "direccion": datos.get("direccion") or None,
            "tel": datos.get("telefono") or None,
            "correo": correo,
            "f_cont": datos.get("fecha_contratacion") or None,
            "cargo": datos.get("cargo", "Conductor"),
            "turno": datos.get("turno_habitual") or None,
            "salario": float(datos.get("salario") or 60000.0),
            "estado": datos.get("estado_laboral", "Activo"),
            "sup_id": datos.get("supervisor_id")
        }
        cursor.execute(sql, params)
        conn.commit()
        return {"success": True, "id_empleado": new_id, "numero_empleado": num_emp}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def modificar_empleado(id_empleado: int, datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Actualiza la información contractual, cargo o supervisor de un empleado.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Evitar que un empleado sea supervisor de sí mismo
        sup_id = datos.get("supervisor_id")
        if sup_id and int(sup_id) == id_empleado:
            return {"success": False, "error": "Un empleado no puede ser su propio supervisor."}

        sql = """
            UPDATE EMPLEADO
            SET numero_empleado = :num_emp,
                nombre_completo = :nombre,
                fecha_nacimiento = CASE WHEN :f_nac IS NOT NULL THEN TO_DATE(:f_nac, 'YYYY-MM-DD') ELSE NULL END,
                direccion = :direccion,
                telefono = :tel,
                correo_electronico = :correo,
                fecha_contratacion = CASE WHEN :f_cont IS NOT NULL THEN TO_DATE(:f_cont, 'YYYY-MM-DD') ELSE fecha_contratacion END,
                cargo = :cargo,
                turno_habitual = :turno,
                salario = :salario,
                supervisor_id = :sup_id
            WHERE id_empleado = :id_emp
        """
        params = {
            "id_emp": id_empleado,
            "num_emp": datos["numero_empleado"].strip().upper(),
            "nombre": datos["nombre_completo"].strip(),
            "f_nac": datos.get("fecha_nacimiento") or None,
            "direccion": datos.get("direccion") or None,
            "tel": datos.get("telefono") or None,
            "correo": datos.get("correo_electronico", "").strip().lower(),
            "f_cont": datos.get("fecha_contratacion") or None,
            "cargo": datos.get("cargo"),
            "turno": datos.get("turno_habitual") or None,
            "salario": float(datos.get("salario") or 0.0),
            "sup_id": sup_id
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


def cambiar_estado_laboral(id_empleado: int, nuevo_estado: str) -> Dict[str, Any]:
    """
    Modifica el estado laboral ('Activo', 'Permiso', 'Vacaciones', 'Suspendido', 'Retirado').
    """
    estados_validos = ["Activo", "Permiso", "Vacaciones", "Suspendido", "Retirado"]
    if nuevo_estado not in estados_validos:
        return {"success": False, "error": f"Estado inválido. Opciones: {', '.join(estados_validos)}"}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE EMPLEADO SET estado_laboral = :est WHERE id_empleado = :id_emp",
            {"est": nuevo_estado, "id_emp": id_empleado}
        )
        conn.commit()
        return {"success": True, "nuevo_estado": nuevo_estado}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def eliminar_empleado(id_empleado: int) -> Dict[str, Any]:
    """
    Elimina un empleado del sistema si no tiene turnos asignados, viajes asignados
    ni empleados a su cargo.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Validar si tiene subordinados
        cursor.execute("SELECT COUNT(*) FROM EMPLEADO WHERE supervisor_id = :id", {"id": id_empleado})
        sub_cnt = cursor.fetchone()[0]
        if sub_cnt > 0:
            return {
                "success": False,
                "error": f"No se puede eliminar: tiene {sub_cnt} empleado(s) bajo su supervisión. Reasigne la supervisión primero."
            }

        # 2. Validar si tiene viajes asignados
        cursor.execute("SELECT COUNT(*) FROM VIAJE_PROGRAMADO WHERE conductor_id = :id", {"id": id_empleado})
        viajes_cnt = cursor.fetchone()[0]
        if viajes_cnt > 0:
            return {
                "success": False,
                "error": f"No se puede eliminar: tiene {viajes_cnt} viaje(s) asignado(s) en el sistema de despacho."
            }

        # 3. Validar si tiene turnos
        cursor.execute("SELECT COUNT(*) FROM TURNO WHERE empleado_id = :id", {"id": id_empleado})
        turnos_cnt = cursor.fetchone()[0]
        if turnos_cnt > 0:
            return {
                "success": False,
                "error": f"No se puede eliminar: tiene {turnos_cnt} turno(s) programado(s) en el historial."
            }

        # 4. Eliminar certificaciones asociadas
        cursor.execute("""
            DELETE FROM CERTIFICACION_MODELO
            WHERE certificacion_id IN (SELECT id_certificacion FROM CERTIFICACION WHERE empleado_id = :id)
        """, {"id": id_empleado})
        cursor.execute("DELETE FROM CERTIFICACION WHERE empleado_id = :id", {"id": id_empleado})

        # 5. Eliminar empleado
        cursor.execute("DELETE FROM EMPLEADO WHERE id_empleado = :id", {"id": id_empleado})

        conn.commit()
        return {"success": True}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 2. GESTION DE CERTIFICACIONES TECNICAS (CERTIFICACION / CERTIFICACION_MODELO)
# ==============================================================================

def get_certificaciones(
    empleado_id: Optional[int] = None,
    estado_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retorna el catálogo de certificaciones y licencias técnicas, detallando los
    modelos de tren habilitados (R142, R160, etc.) y los días restantes para vencimiento.
    """
    sql = """
        SELECT c.id_certificacion, c.empleado_id,
               e.numero_empleado, e.nombre_completo AS nombre_empleado, e.cargo,
               c.tipo_certificacion,
               TO_CHAR(c.fecha_emision, 'YYYY-MM-DD') AS fecha_emision,
               TO_CHAR(c.fecha_vencimiento, 'YYYY-MM-DD') AS fecha_vencimiento,
               c.institucion_emisora,
               c.estado,
               TRUNC(c.fecha_vencimiento) - TRUNC(SYSDATE) AS dias_restantes,
               CASE 
                   WHEN c.fecha_vencimiento IS NOT NULL AND c.fecha_vencimiento < TRUNC(SYSDATE) THEN 1
                   ELSE 0
               END AS esta_vencida,
               (
                   SELECT LISTAGG(m.nombre_modelo, ', ') WITHIN GROUP (ORDER BY m.nombre_modelo)
                   FROM CERTIFICACION_MODELO cm
                   JOIN MODELO_TREN m ON cm.modelo_id = m.id_modelo
                   WHERE cm.certificacion_id = c.id_certificacion
               ) AS modelos_habilitados
        FROM CERTIFICACION c
        JOIN EMPLEADO e ON c.empleado_id = e.id_empleado
        WHERE 1=1
    """
    params: Dict[str, Any] = {}
    if empleado_id is not None:
        sql += " AND c.empleado_id = :emp_id"
        params["emp_id"] = empleado_id

    if estado_filter and estado_filter != "(Todos)":
        sql += " AND c.estado = :estado_filter"
        params["estado_filter"] = estado_filter

    sql += " ORDER BY c.fecha_vencimiento ASC"
    return _query_rows(sql, params)


def crear_certificacion(
    datos: Dict[str, Any],
    modelos_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Registra una certificación técnica o licencia de conducción para un empleado.
    Permite asociarla con uno o varios modelos de tren (CERTIFICACION_MODELO).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT SEQ_CERTIFICACION.NEXTVAL FROM DUAL")
        new_cert_id = int(cursor.fetchone()[0])

        sql = """
            INSERT INTO CERTIFICACION (
                id_certificacion, empleado_id, tipo_certificacion,
                fecha_emision, fecha_vencimiento, institucion_emisora, estado
            ) VALUES (
                :id_cert, :emp_id, :tipo,
                CASE WHEN :f_emi IS NOT NULL THEN TO_DATE(:f_emi, 'YYYY-MM-DD') ELSE SYSDATE END,
                CASE WHEN :f_venc IS NOT NULL THEN TO_DATE(:f_venc, 'YYYY-MM-DD') ELSE NULL END,
                :inst, :estado
            )
        """
        params = {
            "id_cert": new_cert_id,
            "emp_id": int(datos["empleado_id"]),
            "tipo": datos["tipo_certificacion"].strip(),
            "f_emi": datos.get("fecha_emision") or None,
            "f_venc": datos.get("fecha_vencimiento") or None,
            "inst": datos.get("institucion_emisora", "MTA Training Academy"),
            "estado": datos.get("estado", "Vigente")
        }
        cursor.execute(sql, params)

        # Asociar modelos de tren en CERTIFICACION_MODELO
        if modelos_ids:
            for mod_id in modelos_ids:
                cursor.execute("""
                    INSERT INTO CERTIFICACION_MODELO (id_certificacion_modelo, certificacion_id, modelo_id)
                    VALUES (SEQ_CERTIFICACION_MODELO.NEXTVAL, :c_id, :m_id)
                """, {"c_id": new_cert_id, "m_id": mod_id})

        conn.commit()
        return {"success": True, "id_certificacion": new_cert_id}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def modificar_certificacion(
    id_certificacion: int,
    datos: Dict[str, Any],
    modelos_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Actualiza datos de una certificación y renueva la asociación de modelos de tren.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE CERTIFICACION
            SET tipo_certificacion = :tipo,
                fecha_emision = CASE WHEN :f_emi IS NOT NULL THEN TO_DATE(:f_emi, 'YYYY-MM-DD') ELSE fecha_emision END,
                fecha_vencimiento = CASE WHEN :f_venc IS NOT NULL THEN TO_DATE(:f_venc, 'YYYY-MM-DD') ELSE fecha_vencimiento END,
                institucion_emisora = :inst,
                estado = :estado
            WHERE id_certificacion = :id_cert
        """
        params = {
            "id_cert": id_certificacion,
            "tipo": datos["tipo_certificacion"].strip(),
            "f_emi": datos.get("fecha_emision") or None,
            "f_venc": datos.get("fecha_vencimiento") or None,
            "inst": datos.get("institucion_emisora", "MTA Training Academy"),
            "estado": datos.get("estado", "Vigente")
        }
        cursor.execute(sql, params)

        # Actualizar modelos si se proporcionan
        if modelos_ids is not None:
            cursor.execute("DELETE FROM CERTIFICACION_MODELO WHERE certificacion_id = :id_cert", {"id_cert": id_certificacion})
            for mod_id in modelos_ids:
                cursor.execute("""
                    INSERT INTO CERTIFICACION_MODELO (id_certificacion_modelo, certificacion_id, modelo_id)
                    VALUES (SEQ_CERTIFICACION_MODELO.NEXTVAL, :c_id, :m_id)
                """, {"c_id": id_certificacion, "m_id": mod_id})

        conn.commit()
        return {"success": True}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def cambiar_estado_certificacion(id_certificacion: int, nuevo_estado: str) -> Dict[str, Any]:
    """
    Cambia el estado de una certificación ('Vigente', 'Vencida', 'Revocada').
    """
    estados_validos = ["Vigente", "Vencida", "Revocada"]
    if nuevo_estado not in estados_validos:
        return {"success": False, "error": f"Estado inválido. Opciones: {', '.join(estados_validos)}"}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE CERTIFICACION SET estado = :est WHERE id_certificacion = :id_cert",
            {"est": nuevo_estado, "id_cert": id_certificacion}
        )
        conn.commit()
        return {"success": True, "nuevo_estado": nuevo_estado}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def eliminar_certificacion(id_certificacion: int) -> Dict[str, Any]:
    """Elimina una certificación y sus modelos vinculados."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM CERTIFICACION_MODELO WHERE certificacion_id = :id", {"id": id_certificacion})
        cursor.execute("DELETE FROM CERTIFICACION WHERE id_certificacion = :id", {"id": id_certificacion})
        conn.commit()
        return {"success": True}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def controlar_vencimientos_certificaciones() -> Dict[str, Any]:
    """
    Audita todas las certificaciones en Oracle. Marca automáticamente como 'Vencida'
    cualquier certificación cuya fecha de vencimiento sea anterior al día actual.
    Retorna la cantidad de licencias actualizadas.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE CERTIFICACION
            SET estado = 'Vencida'
            WHERE fecha_vencimiento < TRUNC(SYSDATE)
              AND estado = 'Vigente'
        """
        cursor.execute(sql)
        modificados = cursor.rowcount
        conn.commit()
        return {"success": True, "actualizadas": modificados}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 3. PROGRAMACION DE TURNOS LABORALES (TURNO) Y DETECCION DE TRASLAPES
# ==============================================================================

def get_turnos(
    fecha: Optional[str] = None,
    empleado_id: Optional[int] = None,
    tipo_lugar: Optional[str] = None,
    estado_asistencia: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retorna la programación de turnos laborales con datos del empleado,
    intervalo horario y estado de asistencia.
    """
    sql = """
        SELECT t.id_turno, t.codigo_turno, t.empleado_id,
               e.numero_empleado, e.nombre_completo AS nombre_empleado, e.cargo,
               TO_CHAR(t.fecha, 'YYYY-MM-DD') AS fecha,
               TO_CHAR(t.hora_inicio, 'HH24:MI') AS hora_inicio,
               TO_CHAR(t.hora_fin, 'HH24:MI') AS hora_fin,
               TO_CHAR(t.hora_inicio, 'YYYY-MM-DD HH24:MI') AS inicio_completo,
               TO_CHAR(t.hora_fin, 'YYYY-MM-DD HH24:MI') AS fin_completo,
               t.tipo_lugar, t.lugar_id, t.funcion, t.estado_asistencia
        FROM TURNO t
        JOIN EMPLEADO e ON t.empleado_id = e.id_empleado
        WHERE 1=1
    """
    params: Dict[str, Any] = {}
    if fecha:
        sql += " AND t.fecha = TO_DATE(:fecha, 'YYYY-MM-DD')"
        params["fecha"] = fecha

    if empleado_id is not None:
        sql += " AND t.empleado_id = :emp_id"
        params["emp_id"] = empleado_id

    if tipo_lugar and tipo_lugar != "(Todos)":
        sql += " AND t.tipo_lugar = :tipo_lugar"
        params["tipo_lugar"] = tipo_lugar

    if estado_asistencia and estado_asistencia != "(Todos)":
        sql += " AND t.estado_asistencia = :estado_asistencia"
        params["estado_asistencia"] = estado_asistencia

    sql += " ORDER BY t.fecha DESC, t.hora_inicio ASC"
    return _query_rows(sql, params)


def validar_traslape_turno(
    empleado_id: int,
    fecha: str,
    hora_inicio: str,
    hora_fin: str,
    excluir_id_turno: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Verifica si existe solapamiento horario para el mismo empleado en la misma fecha.
    Retorna el turno conflictivo si hay traslape, o None si está libre de conflicto.
    """
    sql = """
        SELECT t.codigo_turno,
               TO_CHAR(t.hora_inicio, 'HH24:MI') AS ini,
               TO_CHAR(t.hora_fin, 'HH24:MI') AS fin,
               t.funcion
        FROM TURNO t
        WHERE t.empleado_id = :emp_id
          AND t.fecha = TO_DATE(:fecha, 'YYYY-MM-DD')
          AND t.id_turno != NVL(:excluir_id, -1)
          AND t.estado_asistencia NOT IN ('Sustituido', 'Permiso', 'Vacaciones')
          AND (
              t.hora_inicio < TO_TIMESTAMP(:fecha || ' ' || :hora_fin || ':00', 'YYYY-MM-DD HH24:MI:SS')
              AND t.hora_fin > TO_TIMESTAMP(:fecha || ' ' || :hora_ini || ':00', 'YYYY-MM-DD HH24:MI:SS')
          )
    """
    params = {
        "emp_id": empleado_id,
        "fecha": fecha,
        "excluir_id": excluir_id_turno,
        "hora_ini": hora_inicio,
        "hora_fin": hora_fin
    }
    rows = _query_rows(sql, params)
    return rows[0] if rows else None


def crear_turno(datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Programa un nuevo turno laboral para un empleado, validando estrictamente
    que no exista traslape con otro turno asignado en la misma fecha y horario.
    """
    emp_id = int(datos["empleado_id"])
    fecha = datos["fecha"].strip()
    h_ini = datos["hora_inicio"].strip()
    h_fin = datos["hora_fin"].strip()

    # 1. Detección inmediata de traslape
    conflicto = validar_traslape_turno(emp_id, fecha, h_ini, h_fin)
    if conflicto:
        return {
            "success": False,
            "error": f"Conflicto de traslape: El empleado ya tiene programado el turno {conflicto['CODIGO_TURNO']} ({conflicto['INI']} - {conflicto['FIN']}) en esa misma franja horaria."
        }

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT SEQ_TURNO.NEXTVAL FROM DUAL")
        seq_val = int(cursor.fetchone()[0])

        cod_turno = datos.get("codigo_turno", "").strip().upper()
        if not cod_turno:
            cod_turno = f"TUR-{seq_val:06d}"
        else:
            cod_turno = cod_turno[:15]

        sql = """
            INSERT INTO TURNO (
                id_turno, codigo_turno, empleado_id, fecha,
                hora_inicio, hora_fin, tipo_lugar, lugar_id,
                funcion, estado_asistencia
            ) VALUES (
                :id_turno, :codigo, :emp_id, TO_DATE(:fecha, 'YYYY-MM-DD'),
                TO_TIMESTAMP(:fecha || ' ' || :h_ini || ':00', 'YYYY-MM-DD HH24:MI:SS'),
                TO_TIMESTAMP(:fecha || ' ' || :h_fin || ':00', 'YYYY-MM-DD HH24:MI:SS'),
                :tipo_lugar, :lugar_id, :funcion, :estado_asistencia
            )
        """
        params = {
            "id_turno": seq_val,
            "codigo": cod_turno,
            "emp_id": emp_id,
            "fecha": fecha,
            "h_ini": h_ini,
            "h_fin": h_fin,
            "tipo_lugar": (datos.get("tipo_lugar") or "Estación")[:20],
            "lugar_id": datos.get("lugar_id"),
            "funcion": (datos.get("funcion") or "Servicio Operativo")[:50],
            "estado_asistencia": (datos.get("estado_asistencia") or "Programado")[:20]
        }
        cursor.execute(sql, params)
        conn.commit()
        return {"success": True, "id_turno": seq_val, "codigo_turno": cod_turno}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def modificar_turno(id_turno: int, datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Actualiza la programación de un turno verificando que no genere solapamientos.
    """
    emp_id = int(datos["empleado_id"])
    fecha = datos["fecha"].strip()
    h_ini = datos["hora_inicio"].strip()
    h_fin = datos["hora_fin"].strip()

    conflicto = validar_traslape_turno(emp_id, fecha, h_ini, h_fin, excluir_id_turno=id_turno)
    if conflicto:
        return {
            "success": False,
            "error": f"Conflicto de traslape: El empleado ya tiene asignado el turno {conflicto['CODIGO_TURNO']} ({conflicto['INI']} - {conflicto['FIN']}) en ese horario."
        }

    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE TURNO
            SET empleado_id = :emp_id,
                fecha = TO_DATE(:fecha, 'YYYY-MM-DD'),
                hora_inicio = TO_TIMESTAMP(:fecha || ' ' || :h_ini || ':00', 'YYYY-MM-DD HH24:MI:SS'),
                hora_fin = TO_TIMESTAMP(:fecha || ' ' || :h_fin || ':00', 'YYYY-MM-DD HH24:MI:SS'),
                tipo_lugar = :tipo_lugar,
                lugar_id = :lugar_id,
                funcion = :funcion,
                estado_asistencia = :estado_asistencia
            WHERE id_turno = :id_turno
        """
        params = {
            "id_turno": id_turno,
            "emp_id": emp_id,
            "fecha": fecha,
            "h_ini": h_ini,
            "h_fin": h_fin,
            "tipo_lugar": (datos.get("tipo_lugar") or "Estación")[:20],
            "lugar_id": datos.get("lugar_id"),
            "funcion": (datos.get("funcion") or "Servicio Operativo")[:50],
            "estado_asistencia": (datos.get("estado_asistencia") or "Programado")[:20]
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


def eliminar_turno(id_turno: int) -> Dict[str, Any]:
    """Elimina un turno programado."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM TURNO WHERE id_turno = :id", {"id": id_turno})
        conn.commit()
        return {"success": True}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def detectar_traslapes_turnos() -> List[Dict[str, Any]]:
    """
    Audita toda la tabla de turnos en Oracle y retorna pares de turnos solapados
    para un mismo empleado (auditoría analítica de calidad).
    """
    sql = """
        SELECT t1.id_turno AS id_turno_1, t1.codigo_turno AS codigo_1,
               t2.id_turno AS id_turno_2, t2.codigo_turno AS codigo_2,
               e.numero_empleado, e.nombre_completo,
               TO_CHAR(t1.fecha, 'YYYY-MM-DD') AS fecha,
               TO_CHAR(t1.hora_inicio, 'HH24:MI') || ' - ' || TO_CHAR(t1.hora_fin, 'HH24:MI') AS horario_1,
               TO_CHAR(t2.hora_inicio, 'HH24:MI') || ' - ' || TO_CHAR(t2.hora_fin, 'HH24:MI') AS horario_2
        FROM TURNO t1
        JOIN TURNO t2 ON t1.empleado_id = t2.empleado_id
                     AND t1.fecha = t2.fecha
                     AND t1.id_turno < t2.id_turno
        JOIN EMPLEADO e ON t1.empleado_id = e.id_empleado
        WHERE t1.estado_asistencia NOT IN ('Sustituido', 'Permiso', 'Vacaciones')
          AND t2.estado_asistencia NOT IN ('Sustituido', 'Permiso', 'Vacaciones')
          AND (t1.hora_inicio < t2.hora_fin AND t1.hora_fin > t2.hora_inicio)
        ORDER BY t1.fecha DESC, e.nombre_completo
    """
    return _query_rows(sql)


# ==============================================================================
# 4. CONTROL DE ASISTENCIA, AUSENCIAS Y SUSTITUCIONES
# ==============================================================================

def registrar_asistencia(id_turno: int, nuevo_estado: str) -> Dict[str, Any]:
    """
    Registra el estado de asistencia de un turno ('Presente', 'Ausente',
    'Permiso', 'Vacaciones', 'Programado', 'Sustituido').
    """
    estados_validos = ["Presente", "Ausente", "Permiso", "Vacaciones", "Programado", "Sustituido"]
    if nuevo_estado not in estados_validos:
        return {"success": False, "error": f"Estado de asistencia inválido. Opciones: {', '.join(estados_validos)}"}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE TURNO SET estado_asistencia = :est WHERE id_turno = :id",
            {"est": nuevo_estado, "id": id_turno}
        )
        conn.commit()
        return {"success": True, "nuevo_estado": nuevo_estado}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def registrar_sustitucion(id_turno: int, sustituto_id: int) -> Dict[str, Any]:
    """
    Registra la ausencia de un empleado en un turno y asigna formalmente a un
    empleado sustituto.
    Efectos:
    1. Marca el turno original como 'Sustituido'.
    2. Valida que el empleado sustituto esté 'Activo'.
    3. Valida que el empleado sustituto no tenga traslapes en esa franja horaria.
    4. Crea un nuevo turno para el sustituto conservando la fecha, horario y lugar.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Obtener datos del turno original
        cursor.execute("""
            SELECT t.fecha, 
                   TO_CHAR(t.fecha, 'YYYY-MM-DD') AS f_str,
                   TO_CHAR(t.hora_inicio, 'HH24:MI') AS h_ini,
                   TO_CHAR(t.hora_fin, 'HH24:MI') AS h_fin,
                   t.tipo_lugar, t.lugar_id, t.funcion,
                   e.nombre_completo AS nombre_titular
            FROM TURNO t
            JOIN EMPLEADO e ON t.empleado_id = e.id_empleado
            WHERE t.id_turno = :id
        """, {"id": id_turno})
        row = cursor.fetchone()
        if not row:
            return {"success": False, "error": "El turno especificado no existe."}

        f_str, h_ini, h_fin = row[1], row[2], row[3]
        tipo_lugar, lugar_id, funcion = row[4], row[5], row[6]
        nom_titular = row[7]

        # 2. Validar que el sustituto esté activo
        cursor.execute("SELECT nombre_completo, estado_laboral FROM EMPLEADO WHERE id_empleado = :id", {"id": sustituto_id})
        sust_row = cursor.fetchone()
        if not sust_row:
            return {"success": False, "error": "El empleado sustituto no existe."}
        if sust_row[1] != "Activo":
            return {
                "success": False,
                "error": f"El sustituto {sust_row[0]} no está activo (Estado actual: '{sust_row[1]}')."
            }

        # 3. Validar que el sustituto no tenga traslapes
        conflicto = validar_traslape_turno(sustituto_id, f_str, h_ini, h_fin)
        if conflicto:
            return {
                "success": False,
                "error": f"El sustituto {sust_row[0]} ya tiene asignado el turno {conflicto['CODIGO_TURNO']} ({conflicto['INI']} - {conflicto['FIN']}) en ese horario."
            }

        # 4. Actualizar turno original a 'Sustituido'
        cursor.execute("UPDATE TURNO SET estado_asistencia = 'Sustituido' WHERE id_turno = :id", {"id": id_turno})

        # 5. Crear nuevo turno para el sustituto
        cursor.execute("SELECT SEQ_TURNO.NEXTVAL FROM DUAL")
        new_turno_id = int(cursor.fetchone()[0])
        cod_sust = f"TUR-S{new_turno_id:06d}"[:15]
        func_sust = f"{funcion} (Suplencia)"[:50]

        sql_new = """
            INSERT INTO TURNO (
                id_turno, codigo_turno, empleado_id, fecha,
                hora_inicio, hora_fin, tipo_lugar, lugar_id,
                funcion, estado_asistencia
            ) VALUES (
                :id, :cod, :emp_id, TO_DATE(:fecha, 'YYYY-MM-DD'),
                TO_TIMESTAMP(:fecha || ' ' || :h_ini || ':00', 'YYYY-MM-DD HH24:MI:SS'),
                TO_TIMESTAMP(:fecha || ' ' || :h_fin || ':00', 'YYYY-MM-DD HH24:MI:SS'),
                :tipo_lugar, :lugar_id, :func, 'Programado'
            )
        """
        cursor.execute(sql_new, {
            "id": new_turno_id,
            "cod": cod_sust,
            "emp_id": sustituto_id,
            "fecha": f_str,
            "h_ini": h_ini,
            "h_fin": h_fin,
            "tipo_lugar": (tipo_lugar or "Estación")[:20],
            "lugar_id": lugar_id,
            "func": func_sust
        })

        conn.commit()
        return {
            "success": True,
            "id_turno_nuevo": new_turno_id,
            "codigo_nuevo": cod_sust,
            "mensaje": f"Sustitución registrada: {sust_row[0]} reemplaza a {nom_titular} en el turno {cod_sust}."
        }
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 5. ASIGNACION DE CONDUCTORES A VIAJES PROGRAMADOS (REGLAS 9 Y 10)
# ==============================================================================

def get_viajes_personal(
    fecha: Optional[str] = None,
    conductor_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Retorna los viajes programados de la red, indicando el maquinista asignado
    y el estado de su certificación técnica.
    """
    sql = """
        SELECT vp.id_viaje, vp.numero_viaje,
               vp.ruta_id, r.codigo AS codigo_ruta,
               l.codigo AS codigo_linea, l.color AS color_linea,
               TO_CHAR(vp.fecha, 'YYYY-MM-DD') AS fecha,
               TO_CHAR(vp.hora_prog_salida, 'YYYY-MM-DD HH24:MI:SS') AS salida_prog,
               TO_CHAR(vp.hora_prog_llegada, 'YYYY-MM-DD HH24:MI:SS') AS llegada_prog,
               TO_CHAR(vp.hora_prog_salida, 'HH24:MI') AS hora_salida_corta,
               TO_CHAR(vp.hora_prog_llegada, 'HH24:MI') AS hora_llegada_corta,
               vp.tren_id, t.codigo_interno AS codigo_tren,
               m.nombre_modelo,
               vp.conductor_id, e.nombre_completo AS conductor,
               e.numero_empleado AS nomina_conductor,
               vp.estado AS estado_viaje,
               CASE
                   WHEN vp.conductor_id IS NULL THEN 'Sin Asignar'
                   WHEN EXISTS (
                       SELECT 1 FROM CERTIFICACION c
                       WHERE c.empleado_id = vp.conductor_id
                         AND c.estado = 'Vigente'
                         AND c.fecha_vencimiento >= vp.fecha
                   ) THEN 'Certificado Vigente'
                   ELSE 'Licencia No Vigente'
               END AS estado_licencia_conductor
        FROM VIAJE_PROGRAMADO vp
        JOIN RUTA r ON vp.ruta_id = r.id_ruta
        JOIN LINEA l ON r.linea_id = l.id_linea
        LEFT JOIN TREN t ON vp.tren_id = t.id_tren
        LEFT JOIN MODELO_TREN m ON t.modelo_id = m.id_modelo
        LEFT JOIN EMPLEADO e ON vp.conductor_id = e.id_empleado
        WHERE 1=1
    """
    params: Dict[str, Any] = {}
    if fecha:
        sql += " AND vp.fecha = TO_DATE(:fecha, 'YYYY-MM-DD')"
        params["fecha"] = fecha

    if conductor_id is not None:
        sql += " AND vp.conductor_id = :cond_id"
        params["cond_id"] = conductor_id

    sql += " ORDER BY vp.fecha DESC, vp.hora_prog_salida DESC"
    return _query_rows(sql, params)


def get_conductores_disponibles(
    fecha: str,
    hora_salida: str,
    hora_llegada: str,
    modelo_tren_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Retorna la lista de conductores aptos para operar un viaje:
    - Cargo = 'Conductor' y Estado Laboral = 'Activo'.
    - Regla 10: Posee certificación técnica vigente a la fecha del viaje.
    - Regla 9: No tiene ningún otro viaje simultáneo solapado en esa misma franja.
    """
    sql = """
        SELECT e.id_empleado, e.numero_empleado, e.nombre_completo,
               c.tipo_certificacion,
               TO_CHAR(c.fecha_vencimiento, 'YYYY-MM-DD') AS vence_licencia
        FROM EMPLEADO e
        JOIN CERTIFICACION c ON e.id_empleado = c.empleado_id
        WHERE e.cargo = 'Conductor'
          AND e.estado_laboral = 'Activo'
          AND c.estado = 'Vigente'
          AND c.fecha_vencimiento >= TO_DATE(:fecha, 'YYYY-MM-DD')
          AND NOT EXISTS (
              SELECT 1 FROM VIAJE_PROGRAMADO vp
              WHERE vp.conductor_id = e.id_empleado
                AND vp.fecha = TO_DATE(:fecha, 'YYYY-MM-DD')
                AND vp.estado NOT IN ('Cancelado', 'Completado')
                AND (
                    vp.hora_prog_salida < TO_TIMESTAMP(:fecha || ' ' || :h_lleg || ':00', 'YYYY-MM-DD HH24:MI:SS')
                    AND vp.hora_prog_llegada > TO_TIMESTAMP(:fecha || ' ' || :h_sal || ':00', 'YYYY-MM-DD HH24:MI:SS')
                )
          )
    """
    params = {
        "fecha": fecha,
        "h_sal": hora_salida,
        "h_lleg": hora_llegada
    }
    sql += " ORDER BY e.nombre_completo"
    return _query_rows(sql, params)


def asignar_conductor_viaje(id_viaje: int, id_conductor: int) -> Dict[str, Any]:
    """
    Asigna un conductor a un viaje programado, garantizando:
    - Regla de Negocio 10: El conductor debe tener certificación técnica vigente.
      (Validado también por el trigger TRG_CERTIFICACION_ALERTA_VENCIDA).
    - Regla de Negocio 9: Un conductor no puede atender dos viajes simultáneos.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Obtener datos del viaje
        cursor.execute("""
            SELECT id_viaje, numero_viaje, fecha,
                   hora_prog_salida, hora_prog_llegada, estado
            FROM VIAJE_PROGRAMADO
            WHERE id_viaje = :id
        """, {"id": id_viaje})
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
                "error": f"No se puede asignar conductor: el viaje {num_viaje} está '{estado_viaje}'."
            }

        # 2. Validar conductor y estado laboral
        cursor.execute("""
            SELECT nombre_completo, cargo, estado_laboral
            FROM EMPLEADO
            WHERE id_empleado = :id
        """, {"id": id_conductor})
        cond_row = cursor.fetchone()
        if not cond_row:
            return {"success": False, "error": "El conductor seleccionado no existe."}

        nom_cond, cargo_cond, est_laboral = cond_row[0], cond_row[1], cond_row[2]

        if est_laboral != "Activo":
            return {
                "success": False,
                "error": f"El conductor {nom_cond} no está activo (Estado: '{est_laboral}')."
            }

        # 3. Validar Regla 10: Certificación vigente para la fecha
        cursor.execute("""
            SELECT COUNT(*)
            FROM CERTIFICACION
            WHERE empleado_id = :id
              AND estado = 'Vigente'
              AND fecha_vencimiento >= :f
        """, {"id": id_conductor, "f": fecha_viaje})
        cert_val = cursor.fetchone()[0]
        if cert_val == 0:
            return {
                "success": False,
                "error": f"Operación rechazada (Regla 10): El conductor {nom_cond} no posee una certificación técnica vigente para la fecha del viaje."
            }

        # 4. Validar Regla 9: Solapamiento con otro viaje simultáneo
        sql_solap = """
            SELECT vp.numero_viaje,
                   TO_CHAR(vp.hora_prog_salida, 'HH24:MI') AS sal,
                   TO_CHAR(vp.hora_prog_llegada, 'HH24:MI') AS lleg
            FROM VIAJE_PROGRAMADO vp
            WHERE vp.conductor_id = :cond_id
              AND vp.fecha = :f
              AND vp.id_viaje != :v_id
              AND vp.estado NOT IN ('Cancelado', 'Completado')
              AND (
                  vp.hora_prog_salida < :lleg_viaje AND vp.hora_prog_llegada > :sal_viaje
              )
        """
        cursor.execute(sql_solap, {
            "cond_id": id_conductor,
            "f": fecha_viaje,
            "v_id": id_viaje,
            "lleg_viaje": llegada_viaje,
            "sal_viaje": salida_viaje
        })
        conflicto = cursor.fetchone()
        if conflicto:
            return {
                "success": False,
                "error": f"Conflicto de despacho (Regla 9): El conductor {nom_cond} ya tiene asignado el viaje {conflicto[0]} ({conflicto[1]} - {conflicto[2]}) en ese horario."
            }

        # 5. Actualizar asignación
        cursor.execute("""
            UPDATE VIAJE_PROGRAMADO
            SET conductor_id = :cond_id
            WHERE id_viaje = :v_id
        """, {"cond_id": id_conductor, "v_id": id_viaje})

        conn.commit()
        return {
            "success": True,
            "mensaje": f"Conductor {nom_cond} asignado exitosamente al viaje {num_viaje}."
        }
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


def desasignar_conductor_viaje(id_viaje: int) -> Dict[str, Any]:
    """Desvincula al conductor asignado si el viaje está en estado 'Programado'."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT numero_viaje, estado, conductor_id FROM VIAJE_PROGRAMADO WHERE id_viaje = :id
        """, {"id": id_viaje})
        row = cursor.fetchone()
        if not row:
            return {"success": False, "error": "El viaje no existe."}

        num_viaje, estado_viaje, cond_id = row[0], row[1], row[2]
        if not cond_id:
            return {"success": False, "error": "El viaje no tiene ningún conductor asignado."}

        if estado_viaje != "Programado":
            return {
                "success": False,
                "error": f"No se puede desasignar conductor: el viaje {num_viaje} se encuentra en estado '{estado_viaje}'."
            }

        cursor.execute("UPDATE VIAJE_PROGRAMADO SET conductor_id = NULL WHERE id_viaje = :id", {"id": id_viaje})
        conn.commit()
        return {"success": True, "mensaje": f"Conductor desasignado del viaje {num_viaje}."}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(exc)}
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 6. KPIS Y METRICAS DE PERSONAL
# ==============================================================================

def get_kpis_personal() -> Dict[str, int]:
    """
    Retorna métricas ejecutivas del personal de la MTA:
    - Total de empleados
    - Empleados activos
    - Total de conductores
    - Certificaciones vigentes vs vencidas
    - Turnos programados para hoy
    """
    sql = """
        SELECT
            (SELECT COUNT(*) FROM EMPLEADO) AS total_empleados,
            (SELECT COUNT(*) FROM EMPLEADO WHERE estado_laboral = 'Activo') AS empleados_activos,
            (SELECT COUNT(*) FROM EMPLEADO WHERE cargo = 'Conductor') AS total_conductores,
            (SELECT COUNT(*) FROM CERTIFICACION WHERE estado = 'Vigente' AND fecha_vencimiento >= TRUNC(SYSDATE)) AS cert_vigentes,
            (SELECT COUNT(*) FROM CERTIFICACION WHERE estado = 'Vencida' OR fecha_vencimiento < TRUNC(SYSDATE)) AS cert_vencidas,
            (SELECT COUNT(*) FROM TURNO WHERE fecha = TRUNC(SYSDATE)) AS turnos_hoy
        FROM DUAL
    """
    rows = _query_rows(sql)
    if rows:
        r = rows[0]
        return {
            "total_empleados": int(r.get("TOTAL_EMPLEADOS") or 0),
            "empleados_activos": int(r.get("EMPLEADOS_ACTIVOS") or 0),
            "total_conductores": int(r.get("TOTAL_CONDUCTORES") or 0),
            "cert_vigentes": int(r.get("CERT_VIGENTES") or 0),
            "cert_vencidas": int(r.get("CERT_VENCIDAS") or 0),
            "turnos_hoy": int(r.get("TURNOS_HOY") or 0),
        }
    return {
        "total_empleados": 0, "empleados_activos": 0, "total_conductores": 0,
        "cert_vigentes": 0, "cert_vencidas": 0, "turnos_hoy": 0
    }
