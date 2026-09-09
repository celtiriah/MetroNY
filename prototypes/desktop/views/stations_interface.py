"""
Stations Interface - Station directory with live search and ADA accessibility attributes.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHeaderView, QTableWidgetItem
from qfluentwidgets import TitleLabel, SubtitleLabel, SearchLineEdit, TableWidget


class StationsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("stationsInterface")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = TitleLabel("Estaciones del Sistema", self)
        subtitle = SubtitleLabel("Directorio de estaciones de la red con plataformas y accesibilidad ADA", self)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Search Bar
        self.search_input = SearchLineEdit(self)
        self.search_input.setPlaceholderText("Buscar estación por nombre, código o distrito (Manhattan, Brooklyn, Queens)...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.filter_stations)
        layout.addWidget(self.search_input)

        # Table
        self.table_stations = TableWidget(self)
        self.table_stations.setBorderVisible(True)
        self.table_stations.setColumnCount(7)
        self.table_stations.setHorizontalHeaderLabels([
            "Código", "Nombre de Estación", "Distrito (Borough)", "Plataformas", "Accesible (ADA)", "Elevadores", "Estado"
        ])
        self.table_stations.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_stations.setEditTriggers(TableWidget.NoEditTriggers)
        self.table_stations.setSelectionBehavior(TableWidget.SelectRows)
        layout.addWidget(self.table_stations)

    def update_stations(self, stations: list):
        self.table_stations.setRowCount(len(stations))
        for r, row in enumerate(stations):
            self.table_stations.setItem(r, 0, QTableWidgetItem(str(row.get("CODIGO", "-"))))
            self.table_stations.setItem(r, 1, QTableWidgetItem(str(row.get("NOMBRE", "-"))))
            self.table_stations.setItem(r, 2, QTableWidgetItem(str(row.get("DISTRITO", "-"))))
            self.table_stations.setItem(r, 3, QTableWidgetItem(str(row.get("PLATAFORMAS", "-"))))
            ada = "♿ Sí (ADA)" if row.get("ACCESIBLE_DISCAPACIDAD") == "S" else "No"
            self.table_stations.setItem(r, 4, QTableWidgetItem(ada))
            elev = "✅ Sí" if row.get("ELEVADORES_DISPONIBLES") == "S" else "❌ No"
            self.table_stations.setItem(r, 5, QTableWidgetItem(elev))
            self.table_stations.setItem(r, 6, QTableWidgetItem(str(row.get("ESTADO_OPERATIVO", "-"))))

    def filter_stations(self, text: str):
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

