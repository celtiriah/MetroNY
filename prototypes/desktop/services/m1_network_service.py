"""
Servicio de Dominio para el Módulo 1: Administración de la Red y Estaciones.
Soporta operaciones CRUD, administración de plataformas, transferencias,
y gestión de la topología secuencial de estaciones y líneas del metro de NY.
"""
from typing import Optional

from services.db import execute_query, execute_dml
from services.actions_service import parse_oracle_error


# ==============================================================================
# GESTIÓN DE ESTACIONES
# ==============================================================================

def get_estaciones_completas(filtro_texto: Optional[str] = None, distrito: Optional[str] = None, estado: Optional[str] = None, solo_ada: bool = False) -> list:
    """
    Retorna la lista detallada de estaciones con conteo de plataformas y líneas que la conectan.
    """
    sql = """
        SELECT e.id_estacion, e.codigo, e.nombre, e.direccion, e.distrito,
               e.latitud, e.longitud, e.fecha_inauguracion,
               e.cantidad_accesos, e.cantidad_plataformas, e.estado_operativo,
               e.horario_funcionamiento, e.elevadores_disponibles,
               e.escaleras_electricas_disponibles, e.accesible_discapacidad,
               e.tipo_estacion,
               (SELECT COUNT(*) FROM LINEA_ESTACION le WHERE le.estacion_id = e.id_estacion) as total_lineas
        FROM ESTACION e
        WHERE 1=1
    """
    params = {}
    if distrito and distrito != "(Todos)":
        sql += " AND e.distrito = :distrito"
        params["distrito"] = distrito
    if estado and estado != "(Todos)":
        sql += " AND e.estado_operativo = :estado"
        params["estado"] = estado
    if solo_ada:
        sql += " AND e.accesible_discapacidad = 'S'"
    if filtro_texto:
        sql += " AND (LOWER(e.nombre) LIKE :txt OR LOWER(e.codigo) LIKE :txt OR LOWER(e.direccion) LIKE :txt)"
        params["txt"] = f"%{filtro_texto.strip().lower()}%"

    sql += " ORDER BY e.nombre ASC"
    return execute_query(sql, params)["rows"]


def get_estacion_detalle(id_estacion: int) -> dict:
    """Retorna los datos maestros de una estación específica."""
    sql = "SELECT * FROM ESTACION WHERE id_estacion = :id"
    rows = execute_query(sql, {"id": id_estacion})["rows"]
    return rows[0] if rows else {}


def crear_estacion(datos: dict) -> dict:
    """
    Crea una nueva estación en la red de metro de Nueva York.
    """
    sql = """
        INSERT INTO ESTACION (
            id_estacion, codigo, nombre, direccion, distrito,
            latitud, longitud, fecha_inauguracion, cantidad_accesos,
            cantidad_plataformas, estado_operativo, horario_funcionamiento,
            elevadores_disponibles, escaleras_electricas_disponibles,
            accesible_discapacidad, tipo_estacion
        ) VALUES (
            SEQ_ESTACION.NEXTVAL, :codigo, :nombre, :direccion, :distrito,
            :latitud, :longitud, SYSDATE, :cantidad_accesos,
            :cantidad_plataformas, :estado_operativo, :horario_funcionamiento,
            :elevadores_disponibles, :escaleras_electricas_disponibles,
            :accesible_discapacidad, :tipo_estacion
        )
    """
    try:
        execute_dml(sql, {
            "codigo": datos["codigo"].strip().upper(),
            "nombre": datos["nombre"].strip(),
            "direccion": datos.get("direccion", "Desconocida").strip(),
            "distrito": datos.get("distrito", "Manhattan"),
            "latitud": float(datos.get("latitud", 40.7128)),
            "longitud": float(datos.get("longitud", -74.0060)),
            "cantidad_accesos": int(datos.get("cantidad_accesos", 2)),
            "cantidad_plataformas": int(datos.get("cantidad_plataformas", 2)),
            "estado_operativo": datos.get("estado_operativo", "Operativa"),
            "horario_funcionamiento": datos.get("horario_funcionamiento", "24/7"),
            "elevadores_disponibles": "S" if datos.get("elevadores") else "N",
            "escaleras_electricas_disponibles": "S" if datos.get("escaleras") else "N",
            "accesible_discapacidad": "S" if datos.get("ada") else "N",
            "tipo_estacion": datos.get("tipo_estacion", "Local")
        })
        return {"success": True, "mensaje": f"Estación {datos['nombre']} registrada exitosamente."}
    except Exception as e:
        return {"success": False, "error": parse_oracle_error(e)}


