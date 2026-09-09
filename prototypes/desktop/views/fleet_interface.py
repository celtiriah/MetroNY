"""
Fleet Interface - Train fleet inventory, operational status, and maintenance inspections.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidgetItem
from qfluentwidgets import TitleLabel, SubtitleLabel, ComboBox, TableWidget, CaptionLabel


class FleetInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("fleetInterface")
        self.fleet_data = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = TitleLabel("Flota de Trenes y Mantenimiento", self)
        subtitle = SubtitleLabel("Inventario de material rodante, depósitos asignados y calendario de inspección técnica", self)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(CaptionLabel("Filtrar por estado operativo:", self))
        self.combo_filter = ComboBox(self)
        self.combo_filter.addItems(["(Todos)", "Disponible", "En Operación", "En Mantenimiento", "Fuera de Servicio"])
        self.combo_filter.currentTextChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.combo_filter)
        filter_layout.addStretch(1)
        layout.addLayout(filter_layout)

        # Table
        self.table_fleet = TableWidget(self)
        self.table_fleet.setBorderVisible(True)
        self.table_fleet.setColumnCount(8)
        self.table_fleet.setHorizontalHeaderLabels([
            "Código Tren", "Modelo", "Fabricante", "Depósito Base",
            "Kilometraje", "Estado Operativo", "Última Insp.", "Próxima Insp."
        ])
        self.table_fleet.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_fleet.setEditTriggers(TableWidget.NoEditTriggers)
        self.table_fleet.setSelectionBehavior(TableWidget.SelectRows)
        layout.addWidget(self.table_fleet)

    def update_fleet(self, fleet: list):
        self.fleet_data = fleet
        self.apply_filter(self.combo_filter.currentText())

    def apply_filter(self, status: str):
        filtered = self.fleet_data if status == "(Todos)" else [
            t for t in self.fleet_data if t.get("ESTADO_OPERATIVO") == status
        ]
        self.table_fleet.setRowCount(len(filtered))
        for r, row in enumerate(filtered):
            self.table_fleet.setItem(r, 0, QTableWidgetItem(str(row.get("CODIGO_INTERNO", "-"))))
            self.table_fleet.setItem(r, 1, QTableWidgetItem(str(row.get("NOMBRE_MODELO", "-"))))
            self.table_fleet.setItem(r, 2, QTableWidgetItem(str(row.get("FABRICANTE", "-"))))
            self.table_fleet.setItem(r, 3, QTableWidgetItem(str(row.get("DEPOSITO", "-"))))
            km = row.get("KILOMETRAJE_ACUMULADO", "0")
            self.table_fleet.setItem(r, 4, QTableWidgetItem(f"{km} km"))
            self.table_fleet.setItem(r, 5, QTableWidgetItem(str(row.get("ESTADO_OPERATIVO", "-"))))
            self.table_fleet.setItem(r, 6, QTableWidgetItem(str(row.get("ULTIMA_INSP", "-"))))
            self.table_fleet.setItem(r, 7, QTableWidgetItem(str(row.get("PROXIMA_INSP", "-"))))

