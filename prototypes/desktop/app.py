"""
Aplicación de Escritorio Nativa (PyQt5) - Sistema de Gestión del Metro de Nueva York (MTA NYCT).
Conexión directa a Oracle Database sin servidor web intermedio.
Soporte para Tema Claro (Por defecto) y Tema Oscuro.
"""
import sys
import os

# Asegurar que el directorio local esté en sys.path
sys.path.insert(0, os.path.dirname(__file__))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QComboBox, QPlainTextEdit, QGroupBox, QGridLayout,
    QHeaderView, QToolBar, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import db
from styles import LIGHT_THEME_QSS, DARK_THEME_QSS


class MetroDesktopApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self.setWindowTitle("MTA New York City Subway - Gestión Operativa (PyQt5)")
        self.resize(1150, 750)
        self.setMinimumSize(900, 600)

        # Configuración de interfaz
        self.init_ui()
        self.apply_theme("light")
        
        # Cargar datos iniciales desde Oracle
        self.refresh_all_data()

    def init_ui(self):
        # 1. Barra de herramientas superior
        toolbar = QToolBar("Barra Principal")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        title_lbl = QLabel("🚇 MTA New York City Transit")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 800; padding-right: 12px;")
        toolbar.addWidget(title_lbl)

        # Status badge
        self.status_lbl = QLabel("🟡 Conectando a Oracle...")
        self.status_lbl.setStyleSheet("font-weight: 600; padding: 4px 10px; border-radius: 4px; background: #e2e8f0;")
        toolbar.addWidget(self.status_lbl)

        # Espaciador
        spacer = QWidget()
        spacer.setSizePolicy(QWidget().sizePolicy().Expanding, QWidget().sizePolicy().Preferred)
        toolbar.addWidget(spacer)

        # Botón de alternancia de tema (Claro / Oscuro)
        self.theme_btn = QPushButton("🌙 Modo Oscuro")
        self.theme_btn.setObjectName("themeToggleBtn")
        self.theme_btn.clicked.connect(self.toggle_theme)
        toolbar.addWidget(self.theme_btn)

        # Botón de refrescar datos
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.clicked.connect(self.refresh_all_data)
        toolbar.addWidget(refresh_btn)

        # 2. Contenedor principal con pestañas
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Crear pestañas
        self.tab_dashboard = QWidget()
        self.tab_estaciones = QWidget()
        self.tab_consultas = QWidget()

        self.tabs.addTab(self.tab_dashboard, "📊 Panel General")
        self.tabs.addTab(self.tab_estaciones, "🚉 Estaciones del Sistema")
        self.tabs.addTab(self.tab_consultas, "🔍 15 Consultas Mínimas")

        self.build_dashboard_tab()
        self.build_stations_tab()
        self.build_queries_tab()

    # -------------------------------------------------------------------------
    # GESTION DE TEMAS (LIGHT / DARK)
    # -------------------------------------------------------------------------
    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        if theme_name == "dark":
            self.setStyleSheet(DARK_THEME_QSS)
            self.theme_btn.setText("☀️ Modo Claro")
        else:
            self.setStyleSheet(LIGHT_THEME_QSS)
            self.theme_btn.setText("🌙 Modo Oscuro")

    def toggle_theme(self):
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme(new_theme)

    # -------------------------------------------------------------------------
    # PESTAÑA 1: DASHBOARD
    # -------------------------------------------------------------------------
    def build_dashboard_tab(self):
        layout = QVBoxLayout(self.tab_dashboard)
        layout.setSpacing(16)

        # Grid de Tarjetas Métricas (KPIs)
        kpi_group = QGroupBox("Métricas Clave de la Red en Tiempo Real")
        kpi_layout = QGridLayout(kpi_group)

        self.kpi_labels = {}
        metrics = [
            ("TOTAL_LINEAS", "Líneas Activas", "🚇", 0, 0),
            ("TOTAL_ESTACIONES", "Estaciones", "🚉", 0, 1),
            ("TOTAL_TRENES", "Trenes en Flota", "🚆", 0, 2),
            ("TOTAL_EMPLEADOS", "Personal MTA", "👷", 1, 0),
            ("TOTAL_TARJETAS", "Tarjetas OMNY", "💳", 1, 1),
            ("INCIDENTES_ABIERTOS", "Incidentes Abiertos", "⚠️", 1, 2),
        ]

        for key, title, icon, r, c in metrics:
            card = QFrame()
            card.setStyleSheet("background: palette(alternate-base); border: 1px solid palette(mid); border-radius: 8px; padding: 10px;")
            card_layout = QVBoxLayout(card)
            
            lbl_title = QLabel(f"{icon} {title}")
            lbl_title.setStyleSheet("font-size: 11px; font-weight: 700; color: palette(text); text-transform: uppercase;")
            
            lbl_val = QLabel("-")
            lbl_val.setStyleSheet("font-size: 24px; font-weight: 800; color: #0039A6; padding-top: 4px;")
            self.kpi_labels[key] = lbl_val
            
            card_layout.addWidget(lbl_title)
            card_layout.addWidget(lbl_val)
            kpi_layout.addWidget(card, r, c)

        layout.addWidget(kpi_group)

        # Tabla de líneas de metro
        lines_group = QGroupBox("Líneas Principales del Metro de Nueva York")
        lines_layout = QVBoxLayout(lines_group)

        self.table_lines = QTableWidget()
        self.table_lines.setColumnCount(6)
        self.table_lines.setHorizontalHeaderLabels([
            "Código", "Nombre de Línea", "Color Oficial", "Servicio Principal", "Estado", "Estaciones"
        ])
        self.table_lines.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_lines.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_lines.setSelectionBehavior(QTableWidget.SelectRows)
        lines_layout.addWidget(self.table_lines)

        layout.addWidget(lines_group)

    # -------------------------------------------------------------------------
    # PESTAÑA 2: ESTACIONES CON BUSCADOR EN VIVO
    # -------------------------------------------------------------------------
    def build_stations_tab(self):
        layout = QVBoxLayout(self.tab_estaciones)
        layout.setSpacing(12)

        # Barra de búsqueda
        search_layout = QHBoxLayout()
        search_lbl = QLabel("🔍 Buscar:")
        search_lbl.setStyleSheet("font-weight: 700;")
        self.station_search_input = QLineEdit()
        self.station_search_input.setPlaceholderText("Escribe para filtrar por nombre, código o distrito (Manhattan, Brooklyn, etc.)...")
        self.station_search_input.textChanged.connect(self.filter_stations_table)
        
        search_layout.addWidget(search_lbl)
        search_layout.addWidget(self.station_search_input)
        layout.addLayout(search_layout)

        # Tabla de estaciones
        self.table_stations = QTableWidget()
        self.table_stations.setColumnCount(7)
        self.table_stations.setHorizontalHeaderLabels([
            "Código", "Nombre de Estación", "Distrito (Borough)", "Plataformas", "Accesible (ADA)", "Elevadores", "Estado"
        ])
        self.table_stations.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_stations.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_stations.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table_stations)

    def filter_stations_table(self, text):
        query = text.strip().lower()
        rows = self.table_stations.rowCount()
        for r in range(rows):
            match = False
            for c in range(self.table_stations.columnCount()):
                item = self.table_stations.item(r, c)
                if item and query in item.text().lower():
                    match = True
                    break
            self.table_stations.setRowHidden(r, not match)

    # -------------------------------------------------------------------------
    # PESTAÑA 3: 15 CONSULTAS MINIMAS OBLIGATORIAS
    # -------------------------------------------------------------------------
    def build_queries_tab(self):
        layout = QVBoxLayout(self.tab_consultas)
        layout.setSpacing(12)

        # Selector de consultas y botón
        controls_group = QGroupBox("Selección y Ejecución de Consultas Mínimas (1-15)")
        controls_layout = QVBoxLayout(controls_group)

        select_layout = QHBoxLayout()
        self.query_combo = QComboBox()
        for qid, q in db.CONSULTAS_CATALOGO.items():
            self.query_combo.addItem(f"{q['titulo']}", qid)
        self.query_combo.currentIndexChanged.connect(self.on_query_selected)

        run_btn = QPushButton("▶ Ejecutar en Oracle")
        run_btn.setStyleSheet("font-weight: 700; padding: 8px 24px;")
        run_btn.clicked.connect(self.run_current_query)

        select_layout.addWidget(self.query_combo, stretch=4)
        select_layout.addWidget(run_btn, stretch=1)
        controls_layout.addLayout(select_layout)

        # Descripción y visor de SQL
        self.query_desc_lbl = QLabel()
        self.query_desc_lbl.setStyleSheet("font-weight: 600; color: #2563eb; padding-top: 6px;")
        controls_layout.addWidget(self.query_desc_lbl)

        self.sql_viewer = QPlainTextEdit()
        self.sql_viewer.setReadOnly(True)
        self.sql_viewer.setMaximumHeight(90)
        self.sql_viewer.setFont(QFont("Consolas", 10))
        controls_layout.addWidget(self.sql_viewer)

        layout.addWidget(controls_group)

        # Tabla de resultados
        results_group = QGroupBox("Resultados de la Consulta")
        results_layout = QVBoxLayout(results_group)

        self.query_results_count = QLabel("0 filas recuperadas")
        self.query_results_count.setStyleSheet("font-size: 11px; font-weight: 700; color: palette(mid);")
        results_layout.addWidget(self.query_results_count)

        self.table_results = QTableWidget()
        self.table_results.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_results.setSelectionBehavior(QTableWidget.SelectRows)
        results_layout.addWidget(self.table_results)

        layout.addWidget(results_group)

        # Cargar primera consulta por defecto
        self.on_query_selected(0)

    def on_query_selected(self, index):
        qid = self.query_combo.currentData()
        if qid in db.CONSULTAS_CATALOGO:
            qinfo = db.CONSULTAS_CATALOGO[qid]
            self.query_desc_lbl.setText(f"Objetivo: {qinfo['descripcion']}")
            self.sql_viewer.setPlainText(qinfo['sql'].strip())

    def run_current_query(self):
        qid = self.query_combo.currentData()
        if not qid or qid not in db.CONSULTAS_CATALOGO:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            res = db.execute_query(db.CONSULTAS_CATALOGO[qid]["sql"])
            columns = res["columns"]
            rows = res["rows"]

            self.table_results.clear()
            self.table_results.setColumnCount(len(columns))
            self.table_results.setRowCount(len(rows))
            self.table_results.setHorizontalHeaderLabels(columns)

            for r, row in enumerate(rows):
                for c, col in enumerate(columns):
                    val = str(row.get(col, "-"))
                    self.table_results.setItem(r, c, QTableWidgetItem(val))

            self.table_results.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.query_results_count.setText(f"✅ {len(rows)} filas devueltas por Oracle ({res.get('pdb', 'FREEPDB1')})")
        except Exception as e:
            QMessageBox.critical(self, "Error de Oracle", f"Fallo al ejecutar la consulta:\n{e}")
        finally:
            QApplication.restoreOverrideCursor()

    # -------------------------------------------------------------------------
    # CARGA DE DATOS DESDE ORACLE
    # -------------------------------------------------------------------------
    def refresh_all_data(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            # 1. Verificar estado de Oracle
            res_test = db.execute_query("SELECT 1 FROM DUAL")
            pdb_name = res_test.get("pdb", "FREEPDB1")
            self.status_lbl.setText(f"🟢 Oracle Activo ({pdb_name}) | METRO_NY")
            self.status_lbl.setStyleSheet("font-weight: 700; padding: 4px 10px; border-radius: 4px; background: rgba(16, 185, 129, 0.15); color: #059669;")

            # 2. KPIs
            sql_kpis = """
                SELECT 
                    (SELECT COUNT(*) FROM LINEA) AS TOTAL_LINEAS,
                    (SELECT COUNT(*) FROM ESTACION) AS TOTAL_ESTACIONES,
                    (SELECT COUNT(*) FROM TREN) AS TOTAL_TRENES,
                    (SELECT COUNT(*) FROM EMPLEADO) AS TOTAL_EMPLEADOS,
                    (SELECT COUNT(*) FROM TARJETA) AS TOTAL_TARJETAS,
                    (SELECT COUNT(*) FROM INCIDENTE WHERE estado != 'Cerrado') AS INCIDENTES_ABIERTOS
                FROM DUAL
            """
            kpis = db.execute_query(sql_kpis)["rows"][0]
            for key, lbl in self.kpi_labels.items():
                lbl.setText(str(kpis.get(key, "-")))

            # 3. Líneas
            sql_lines = """
                SELECT l.codigo, l.nombre, l.color, l.tipo_servicio_principal, l.estado_operativo,
                       COUNT(le.estacion_id) AS estaciones
                FROM LINEA l
                LEFT JOIN LINEA_ESTACION le ON l.id_linea = le.linea_id
                GROUP BY l.codigo, l.nombre, l.color, l.tipo_servicio_principal, l.estado_operativo
                ORDER BY l.codigo
            """
            lines_data = db.execute_query(sql_lines)["rows"]
            self.table_lines.setRowCount(len(lines_data))
            for r, row in enumerate(lines_data):
                self.table_lines.setItem(r, 0, QTableWidgetItem(str(row["CODIGO"])))
                self.table_lines.setItem(r, 1, QTableWidgetItem(str(row["NOMBRE"])))
                self.table_lines.setItem(r, 2, QTableWidgetItem(str(row["COLOR"])))
                self.table_lines.setItem(r, 3, QTableWidgetItem(str(row["TIPO_SERVICIO_PRINCIPAL"])))
                self.table_lines.setItem(r, 4, QTableWidgetItem(str(row["ESTADO_OPERATIVO"])))
                self.table_lines.setItem(r, 5, QTableWidgetItem(f"{row['ESTACIONES']} paradas"))

            # 4. Estaciones
            sql_stations = """
                SELECT e.codigo, e.nombre, e.distrito, 
                       NVL(e.cantidad_plataformas, 2) AS plataformas,
                       e.accesible_discapacidad, e.elevadores_disponibles, e.estado_operativo
                FROM ESTACION e
                ORDER BY e.distrito, e.nombre
            """
            st_data = db.execute_query(sql_stations)["rows"]
            self.table_stations.setRowCount(len(st_data))
            for r, row in enumerate(st_data):
                self.table_stations.setItem(r, 0, QTableWidgetItem(str(row["CODIGO"])))
                self.table_stations.setItem(r, 1, QTableWidgetItem(str(row["NOMBRE"])))
                self.table_stations.setItem(r, 2, QTableWidgetItem(str(row["DISTRITO"])))
                self.table_stations.setItem(r, 3, QTableWidgetItem(str(row["PLATAFORMAS"])))
                ada = "♿ Sí (ADA)" if row["ACCESIBLE_DISCAPACIDAD"] == "S" else "No"
                self.table_stations.setItem(r, 4, QTableWidgetItem(ada))
                elev = "✅ Sí" if row["ELEVADORES_DISPONIBLES"] == "S" else "❌ No"
                self.table_stations.setItem(r, 5, QTableWidgetItem(elev))
                self.table_stations.setItem(r, 6, QTableWidgetItem(str(row["ESTADO_OPERATIVO"])))

        except Exception as e:
            self.status_lbl.setText("🔴 Error de conexión a Oracle")
            self.status_lbl.setStyleSheet("font-weight: 700; padding: 4px 10px; border-radius: 4px; background: rgba(239, 68, 68, 0.15); color: #dc2626;")
            QMessageBox.warning(self, "Conexión a Oracle", f"No se pudo conectar a la base de datos:\n{e}")
        finally:
            QApplication.restoreOverrideCursor()


def main():
    app = QApplication(sys.argv)
    window = MetroDesktopApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
