"""
Servicio de Acciones Transaccionales del Dominio Metro NY (MTA NYCT).
Capa de enlace entre la aplicación PyQt5 / QFluentWidgets y los
Procedimientos Almacenados (SPs), Funciones y Vistas de Oracle Database.
"""
import re
from datetime import datetime, date
from typing import Dict, List, Tuple, Any, Optional
import oracledb

from services.db import get_connection, execute_query


def parse_oracle_error(exc: Exception) -> str:
    """
    Limpia y extrae un mensaje legible en español de una excepción de Oracle.
    Extrae la causa raíz ignorando las trazas técnicas de ORA-06512.
    """
    err_str = str(exc)

    # 1. Reglas de negocio personalizadas de la aplicación (ORA-20001 a ORA-20015)
    match_app = re.search(r"ORA-(20\d{3}):\s*([^\n\r]+)", err_str)
    if match_app:
        return match_app.group(2).strip()

    # 2. Violaciones de Check Constraint (ORA-02290)
    if "ORA-02290" in err_str:
        return "Los valores ingresados no cumplen con las restricciones de dominio del sistema."

    # 3. Violaciones de Integridad Referencial / Clave Foránea (ORA-02291 / ORA-02292)
    if "ORA-02291" in err_str:
        return "El registro referenciado no existe en la base de datos."
    if "ORA-02292" in err_str:
        return "No se puede modificar o eliminar el registro porque tiene datos asociados."

    # 4. Longitud de campo excedida (ORA-12899)
    if "ORA-12899" in err_str:
        return "Uno de los campos de texto excede la longitud máxima permitida."

    # 5. Registro duplicado en clave primaria o única (ORA-00001)
    if "ORA-00001" in err_str:
        return "Ya existe un registro con el mismo identificador o código en el sistema."

    # 6. Fallback limpio: primera línea del error
    first_line = err_str.split("\n")[0]
    return first_line.strip()


# ======================================================================
# PROCEDIMIENTOS ALMACENADOS (SP_*)
# ======================================================================