def modificar_estacion(id_estacion: int, datos: dict) -> dict:
    """
    Actualiza los atributos de una estación existente.
    """
    sql = """
        UPDATE ESTACION SET
            nombre = :nombre,
            direccion = :direccion,
            distrito = :distrito,
            latitud = :latitud,
            longitud = :longitud,
            cantidad_accesos = :cantidad_accesos,
            cantidad_plataformas = :cantidad_plataformas,
            estado_operativo = :estado_operativo,
            horario_funcionamiento = :horario_funcionamiento,
            elevadores_disponibles = :elevadores_disponibles,
            escaleras_electricas_disponibles = :escaleras_electricas_disponibles,
            accesible_discapacidad = :accesible_discapacidad,
            tipo_estacion = :tipo_estacion
        WHERE id_estacion = :id
    """
    try:
        execute_dml(sql, {
            "id": id_estacion,
            "nombre": datos["nombre"].strip(),
            "direccion": datos.get("direccion", "Desconocida").strip(),
            "distrito": datos.get("distrito", "Manhattan"),
            "latitud": float(datos.get("latitud", 40.7128)),
            "longitud": float(datos.get("longitud", -74.0060)),
            "cantidad_accesos": int(datos.get("cantidad_accesos", 2)),
            "cantidad_plataformas": int(datos.get("cantidad_plataformas", 2)),
            "estado_operativo": datos.get("estado_operativo", "Operativa"),
            "horario_funcionamiento": datos.get("horario_funcionamiento", "24/7"),
            "elevadores_disponibles": "S" if datos.get("elevadores") else "N",
            "escaleras_electricas_disponibles": "S" if datos.get("escaleras") else "N",
            "accesible_discapacidad": "S" if datos.get("ada") else "N",
            "tipo_estacion": datos.get("tipo_estacion", "Local")
        })
        return {"success": True, "mensaje": f"Estación actualizada correctamente."}
    except Exception as e:
        return {"success": False, "error": parse_oracle_error(e)}


def cambiar_estado_estacion(id_estacion: int, nuevo_estado: str) -> dict:
    """Cambia el estado operativo de una estación ('Operativa', 'Cerrada', 'Cerrada Temporalmente')."""
    sql = "UPDATE ESTACION SET estado_operativo = :estado WHERE id_estacion = :id"
    try:
        execute_dml(sql, {"estado": nuevo_estado, "id": id_estacion})
        return {"success": True, "mensaje": f"Estado de la estación cambiado a '{nuevo_estado}'."}
    except Exception as e:
        return {"success": False, "error": parse_oracle_error(e)}


# ==============================================================================
# GESTIÓN DE PLATAFORMAS (ANDENES)
# ==============================================================================

def get_plataformas_estacion(id_estacion: int) -> list:
    """Retorna las plataformas y andenes de una estación específica."""
    sql = """
        SELECT id_plataforma, identificador, direccion_viaje, capacidad_aproximada, estado_operativo
        FROM PLATAFORMA
        WHERE estacion_id = :id
        ORDER BY identificador ASC
    """
    return execute_query(sql, {"id": id_estacion})["rows"]


def agregar_plataforma(id_estacion: int, identificador: str, direccion_viaje: str, capacidad: int, estado: str) -> dict:
    """Crea una nueva plataforma en la estación y actualiza el contador."""
    sql = """
        INSERT INTO PLATAFORMA (
            id_plataforma, estacion_id, identificador, direccion_viaje,
            capacidad_aproximada, estado_operativo
        ) VALUES (
            SEQ_PLATAFORMA.NEXTVAL, :est_id, :identificador, :direccion, :capacidad, :estado
        )
    """
    try:
        execute_dml(sql, {
            "est_id": id_estacion,
            "identificador": identificador.strip().upper(),
            "direccion": direccion_viaje.strip(),
            "capacidad": int(capacidad),
            "estado": estado
        })
        # Actualizar cantidad en la tabla maestra
        execute_dml("UPDATE ESTACION SET cantidad_plataformas = (SELECT COUNT(*) FROM PLATAFORMA WHERE estacion_id = :id) WHERE id_estacion = :id", {"id": id_estacion})
        return {"success": True, "mensaje": f"Plataforma '{identificador}' agregada con éxito."}
    except Exception as e:
        return {"success": False, "error": parse_oracle_error(e)}


