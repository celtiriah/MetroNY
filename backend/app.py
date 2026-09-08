"""
Servidor API REST y Servidor Web Estático para Metro NY.
Sirve el frontend HTML/CSS/JS y responde a peticiones a Oracle Database.
"""
import os
import sys
from flask import Flask, jsonify, send_from_directory, request

# Asegurar que el directorio raíz esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.db import execute_query, CONSULTAS_CATALOGO, DB_USER, DB_HOST, DB_PORT

# Directorio del frontend
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

app = Flask(__name__, static_folder=FRONTEND_DIR)


# -----------------------------------------------------------------------------
# RUTAS DE FRONTEND (Servir HTML, CSS, JS)
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(FRONTEND_DIR, path)


# -----------------------------------------------------------------------------
# RUTAS DE API REST
# -----------------------------------------------------------------------------
@app.route("/api/status")
def get_status():
    """Estado del servidor y conexión a Oracle."""
    try:
        data = execute_query("SELECT 1 AS TEST FROM DUAL")
        return jsonify({
            "status": "online",
            "database": "Oracle Database",
            "host": DB_HOST,
            "port": DB_PORT,
            "user": DB_USER,
            "pdb": data.get("pdb"),
            "connected": True
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "connected": False,
            "error": str(e)
        }), 500


@app.route("/api/resumen")
def get_resumen():
    """Estadísticas generales de la red en tiempo real."""
    try:
        sql = """
            SELECT 
                (SELECT COUNT(*) FROM LINEA) AS TOTAL_LINEAS,
                (SELECT COUNT(*) FROM ESTACION) AS TOTAL_ESTACIONES,
                (SELECT COUNT(*) FROM TREN) AS TOTAL_TRENES,
                (SELECT COUNT(*) FROM EMPLEADO) AS TOTAL_EMPLEADOS,
                (SELECT COUNT(*) FROM TARJETA) AS TOTAL_TARJETAS,
                (SELECT COUNT(*) FROM INCIDENTE WHERE estado != 'Cerrado') AS INCIDENTES_ABIERTOS
            FROM DUAL
        """
        res = execute_query(sql)
        return jsonify(res["rows"][0] if res["rows"] else {})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/lineas")
def get_lineas():
    """Lista las líneas del metro con información detallada."""
    try:
        sql = """
            SELECT l.id_linea,
                   l.codigo,
                   l.nombre,
                   l.color,
                   l.tipo_servicio_principal AS tipo_servicio,
                   l.estado_operativo,
                   COUNT(le.estacion_id) AS total_estaciones
            FROM LINEA l
            LEFT JOIN LINEA_ESTACION le ON l.id_linea = le.linea_id
            GROUP BY l.id_linea, l.codigo, l.nombre, l.color, l.tipo_servicio_principal, l.estado_operativo
            ORDER BY l.codigo
        """
        return jsonify(execute_query(sql))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/estaciones")
def get_estaciones():
    """Lista todas las estaciones de la red."""
    try:
        sql = """
            SELECT e.id_estacion,
                   e.codigo,
                   e.nombre,
                   e.distrito,
                   e.accesible_discapacidad AS accesibilidad,
                   e.elevadores_disponibles,
                   e.estado_operativo,
                   NVL(e.cantidad_plataformas, (SELECT COUNT(*) FROM PLATAFORMA p WHERE p.estacion_id = e.id_estacion)) AS total_plataformas
            FROM ESTACION e
            ORDER BY e.distrito, e.nombre
        """
        return jsonify(execute_query(sql))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/consultas")
def list_consultas():
    """Catálogo de las 15 consultas mínimas obligatorias."""
    lista = [
        {"id": qid, "titulo": q["titulo"], "descripcion": q["descripcion"]}
        for qid, q in CONSULTAS_CATALOGO.items()
    ]
    return jsonify(lista)


@app.route("/api/consultas/<int:qid>")
def run_consulta(qid):
    """Ejecuta una de las 15 consultas del catálogo y retorna filas tabulares."""
    if qid not in CONSULTAS_CATALOGO:
        return jsonify({"error": f"Consulta #{qid} no existe. El rango es 1-15."}), 404

    qinfo = CONSULTAS_CATALOGO[qid]
    try:
        resultado = execute_query(qinfo["sql"])
        return jsonify({
            "id": qid,
            "titulo": qinfo["titulo"],
            "descripcion": qinfo["descripcion"],
            "sql": qinfo["sql"].strip(),
            "columns": resultado["columns"],
            "rows": resultado["rows"],
            "total": resultado["total"],
            "pdb": resultado.get("pdb")
        })
    except Exception as e:
        return jsonify({
            "id": qid,
            "titulo": qinfo["titulo"],
            "error": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"==================================================")
    print(f"  MetroNY - Servidor Web & API Activo")
    print(f"  URL Local: http://localhost:{port}")
    print(f"==================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