def recargar_tarjeta(
    numero_tarjeta: str,
    monto: float,
    medio_pago: str = "Efectivo",
    estacion_canal: str = "Torniquete Estación"
) -> Dict[str, Any]:
    """
    Ejecuta SP_RECARGAR_TARJETA para abonar saldo a una tarjeta OMNY / MetroCard.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        v_saldo = cursor.var(oracledb.NUMBER)
        v_tx = cursor.var(str)

        cursor.callproc(
            "SP_RECARGAR_TARJETA",
            [numero_tarjeta, float(monto), medio_pago, estacion_canal, v_saldo, v_tx]
        )
        conn.commit()

        nuevo_saldo = float(v_saldo.getvalue() or 0)
        num_tx = str(v_tx.getvalue() or "")

        return {
            "success": True,
            "nuevo_saldo": nuevo_saldo,
            "num_transaccion": num_tx,
            "mensaje": f"Recarga exitosa de ${monto:.2f}. Saldo actual: ${nuevo_saldo:.2f} (Tx: {num_tx})"
        }
    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "nuevo_saldo": 0.0,
            "num_transaccion": "",
            "error": parse_oracle_error(e)
        }
    finally:
        cursor.close()
        conn.close()


def registrar_ingreso(
    numero_tarjeta: str,
    estacion_id: int,
    viaje_programado_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Ejecuta SP_REGISTRAR_INGRESO simulando la validación de torniquete OMNY.
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
            [numero_tarjeta, int(estacion_id), viaje_programado_id, v_resultado, v_mensaje, v_cobrado, v_saldo]
        )
        conn.commit()

        res = str(v_resultado.getvalue() or "ERROR")
        msg = str(v_mensaje.getvalue() or "")
        cobrado = float(v_cobrado.getvalue() or 0)
        nuevo_saldo = float(v_saldo.getvalue() or 0)

        return {
            "success": (res == "AUTORIZADO"),
            "resultado": res,
            "mensaje": msg,
            "monto_cobrado": cobrado,
            "nuevo_saldo": nuevo_saldo
        }
    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "resultado": "ERROR",
            "mensaje": parse_oracle_error(e),
            "monto_cobrado": 0.0,
            "nuevo_saldo": 0.0
        }
    finally:
        cursor.close()
        conn.close()


def programar_viaje(
    ruta_id: int,
    fecha: Any,
    hora_prog_salida: Any,
    hora_prog_llegada: Any,
    tren_id: int,
    conductor_id: int,
    horario_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Ejecuta SP_PROGRAMAR_VIAJE con validación técnica de compatibilidad, unidad y maquinista.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Normalizar fecha
        if isinstance(fecha, str):
            d_fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
        else:
            d_fecha = fecha

        # Normalizar horas
        if isinstance(hora_prog_salida, str):
            if len(hora_prog_salida) <= 5:
                t_salida = datetime.strptime(f"{d_fecha} {hora_prog_salida}", "%Y-%m-%d %H:%M")
            else:
                t_salida = datetime.strptime(hora_prog_salida, "%Y-%m-%d %H:%M")
        else:
            t_salida = hora_prog_salida

        if isinstance(hora_prog_llegada, str):
            if len(hora_prog_llegada) <= 5:
                t_llegada = datetime.strptime(f"{d_fecha} {hora_prog_llegada}", "%Y-%m-%d %H:%M")
            else:
                t_llegada = datetime.strptime(hora_prog_llegada, "%Y-%m-%d %H:%M")
        else:
            t_llegada = hora_prog_llegada

        v_numero_viaje = cursor.var(str)
        v_id_viaje = cursor.var(oracledb.NUMBER)

        cursor.callproc(
            "SP_PROGRAMAR_VIAJE",
            [
                int(ruta_id), d_fecha, t_salida, t_llegada,
                int(tren_id), int(conductor_id), horario_id,
                v_numero_viaje, v_id_viaje
            ]
        )
        conn.commit()

        num_viaje = str(v_numero_viaje.getvalue() or "")
        id_viaje = int(v_id_viaje.getvalue() or 0)

        return {
            "success": True,
            "numero_viaje": num_viaje,
            "id_viaje": id_viaje,
            "mensaje": f"Viaje {num_viaje} programado exitosamente."
        }
    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "numero_viaje": "",
            "id_viaje": 0,
            "error": parse_oracle_error(e)
        }
    finally:
        cursor.close()
        conn.close()


def crear_orden_mantenimiento(
    equipo_id: int,
    tipo_mantenimiento: str,
    descripcion: str,
    prioridad: str = "Media",
    tecnico_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Ejecuta SP_CREAR_ORDEN_MANTENIMIENTO y actualiza el estado de trenes en taller.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        v_numero_orden = cursor.var(str)
        v_id_orden = cursor.var(oracledb.NUMBER)

        cursor.callproc(
            "SP_CREAR_ORDEN_MANTENIMIENTO",
            [
                int(equipo_id), tipo_mantenimiento, descripcion,
                prioridad, tecnico_id, v_numero_orden, v_id_orden
            ]
        )
        conn.commit()

        num_orden = str(v_numero_orden.getvalue() or "")
        id_orden = int(v_id_orden.getvalue() or 0)

        return {
            "success": True,
            "numero_orden": num_orden,
            "id_orden": id_orden,
            "mensaje": f"Orden de mantenimiento {num_orden} creada correctamente."
        }
    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "numero_orden": "",
            "id_orden": 0,
            "error": parse_oracle_error(e)
        }
    finally:
        cursor.close()
        conn.close()


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
    Ejecuta SP_REGISTRAR_INCIDENTE y asocia el elemento de red afectado.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        v_numero_incidente = cursor.var(str)
        v_id_incidente = cursor.var(oracledb.NUMBER)

        cursor.callproc(
            "SP_REGISTRAR_INCIDENTE",
            [
                tipo, descripcion, nivel_severidad, int(reportado_por_id),
                tipo_elemento, elemento_id, v_numero_incidente, v_id_incidente
            ]
        )
        conn.commit()

        num_incidente = str(v_numero_incidente.getvalue() or "")
        id_incidente = int(v_id_incidente.getvalue() or 0)

        return {
            "success": True,
            "numero_incidente": num_incidente,
            "id_incidente": id_incidente,
            "mensaje": f"Incidente {num_incidente} registrado exitosamente."
        }
    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "numero_incidente": "",
            "id_incidente": 0,
            "error": parse_oracle_error(e)
        }
    finally:
        cursor.close()
        conn.close()


def cancelar_viajes_afectados(incidente_id: int) -> Dict[str, Any]:
    """
    Ejecuta SP_CANCELAR_VIAJES_AFECTADOS para cancelar viajes vinculados al incidente.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        v_viajes_cancelados = cursor.var(oracledb.NUMBER)

        cursor.callproc(
            "SP_CANCELAR_VIAJES_AFECTADOS",
            [int(incidente_id), v_viajes_cancelados]
        )
        conn.commit()

        total = int(v_viajes_cancelados.getvalue() or 0)
        return {
            "success": True,
            "viajes_cancelados": total,
            "mensaje": f"Se cancelaron {total} viajes programados afectados por el incidente."
        }
    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "viajes_cancelados": 0,
            "error": parse_oracle_error(e)
        }
    finally:
        cursor.close()
        conn.close()


