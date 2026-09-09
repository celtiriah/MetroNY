"""
Dashboard Interface - Overview of network status, KPIs, and active lines.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QHeaderView, QTableWidgetItem
from qfluentwidgets import TitleLabel, SubtitleLabel, StrongBodyLabel, TableWidget
from components.stat_card import StatCard
from components.status_card import StatusCard


class DashboardInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("dashboardInterface")
        self.kpi_cards = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        title = TitleLabel("MTA New York City Subway", self)
        subtitle = SubtitleLabel("Panel Operativo de Gestión de Red (Oracle Database)", self)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Connection Banner
        self.status_card = StatusCard(self)
        layout.addWidget(self.status_card)

        # 6 KPI Metric Cards
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(12)

        metrics = [
            ("TOTAL_LINEAS", "Líneas Activas", "🚇", 0, 0),
            ("TOTAL_ESTACIONES", "Estaciones", "🚉", 0, 1),
            ("TOTAL_TRENES", "Trenes en Flota", "🚆", 0, 2),
            ("TOTAL_EMPLEADOS", "Personal MTA", "👷", 1, 0),
            ("TOTAL_TARJETAS", "Tarjetas OMNY", "💳", 1, 1),
            ("INCIDENTES_ABIERTOS", "Incidentes Abiertos", "⚠️", 1, 2),
        ]

        for key, title_text, icon, r, c in metrics:
            card = StatCard(title_text, icon, "-", self)
            self.kpi_cards[key] = card
            kpi_grid.addWidget(card, r, c)

        layout.addLayout(kpi_grid)

        # Lines Table
        layout.addWidget(StrongBodyLabel("Líneas Principales del Metro", self))
        self.table_lines = TableWidget(self)
        self.table_lines.setBorderVisible(True)
        self.table_lines.setColumnCount(6)
        self.table_lines.setHorizontalHeaderLabels([
            "Código", "Nombre Oficial", "Color", "Servicio Principal", "Estado", "Estaciones"
        ])
        self.table_lines.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_lines.setEditTriggers(TableWidget.NoEditTriggers)
        self.table_lines.setSelectionBehavior(TableWidget.SelectRows)
        layout.addWidget(self.table_lines)

    def update_kpis(self, kpis: dict):
        for key, card in self.kpi_cards.items():
            card.set_value(kpis.get(key, "-"))

    def update_lines(self, lines: list):
        self.table_lines.setRowCount(len(lines))
        for r, row in enumerate(lines):
            self.table_lines.setItem(r, 0, QTableWidgetItem(str(row.get("CODIGO", "-"))))
            self.table_lines.setItem(r, 1, QTableWidgetItem(str(row.get("NOMBRE", "-"))))
            self.table_lines.setItem(r, 2, QTableWidgetItem(str(row.get("COLOR", "-"))))
            self.table_lines.setItem(r, 3, QTableWidgetItem(str(row.get("TIPO_SERVICIO_PRINCIPAL", "-"))))
            self.table_lines.setItem(r, 4, QTableWidgetItem(str(row.get("ESTADO_OPERATIVO", "-"))))
            self.table_lines.setItem(r, 5, QTableWidgetItem(f"{row.get('ESTACIONES', 0)} paradas"))