def modificar_plataforma(id_plataforma: int, identificador: str, direccion_viaje: str, capacidad: int, estado: str) -> dict:
    """Modifica los atributos de una plataforma existente."""
    sql = """
        UPDATE PLATAFORMA SET
            identificador = :identificador,
            direccion_viaje = :direccion,
            capacidad_aproximada = :capacidad,
            estado_operativo = :estado
        WHERE id_plataforma = :id
    """
    try:
        execute_dml(sql, {
            "id": id_plataforma,
            "identificador": identificador.strip().upper(),
            "direccion": direccion_viaje.strip(),
            "capacidad": int(capacidad),
            "estado": estado
        })
        return {"success": True, "mensaje": "Plataforma actualizada exitosamente."}
    except Exception as e:
        return {"success": False, "error": parse_oracle_error(e)}


def eliminar_plataforma(id_plataforma: int, id_estacion: int) -> dict:
    """Elimina una plataforma de la estación."""
    try:
        execute_dml("DELETE FROM PLATAFORMA WHERE id_plataforma = :id", {"id": id_plataforma})
        execute_dml("UPDATE ESTACION SET cantidad_plataformas = (SELECT COUNT(*) FROM PLATAFORMA WHERE estacion_id = :id) WHERE id_estacion = :id", {"id": id_estacion})
        return {"success": True, "mensaje": "Plataforma eliminada correctamente."}
    except Exception as e:
        return {"success": False, "error": parse_oracle_error(e)}


# ==============================================================================
# LÍNEAS POR ESTACIÓN Y TRANSFERENCIAS (REQUERIMIENTOS 7 Y 8)
# ==============================================================================

def get_lineas_por_estacion(id_estacion: int) -> list:
    """
    Requerimiento 8: Consultar todas las líneas que pasan por una estación.
    """
    sql = """
        SELECT l.id_linea, l.codigo as codigo_linea, l.nombre as nombre_linea,
               l.color, l.estado_operativo as estado_linea,
               le.orden, le.distancia_km, le.tiempo_estimado_min,
               l.tipo_servicio_principal
        FROM LINEA_ESTACION le
        JOIN LINEA l ON le.linea_id = l.id_linea
        WHERE le.estacion_id = :id
        ORDER BY l.codigo ASC
    """
    return execute_query(sql, {"id": id_estacion})["rows"]


def get_transferencias_estacion(id_estacion: int) -> list:
    """
    Requerimiento 7: Consultar conexiones de transferencia definidas en una estación.
    """
    sql = """
        SELECT t.id_transferencia,
               l1.id_linea as linea_orig_id, l1.codigo as codigo_orig, l1.nombre as nombre_orig, l1.color as color_orig,
               l2.id_linea as linea_dest_id, l2.codigo as codigo_dest, l2.nombre as nombre_dest, l2.color as color_dest,
               t.tiempo_estimado_min
        FROM TRANSFERENCIA t
        JOIN LINEA l1 ON t.linea_origen_id = l1.id_linea
        JOIN LINEA l2 ON t.linea_destino_id = l2.id_linea
        WHERE t.estacion_id = :id
        ORDER BY l1.codigo, l2.codigo
    """
    return execute_query(sql, {"id": id_estacion})["rows"]


def definir_transferencia(id_estacion: int, id_linea_origen: int, id_linea_destino: int, tiempo_min: int) -> dict:
    """
    Requerimiento 7: Definir enlace de transferencia peatonal entre dos líneas.
    """
    if id_linea_origen == id_linea_destino:
        return {"success": False, "error": "La línea de origen y destino deben ser distintas."}

    sql = """
        INSERT INTO TRANSFERENCIA (
            id_transferencia, estacion_id, linea_origen_id, linea_destino_id, tiempo_estimado_min
        ) VALUES (
            SEQ_TRANSFERENCIA.NEXTVAL, :est_id, :orig_id, :dest_id, :tiempo
        )
    """
    try:
        execute_dml(sql, {
            "est_id": id_estacion,
            "orig_id": id_linea_origen,
            "dest_id": id_linea_destino,
            "tiempo": int(tiempo_min)
        })
        # Actualizar tipo de estación a Transferencia si era local
        execute_dml("UPDATE ESTACION SET tipo_estacion = 'Transferencia' WHERE id_estacion = :id AND tipo_estacion = 'Local'", {"id": id_estacion})
        return {"success": True, "mensaje": "Transferencia configurada exitosamente."}
    except Exception as e:
        return {"success": False, "error": parse_oracle_error(e)}