# ======================================================================
# FUNCIONES PL/SQL (FN_*)
# ======================================================================

def consultar_saldo_tarjeta(numero_tarjeta: str) -> float:
    """Invoca FN_SALDO_TARJETA."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        res = cursor.callfunc("FN_SALDO_TARJETA", oracledb.NUMBER, [numero_tarjeta])
        return float(res if res is not None else -1)
    finally:
        cursor.close()
        conn.close()


def verificar_tarjeta_valida(numero_tarjeta: str) -> bool:
    """Invoca FN_TARJETA_VALIDA."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        res = cursor.callfunc("FN_TARJETA_VALIDA", oracledb.NUMBER, [numero_tarjeta])
        return bool(res == 1)
    finally:
        cursor.close()
        conn.close()


def verificar_tren_disponible(tren_id: int) -> bool:
    """Invoca FN_TREN_DISPONIBLE."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        res = cursor.callfunc("FN_TREN_DISPONIBLE", oracledb.NUMBER, [int(tren_id)])
        return bool(res == 1)
    finally:
        cursor.close()
        conn.close()


def verificar_ruta_operativa(ruta_id: int) -> bool:
    """Invoca FN_RUTA_OPERATIVA."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        res = cursor.callfunc("FN_RUTA_OPERATIVA", oracledb.NUMBER, [int(ruta_id)])
        return bool(res == 1)
    finally:
        cursor.close()
        conn.close()


def calcular_costo_mantenimiento(orden_id: int) -> float:
    """Invoca FN_COSTO_ORDEN_MANTENIMIENTO."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        res = cursor.callfunc("FN_COSTO_ORDEN_MANTENIMIENTO", oracledb.NUMBER, [int(orden_id)])
        return float(res if res is not None else 0)
    finally:
        cursor.close()
        conn.close()


def calcular_duracion_viaje(viaje_id: int) -> int:
    """Invoca FN_DURACION_VIAJE."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        res = cursor.callfunc("FN_DURACION_VIAJE", oracledb.NUMBER, [int(viaje_id)])
        return int(res if res is not None else 0)
    finally:
        cursor.close()
        conn.close()


def calcular_minutos_retraso(viaje_id: int) -> int:
    """Invoca FN_MINUTOS_RETRASO."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        res = cursor.callfunc("FN_MINUTOS_RETRASO", oracledb.NUMBER, [int(viaje_id)])
        return int(res if res is not None else 0)
    finally:
        cursor.close()
        conn.close()


# ======================================================================
# CONSULTAS Y HELPERS DE APOYO PARA LA UI (MODULO TARJETAS Y ACCIONES)
# ======================================================================

def get_tarjetas_resumen(filtro_estado: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lista completa de tarjetas con pasajero titular, tarifa asociada,
    saldo y vigencia para el catálogo del Módulo 5.
    """
    sql = """
        SELECT t.id_tarjeta,
               t.numero_tarjeta,
               NVL(p.nombre, 'Tarjeta Anónima') AS pasajero,
               NVL(p.tipo_pasajero, 'General') AS tipo_pasajero,
               tar.nombre AS tarifa_nombre,
               tar.monto AS tarifa_monto,
               t.saldo_disponible,
               TO_CHAR(t.fecha_vencimiento, 'YYYY-MM-DD') AS fecha_vencimiento,
               t.estado
        FROM TARJETA t
        LEFT JOIN PASAJERO p ON t.pasajero_id = p.id_pasajero
        JOIN TARIFA tar ON t.tarifa_id = tar.id_tarifa
    """
    params = {}
    if filtro_estado and filtro_estado != "(Todos)":
        sql += " WHERE t.estado = :estado"
        params["estado"] = filtro_estado

    sql += " ORDER BY t.numero_tarjeta"
    return execute_query(sql, params)["rows"]


