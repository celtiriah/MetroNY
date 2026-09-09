"""
Catalogue of the 15 Mandatory SQL Queries required by the Metro NY specification.
Supports dynamic parameter injection (stations, routes, dates, thresholds, severity).
"""

CONSULTAS_CATALOGO = {
    1: {
        "titulo": "1. Líneas que pasan por una estación",
        "descripcion": "¿Qué líneas pasan por una estación determinada? (Relación N:M entre Línea y Estación)",
        "params": [
            {
                "key": "station_code",
                "label": "Estación:",
                "type": "combo",
                "source": "stations",
                "default": "TSQ42"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT e.nombre AS "Estación",
                   e.codigo AS "Código Estación",
                   l.codigo AS "Línea",
                   l.nombre AS "Nombre de Línea",
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
        "titulo": "2. Paradas secuenciales de una ruta",
        "descripcion": "¿Cuáles son las estaciones de una ruta y en qué orden se visitan?",
        "params": [
            {
                "key": "route_code",
                "label": "Ruta:",
                "type": "combo",
                "source": "routes",
                "default": "RUT-1-SB"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT r.codigo         AS "Código Ruta",
                   r.sentido        AS "Sentido",
                   rd.orden_llegada AS "Secuencia",
                   e.nombre         AS "Estación",
                   e.distrito       AS "Distrito",
                   CASE rd.se_detiene WHEN 'S' THEN 'Sí (Parada)' ELSE 'Pasa Expreso' END AS "Detención"
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
        "titulo": "3. Estaciones de transferencia entre líneas",
        "descripcion": "¿Qué estaciones permiten transbordo entre líneas y cuál es el tiempo de caminata?",
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
            SELECT e.nombre AS "Estación de Conexión",
                   e.distrito AS "Distrito",
                   lo.codigo || ' (' || lo.color || ')' AS "Línea Origen",
                   ld.codigo || ' (' || ld.color || ')' AS "Línea Destino",
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
        "titulo": "4. Viajes programados para una fecha",
        "descripcion": "¿Qué viajes están asignados para una fecha con su tren y conductor?",
        "params": [
            {
                "key": "trip_date",
                "label": "Fecha (YYYY-MM-DD):",
                "type": "text",
                "default": "2026-09-01"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT vp.numero_viaje AS "Número Viaje",
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
        "titulo": "5. Viajes con retrasos mayores al umbral",
        "descripcion": "¿Qué viajes salieron con más de N minutos de demora según el horario programado?",
        "params": [
            {
                "key": "min_delay",
                "label": "Demora mínima (minutos):",
                "type": "number",
                "default": "15"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT vp.numero_viaje  AS "Número Viaje",
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
        "titulo": "6. Trenes por estado operativo",
        "descripcion": "¿Qué unidades de material rodante están operativas y listas para el servicio?",
        "params": [
            {
                "key": "status",
                "label": "Estado Operativo:",
                "type": "combo",
                "options": ["(Todos)", "Disponible", "En Operación", "En Mantenimiento", "Fuera de Servicio", "Retirado"],
                "default": "Disponible"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT t.codigo_interno  AS "Código Tren",
                   m.nombre_modelo   AS "Modelo",
                   m.fabricante      AS "Fabricante",
                   NVL(d.nombre, 'Sin Depósito') AS "Depósito Base",
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
    7: {
        "titulo": "7. Trenes con inspección vencida o en taller",
        "descripcion": "¿Qué trenes requieren mantenimiento preventivo inmediato o están en reparación?",
        "params": [
            {
                "key": "filter_type",
                "label": "Condición requerida:",
                "type": "combo",
                "options": ["(Todos)", "Solo En Taller (Mantenimiento)", "Solo Inspección Vencida"],
                "default": "(Todos)"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT t.codigo_interno  AS "Tren",
                   m.nombre_modelo   AS "Modelo",
                   t.kilometraje_acumulado AS "Kilometraje",
                   TO_CHAR(t.fecha_ultima_inspeccion, 'YYYY-MM-DD') AS "Última Insp.",
                   TO_CHAR(t.fecha_proxima_inspeccion, 'YYYY-MM-DD') AS "Próxima Insp.",
                   CASE 
                       WHEN t.estado_operativo = 'En Mantenimiento' THEN 'EN TALLER (Correctivo)'
                       WHEN t.fecha_proxima_inspeccion < SYSDATE    THEN 'VENCIDO - INSPECCIONAR'
                       ELSE 'Al Día'
                   END AS "Condición"
            FROM TREN t
            JOIN MODELO_TREN m ON t.modelo_id = m.id_modelo
            WHERE """ + (
                "t.estado_operativo = 'En Mantenimiento'" if p.get("filter_type") == "Solo En Taller (Mantenimiento)" else
                ("t.fecha_proxima_inspeccion < SYSDATE" if p.get("filter_type") == "Solo Inspección Vencida" else
                "(t.fecha_proxima_inspeccion < SYSDATE OR t.estado_operativo = 'En Mantenimiento')")
            ) + """
            ORDER BY t.fecha_proxima_inspeccion
            """,
            {}
        )
    },
    8: {
        "titulo": "8. Asignación de conductor y certificación por viaje",
        "descripcion": "¿Qué conductor operó cada viaje y cuál es su licencia de conducción MTA?",
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
    9: {
        "titulo": "9. Pasajeros transportados por línea",
        "descripcion": "¿Cuántos pasajeros utilizaron cada línea durante el período?",
        "params": [],
        "sql_generator": lambda p: (
            """
            SELECT l.codigo          AS "Línea",
                   l.nombre          AS "Nombre de la Línea",
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
    10: {
        "titulo": "10. Recaudación por fecha, estación y tarifa",
        "descripcion": "¿Cuánto dinero ingresó al sistema desglosado por estación y perfil de tarjeta?",
        "params": [
            {
                "key": "station_filter",
                "label": "Estación:",
                "type": "combo",
                "source": "stations",
                "default": "(Todas)"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT TO_CHAR(CAST(vp.fecha_hora_ingreso AS DATE), 'YYYY-MM-DD') AS "Fecha",
                   e.nombre  AS "Estación de Ingreso",
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
            ORDER BY "Fecha", "Estación de Ingreso", "Total Recaudado ($)" DESC
            """,
            {"st_code": p.get("station_filter")} if p.get("station_filter") and p.get("station_filter") != "(Todas)" else {}
        )
    },
    11: {
        "titulo": "11. Estaciones con mayor afluencia de pasajeros",
        "descripcion": "Ranking de estaciones con más ingresos de pasajeros registrados en torniquetes",
        "params": [
            {
                "key": "top_n",
                "label": "Límite de Estaciones (Top N):",
                "type": "number",
                "default": "10"
            }
        ],
        "sql_generator": lambda p: (
            """
            SELECT e.nombre   AS "Estación",
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
    12: {
        "titulo": "12. Incidentes abiertos en la red",
        "descripcion": "Incidentes no resueltos con su nivel de severidad y elemento de la red afectado",
        "params": [
            {
                "key": "severity",
                "label": "Nivel de Severidad:",
                "type": "combo",
                "options": ["(Todas)", "Bajo", "Medio", "Alto", "Crítico"],
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
    },
    13: {
        "titulo": "13. Líneas con más minutos de retraso acumulados",
        "descripcion": "Total de minutos perdidos por demoras operativas agrupados por línea",
        "params": [],
        "sql_generator": lambda p: (
            """
            SELECT l.codigo AS "Línea",
                   l.nombre AS "Nombre Línea",
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
    14: {
        "titulo": "14. Tarjetas OMNY bloqueadas o vencidas",
        "descripcion": "Tarjetas fuera de servicio o con fecha de vigencia anterior a hoy",
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
            SELECT t.numero_tarjeta        AS "Número Tarjeta",
                   tar.nombre              AS "Perfil Tarifa",
                   NVL(p.nombre, '(Anónima)') AS "Pasajero Titular",
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
    15: {
        "titulo": "15. Técnicos en órdenes de mantenimiento",
        "descripcion": "Detalle de técnicos asignados y rol desempeñado en cada trabajo de mantenimiento",
        "params": [
            {
                "key": "order_num",
                "label": "Número de Orden:",
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
                   e.nombre_completo     AS "Técnico Especialista",
                   ot.rol_en_orden       AS "Rol Desempeñado",
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
    }
}