def eliminar_transferencia(id_transferencia: int) -> dict:
    """Elimina una regla de transferencia peatonal."""
    sql = "DELETE FROM TRANSFERENCIA WHERE id_transferencia = :id"
    try:
        execute_dml(sql, {"id": id_transferencia})
        return {"success": True, "mensaje": "Transferencia eliminada exitosamente."}
    except Exception as e:
        return {"success": False, "error": parse_oracle_error(e)}


# ==============================================================================
# GESTIÓN DE LÍNEAS (REQUERIMIENTO 1)
# ==============================================================================

def get_lineas_completas() -> list:
    """
    Retorna la lista completa de líneas con sus terminales y conteo de estaciones.
    """
    sql = """
        SELECT l.id_linea, l.codigo, l.nombre, l.color,
               l.estado_operativo, l.tipo_servicio_principal,
               l.fecha_inauguracion, l.longitud_km, l.operador_responsable,
               e1.nombre as terminal_origen, e2.nombre as terminal_destino,
               l.estacion_origen_id, l.estacion_destino_id,
               (SELECT COUNT(*) FROM LINEA_ESTACION le WHERE le.linea_id = l.id_linea) as total_estaciones
        FROM LINEA l
        LEFT JOIN ESTACION e1 ON l.estacion_origen_id = e1.id_estacion
        LEFT JOIN ESTACION e2 ON l.estacion_destino_id = e2.id_estacion
        ORDER BY l.codigo ASC
    """
    return execute_query(sql)["rows"]


def crear_linea(datos: dict) -> dict:
    """
    Requerimiento 1: Crear nueva línea troncal en el sistema.
    """
    sql = """
        INSERT INTO LINEA (
            id_linea, codigo, nombre, color, estacion_origen_id, estacion_destino_id,
            estado_operativo, tipo_servicio_principal, fecha_inauguracion, longitud_km, operador_responsable
        ) VALUES (
            SEQ_LINEA.NEXTVAL, :codigo, :nombre, :color, :origen_id, :destino_id,
            :estado, :tipo_servicio, SYSDATE, :longitud, :operador
        )
    """
    try:
        execute_dml(sql, {
            "codigo": datos["codigo"].strip().upper(),
            "nombre": datos["nombre"].strip(),
            "color": datos.get("color", "#0039A6").strip(),
            "origen_id": int(datos["origen_id"]) if datos.get("origen_id") else None,
            "destino_id": int(datos["destino_id"]) if datos.get("destino_id") else None,
            "estado": datos.get("estado_operativo", "Activa"),
            "tipo_servicio": datos.get("tipo_servicio", "Local"),
            "longitud": float(datos.get("longitud_km", 20.0)),
            "operador": datos.get("operador", "NYCT").strip()
        })
        return {"success": True, "mensaje": f"Línea '{datos['codigo']}' creada exitosamente."}
    except Exception as e:
        return {"success": False, "error": parse_oracle_error(e)}


def modificar_linea(id_linea: int, datos: dict) -> dict:
    """
    Requerimiento 1: Modificar atributos de una línea existente.
    """
    sql = """
        UPDATE LINEA SET
            nombre = :nombre,
            color = :color,
            estacion_origen_id = :origen_id,
            estacion_destino_id = :destino_id,
            estado_operativo = :estado,
            tipo_servicio_principal = :tipo_servicio,
            longitud_km = :longitud,
            operador_responsable = :operador
        WHERE id_linea = :id
    """
    try:
        execute_dml(sql, {
            "id": id_linea,
            "nombre": datos["nombre"].strip(),
            "color": datos.get("color", "#0039A6").strip(),
            "origen_id": int(datos["origen_id"]) if datos.get("origen_id") else None,
            "destino_id": int(datos["destino_id"]) if datos.get("destino_id") else None,
            "estado": datos.get("estado_operativo", "Activa"),
            "tipo_servicio": datos.get("tipo_servicio", "Local"),
            "longitud": float(datos.get("longitud_km", 20.0)),
            "operador": datos.get("operador", "NYCT").strip()
        })
        return {"success": True, "mensaje": "Línea actualizada exitosamente."}
    except Exception as e:
        return {"success": False, "error": parse_oracle_error(e)}


