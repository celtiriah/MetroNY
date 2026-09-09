"""
Staff Interface - Operational personnel, job titles, supervisory chain, and MTA certifications.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHeaderView, QTableWidgetItem
from qfluentwidgets import TitleLabel, SubtitleLabel, SearchLineEdit, TableWidget


class StaffInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("staffInterface")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = TitleLabel("Personal Operativo y Turnos", self)
        subtitle = SubtitleLabel("Gestión de empleados de la MTA, cargos, turnos laborales y licencias de conducción", self)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Search Bar
        self.search_input = SearchLineEdit(self)
        self.search_input.setPlaceholderText("Buscar empleado por nombre, número de nómina, cargo o turno...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.filter_staff)
        layout.addWidget(self.search_input)

        # Table
        self.table_staff = TableWidget(self)
        self.table_staff.setBorderVisible(True)
        self.table_staff.setColumnCount(7)
        self.table_staff.setHorizontalHeaderLabels([
            "Nº Empleado", "Nombre Completo", "Cargo", "Turno", "Supervisor Directo", "Licencia MTA", "Estado"
        ])
        self.table_staff.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_staff.setEditTriggers(TableWidget.NoEditTriggers)
        self.table_staff.setSelectionBehavior(TableWidget.SelectRows)
        layout.addWidget(self.table_staff)

    def update_staff(self, staff: list):
        self.table_staff.setRowCount(len(staff))
        for r, row in enumerate(staff):
            self.table_staff.setItem(r, 0, QTableWidgetItem(str(row.get("NUMERO_EMPLEADO", "-"))))
            self.table_staff.setItem(r, 1, QTableWidgetItem(str(row.get("NOMBRE_COMPLETO", "-"))))
            self.table_staff.setItem(r, 2, QTableWidgetItem(str(row.get("CARGO", "-"))))
            self.table_staff.setItem(r, 3, QTableWidgetItem(str(row.get("TURNO", "-"))))
            self.table_staff.setItem(r, 4, QTableWidgetItem(str(row.get("SUPERVISOR", "-"))))
            self.table_staff.setItem(r, 5, QTableWidgetItem(str(row.get("CERTIFICACION", "-"))))
            self.table_staff.setItem(r, 6, QTableWidgetItem(str(row.get("ESTADO_LABORAL", "-"))))

    def filter_staff(self, text: str):
        query = text.strip().lower()
        rows = self.table_staff.rowCount()
        for r in range(rows):
            match = False
            for c in range(self.table_staff.columnCount()):
                item = self.table_staff.item(r, c)
                if item and query in item.text().lower():
                    match = True
                    break
            self.table_staff.setRowHidden(r, not match)