def get_tarjeta_detalle(numero_tarjeta: str) -> Optional[Dict[str, Any]]:
    """
    Información detallada de una tarjeta específica.
    """
    sql = """
        SELECT t.id_tarjeta,
               t.numero_tarjeta,
               NVL(p.nombre, 'Tarjeta Anónima') AS pasajero,
               NVL(p.identificador, '-') AS identificador_pasajero,
               NVL(p.tipo_pasajero, 'General') AS tipo_pasajero,
               NVL(p.correo_electronico, '-') AS correo,
               tar.nombre AS tarifa_nombre,
               tar.monto AS tarifa_monto,
               t.saldo_disponible,
               TO_CHAR(t.fecha_emision, 'YYYY-MM-DD') AS fecha_emision,
               TO_CHAR(t.fecha_vencimiento, 'YYYY-MM-DD') AS fecha_vencimiento,
               t.estado
        FROM TARJETA t
        LEFT JOIN PASAJERO p ON t.pasajero_id = p.id_pasajero
        JOIN TARIFA tar ON t.tarifa_id = tar.id_tarifa
        WHERE t.numero_tarjeta = :num
    """
    rows = execute_query(sql, {"num": numero_tarjeta})["rows"]
    return rows[0] if rows else None


def get_historial_viajes_tarjeta(numero_tarjeta: str, limit: int = 15) -> List[Dict[str, Any]]:
    """
    Historial de validaciones y pasos por torniquete de una tarjeta.
    """
    sql = f"""
        SELECT vp.numero_transaccion,
               e.nombre AS estacion_ingreso,
               e.distrito,
               TO_CHAR(vp.fecha_hora_ingreso, 'YYYY-MM-DD HH24:MI:SS') AS fecha_hora,
               vp.monto_cobrado,
               vp.estado_transaccion
        FROM VIAJE_PASAJERO vp
        JOIN TARJETA t ON vp.tarjeta_id = t.id_tarjeta
        JOIN ESTACION e ON vp.estacion_ingreso_id = e.id_estacion
        WHERE t.numero_tarjeta = :num
        ORDER BY vp.fecha_hora_ingreso DESC
        FETCH FIRST {int(limit)} ROWS ONLY
    """
    return execute_query(sql, {"num": numero_tarjeta})["rows"]


def get_historial_recargas_tarjeta(numero_tarjeta: str, limit: int = 15) -> List[Dict[str, Any]]:
    """
    Historial de abonos y recargas de una tarjeta.
    """
    sql = f"""
        SELECT r.numero_transaccion,
               r.monto,
               r.medio_pago,
               r.estacion_canal,
               r.saldo_anterior,
               r.saldo_posterior,
               TO_CHAR(r.fecha_hora, 'YYYY-MM-DD HH24:MI:SS') AS fecha_hora
        FROM RECARGA r
        JOIN TARJETA t ON r.tarjeta_id = t.id_tarjeta
        WHERE t.numero_tarjeta = :num
        ORDER BY r.fecha_hora DESC
        FETCH FIRST {int(limit)} ROWS ONLY
    """
    return execute_query(sql, {"num": numero_tarjeta})["rows"]


def get_tarjetas_combo() -> List[Tuple[str, str]]:
    """
    Opciones de tarjetas para ComboBoxes interactivos.
    """
    res = execute_query("""
        SELECT t.numero_tarjeta, 
               NVL(p.nombre, 'Anónima') AS titular,
               t.saldo_disponible,
               t.estado
        FROM TARJETA t
        LEFT JOIN PASAJERO p ON t.pasajero_id = p.id_pasajero
        ORDER BY t.numero_tarjeta
    """)
    options = []
    for r in res["rows"]:
        saldo_val = float(r["SALDO_DISPONIBLE"]) if r["SALDO_DISPONIBLE"] != "-" else 0.0
        label = f"{r['NUMERO_TARJETA']} - {r['TITULAR']} (${saldo_val:.2f}) [{r['ESTADO']}]"
        options.append((r["NUMERO_TARJETA"], label))
    return options


def get_estaciones_combo() -> List[Tuple[int, str]]:
    """
    Opciones de estaciones para ComboBoxes.
    """
    res = execute_query("""
        SELECT id_estacion, codigo, nombre, distrito 
        FROM ESTACION 
        WHERE estado_operativo = 'Operativa'
        ORDER BY distrito, nombre
    """)
    return [(int(r["ID_ESTACION"]), f"{r['NOMBRE']} ({r['CODIGO']}) - {r['DISTRITO']}") for r in res["rows"]]


def get_rutas_combo() -> List[Tuple[int, str]]:
    """
    Opciones de rutas activas para programar viajes.
    """
    res = execute_query("""
        SELECT r.id_ruta, r.codigo, r.sentido, l.codigo AS linea
        FROM RUTA r
        JOIN LINEA l ON r.linea_id = l.id_linea
        WHERE r.estado = 'Activa'
        ORDER BY l.codigo, r.codigo
    """)
    return [(int(r["ID_RUTA"]), f"Ruta {r['CODIGO']} (Línea {r['LINEA']} - {r['SENTIDO']})") for r in res["rows"]]


