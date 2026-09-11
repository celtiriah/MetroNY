"""
Incidents Interface - Operational incidents log, severity levels, and affected network assets.
Includes interactive registration of new incidents and trip cancellation dispatch.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidgetItem,
    QLabel
)
from PyQt5.QtCore import Qt

from qfluentwidgets import (
    TitleLabel, SubtitleLabel, CaptionLabel, StrongBodyLabel,
    ComboBox, TableWidget, PrimaryPushButton, PushButton,
    LineEdit, MessageBoxBase, InfoBar, InfoBarPosition,
    FluentIcon as FIF
)

from services import metro_service, actions_service


class RegistrarIncidenteDialog(MessageBoxBase):
    """
    Diálogo modal Fluent para reportar y registrar una contingencia operativa en la red.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("Reportar Nuevo Incidente Operativo", self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        # 1. Tipo de Incidente
        self.viewLayout.addWidget(CaptionLabel("Tipo de Eventualidad:", self))
        self.combo_tipo = ComboBox(self)
        self.combo_tipo.addItems([
            "Falla Mecánica", "Falla Eléctrica", "Falla de Señalización",
            "Emergencia Médica", "Accidente", "Problema de Seguridad",
            "Objeto en la Vía", "Inundación", "Incendio", "Congestión",
            "Mantenimiento no Programado"
        ])
        self.viewLayout.addWidget(self.combo_tipo)

        # 2. Severidad
        self.viewLayout.addWidget(CaptionLabel("Nivel de Severidad:", self))
        self.combo_severidad = ComboBox(self)
        self.combo_severidad.addItems(["Bajo", "Medio", "Alto", "Crítico"])
        self.viewLayout.addWidget(self.combo_severidad)

        # 3. Reportado Por
        self.viewLayout.addWidget(CaptionLabel("Personal que Reporta:", self))
        self.combo_reportado = ComboBox(self)
        empleados = actions_service.get_empleados_combo()
        for emp_id, label in empleados:
            self.combo_reportado.addItem(label, userData=emp_id)
        self.viewLayout.addWidget(self.combo_reportado)

        # 4. Tipo de Elemento Afectado
        self.viewLayout.addWidget(CaptionLabel("Elemento de Red Afectado:", self))
        row_elem = QHBoxLayout()
        self.combo_tipo_elem = ComboBox(self)
        self.combo_tipo_elem.addItems(["ESTACION", "TREN", "RUTA", "LINEA"])
        self.combo_tipo_elem.currentTextChanged.connect(self.on_tipo_elem_changed)
        row_elem.addWidget(self.combo_tipo_elem, stretch=2)

        self.combo_elem = ComboBox(self)
        row_elem.addWidget(self.combo_elem, stretch=4)
        self.viewLayout.addLayout(row_elem)

        # 5. Tipo de Afectación
        self.viewLayout.addWidget(CaptionLabel("Tipo de Afectación Operativa:", self))
        self.combo_afectacion = ComboBox(self)
        self.combo_afectacion.addItems([
            "Retraso", "Cambio de Ruta", "Cancelación", "Cierre de Estación",
            "Cierre de Plataforma", "Retiro de Tren", "Suspensión de Tramo"
        ])
        self.viewLayout.addWidget(self.combo_afectacion)

        # 6. Descripción
        self.viewLayout.addWidget(CaptionLabel("Descripción del Hecho:", self))
        self.txt_desc = LineEdit(self)
        self.txt_desc.setPlaceholderText("Detalle técnico breve del incidente...")
        self.viewLayout.addWidget(self.txt_desc)

        # Botones
        self.yesButton.setText("Registrar Incidente")
        self.cancelButton.setText("Cancelar")

        # Cargar elementos iniciales
        self.on_tipo_elem_changed("ESTACION")

    def on_tipo_elem_changed(self, tipo: str):
        self.combo_elem.clear()
        if tipo == "ESTACION":
            for est_id, label in actions_service.get_estaciones_combo():
                self.combo_elem.addItem(label, userData=est_id)
        elif tipo == "TREN":
            for tren_id, label in actions_service.get_trenes_combo():
                self.combo_elem.addItem(label, userData=tren_id)
        elif tipo == "RUTA":
            for ruta_id, label in actions_service.get_rutas_combo():
                self.combo_elem.addItem(label, userData=ruta_id)
        elif tipo == "LINEA":
            for lin_id, label in actions_service.get_lineas_combo():
                self.combo_elem.addItem(label, userData=lin_id)


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
        subtitle = SubtitleLabel(
            "Monitoreo de anomalías en la red, niveles de severidad y elementos de infraestructura afectados", self
        )
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Barra de Acciones y Filtros
        actions_bar = QHBoxLayout()
        actions_bar.setSpacing(10)

        actions_bar.addWidget(CaptionLabel("Filtrar por severidad:", self))
        self.combo_filter = ComboBox(self)
        self.combo_filter.addItems(["(Todas)", "Bajo", "Medio", "Alto", "Crítico"])
        self.combo_filter.currentTextChanged.connect(self.apply_filter)
        actions_bar.addWidget(self.combo_filter)

        actions_bar.addStretch(1)

        self.btn_cancel_trips = PushButton("Cancelar Viajes Afectados", self, FIF.CANCEL)
        self.btn_cancel_trips.clicked.connect(self.handle_cancel_affected_trips)
        actions_bar.addWidget(self.btn_cancel_trips)

        self.btn_new_incident = PrimaryPushButton("Reportar Incidente", self, FIF.ADD)
        self.btn_new_incident.clicked.connect(self.open_new_incident_dialog)
        actions_bar.addWidget(self.btn_new_incident)

        layout.addLayout(actions_bar)

        # Table
        self.table_incidents = TableWidget(self)
        self.table_incidents.setBorderVisible(True)
        self.table_incidents.setColumnCount(7)
        self.table_incidents.setHorizontalHeaderLabels([
            "Nº Incidente", "Tipo", "Severidad", "Elemento Afectado", "Fecha Inicio", "Estado", "Descripción"
        ])
        header = self.table_incidents.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.Stretch)
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

    def open_new_incident_dialog(self):
        """Abre el diálogo modal Fluent para reportar un incidente."""
        dlg = RegistrarIncidenteDialog(self.window())
        if dlg.exec():
            tipo = dlg.combo_tipo.currentText()
            severidad = dlg.combo_severidad.currentText()
            rep_id = dlg.combo_reportado.currentData() or 1
            tipo_elem = dlg.combo_tipo_elem.currentText()
            elem_id = dlg.combo_elem.currentData()
            afectacion = dlg.combo_afectacion.currentText()
            desc = dlg.txt_desc.text().strip() or f"Incidente tipo {tipo} en {tipo_elem}"

            res = actions_service.registrar_incidente(
                tipo=tipo,
                descripcion=desc,
                nivel_severidad=severidad,
                reportado_por_id=rep_id,
                tipo_elemento=tipo_elem,
                elemento_id=elem_id,
                tipo_afectacion=afectacion
            )

            if res.get("success"):
                InfoBar.success(
                    title="Incidente Registrado",
                    content=f"Incidente {res.get('numero_incidente')} registrado exitosamente en Oracle.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                # Recargar tabla de incidentes
                fresh = metro_service.get_incidents_summary()
                self.update_incidents(fresh)
            else:
                InfoBar.error(
                    title="Error al Registrar",
                    content=res.get("error", "No se pudo registrar el incidente."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4000
                )

    def handle_cancel_affected_trips(self):
        """Cancela viajes afectados por el incidente seleccionado en la tabla."""
        selected_items = self.table_incidents.selectedItems()
        if not selected_items:
            InfoBar.warning(
                title="Sin Selección",
                content="Selecciona un incidente en la tabla para despachar cancelaciones.",
                parent=self.window()
            )
            return

        row = selected_items[0].row()
        item = self.table_incidents.item(row, 0)
        if item is None:
            return
        num_inc = item.text()

        # Obtener ID del incidente
        inc_data = next((i for i in self.incidents_data if i.get("NUMERO_INCIDENTE") == num_inc), None)
        if not inc_data:
            return

        # Query ID en Oracle
        sql = "SELECT id_incidente FROM INCIDENTE WHERE numero_incidente = :num"
        from services.db import execute_query
        rows = execute_query(sql, {"num": num_inc})["rows"]
        if not rows:
            return

        id_inc = int(rows[0]["ID_INCIDENTE"])
        res = actions_service.cancelar_viajes_afectados(id_inc)

        if res.get("success"):
            total = res.get("viajes_cancelados", 0)
            InfoBar.info(
                title="Despacho de Cancelación",
                content=f"Se cancelaron {total} viaje(s) asociados al incidente {num_inc}.",
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
                duration=3500
            )
        else:
            InfoBar.error(
                title="Error al Cancelar",
                content=res.get("error", "No se pudieron cancelar los viajes."),
                parent=self.window()
            )
