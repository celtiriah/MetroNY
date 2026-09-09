"""
Incidents Interface - Operational incidents log, severity levels, and affected network assets.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidgetItem
from qfluentwidgets import TitleLabel, SubtitleLabel, ComboBox, TableWidget, CaptionLabel


class IncidentsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("incidentsInterface")
        self.incidents_data = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = TitleLabel("Incidentes Operativos y Contingencias", self)
        subtitle = SubtitleLabel("Monitoreo de anomalías en la red, niveles de severidad y elementos de infraestructura afectados", self)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(CaptionLabel("Filtrar por severidad:", self))
        self.combo_filter = ComboBox(self)
        self.combo_filter.addItems(["(Todas)", "Bajo", "Medio", "Alto", "Crítico"])
        self.combo_filter.currentTextChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.combo_filter)
        filter_layout.addStretch(1)
        layout.addLayout(filter_layout)

        # Table
        self.table_incidents = TableWidget(self)
        self.table_incidents.setBorderVisible(True)
        self.table_incidents.setColumnCount(7)
        self.table_incidents.setHorizontalHeaderLabels([
            "Nº Incidente", "Tipo", "Severidad", "Elemento Afectado", "Fecha Inicio", "Estado", "Descripción"
        ])
        self.table_incidents.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_incidents.setEditTriggers(TableWidget.NoEditTriggers)
        self.table_incidents.setSelectionBehavior(TableWidget.SelectRows)
        layout.addWidget(self.table_incidents)

    def update_incidents(self, incidents: list):
        self.incidents_data = incidents
        self.apply_filter(self.combo_filter.currentText())

    def apply_filter(self, severity: str):
        filtered = self.incidents_data if severity == "(Todas)" else [
            inc for inc in self.incidents_data if inc.get("NIVEL_SEVERIDAD") == severity
        ]
        self.table_incidents.setRowCount(len(filtered))
        for r, row in enumerate(filtered):
            self.table_incidents.setItem(r, 0, QTableWidgetItem(str(row.get("NUMERO_INCIDENTE", "-"))))
            self.table_incidents.setItem(r, 1, QTableWidgetItem(str(row.get("TIPO", "-"))))
            self.table_incidents.setItem(r, 2, QTableWidgetItem(str(row.get("NIVEL_SEVERIDAD", "-"))))
            self.table_incidents.setItem(r, 3, QTableWidgetItem(str(row.get("ELEMENTO_AFECTADO", "-"))))
            self.table_incidents.setItem(r, 4, QTableWidgetItem(str(row.get("INICIO", "-"))))
            self.table_incidents.setItem(r, 5, QTableWidgetItem(str(row.get("ESTADO", "-"))))
            self.table_incidents.setItem(r, 6, QTableWidgetItem(str(row.get("DESCRIPCION", "-"))))