def get_trenes_combo() -> List[Tuple[int, str]]:
    """
    Opciones de trenes para programación operativa.
    """
    res = execute_query("""
        SELECT t.id_tren, t.codigo_interno, m.nombre_modelo, t.estado_operativo
        FROM TREN t
        JOIN MODELO_TREN m ON t.modelo_id = m.id_modelo
        ORDER BY t.codigo_interno
    """)
    return [(int(r["ID_TREN"]), f"{r['CODIGO_INTERNO']} ({r['NOMBRE_MODELO']}) - {r['ESTADO_OPERATIVO']}") for r in res["rows"]]


def get_conductores_combo() -> List[Tuple[int, str]]:
    """
    Opciones de conductores con certificación técnica.
    """
    res = execute_query("""
        SELECT e.id_empleado, e.numero_empleado, e.nombre_completo, NVL(c.tipo_certificacion, 'Sin Certificar') AS cert
        FROM EMPLEADO e
        LEFT JOIN CERTIFICACION c ON e.id_empleado = c.empleado_id AND c.estado = 'Vigente'
        WHERE e.cargo IN ('Conductor de Metro', 'Maquinista', 'Operador de Tren')
           OR e.id_empleado IN (SELECT empleado_id FROM CERTIFICACION WHERE estado = 'Vigente')
        ORDER BY e.nombre_completo
    """)
    return [(int(r["ID_EMPLEADO"]), f"{r['NOMBRE_COMPLETO']} ({r['NUMERO_EMPLEADO']}) - {r['CERT']}") for r in res["rows"]]


def get_tecnicos_combo() -> List[Tuple[int, str]]:
    """
    Opciones de técnicos para órdenes de mantenimiento.
    """
    res = execute_query("""
        SELECT e.id_empleado, e.numero_empleado, e.nombre_completo, e.cargo
        FROM EMPLEADO e
        WHERE e.cargo LIKE '%Técnico%' OR e.cargo LIKE '%Mecánico%' OR e.cargo LIKE '%Mantenimiento%' OR e.cargo LIKE '%Inspector%'
        ORDER BY e.nombre_completo
    """)
    return [(int(r["ID_EMPLEADO"]), f"{r['NOMBRE_COMPLETO']} ({r['CARGO']})") for r in res["rows"]]


def get_equipos_combo() -> List[Tuple[int, str]]:
    """
    Opciones de equipos de infraestructura para mantenimiento.
    """
    res = execute_query("""
        SELECT id_equipo, codigo_equipo, tipo_equipo, modelo, estado
        FROM EQUIPO
        ORDER BY tipo_equipo, codigo_equipo
    """)
    return [(int(r["ID_EQUIPO"]), f"{r['CODIGO_EQUIPO']} [{r['TIPO_EQUIPO']}] {r['MODELO']} - {r['ESTADO']}") for r in res["rows"]]


def get_lineas_combo() -> List[Tuple[int, str]]:
    """
    Opciones de líneas de metro para incidentes o asignaciones.
    """
    res = execute_query("""
        SELECT id_linea, codigo, nombre 
        FROM LINEA 
        ORDER BY codigo
    """)
    return [(int(r["ID_LINEA"]), f"Línea {r['CODIGO']} - {r['NOMBRE']}") for r in res["rows"]]


def get_empleados_combo() -> List[Tuple[int, str]]:
    """
    Opciones de empleados del sistema (reportantes, supervisores, técnicos).
    """
    res = execute_query("""
        SELECT id_empleado, numero_empleado, nombre_completo, cargo 
        FROM EMPLEADO 
        ORDER BY nombre_completo
    """)
    return [(int(r["ID_EMPLEADO"]), f"{r['NOMBRE_COMPLETO']} ({r['NUMERO_EMPLEADO']}) - {r['CARGO']}") for r in res["rows"]]


def get_incidentes_abiertos_combo() -> List[Tuple[int, str]]:
    """
    Opciones de incidentes no resueltos para cancelación de viajes o seguimiento.
    """
    res = execute_query("""
        SELECT id_incidente, numero_incidente, tipo, nivel_severidad 
        FROM INCIDENTE 
        WHERE estado != 'Cerrado' 
        ORDER BY id_incidente DESC
    """)
    return [(int(r["ID_INCIDENTE"]), f"{r['NUMERO_INCIDENTE']} ({r['TIPO']}) [{r['NIVEL_SEVERIDAD']}]") for r in res["rows"]]


