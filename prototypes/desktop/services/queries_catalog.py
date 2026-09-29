"""
Catalogue of the 15 Mandatory SQL Queries restructured for the
Centro de Reporteria Analitica y Extraccion de Datos (Business Intelligence).

Organized thematically into 4 core operational areas:
1. Infraestructura y Red (REP-01 to REP-03)
2. Operaciones y Servicios de Transporte (REP-04 to REP-07)
3. Finanzas, Pasajeros y Recaudacion (REP-08 to REP-11)
4. Flota, Mantenimiento e Incidentes (REP-12 to REP-15)

Supports dynamic parameter injection (stations, routes, dates, thresholds, severity).
"""

CONSULTAS_CATALOGO = {
    1: {
        "codigo": "REP-01",
        "area": "Infraestructura y Red",
        "titulo": "REP-01: Densidad de lineas convergentes por estacion",
        "descripcion": "Analiza la convergencia y densidad de lineas metropolitanas en cada estacion del sistema (Relacion N:M).",
        "params": [
            {
                "key": "station_code",
                "label": "Estacion:",
                "type": "combo",
                "source": "stations",
                "default": "TSQ42"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT e.nombre AS "Estacion",
                   e.codigo AS "Codigo Estacion",
                   l.codigo AS "Linea",
                   l.nombre AS "Nombre de Linea",
                   l.color  AS "Color Dist.",
                   le.orden AS "Orden Secuencia"
            FROM ESTACION e
            JOIN LINEA_ESTACION le ON e.id_estacion = le.estacion_id
            JOIN LINEA l           ON le.linea_id = l.id_linea
            """ + (
                " WHERE e.codigo = :station_code " if p.get("station_code") and p.get("station_code") != "(Todas)" else ""
            ) + """
            ORDER BY e.nombre, le.orden
            """,
            {"station_code": p.get("station_code")} if p.get("station_code") and p.get("station_code") != "(Todas)" else {}
        )
    },
    2: {
        "codigo": "REP-02",
        "area": "Infraestructura y Red",
        "titulo": "REP-02: Paradas secuenciales de recorrido por ruta operativa",
        "descripcion": "Audita la secuencia topologica de estaciones y paradas directas o expresas por itinerario de ruta.",
        "params": [
            {
                "key": "route_code",
                "label": "Ruta Operativa:",
                "type": "combo",
                "source": "routes",
                "default": "RUT-1-SB"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT r.codigo         AS "Codigo Ruta",
                   r.sentido        AS "Sentido",
                   rd.orden_llegada AS "Secuencia",
                   e.nombre         AS "Estacion",
                   e.distrito       AS "Distrito",
                   CASE rd.se_detiene WHEN 'S' THEN 'Si (Parada)' ELSE 'Pasa Expreso' END AS "Detencion"
            FROM RUTA r
            JOIN RUTA_DETALLE rd ON r.id_ruta = rd.ruta_id
            JOIN ESTACION e      ON rd.estacion_id = e.id_estacion
            """ + (
                " WHERE r.codigo = :route_code " if p.get("route_code") and p.get("route_code") != "(Todas)" else ""
            ) + """
            ORDER BY r.codigo, rd.orden_llegada
            """,
            {"route_code": p.get("route_code")} if p.get("route_code") and p.get("route_code") != "(Todas)" else {}
        )
    },
    3: {
        "codigo": "REP-03",
        "area": "Infraestructura y Red",
        "titulo": "REP-03: Estaciones de transferencia intermodal y tiempos de conexion",
        "descripcion": "Monitorea nodos de intercambio modal entre lineas y tiempos estimados de caminata peatonal.",
        "params": [
            {
                "key": "borough",
                "label": "Distrito (Borough):",
                "type": "combo",
                "options": ["(Todos)", "Manhattan", "Brooklyn", "Queens", "The Bronx"],
                "default": "(Todos)"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT e.nombre AS "Estacion de Conexion",
                   e.distrito AS "Distrito",
                   lo.codigo || ' (' || lo.color || ')' AS "Linea Origen",
                   ld.codigo || ' (' || ld.color || ')' AS "Linea Destino",
                   t.tiempo_estimado_min AS "Min. Caminata"
            FROM TRANSFERENCIA t
            JOIN ESTACION e  ON t.estacion_id = e.id_estacion
            JOIN LINEA lo    ON t.linea_origen_id = lo.id_linea
            JOIN LINEA ld    ON t.linea_destino_id = ld.id_linea
            """ + (
                " WHERE e.distrito = :borough " if p.get("borough") and p.get("borough") != "(Todos)" else ""
            ) + """
            ORDER BY e.nombre, t.tiempo_estimado_min
            """,
            {"borough": p.get("borough")} if p.get("borough") and p.get("borough") != "(Todos)" else {}
        )
    },
    4: {
        "codigo": "REP-04",
        "area": "Operaciones y Servicios de Transporte",
        "titulo": "REP-04: Programacion de despacho de viajes e itinerario diario",
        "descripcion": "Audita despachos programados, asignacion de material rodante y personal de conduccion por fecha.",
        "params": [
            {
                "key": "trip_date",
                "label": "Fecha de Despacho:",
                "type": "date",
                "default": "2026-09-01"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT vp.numero_viaje AS "Numero Viaje",
                   r.codigo        AS "Ruta",
                   TO_CHAR(vp.hora_prog_salida, 'HH24:MI') AS "Hora Prog.",
                   t.codigo_interno AS "Tren Asignado",
                   e.nombre_completo AS "Conductor",
                   vp.estado       AS "Estado"
            FROM VIAJE_PROGRAMADO vp
            JOIN RUTA r     ON vp.ruta_id = r.id_ruta
            JOIN TREN t     ON vp.tren_id = t.id_tren
            JOIN EMPLEADO e ON vp.conductor_id = e.id_empleado
            """ + (
                " WHERE TRUNC(vp.fecha) = TO_DATE(:trip_date, 'YYYY-MM-DD') " if p.get("trip_date") else ""
            ) + """
            ORDER BY vp.hora_prog_salida
            """,
            {"trip_date": p.get("trip_date")} if p.get("trip_date") else {}
        )
    },
    5: {
        "codigo": "REP-05",
        "area": "Operaciones y Servicios de Transporte",
        "titulo": "REP-05: Auditoria de retrasos en salida y cumplimiento horario",
        "descripcion": "Identifica viajes con desviacion horaria superior al umbral de tolerancia operacional configurado.",
        "params": [
            {
                "key": "min_delay",
                "label": "Demora minima (minutos):",
                "type": "number",
                "default": "15"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT vp.numero_viaje  AS "Numero Viaje",
                   r.codigo         AS "Ruta",
                   TO_CHAR(vp.hora_prog_salida, 'HH24:MI') AS "Salida Prog.",
                   TO_CHAR(vp.hora_real_salida, 'HH24:MI') AS "Salida Real",
                   ROUND((CAST(vp.hora_real_salida AS DATE) - CAST(vp.hora_prog_salida AS DATE)) * 24 * 60) AS "Min. Demora",
                   vp.estado        AS "Estado"
            FROM VIAJE_PROGRAMADO vp
            JOIN RUTA r ON vp.ruta_id = r.id_ruta
            WHERE vp.hora_real_salida IS NOT NULL
              AND (CAST(vp.hora_real_salida AS DATE) - CAST(vp.hora_prog_salida AS DATE)) * 24 * 60 > :min_delay
            ORDER BY "Min. Demora" DESC
            """,
            {"min_delay": int(p.get("min_delay") or 15)}
        )
    },
    6: {
        "codigo": "REP-06",
        "area": "Operaciones y Servicios de Transporte",
        "titulo": "REP-06: Asignacion de personal de conduccion y certificaciones activas",
        "descripcion": "Verifica habilitacion tecnica y vigencia de licencias MTA del personal asignado a servicios de tren.",
        "params": [
            {
                "key": "conductor_query",
                "label": "Filtro Conductor (Nombre o ID):",
                "type": "text",
                "default": ""
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT vp.numero_viaje   AS "Viaje",
                   r.codigo          AS "Ruta",
                   emp.numero_empleado AS "Num. Empleado",
                   emp.nombre_completo AS "Nombre Conductor",
                   NVL(c.tipo_certificacion, 'Sin Certificar') AS "Licencia MTA",
                   TO_CHAR(vp.fecha, 'YYYY-MM-DD') AS "Fecha"
            FROM VIAJE_PROGRAMADO vp
            JOIN RUTA r     ON vp.ruta_id = r.id_ruta
            JOIN EMPLEADO emp ON vp.conductor_id = emp.id_empleado
            LEFT JOIN CERTIFICACION c ON emp.id_empleado = c.empleado_id AND c.estado = 'Vigente'
            """ + (
                " WHERE UPPER(emp.nombre_completo) LIKE UPPER('%' || :cond || '%') OR UPPER(emp.numero_empleado) LIKE UPPER('%' || :cond || '%') "
                if p.get("conductor_query") else ""
            ) + """
            ORDER BY vp.fecha, vp.hora_prog_salida
            """,
            {"cond": p.get("conductor_query")} if p.get("conductor_query") else {}
        )
    },
    7: {
        "codigo": "REP-07",
        "area": "Operaciones y Servicios de Transporte",
        "titulo": "REP-07: Minutos acumulados de demora y confiabilidad por linea",
        "descripcion": "Totaliza el tiempo perdido por retrasos operacionales agregados por linea de servicio.",
        "params": [],
        "sql_generator": lambda p: (
            """
            SELECT l.codigo AS "Linea",
                   l.nombre AS "Nombre Linea",
                   l.color  AS "Color",
                   COUNT(vp.id_viaje) AS "Viajes Demorados",
                   NVL(SUM(ROUND((CAST(vp.hora_real_salida AS DATE) - CAST(vp.hora_prog_salida AS DATE)) * 24 * 60)), 0) AS "Minutos Demora"
            FROM LINEA l
            JOIN RUTA r ON l.id_linea = r.linea_id
            JOIN VIAJE_PROGRAMADO vp ON r.id_ruta = vp.ruta_id
            WHERE vp.hora_real_salida > vp.hora_prog_salida
            GROUP BY l.codigo, l.nombre, l.color
            ORDER BY "Minutos Demora" DESC
            """,
            {}
        )
    },
    8: {
        "codigo": "REP-08",
        "area": "Finanzas, Pasajeros y Recaudacion",
        "titulo": "REP-08: Afluencia consolidada de pasajeros transportados por linea",
        "descripcion": "Cuantifica el volumen neto de pasajeros transportados a traves de la red por cada linea metropolitana.",
        "params": [],
        "sql_generator": lambda p: (
            """
            SELECT l.codigo          AS "Linea",
                   l.nombre          AS "Nombre de la Linea",
                   COUNT(vp.id_viaje_pasajero) AS "Total Pasajeros"
            FROM LINEA l
            LEFT JOIN RUTA r             ON l.id_linea = r.linea_id
            LEFT JOIN VIAJE_PROGRAMADO vprog ON r.id_ruta = vprog.ruta_id
            LEFT JOIN VIAJE_PASAJERO vp  ON vprog.id_viaje = vp.viaje_programado_id
            GROUP BY l.codigo, l.nombre
            ORDER BY "Total Pasajeros" DESC
            """,
            {}
        )
    },
    9: {
        "codigo": "REP-09",
        "area": "Finanzas, Pasajeros y Recaudacion",
        "titulo": "REP-09: Arqueo de recaudacion por estacion y perfil tarifario",
        "descripcion": "Consolida ingresos financieros y volumen de pasajes validados desglosados por estacion y tarifa.",
        "params": [
            {
                "key": "station_filter",
                "label": "Estacion:",
                "type": "combo",
                "source": "stations",
                "default": "(Todas)"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT TO_CHAR(CAST(vp.fecha_hora_ingreso AS DATE), 'YYYY-MM-DD') AS "Fecha",
                   e.nombre  AS "Estacion de Ingreso",
                   t.nombre  AS "Perfil Tarifa",
                   COUNT(vp.id_viaje_pasajero) AS "Pasajes Validados",
                   SUM(vp.monto_cobrado)       AS "Total Recaudado ($)"
            FROM VIAJE_PASAJERO vp
            JOIN ESTACION e ON vp.estacion_ingreso_id = e.id_estacion
            JOIN TARIFA t   ON vp.tarifa_id = t.id_tarifa
            """ + (
                " WHERE e.codigo = :st_code " if p.get("station_filter") and p.get("station_filter") != "(Todas)" else ""
            ) + """
            GROUP BY TO_CHAR(CAST(vp.fecha_hora_ingreso AS DATE), 'YYYY-MM-DD'), e.nombre, t.nombre
            ORDER BY "Fecha", "Estacion de Ingreso", "Total Recaudado ($)" DESC
            """,
            {"st_code": p.get("station_filter")} if p.get("station_filter") and p.get("station_filter") != "(Todas)" else {}
        )
    },
    10: {
        "codigo": "REP-10",
        "area": "Finanzas, Pasajeros y Recaudacion",
        "titulo": "REP-10: Ranking de estaciones por volumen de validaciones en torniquetes",
        "descripcion": "Jerarquiza las estaciones con mayor flujo de entrada segun registros de validacion en torniquetes.",
        "params": [
            {
                "key": "top_n",
                "label": "Limite de Estaciones (Top N):",
                "type": "number",
                "default": "10"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT e.nombre   AS "Estacion",
                   e.distrito AS "Distrito",
                   COUNT(vp.id_viaje_pasajero) AS "Total Pasajeros Validados"
            FROM ESTACION e
            JOIN VIAJE_PASAJERO vp ON e.id_estacion = vp.estacion_ingreso_id
            GROUP BY e.nombre, e.distrito
            ORDER BY "Total Pasajeros Validados" DESC
            FETCH FIRST :top_n ROWS ONLY
            """,
            {"top_n": int(p.get("top_n") or 10)}
        )
    },
    11: {
        "codigo": "REP-11",
        "area": "Finanzas, Pasajeros y Recaudacion",
        "titulo": "REP-11: Monitoreo de tarjetas OMNY bloqueadas o vencidas en red",
        "descripcion": "Audita el estado de tarjetas OMNY fuera de servicio, bloqueadas o con vigencia de contrato expirada.",
        "params": [
            {
                "key": "card_status",
                "label": "Estado Tarjeta:",
                "type": "combo",
                "options": ["(Todas irregulares/vencidas)", "Bloqueada", "Vencida", "Activa"],
                "default": "(Todas irregulares/vencidas)"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT t.numero_tarjeta        AS "Numero Tarjeta",
                   tar.nombre              AS "Perfil Tarifa",
                   NVL(p.nombre, '(Anonima)') AS "Pasajero Titular",
                   t.saldo_disponible      AS "Saldo ($)",
                   TO_CHAR(t.fecha_vencimiento, 'YYYY-MM-DD') AS "Vencimiento",
                   t.estado                AS "Estado Tarjeta"
            FROM TARJETA t
            JOIN TARIFA tar ON t.tarifa_id = tar.id_tarifa
            LEFT JOIN PASAJERO p ON t.pasajero_id = p.id_pasajero
            """ + (
                " WHERE t.estado = :status " if p.get("card_status") in ["Bloqueada", "Vencida", "Activa"] else
                " WHERE t.estado IN ('Bloqueada', 'Vencida') OR t.fecha_vencimiento < SYSDATE "
            ) + """
            ORDER BY t.estado, t.fecha_vencimiento
            """,
            {"status": p.get("card_status")} if p.get("card_status") in ["Bloqueada", "Vencida", "Activa"] else {}
        )
    },
    12: {
        "codigo": "REP-12",
        "area": "Flota, Mantenimiento e Incidentes",
        "titulo": "REP-12: Disponibilidad y estado operativo de flota de trenes",
        "descripcion": "Censa el inventario de material rodante clasificado por su condicion operativa y deposito base.",
        "params": [
            {
                "key": "status",
                "label": "Estado Operativo:",
                "type": "combo",
                "options": ["(Todos)", "Disponible", "En Operacion", "En Mantenimiento", "Fuera de Servicio", "Retirado"],
                "default": "Disponible"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT t.codigo_interno  AS "Codigo Tren",
                   m.nombre_modelo   AS "Modelo",
                   m.fabricante      AS "Fabricante",
                   NVL(d.nombre, 'Sin Deposito') AS "Deposito Base",
                   t.estado_operativo AS "Estado"
            FROM TREN t
            JOIN MODELO_TREN m  ON t.modelo_id = m.id_modelo
            LEFT JOIN DEPOSITO d ON t.deposito_id = d.id_deposito
            """ + (
                " WHERE t.estado_operativo = :status " if p.get("status") and p.get("status") != "(Todos)" else ""
            ) + """
            ORDER BY t.codigo_interno
            """,
            {"status": p.get("status")} if p.get("status") and p.get("status") != "(Todos)" else {}
        )
    },
    13: {
        "codigo": "REP-13",
        "area": "Flota, Mantenimiento e Incidentes",
        "titulo": "REP-13: Control de flota con inspeccion vencida o en taller correctivo",
        "descripcion": "Detecta unidades de tren que requieren inspeccion inmediata o estan asignadas a mantenimiento correctivo.",
        "params": [
            {
                "key": "filter_type",
                "label": "Condicion requerida:",
                "type": "combo",
                "options": ["(Todos)", "Solo En Taller (Mantenimiento)", "Solo Inspeccion Vencida"],
                "default": "(Todos)"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT t.codigo_interno  AS "Tren",
                   m.nombre_modelo   AS "Modelo",
                   t.kilometraje_acumulado AS "Kilometraje",
                   TO_CHAR(t.fecha_ultima_inspeccion, 'YYYY-MM-DD') AS "Ultima Insp.",
                   TO_CHAR(t.fecha_proxima_inspeccion, 'YYYY-MM-DD') AS "Proxima Insp.",
                   CASE 
                       WHEN t.estado_operativo = 'En Mantenimiento' THEN 'EN TALLER (Correctivo)'
                       WHEN t.fecha_proxima_inspeccion < SYSDATE    THEN 'VENCIDO - INSPECCIONAR'
                       ELSE 'Al Dia'
                   END AS "Condicion"
            FROM TREN t
            JOIN MODELO_TREN m ON t.modelo_id = m.id_modelo
            WHERE """ + (
                "t.estado_operativo = 'En Mantenimiento'" if p.get("filter_type") == "Solo En Taller (Mantenimiento)" else
                ("t.fecha_proxima_inspeccion < SYSDATE" if p.get("filter_type") == "Solo Inspeccion Vencida" else
                "(t.fecha_proxima_inspeccion < SYSDATE OR t.estado_operativo = 'En Mantenimiento')")
            ) + """
            ORDER BY t.fecha_proxima_inspeccion
            """,
            {}
        )
    },
    14: {
        "codigo": "REP-14",
        "area": "Flota, Mantenimiento e Incidentes",
        "titulo": "REP-14: Asignacion tecnica y roles en ordenes de mantenimiento",
        "descripcion": "Detalla tecnicos especialistas asignados y sus roles correspondientes en cada orden de trabajo.",
        "params": [
            {
                "key": "order_num",
                "label": "Numero de Orden:",
                "type": "combo",
                "source": "orders",
                "default": "(Todas)"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT om.numero_orden       AS "Orden Mantenimiento",
                   om.tipo_mantenimiento AS "Tipo",
                   eq.codigo_equipo      AS "Equipo",
                   e.nombre_completo     AS "Tecnico Especialista",
                   ot.rol_en_orden       AS "Rol Desempenado",
                   om.estado             AS "Estado Orden"
            FROM ORDEN_MANTENIMIENTO om
            JOIN EQUIPO eq        ON om.equipo_id = eq.id_equipo
            JOIN ORDEN_TECNICO ot ON om.id_orden = ot.orden_id
            JOIN EMPLEADO e       ON ot.empleado_id = e.id_empleado
            """ + (
                " WHERE om.numero_orden = :order_num " if p.get("order_num") and p.get("order_num") != "(Todas)" else ""
            ) + """
            ORDER BY om.numero_orden, e.nombre_completo
            """,
            {"order_num": p.get("order_num")} if p.get("order_num") and p.get("order_num") != "(Todas)" else {}
        )
    },
    15: {
        "codigo": "REP-15",
        "area": "Flota, Mantenimiento e Incidentes",
        "titulo": "REP-15: Auditoria de incidentes criticos y afectaciones en red",
        "descripcion": "Monitorea incidentes no resueltos, nivel de severidad y elementos afectados (estaciones, trenes o rutas).",
        "params": [
            {
                "key": "severity",
                "label": "Nivel de Severidad:",
                "type": "combo",
                "options": ["(Todas)", "Bajo", "Medio", "Alto", "Critico"],
                "default": "(Todas)"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT i.numero_incidente AS "Incidente",
                   i.tipo             AS "Tipo Incidente",
                   i.nivel_severidad  AS "Severidad",
                   TO_CHAR(i.fecha_hora_inicio, 'YYYY-MM-DD HH24:MI') AS "Fecha Inicio",
                   i.estado           AS "Estado",
                   NVL(e.nombre, NVL(t.codigo_interno, NVL(r.codigo, 'General de Red'))) AS "Elemento Afectado"
            FROM INCIDENTE i
            LEFT JOIN INCIDENTE_ELEMENTO_AFECTADO a ON i.id_incidente = a.incidente_id
            LEFT JOIN ESTACION e ON a.estacion_id = e.id_estacion
            LEFT JOIN TREN t     ON a.tren_id = t.id_tren
            LEFT JOIN RUTA r     ON a.ruta_id = r.id_ruta
            WHERE i.estado != 'Cerrado'
            """ + (
                " AND i.nivel_severidad = :sev " if p.get("severity") and p.get("severity") != "(Todas)" else ""
            ) + """
            ORDER BY i.fecha_hora_inicio DESC
            """,
            {"sev": p.get("severity")} if p.get("severity") and p.get("severity") != "(Todas)" else {}
        )
    }
}
