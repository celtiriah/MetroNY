"""
Servicio especializado para el Módulo 2: Rutas y Horarios.
Proporciona operaciones CRUD y consultas para:
- Rutas (locales, expresas, nocturnas)
- Paradas secuenciales de ruta (RUTA_DETALLE) con saltos expresos
- Horarios y frecuencias de operacion (HORARIO)
- Despacho y programacion de viajes (VIAJE_PROGRAMADO via SP_PROGRAMAR_VIAJE)
- Proximos arribos por estacion y deteccion de rutas afectadas por incidentes.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import oracledb

from services.db import get_connection, execute_query
from services.actions_service import parse_oracle_error, programar_viaje as sp_programar_viaje, cancelar_viajes_afectados as sp_cancelar_viajes


def _query_rows(sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Ejecuta una consulta SQL y retorna la lista de diccionarios de filas."""
    res = execute_query(sql, params)
    return res.get("rows", [])


# ==============================================================================
# 1. GESTION DE RUTAS (RUTA)
# ==============================================================================

def get_rutas(linea_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Retorna el catalogo de rutas con detalles de linea, terminales y conteos.
    """
    sql = """
        SELECT r.id_ruta, r.codigo, r.linea_id,
               l.codigo AS codigo_linea, l.nombre AS nombre_linea, l.color AS color_linea,
               r.estacion_origen_id, eo.nombre AS origen,
               r.estacion_destino_id, ed.nombre AS destino,
               r.sentido, r.tipo_servicio,
               r.distancia_total_km, r.duracion_estimada_min,
               r.estado,
               TO_CHAR(r.fecha_vigencia_desde, 'YYYY-MM-DD') AS vigencia_desde,
               TO_CHAR(r.fecha_vigencia_hasta, 'YYYY-MM-DD') AS vigencia_hasta,
               (SELECT COUNT(*) FROM RUTA_DETALLE rd WHERE rd.ruta_id = r.id_ruta) AS total_paradas,
               (SELECT COUNT(*) FROM HORARIO h WHERE h.ruta_id = r.id_ruta) AS total_horarios
        FROM RUTA r
        JOIN LINEA l ON r.linea_id = l.id_linea
        JOIN ESTACION eo ON r.estacion_origen_id = eo.id_estacion
        JOIN ESTACION ed ON r.estacion_destino_id = ed.id_estacion
    """
    params: Dict[str, Any] = {}
    if linea_id is not None:
        sql += " WHERE r.linea_id = :linea_id"
        params["linea_id"] = linea_id

    sql += " ORDER BY l.codigo, r.codigo"
    return _query_rows(sql, params)


def crear_ruta(datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crea una nueva ruta en la tabla RUTA.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        v_id = cursor.var(oracledb.NUMBER)
        sql = """
            INSERT INTO RUTA (
                id_ruta, codigo, linea_id, estacion_origen_id, estacion_destino_id,
                sentido, tipo_servicio, distancia_total_km, duracion_estimada_min,
                estado, fecha_vigencia_desde, fecha_vigencia_hasta
            ) VALUES (
                SEQ_RUTA.NEXTVAL, :codigo, :linea_id, :origen_id, :destino_id,
                :sentido, :tipo_servicio, :distancia_km, :duracion_min,
                :estado, TO_DATE(:vigencia_desde, 'YYYY-MM-DD'),
                CASE WHEN :vigencia_hasta IS NOT NULL THEN TO_DATE(:vigencia_hasta, 'YYYY-MM-DD') ELSE NULL END
            ) RETURNING id_ruta INTO :v_id
        """
        cursor.execute(sql, {
            "codigo": datos["codigo"],
            "linea_id": int(datos["linea_id"]),
            "origen_id": int(datos["estacion_origen_id"]),
            "destino_id": int(datos["estacion_destino_id"]),
            "sentido": datos.get("sentido", "Norte-Sur"),
            "tipo_servicio": datos.get("tipo_servicio", "Local"),
            "distancia_km": float(datos.get("distancia_total_km", 0.0)),
            "duracion_min": int(datos.get("duracion_estimada_min", 30)),
            "estado": datos.get("estado", "Activa"),
            "vigencia_desde": datos.get("fecha_vigencia_desde", date.today().strftime("%Y-%m-%d")),
            "vigencia_hasta": datos.get("fecha_vigencia_hasta"),
            "v_id": v_id
        })
        conn.commit()
        val = v_id.getvalue()
        new_id = int(val[0]) if isinstance(val, list) else int(val or 0)
        return {"success": True, "id_ruta": new_id, "mensaje": f"Ruta {datos['codigo']} creada exitosamente."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def modificar_ruta(id_ruta: int, datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Modifica una ruta existente.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE RUTA SET
                codigo = :codigo,
                linea_id = :linea_id,
                estacion_origen_id = :origen_id,
                estacion_destino_id = :destino_id,
                sentido = :sentido,
                tipo_servicio = :tipo_servicio,
                distancia_total_km = :distancia_km,
                duracion_estimada_min = :duracion_min,
                estado = :estado
            WHERE id_ruta = :id_ruta
        """
        cursor.execute(sql, {
            "codigo": datos["codigo"],
            "linea_id": int(datos["linea_id"]),
            "origen_id": int(datos["estacion_origen_id"]),
            "destino_id": int(datos["estacion_destino_id"]),
            "sentido": datos.get("sentido", "Norte-Sur"),
            "tipo_servicio": datos.get("tipo_servicio", "Local"),
            "distancia_km": float(datos.get("distancia_total_km", 0.0)),
            "duracion_min": int(datos.get("duracion_estimada_min", 30)),
            "estado": datos.get("estado", "Activa"),
            "id_ruta": int(id_ruta)
        })
        conn.commit()
        return {"success": True, "mensaje": f"Ruta {datos['codigo']} actualizada correctamente."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def cambiar_estado_ruta(id_ruta: int, nuevo_estado: str) -> Dict[str, Any]:
    """
    Cambia el estado operativo de una ruta ('Activa', 'Cerrada Temporalmente', 'Cancelada').
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = "UPDATE RUTA SET estado = :estado WHERE id_ruta = :id_ruta"
        cursor.execute(sql, {"estado": nuevo_estado, "id_ruta": int(id_ruta)})
        conn.commit()
        return {"success": True, "mensaje": f"Estado de ruta actualizado a '{nuevo_estado}'."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def get_dependencias_ruta(ruta_id: int) -> Dict[str, int]:
    """
    Retorna el conteo de paradas, horarios y viajes vinculados a una ruta.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            SELECT
                (SELECT COUNT(*) FROM RUTA_DETALLE WHERE ruta_id = :rid) AS paradas,
                (SELECT COUNT(*) FROM HORARIO WHERE ruta_id = :rid) AS horarios,
                (SELECT COUNT(*) FROM VIAJE_PROGRAMADO WHERE ruta_id = :rid) AS viajes
            FROM DUAL
        """
        cursor.execute(sql, {"rid": int(ruta_id)})
        row = cursor.fetchone()
        if row:
            return {
                "paradas": int(row[0] or 0),
                "horarios": int(row[1] or 0),
                "viajes": int(row[2] or 0)
            }
        return {"paradas": 0, "horarios": 0, "viajes": 0}
    except Exception:
        return {"paradas": 0, "horarios": 0, "viajes": 0}
    finally:
        cursor.close()
        conn.close()


def eliminar_ruta(ruta_id: int) -> Dict[str, Any]:
    """
    Elimina una ruta y todos sus registros vinculados en cascada de forma atomica.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        rid = int(ruta_id)
        # 1. Eliminar referencias de incidentes a viajes de esta ruta
        cursor.execute("""
            DELETE FROM INCIDENTE_ELEMENTO_AFECTADO
            WHERE viaje_id IN (SELECT id_viaje FROM VIAJE_PROGRAMADO WHERE ruta_id = :rid)
        """, {"rid": rid})

        # 2. Eliminar validaciones de pasajeros en viajes de esta ruta
        cursor.execute("""
            DELETE FROM VIAJE_PASAJERO 
            WHERE viaje_programado_id IN (SELECT id_viaje FROM VIAJE_PROGRAMADO WHERE ruta_id = :rid)
        """, {"rid": rid})

        # 3. Eliminar viajes programados
        cursor.execute("DELETE FROM VIAJE_PROGRAMADO WHERE ruta_id = :rid", {"rid": rid})

        # 3. Eliminar horarios
        cursor.execute("DELETE FROM HORARIO WHERE ruta_id = :rid", {"rid": rid})

        # 4. Eliminar asociaciones de incidentes a esta ruta
        cursor.execute("DELETE FROM INCIDENTE_ELEMENTO_AFECTADO WHERE ruta_id = :rid", {"rid": rid})

        # 5. Eliminar secuencia de paradas
        cursor.execute("DELETE FROM RUTA_DETALLE WHERE ruta_id = :rid", {"rid": rid})

        # 6. Eliminar la ruta
        cursor.execute("DELETE FROM RUTA WHERE id_ruta = :rid", {"rid": rid})

        conn.commit()
        return {"success": True, "mensaje": "Ruta y registros dependientes eliminados exitosamente."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 2. PARADAS SECUENCIALES (RUTA_DETALLE)
# ==============================================================================

def get_paradas_ruta(ruta_id: int) -> List[Dict[str, Any]]:
    """
    Retorna la secuencia ordenada de paradas de una ruta con bandera de parada efectiva.
    """
    sql = """
        SELECT rd.id_ruta_detalle, rd.ruta_id, rd.estacion_id, rd.orden_llegada,
               e.codigo AS codigo_estacion, e.nombre AS nombre_estacion, e.distrito,
               TO_CHAR(rd.hora_estimada_llegada, 'HH24:MI') AS hora_llegada,
               TO_CHAR(rd.hora_estimada_salida, 'HH24:MI') AS hora_salida,
               rd.distancia_desde_anterior_km, rd.tiempo_desde_anterior_min,
               rd.se_detiene, e.accesible_discapacidad
        FROM RUTA_DETALLE rd
        JOIN ESTACION e ON rd.estacion_id = e.id_estacion
        WHERE rd.ruta_id = :ruta_id
        ORDER BY rd.orden_llegada ASC
    """
    return _query_rows(sql, {"ruta_id": int(ruta_id)})


def agregar_parada_ruta(datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agrega una parada a la secuencia de la ruta.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        hora_llegada = datos.get("hora_estimada_llegada")
        hora_salida = datos.get("hora_estimada_salida")

        sql = """
            INSERT INTO RUTA_DETALLE (
                id_ruta_detalle, ruta_id, estacion_id, orden_llegada,
                hora_estimada_llegada, hora_estimada_salida,
                distancia_desde_anterior_km, tiempo_desde_anterior_min, se_detiene
            ) VALUES (
                SEQ_RUTA_DETALLE.NEXTVAL, :ruta_id, :estacion_id, :orden_llegada,
                CASE WHEN :h_llegada IS NOT NULL THEN TO_DATE(:h_llegada, 'HH24:MI') ELSE NULL END,
                CASE WHEN :h_salida IS NOT NULL THEN TO_DATE(:h_salida, 'HH24:MI') ELSE NULL END,
                :distancia_km, :tiempo_min, :se_detiene
            )
        """
        cursor.execute(sql, {
            "ruta_id": int(datos["ruta_id"]),
            "estacion_id": int(datos["estacion_id"]),
            "orden_llegada": int(datos["orden_llegada"]),
            "h_llegada": hora_llegada if hora_llegada else None,
            "h_salida": hora_salida if hora_salida else None,
            "distancia_km": float(datos.get("distancia_desde_anterior_km", 0.0)),
            "tiempo_min": int(datos.get("tiempo_desde_anterior_min", 0)),
            "se_detiene": datos.get("se_detiene", "S")
        })
        conn.commit()
        return {"success": True, "mensaje": "Parada agregada correctamente a la ruta."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


# Alias for compatibility
asociar_parada_ruta = agregar_parada_ruta


def modificar_parada_ruta(id_ruta_detalle: int, datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Modifica orden o condicion de parada en la ruta.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        hora_llegada = datos.get("hora_estimada_llegada")
        hora_salida = datos.get("hora_estimada_salida")

        sql = """
            UPDATE RUTA_DETALLE SET
                orden_llegada = :orden_llegada,
                hora_estimada_llegada = CASE WHEN :h_llegada IS NOT NULL THEN TO_DATE(:h_llegada, 'HH24:MI') ELSE NULL END,
                hora_estimada_salida = CASE WHEN :h_salida IS NOT NULL THEN TO_DATE(:h_salida, 'HH24:MI') ELSE NULL END,
                distancia_desde_anterior_km = :distancia_km,
                tiempo_desde_anterior_min = :tiempo_min,
                se_detiene = :se_detiene
            WHERE id_ruta_detalle = :id_rd
        """
        cursor.execute(sql, {
            "orden_llegada": int(datos["orden_llegada"]),
            "h_llegada": hora_llegada if hora_llegada else None,
            "h_salida": hora_salida if hora_salida else None,
            "distancia_km": float(datos.get("distancia_desde_anterior_km", 0.0)),
            "tiempo_min": int(datos.get("tiempo_desde_anterior_min", 0)),
            "se_detiene": datos.get("se_detiene", "S"),
            "id_rd": int(id_ruta_detalle)
        })
        conn.commit()
        return {"success": True, "mensaje": "Parada de ruta actualizada correctamente."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def eliminar_parada_ruta(id_ruta_detalle: int) -> Dict[str, Any]:
    """
    Elimina una parada de la secuencia de una ruta.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM RUTA_DETALLE WHERE id_ruta_detalle = :id_rd", {"id_rd": int(id_ruta_detalle)})
        conn.commit()
        return {"success": True, "mensaje": "Parada desvinculada de la ruta."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 3. HORARIOS Y FRECUENCIAS (HORARIO)
# ==============================================================================

def get_horarios_ruta(ruta_id: int) -> List[Dict[str, Any]]:
    """
    Consulta los horarios programados de una ruta.
    """
    sql = """
        SELECT h.id_horario, h.ruta_id, h.dia_semana,
               TO_CHAR(h.hora_inicio, 'HH24:MI') AS hora_inicio,
               TO_CHAR(h.hora_fin, 'HH24:MI') AS hora_fin,
               h.frecuencia_minutos, h.tipo_servicio,
               TO_CHAR(h.fecha_vigencia_desde, 'YYYY-MM-DD') AS vigencia_desde,
               TO_CHAR(h.fecha_vigencia_hasta, 'YYYY-MM-DD') AS vigencia_hasta
        FROM HORARIO h
        WHERE h.ruta_id = :ruta_id
        ORDER BY h.dia_semana, h.hora_inicio
    """
    return _query_rows(sql, {"ruta_id": int(ruta_id)})


def crear_horario(datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crea un nuevo horario para una ruta.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            INSERT INTO HORARIO (
                id_horario, ruta_id, dia_semana, hora_inicio, hora_fin,
                frecuencia_minutos, tipo_servicio, fecha_vigencia_desde, fecha_vigencia_hasta
            ) VALUES (
                SEQ_HORARIO.NEXTVAL, :ruta_id, :dia_semana,
                TO_DATE(:h_inicio, 'HH24:MI'), TO_DATE(:h_fin, 'HH24:MI'),
                :frecuencia, :tipo_servicio,
                TO_DATE(:vigencia_desde, 'YYYY-MM-DD'),
                CASE WHEN :vigencia_hasta IS NOT NULL THEN TO_DATE(:vigencia_hasta, 'YYYY-MM-DD') ELSE NULL END
            )
        """
        cursor.execute(sql, {
            "ruta_id": int(datos["ruta_id"]),
            "dia_semana": datos["dia_semana"],
            "h_inicio": datos["hora_inicio"],
            "h_fin": datos["hora_fin"],
            "frecuencia": int(datos["frecuencia_minutos"]),
            "tipo_servicio": datos.get("tipo_servicio", "Regular"),
            "vigencia_desde": datos.get("fecha_vigencia_desde", date.today().strftime("%Y-%m-%d")),
            "vigencia_hasta": datos.get("fecha_vigencia_hasta")
        })
        conn.commit()
        return {"success": True, "mensaje": "Horario configurado exitosamente."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def eliminar_horario(id_horario: int) -> Dict[str, Any]:
    """
    Elimina un horario programado.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM HORARIO WHERE id_horario = :id_h", {"id_h": int(id_horario)})
        conn.commit()
        return {"success": True, "mensaje": "Horario eliminado correctamente."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def modificar_horario(id_horario: int, datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Modifica un horario de operacion existente.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE HORARIO
            SET dia_semana = :dia_semana,
                hora_inicio = TO_DATE(:h_inicio, 'HH24:MI'),
                hora_fin = TO_DATE(:h_fin, 'HH24:MI'),
                frecuencia_minutos = :frecuencia,
                tipo_servicio = :tipo_servicio
            WHERE id_horario = :id_h
        """
        cursor.execute(sql, {
            "dia_semana": datos["dia_semana"],
            "h_inicio": datos["hora_inicio"],
            "h_fin": datos["hora_fin"],
            "frecuencia": int(datos["frecuencia_minutos"]),
            "tipo_servicio": datos.get("tipo_servicio", "Regular"),
            "id_h": int(id_horario)
        })
        conn.commit()
        return {"success": True, "mensaje": "Horario modificado correctamente."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 4. VIAJES PROGRAMADOS Y DESPACHO (VIAJE_PROGRAMADO)
# ==============================================================================

def get_viajes_programados(
    fecha: Optional[str] = None,
    ruta_id: Optional[int] = None,
    estado: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retorna la lista de viajes programados con filtros interactivos.
    """
    sql = """
        SELECT vp.id_viaje, vp.numero_viaje, vp.ruta_id,
               r.codigo AS codigo_ruta, r.tipo_servicio AS tipo_servicio_ruta,
               l.codigo AS codigo_linea, l.color AS color_linea,
               TO_CHAR(vp.fecha, 'YYYY-MM-DD') AS fecha,
               TO_CHAR(vp.hora_prog_salida, 'HH24:MI') AS hora_prog_salida,
               TO_CHAR(vp.hora_prog_llegada, 'HH24:MI') AS hora_prog_llegada,
               TO_CHAR(vp.hora_real_salida, 'HH24:MI') AS hora_real_salida,
               TO_CHAR(vp.hora_real_llegada, 'HH24:MI') AS hora_real_llegada,
               vp.tren_id, NVL(t.codigo_interno, 'Sin Tren') AS codigo_tren,
               NVL(m.nombre_modelo, 'N/A') AS modelo_tren,
               vp.conductor_id, NVL(emp.nombre_completo, 'Sin Asignar') AS conductor,
               vp.estado, vp.cantidad_estimada_pasajeros
        FROM VIAJE_PROGRAMADO vp
        JOIN RUTA r ON vp.ruta_id = r.id_ruta
        JOIN LINEA l ON r.linea_id = l.id_linea
        LEFT JOIN TREN t ON vp.tren_id = t.id_tren
        LEFT JOIN MODELO_TREN m ON t.modelo_id = m.id_modelo
        LEFT JOIN EMPLEADO emp ON vp.conductor_id = emp.id_empleado
        WHERE 1=1
    """
    params: Dict[str, Any] = {}
    if fecha:
        sql += " AND vp.fecha = TO_DATE(:fecha, 'YYYY-MM-DD')"
        params["fecha"] = fecha
    if ruta_id:
        sql += " AND vp.ruta_id = :ruta_id"
        params["ruta_id"] = int(ruta_id)
    if estado and estado != "(Todos)":
        sql += " AND vp.estado = :estado"
        params["estado"] = estado

    sql += " ORDER BY vp.fecha DESC, vp.hora_prog_salida DESC"
    return _query_rows(sql, params)


def programar_nuevo_viaje(
    ruta_id: int,
    fecha_str: str,
    hora_salida_str: str,
    hora_llegada_str: str,
    tren_id: int,
    conductor_id: int,
    horario_id: Optional[int] = None,
    estado: Optional[str] = None,
    cantidad_estimada_pasajeros: Optional[int] = None
) -> Dict[str, Any]:
    """
    Llama al procedimiento almacenado SP_PROGRAMAR_VIAJE y actualiza estado y pasajeros si se especifican.
    """
    res = sp_programar_viaje(
        ruta_id=ruta_id,
        fecha=fecha_str,
        hora_prog_salida=hora_salida_str,
        hora_prog_llegada=hora_llegada_str,
        tren_id=tren_id,
        conductor_id=conductor_id,
        horario_id=horario_id
    )
    if not res.get("success"):
        return res

    id_viaje = res.get("id_viaje")
    if id_viaje and (estado or cantidad_estimada_pasajeros is not None):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            sets = []
            params: Dict[str, Any] = {"vid": int(id_viaje)}
            if estado:
                sets.append("estado = :estado")
                params["estado"] = estado
            if cantidad_estimada_pasajeros is not None:
                sets.append("cantidad_estimada_pasajeros = :pasajeros")
                params["pasajeros"] = int(cantidad_estimada_pasajeros)
            if sets:
                sql = f"UPDATE VIAJE_PROGRAMADO SET {', '.join(sets)} WHERE id_viaje = :vid"
                cursor.execute(sql, params)
                conn.commit()
        except Exception:
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    return res


def cancelar_viaje(id_viaje: int) -> Dict[str, Any]:
    """
    Cancela un viaje programado individual.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = "UPDATE VIAJE_PROGRAMADO SET estado = 'Cancelado' WHERE id_viaje = :id_v"
        cursor.execute(sql, {"id_v": int(id_viaje)})
        conn.commit()
        return {"success": True, "mensaje": f"Viaje #{id_viaje} cancelado correctamente."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def reprogramar_viaje(id_viaje: int, nueva_fecha: str, nueva_salida: str, nueva_llegada: str) -> Dict[str, Any]:
    """
    Reprograma la fecha y horas de un viaje programado.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE VIAJE_PROGRAMADO SET
                fecha = TO_DATE(:fecha, 'YYYY-MM-DD'),
                hora_prog_salida = TO_TIMESTAMP(:fecha || ' ' || :salida || ':00', 'YYYY-MM-DD HH24:MI:SS'),
                hora_prog_llegada = TO_TIMESTAMP(:fecha || ' ' || :llegada || ':00', 'YYYY-MM-DD HH24:MI:SS'),
                estado = 'Programado'
            WHERE id_viaje = :id_v
        """
        cursor.execute(sql, {
            "fecha": nueva_fecha,
            "salida": nueva_salida,
            "llegada": nueva_llegada,
            "id_v": int(id_viaje)
        })
        conn.commit()
        return {"success": True, "mensaje": f"Viaje #{id_viaje} reprogramado exitosamente."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def eliminar_viaje(id_viaje: int) -> Dict[str, Any]:
    """
    Elimina un viaje programado y sus validaciones de pasajeros en cascada.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        vid = int(id_viaje)
        cursor.execute("DELETE FROM INCIDENTE_ELEMENTO_AFECTADO WHERE viaje_id = :vid", {"vid": vid})
        cursor.execute("DELETE FROM VIAJE_PASAJERO WHERE viaje_programado_id = :vid", {"vid": vid})
        cursor.execute("DELETE FROM VIAJE_PROGRAMADO WHERE id_viaje = :vid", {"vid": vid})
        conn.commit()
        return {"success": True, "mensaje": f"Viaje #{vid} eliminado correctamente."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


def modificar_viaje(id_viaje: int, datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Modifica integralmente los datos de un viaje programado (fecha, horas, tren, conductor, estado, pasajeros).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        vid = int(id_viaje)
        fecha = datos["fecha"]
        salida = datos["hora_salida"]
        llegada = datos["hora_llegada"]
        tren_id = int(datos["tren_id"])
        cond_id = int(datos["conductor_id"])
        estado = datos.get("estado", "Programado")
        pasajeros = datos.get("cantidad_estimada_pasajeros")

        sql = """
            UPDATE VIAJE_PROGRAMADO SET
                fecha = TO_DATE(:fecha, 'YYYY-MM-DD'),
                hora_prog_salida = TO_TIMESTAMP(:fecha || ' ' || :salida || ':00', 'YYYY-MM-DD HH24:MI:SS'),
                hora_prog_llegada = TO_TIMESTAMP(:fecha || ' ' || :llegada || ':00', 'YYYY-MM-DD HH24:MI:SS'),
                tren_id = :tren_id,
                conductor_id = :cond_id,
                estado = :estado,
                cantidad_estimada_pasajeros = :pasajeros
            WHERE id_viaje = :vid
        """
        cursor.execute(sql, {
            "fecha": fecha,
            "salida": salida,
            "llegada": llegada,
            "tren_id": tren_id,
            "cond_id": cond_id,
            "estado": estado,
            "pasajeros": int(pasajeros) if pasajeros is not None and str(pasajeros).strip() != "" and str(pasajeros) != "-" else None,
            "vid": vid
        })
        conn.commit()
        return {"success": True, "mensaje": f"Viaje #{vid} actualizado exitosamente."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": parse_oracle_error(e)}
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# 5. CONSULTAS ESPECIALES (PROXIMOS VIAJES E INCIDENTES)
# ==============================================================================

def get_proximos_viajes_estacion(id_estacion: int) -> List[Dict[str, Any]]:
    """
    Consulta los proximos arribos de viajes programados para una estacion (Requerimiento 8).
    """
    sql = """
        SELECT vp.id_viaje, vp.numero_viaje,
               r.codigo AS codigo_ruta, r.tipo_servicio,
               l.codigo AS codigo_linea, l.color AS color_linea,
               ed.nombre AS destino_final,
               TO_CHAR(vp.fecha, 'YYYY-MM-DD') AS fecha,
               TO_CHAR(rd.hora_estimada_llegada, 'HH24:MI') AS arribo_estimado,
               vp.estado,
               t.codigo_interno AS tren,
               emp.nombre_completo AS conductor
        FROM VIAJE_PROGRAMADO vp
        JOIN RUTA r ON vp.ruta_id = r.id_ruta
        JOIN LINEA l ON r.linea_id = l.id_linea
        JOIN ESTACION ed ON r.estacion_destino_id = ed.id_estacion
        JOIN RUTA_DETALLE rd ON r.id_ruta = rd.ruta_id
        LEFT JOIN TREN t ON vp.tren_id = t.id_tren
        LEFT JOIN EMPLEADO emp ON vp.conductor_id = emp.id_empleado
        WHERE rd.estacion_id = :id_estacion
          AND rd.se_detiene = 'S'
          AND vp.estado NOT IN ('Cancelado', 'Completado')
        ORDER BY vp.fecha, rd.hora_estimada_llegada
    """
    return _query_rows(sql, {"id_estacion": int(id_estacion)})


def get_rutas_afectadas_incidentes() -> List[Dict[str, Any]]:
    """
    Identifica rutas que tienen incidentes activos en su recorrido o estaciones (Requerimiento 9).
    """
    sql = """
        SELECT DISTINCT r.id_ruta, r.codigo AS codigo_ruta,
               l.codigo AS codigo_linea, l.color AS color_linea,
               i.id_incidente, i.numero_incidente, i.tipo AS tipo_incidente,
               i.nivel_severidad, i.descripcion,
               a.tipo_elemento, a.tipo_afectacion,
               TO_CHAR(i.fecha_hora_inicio, 'YYYY-MM-DD HH24:MI') AS inicio_incidente
        FROM INCIDENTE i
        JOIN INCIDENTE_ELEMENTO_AFECTADO a ON i.id_incidente = a.incidente_id
        JOIN RUTA r ON (
            (a.tipo_elemento = 'RUTA' AND a.ruta_id = r.id_ruta)
            OR (a.tipo_elemento = 'LINEA' AND a.linea_id = r.linea_id)
            OR (a.tipo_elemento = 'ESTACION' AND a.estacion_id IN (
                SELECT rd.estacion_id FROM RUTA_DETALLE rd WHERE rd.ruta_id = r.id_ruta
            ))
        )
        JOIN LINEA l ON r.linea_id = l.id_linea
        WHERE i.estado IN ('Abierto', 'En Atención', 'En Atencion')
        ORDER BY i.nivel_severidad DESC, r.codigo
    """
    return _query_rows(sql)


# Alias
get_afectaciones_activas = get_rutas_afectadas_incidentes


def cancelar_viajes_por_incidente(incidente_id: int) -> Dict[str, Any]:
    """
    Cancela en cascada los viajes afectados por un incidente via SP_CANCELAR_VIAJES_AFECTADOS.
    """
    return sp_cancelar_viajes(incidente_id)


# ==============================================================================
# 6. AUXILIARES PARA FORMULARIOS Y COMBOS
# ==============================================================================

def get_lineas_combo() -> List[Dict[str, Any]]:
    sql = "SELECT id_linea, codigo, nombre, color FROM LINEA WHERE estado_operativo = 'Activa' ORDER BY codigo"
    return _query_rows(sql)


def get_estaciones_combo() -> List[Dict[str, Any]]:
    sql = "SELECT id_estacion, codigo, nombre, distrito FROM ESTACION WHERE estado_operativo = 'Operativa' ORDER BY nombre"
    return _query_rows(sql)


def get_trenes_disponibles_combo() -> List[Dict[str, Any]]:
    sql = """
        SELECT t.id_tren, t.codigo_interno, m.nombre_modelo, t.capacidad_total
        FROM TREN t
        JOIN MODELO_TREN m ON t.modelo_id = m.id_modelo
        WHERE t.estado_operativo = 'Disponible'
        ORDER BY t.codigo_interno
    """
    return _query_rows(sql)


def get_todos_trenes_combo() -> List[Dict[str, Any]]:
    sql = """
        SELECT t.id_tren, t.codigo_interno, m.nombre_modelo, t.capacidad_total, t.estado_operativo
        FROM TREN t
        JOIN MODELO_TREN m ON t.modelo_id = m.id_modelo
        WHERE t.estado_operativo IN ('Disponible', 'En Operación')
        ORDER BY t.codigo_interno
    """
    return _query_rows(sql)


def get_conductores_combo() -> List[Dict[str, Any]]:
    sql = """
        SELECT e.id_empleado, e.numero_empleado, e.nombre_completo, e.cargo,
               CASE 
                   WHEN EXISTS (
                       SELECT 1 FROM CERTIFICACION c 
                       WHERE c.empleado_id = e.id_empleado 
                         AND c.estado = 'Vigente' 
                         AND c.fecha_vencimiento >= SYSDATE
                   ) THEN 'Vigente' 
                   ELSE 'Vencida / Sin Certificación' 
               END AS estado_certificacion
        FROM EMPLEADO e
        WHERE e.cargo = 'Conductor'
          AND e.estado_laboral = 'Activo'
        ORDER BY CASE WHEN EXISTS (
                       SELECT 1 FROM CERTIFICACION c 
                       WHERE c.empleado_id = e.id_empleado 
                         AND c.estado = 'Vigente' 
                         AND c.fecha_vencimiento >= SYSDATE
                   ) THEN 0 ELSE 1 END, e.nombre_completo
    """
    return _query_rows(sql)
