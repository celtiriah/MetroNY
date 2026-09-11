"""
Fleet Interface - Train fleet inventory, operational status, and maintenance inspections.
Includes interactive work order creation to dispatch trains to maintenance shops.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidgetItem
)
from PyQt5.QtCore import Qt

from qfluentwidgets import (
    TitleLabel, SubtitleLabel, CaptionLabel, ComboBox, TableWidget,
    PrimaryPushButton, LineEdit, MessageBoxBase, InfoBar, InfoBarPosition,
    FluentIcon as FIF
)

from services import metro_service, actions_service


class CrearOrdenMantenimientoDialog(MessageBoxBase):
    """
    Diálogo modal Fluent para enviar material rodante o equipos a taller de mantenimiento.
    """
    def __init__(self, preselected_equipo_id=None, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("Crear Orden de Mantenimiento / Taller", self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        # 1. Equipo / Tren a Intervenir
        self.viewLayout.addWidget(CaptionLabel("Activo / Unidad a Intervenir:", self))
        self.combo_equipo = ComboBox(self)
        equipos = actions_service.get_equipos_combo()
        target_idx = 0
        for i, (eq_id, label) in enumerate(equipos):
            self.combo_equipo.addItem(label, userData=eq_id)
            if preselected_equipo_id and eq_id == preselected_equipo_id:
                target_idx = i
        self.combo_equipo.setCurrentIndex(target_idx)
        self.viewLayout.addWidget(self.combo_equipo)

        # 2. Tipo de Mantenimiento
        self.viewLayout.addWidget(CaptionLabel("Tipo de Mantenimiento:", self))
        self.combo_tipo = ComboBox(self)
        self.combo_tipo.addItems(["Preventivo", "Correctivo", "Predictivo", "Inspección de Seguridad"])
        self.viewLayout.addWidget(self.combo_tipo)

        # 3. Prioridad
        self.viewLayout.addWidget(CaptionLabel("Nivel de Prioridad:", self))
        self.combo_prioridad = ComboBox(self)
        self.combo_prioridad.addItems(["Media", "Alta", "Urgente", "Baja"])
        self.viewLayout.addWidget(self.combo_prioridad)

        # 4. Técnico Líder Responsable
        self.viewLayout.addWidget(CaptionLabel("Técnico Asignado (Líder de Reparación):", self))
        self.combo_tecnico = ComboBox(self)
        tecnicos = actions_service.get_tecnicos_combo()
        for tec_id, label in tecnicos:
            self.combo_tecnico.addItem(label, userData=tec_id)
        self.viewLayout.addWidget(self.combo_tecnico)

        # 5. Descripción del Trabajo
        self.viewLayout.addWidget(CaptionLabel("Descripción del Trabajo / Falla Reportada:", self))
        self.txt_desc = LineEdit(self)
        self.txt_desc.setPlaceholderText("p.ej. Torneado de ruedas y sustitución de zapatas de freno...")
        self.viewLayout.addWidget(self.txt_desc)

        # Botones
        self.yesButton.setText("Crear Orden de Trabajo")
        self.cancelButton.setText("Cancelar")


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
        subtitle = SubtitleLabel(
            "Inventario de material rodante, depósitos asignados y calendario de inspección técnica", self
        )
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Barra de Filtros y Acciones
        actions_bar = QHBoxLayout()
        actions_bar.setSpacing(10)

        actions_bar.addWidget(CaptionLabel("Filtrar por estado operativo:", self))
        self.combo_filter = ComboBox(self)
        self.combo_filter.addItems(["(Todos)", "Disponible", "En Operación", "En Mantenimiento", "Fuera de Servicio"])
        self.combo_filter.currentTextChanged.connect(self.apply_filter)
        actions_bar.addWidget(self.combo_filter)

        actions_bar.addStretch(1)

        self.btn_send_maint = PrimaryPushButton("Enviar Unidad a Taller", self, FIF.ADD)
        self.btn_send_maint.clicked.connect(self.open_maintenance_dialog)
        actions_bar.addWidget(self.btn_send_maint)

        layout.addLayout(actions_bar)

        # Table
        self.table_fleet = TableWidget(self)
        self.table_fleet.setBorderVisible(True)
        self.table_fleet.setColumnCount(8)
        self.table_fleet.setHorizontalHeaderLabels([
            "Código Tren", "Modelo", "Fabricante", "Depósito Base",
            "Kilometraje", "Estado Operativo", "Última Insp.", "Próxima Insp."
        ])
        header = self.table_fleet.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.Stretch)
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
            self.table_fleet.setItem(r, 1, QTableWidgetItem(str(row.get("MODELO", "-"))))
            self.table_fleet.setItem(r, 2, QTableWidgetItem(str(row.get("FABRICANTE", "-"))))
            self.table_fleet.setItem(r, 3, QTableWidgetItem(str(row.get("DEPOSITO", "-"))))
            self.table_fleet.setItem(r, 4, QTableWidgetItem(f"{row.get('KILOMETRAJE', 0):,} km"))
            self.table_fleet.setItem(r, 5, QTableWidgetItem(str(row.get("ESTADO_OPERATIVO", "-"))))
            self.table_fleet.setItem(r, 6, QTableWidgetItem(str(row.get("ULTIMA_INSP", "-"))))
            self.table_fleet.setItem(r, 7, QTableWidgetItem(str(row.get("PROXIMA_INSP", "-"))))

    def open_maintenance_dialog(self):
        """Abre el diálogo para crear una orden de trabajo de mantenimiento."""
        pre_id = None
        selected_items = self.table_fleet.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            item = self.table_fleet.item(row, 0)
            if item is not None:
                cod_tren = item.text()
                # Buscar equipo correspondiente al tren
                from services.db import execute_query
                sql = """
                    SELECT eq.id_equipo FROM EQUIPO eq 
                    JOIN TREN t ON eq.referencia_id = t.id_tren AND eq.tipo_referencia = 'TREN'
                    WHERE t.codigo_interno = :cod
                """
                rows = execute_query(sql, {"cod": cod_tren})["rows"]
                if rows:
                    pre_id = int(rows[0]["ID_EQUIPO"])

        dlg = CrearOrdenMantenimientoDialog(preselected_equipo_id=pre_id, parent=self.window())
        if dlg.exec():
            eq_id = dlg.combo_equipo.currentData() or 1
            tipo = dlg.combo_tipo.currentText()
            prioridad = dlg.combo_prioridad.currentText()
            tec_id = dlg.combo_tecnico.currentData()
            desc = dlg.txt_desc.text().strip() or f"Mantenimiento {tipo} rutinario programado"

            res = actions_service.crear_orden_mantenimiento(
                equipo_id=eq_id,
                tipo_mantenimiento=tipo,
                descripcion=desc,
                prioridad=prioridad,
                tecnico_id=tec_id
            )

            if res.get("success"):
                InfoBar.success(
                    title="Orden de Taller Creada",
                    content=f"Orden {res.get('numero_orden')} creada exitosamente. El estado operativo se actualizó en Oracle.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                # Recargar flota
                fresh = metro_service.get_fleet_summary()
                self.update_fleet(fresh)
            else:
                InfoBar.error(
                    title="Error al Crear Orden",
                    content=res.get("error", "No se pudo crear la orden."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4000
                )