def cambiar_estado_linea(id_linea: int, nuevo_estado: str) -> dict:
    """
    Requerimiento 1: Desactivar ('Suspendida', 'Fuera de Servicio') o reactivar ('Activa') una línea.
    """
    sql = "UPDATE LINEA SET estado_operativo = :estado WHERE id_linea = :id"
    try:
        execute_dml(sql, {"estado": nuevo_estado, "id": id_linea})
        return {"success": True, "mensaje": f"Estado de la línea cambiado a '{nuevo_estado}'."}
    except Exception as e:
        return {"success": False, "error": parse_oracle_error(e)}


# ==============================================================================
# TOPOLOGÍA: ORDEN SECUENCIAL, DISTANCIAS Y TIEMPOS (REQUERIMIENTOS 3, 4, 5 Y 9)
# ==============================================================================

def get_estaciones_de_linea_ordenadas(id_linea: int) -> list:
    """
    Requerimiento 9: Consultar todas las estaciones de una línea en el orden correcto.
    """
    sql = """
        SELECT le.id_linea_estacion, le.orden,
               e.id_estacion, e.codigo as codigo_estacion, e.nombre as nombre_estacion,
               e.distrito, e.tipo_estacion, e.estado_operativo as estado_estacion,
               e.accesible_discapacidad,
               le.distancia_km, le.tiempo_estimado_min
        FROM LINEA_ESTACION le
        JOIN ESTACION e ON le.estacion_id = e.id_estacion
        WHERE le.linea_id = :id
        ORDER BY le.orden ASC
    """
    return execute_query(sql, {"id": id_linea})["rows"]


def asociar_estacion_linea(id_linea: int, id_estacion: int, orden: int, distancia_km: float, tiempo_min: int) -> dict:
    """
    Requerimientos 3, 4 y 5: Asociar estación con línea definiendo su orden, distancia y tiempo.
    """
    # Verificar si ya existe
    chk = execute_query("SELECT id_linea_estacion FROM LINEA_ESTACION WHERE linea_id = :lid AND estacion_id = :eid", {"lid": id_linea, "eid": id_estacion})["rows"]
    if chk:
        return {"success": False, "error": "Esta estación ya forma parte del recorrido de la línea."}

    sql = """
        INSERT INTO LINEA_ESTACION (
            id_linea_estacion, linea_id, estacion_id, orden, distancia_km, tiempo_estimado_min
        ) VALUES (
            SEQ_LINEA_ESTACION.NEXTVAL, :lid, :eid, :orden, :distancia, :tiempo
        )
    """
    try:
        execute_dml(sql, {
            "lid": id_linea,
            "eid": id_estacion,
            "orden": int(orden),
            "distancia": float(distancia_km),
            "tiempo": int(tiempo_min)
        })
        return {"success": True, "mensaje": "Estación vinculada al recorrido de la línea exitosamente."}
    except Exception as e:
        return {"success": False, "error": parse_oracle_error(e)}


def modificar_tramo_linea_estacion(id_linea_estacion: int, orden: int, distancia_km: float, tiempo_min: int) -> dict:
    """
    Requerimientos 4 y 5: Modificar el orden secuencial, distancia o tiempo de un tramo.
    """
    sql = """
        UPDATE LINEA_ESTACION SET
            orden = :orden,
            distancia_km = :distancia,
            tiempo_estimado_min = :tiempo
        WHERE id_linea_estacion = :id
    """
    try:
        execute_dml(sql, {
            "id": id_linea_estacion,
            "orden": int(orden),
            "distancia": float(distancia_km),
            "tiempo": int(tiempo_min)
        })
        return {"success": True, "mensaje": "Tramo topológico actualizado exitosamente."}
    except Exception as e:
        return {"success": False, "error": parse_oracle_error(e)}


def desvincular_estacion_linea(id_linea_estacion: int) -> dict:
    """Elimina una estación del recorrido de una línea."""
    sql = "DELETE FROM LINEA_ESTACION WHERE id_linea_estacion = :id"
    try:
        execute_dml(sql, {"id": id_linea_estacion})
        return {"success": True, "mensaje": "Estación desvinculada del recorrido correctamente."}
    except Exception as e:
        return {"success": False, "error": parse_oracle_error(e)}


def get_estaciones_disponibles_para_linea(id_linea: int) -> list:
    """Retorna las estaciones que aún no están asociadas a la línea para el combo selector."""
    sql = """
        SELECT id_estacion, codigo, nombre, distrito
        FROM ESTACION
        WHERE id_estacion NOT IN (
            SELECT estacion_id FROM LINEA_ESTACION WHERE linea_id = :id
        )
        ORDER BY nombre ASC
    """
    return execute_query(sql, {"id": id_linea})["rows"]

