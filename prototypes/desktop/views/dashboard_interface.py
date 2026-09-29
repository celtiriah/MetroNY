"""
Dashboard Interface - Centro de Control y Monitoreo Operativo de Red (MTA New York).
Provides holistic real-time visibility across operational KPIs, active incidents feed,
fleet availability, universal ADA accessibility, passenger demand rankings,
direct modal quick actions, and card-encapsulated subway lines directory with live search.
Fully responsive to Light and Dark themes in real time.
"""
from typing import Dict, List, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTableWidgetItem, QHeaderView, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from qfluentwidgets import (
    TitleLabel, SubtitleLabel, CaptionLabel, StrongBodyLabel, BodyLabel,
    CardWidget, PushButton, PrimaryPushButton, ToolButton, TableWidget,
    SearchLineEdit, ProgressBar, SmoothScrollArea, FluentIcon as FIF,
    isDarkTheme, qconfig
)

from components.stat_card import StatCard
from components.status_card import StatusCard
from views.components import (
    StatusBadge, LineColorChip, configure_interactive_table, auto_fit_table_columns
)


class DashboardInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("dashboardInterface")
        self.kpi_cards = {}
        self._all_lines_data: List[Dict[str, Any]] = []
        self.init_ui()

    def init_ui(self):
        # Outer layout containing the SmoothScrollArea
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.scroll_area = SmoothScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        vp = self.scroll_area.viewport()
        if vp is not None:
            vp.setStyleSheet("background: transparent;")

        # Inner container widget
        container = QWidget()
        container.setObjectName("dashboardContainer")
        container.setStyleSheet("#dashboardContainer { background: transparent; }")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        # Header Titles
        title = TitleLabel("MTA New York City Subway", container)
        subtitle = SubtitleLabel("Centro de Control y Monitoreo Operativo de Red (Oracle Database)", container)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Nivel 1: Conectividad y Acciones Rapidas con Modales Directos
        self.status_card = StatusCard(container)
        layout.addWidget(self.status_card)

        # Quick Actions Bar
        actions_card = CardWidget(container)
        actions_layout = QHBoxLayout(actions_card)
        actions_layout.setContentsMargins(16, 12, 16, 12)
        actions_layout.setSpacing(10)

        lbl_actions = StrongBodyLabel("Acciones Rapidas:", actions_card)
        actions_layout.addWidget(lbl_actions)

        # 4 Quick Actions that launch modals directly on the panel
        self.btn_report_incident = PushButton("Reportar Incidente", actions_card, FIF.INFO)
        self.btn_report_incident.clicked.connect(self._action_reportar_incidente)
        actions_layout.addWidget(self.btn_report_incident)

        self.btn_issue_card = PushButton("Emitir Tarjeta OMNY", actions_card, FIF.QRCODE)
        self.btn_issue_card.clicked.connect(self._action_emitir_tarjeta)
        actions_layout.addWidget(self.btn_issue_card)

        self.btn_recharge_card = PushButton("Recargar Saldo OMNY", actions_card, FIF.TAG)
        self.btn_recharge_card.clicked.connect(self._action_recargar_saldo)
        actions_layout.addWidget(self.btn_recharge_card)

        self.btn_create_order = PushButton("Crear Orden de Taller", actions_card, FIF.DEVELOPER_TOOLS)
        self.btn_create_order.clicked.connect(self._action_crear_orden)
        actions_layout.addWidget(self.btn_create_order)

        actions_layout.addStretch(1)

        self.btn_refresh = ToolButton(FIF.SYNC, actions_card)
        self.btn_refresh.setToolTip("Actualizar datos del panel")
        self.btn_refresh.clicked.connect(self._on_refresh_clicked)
        actions_layout.addWidget(self.btn_refresh)

        layout.addWidget(actions_card)

        # Nivel 2: Cuadricula Ejecutiva de 8 KPIs
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(12)

        metrics = [
            ("TOTAL_LINEAS", "Lineas Activas", FIF.TRAIN, 0, 0),
            ("TOTAL_ESTACIONES", "Estaciones", FIF.PIN, 0, 1),
            ("TOTAL_TRENES", "Flota Total", FIF.BUS, 0, 2),
            ("DISP_FLOTA", "Disponibilidad Flota", FIF.ACCEPT, 0, 3),
            ("OTP_PUNTUALIDAD", "Puntualidad OTP", FIF.SPEED_HIGH, 1, 0),
            ("TOTAL_PASAJEROS", "Pasajeros Movilizados", FIF.PEOPLE, 1, 1),
            ("TOTAL_RECAUDADO", "Recaudacion OMNY", FIF.TAG, 1, 2),
            ("INCIDENTES_ABIERTOS", "Incidentes Activos", FIF.INFO, 1, 3),
        ]

        for key, title_text, icon, r, c in metrics:
            card = StatCard(title_text, icon, "-", container)
            self.kpi_cards[key] = card
            kpi_grid.addWidget(card, r, c)

        layout.addLayout(kpi_grid)

        # Nivel 3: Centro Operativo en Vista Dividida (Dos Columnas)
        split_row = QHBoxLayout()
        split_row.setSpacing(16)

        # Columna Izquierda: Feed de Incidentes Criticos
        card_incidents = CardWidget(container)
        card_inc_layout = QVBoxLayout(card_incidents)
        card_inc_layout.setContentsMargins(16, 14, 16, 14)
        card_inc_layout.setSpacing(10)

        inc_header = QHBoxLayout()
        inc_header.addWidget(StrongBodyLabel("Incidentes Criticos en Red", card_incidents))
        inc_header.addStretch(1)
        self.btn_all_incidents = PushButton("Ver Todo", card_incidents, FIF.CHEVRON_RIGHT)
        self.btn_all_incidents.clicked.connect(self._nav_to_incidents)
        inc_header.addWidget(self.btn_all_incidents)
        card_inc_layout.addLayout(inc_header)

        self.table_incidents = TableWidget(card_incidents)
        self.table_incidents.setBorderVisible(True)
        self.table_incidents.setColumnCount(5)
        self.table_incidents.setHorizontalHeaderLabels([
            "Incidente", "Tipo", "Severidad", "Elemento Afectado", "Fecha"
        ])
        configure_interactive_table(self.table_incidents, min_col_width=70)
        self.table_incidents.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_incidents.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table_incidents.setMinimumHeight(190)
        self.table_incidents.itemDoubleClicked.connect(self._on_incident_double_clicked)
        card_inc_layout.addWidget(self.table_incidents)

        split_row.addWidget(card_incidents, stretch=3)

        # Columna Derecha: Salud de Flota/ADA y Top Afluencia
        right_col_layout = QVBoxLayout()
        right_col_layout.setSpacing(14)

        # Card Salud de Red
        card_health = CardWidget(container)
        card_health_layout = QVBoxLayout(card_health)
        card_health_layout.setContentsMargins(16, 14, 16, 14)
        card_health_layout.setSpacing(8)

        card_health_layout.addWidget(StrongBodyLabel("Salud de Flota y Accesibilidad ADA", card_health))

        self.lbl_fleet_health = CaptionLabel("Flota en Servicio: -", card_health)
        font_bold = self.lbl_fleet_health.font()
        font_bold.setBold(True)
        self.lbl_fleet_health.setFont(font_bold)
        card_health_layout.addWidget(self.lbl_fleet_health)

        self.progress_fleet = ProgressBar(card_health)
        self.progress_fleet.setValue(0)
        card_health_layout.addWidget(self.progress_fleet)

        self.lbl_ada_health = CaptionLabel("Estaciones Accesibles ADA: -", card_health)
        self.lbl_ada_health.setFont(font_bold)
        card_health_layout.addWidget(self.lbl_ada_health)

        self.progress_ada = ProgressBar(card_health)
        self.progress_ada.setValue(0)
        card_health_layout.addWidget(self.progress_ada)

        right_col_layout.addWidget(card_health)

        # Card Top Estaciones
        card_stations = CardWidget(container)
        card_stations_layout = QVBoxLayout(card_stations)
        card_stations_layout.setContentsMargins(16, 14, 16, 14)
        card_stations_layout.setSpacing(8)

        card_stations_layout.addWidget(StrongBodyLabel("Top Estaciones con Mayor Afluencia", card_stations))

        self.table_top_stations = TableWidget(card_stations)
        self.table_top_stations.setBorderVisible(True)
        self.table_top_stations.setColumnCount(5)
        self.table_top_stations.setHorizontalHeaderLabels([
            "#", "Estacion", "Distrito", "Pasajes", "Recaudacion ($)"
        ])
        configure_interactive_table(self.table_top_stations, min_col_width=55)
        self.table_top_stations.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_top_stations.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table_top_stations.setMinimumHeight(155)
        card_stations_layout.addWidget(self.table_top_stations)

        right_col_layout.addWidget(card_stations)

        split_row.addLayout(right_col_layout, stretch=2)
        layout.addLayout(split_row)

        # Nivel 4: Directorio de Lineas Encapsulado en CardWidget con Buscador en Vivo
        card_lines = CardWidget(container)
        card_lines_layout = QVBoxLayout(card_lines)
        card_lines_layout.setContentsMargins(16, 14, 16, 14)
        card_lines_layout.setSpacing(10)

        lines_header = QHBoxLayout()
        lines_header.addWidget(StrongBodyLabel("Directorio de Lineas Principales del Metro", card_lines))
        lines_header.addStretch(1)

        self.search_lines = SearchLineEdit(card_lines)
        self.search_lines.setPlaceholderText("Buscar linea por codigo, nombre o servicio...")
        self.search_lines.setClearButtonEnabled(True)
        self.search_lines.setFixedWidth(320)
        self.search_lines.textChanged.connect(self._filter_lines)
        lines_header.addWidget(self.search_lines)

        card_lines_layout.addLayout(lines_header)

        self.table_lines = TableWidget(card_lines)
        self.table_lines.setBorderVisible(True)
        self.table_lines.setColumnCount(6)
        self.table_lines.setHorizontalHeaderLabels([
            "Codigo", "Nombre Oficial", "Color", "Servicio Principal", "Estado", "Estaciones"
        ])
        configure_interactive_table(self.table_lines, min_col_width=75)
        self.table_lines.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_lines.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table_lines.setMinimumHeight(240)
        card_lines_layout.addWidget(self.table_lines)

        layout.addWidget(card_lines)

        self.scroll_area.setWidget(container)
        outer_layout.addWidget(self.scroll_area)

    # -------------------------------------------------------------------------
    # Acciones Rapidas que abren Modales Directamente desde el Panel
    # -------------------------------------------------------------------------
    def _action_reportar_incidente(self):
        win: Any = self.window()
        if win is not None and hasattr(win, "incidents_interface"):
            win.incidents_interface.handle_nuevo_incidente()
            if hasattr(win, "load_dashboard_data"):
                win.load_dashboard_data()

    def _action_emitir_tarjeta(self):
        win: Any = self.window()
        if win is not None and hasattr(win, "cards_interface"):
            win.cards_interface.handle_emitir_tarjeta()
            if hasattr(win, "load_dashboard_data"):
                win.load_dashboard_data()

    def _action_recargar_saldo(self):
        win: Any = self.window()
        if win is not None and hasattr(win, "cards_interface"):
            win.cards_interface.handle_recargar_tarjeta_dialog()
            if hasattr(win, "load_dashboard_data"):
                win.load_dashboard_data()

    def _action_crear_orden(self):
        win: Any = self.window()
        if win is not None and hasattr(win, "maintenance_interface"):
            win.maintenance_interface.handle_nueva_orden()
            if hasattr(win, "load_dashboard_data"):
                win.load_dashboard_data()

    def _nav_to_incidents(self):
        win: Any = self.window()
        if win is not None and hasattr(win, "switchTo") and hasattr(win, "incidents_interface"):
            win.switchTo(win.incidents_interface)

    def _on_refresh_clicked(self):
        win: Any = self.window()
        if win is not None and hasattr(win, "load_dashboard_data"):
            win.load_dashboard_data()

    def _on_incident_double_clicked(self, item: QTableWidgetItem):
        row = item.row()
        inc_item = self.table_incidents.item(row, 0)
        inc_num = inc_item.text() if inc_item is not None else ""
        win: Any = self.window()
        if win is not None and hasattr(win, "switchTo") and hasattr(win, "incidents_interface"):
            win.switchTo(win.incidents_interface)

    # -------------------------------------------------------------------------
    # Actualizacion de Datos Reactiva
    # -------------------------------------------------------------------------
    def update_kpis(self, kpis: dict):
        for key, card in self.kpi_cards.items():
            raw_val = kpis.get(key, "-")
            display_val = str(raw_val)

            if key in ["DISP_FLOTA", "OTP_PUNTUALIDAD"]:
                try:
                    display_val = f"{float(raw_val):.1f}%"
                except (ValueError, TypeError):
                    display_val = f"{raw_val}%"
            elif key == "TOTAL_RECAUDADO":
                try:
                    display_val = f"${float(raw_val):,.2f}"
                except (ValueError, TypeError):
                    display_val = f"${raw_val}"
            elif key == "TOTAL_PASAJEROS":
                try:
                    display_val = f"{int(raw_val):,}"
                except (ValueError, TypeError):
                    display_val = str(raw_val)

            card.set_value(display_val)

        # Actualizar Barras de Progreso de Salud de Red
        try:
            disp_flota = float(kpis.get("DISP_FLOTA", 0))
            tot_trenes = kpis.get("TOTAL_TRENES", "0")
            self.lbl_fleet_health.setText(f"Flota en Servicio: {disp_flota:.1f}% ({tot_trenes} unidades)")
            self.progress_fleet.setValue(int(min(max(disp_flota, 0), 100)))
        except (ValueError, TypeError):
            self.progress_fleet.setValue(0)

        try:
            ada_pct = float(kpis.get("ACCESIBILIDAD_ADA", 0))
            tot_est = kpis.get("TOTAL_ESTACIONES", "0")
            self.lbl_ada_health.setText(f"Estaciones Accesibles ADA: {ada_pct:.1f}% ({tot_est} estaciones)")
            self.progress_ada.setValue(int(min(max(ada_pct, 0), 100)))
        except (ValueError, TypeError):
            self.progress_ada.setValue(0)

    def update_active_incidents(self, incidents: list):
        self.table_incidents.clearContents()
        if not incidents:
            self.table_incidents.setRowCount(1)
            self.table_incidents.setItem(0, 0, QTableWidgetItem("Sin incidentes activos en la red"))
            self.table_incidents.setItem(0, 1, QTableWidgetItem("-"))
            self.table_incidents.setItem(0, 2, QTableWidgetItem("-"))
            self.table_incidents.setItem(0, 3, QTableWidgetItem("-"))
            self.table_incidents.setItem(0, 4, QTableWidgetItem("-"))
            return

        self.table_incidents.setRowCount(len(incidents))
        for r, row in enumerate(incidents):
            inc_code = str(row.get("NUMERO_INCIDENTE", "-"))
            tipo = str(row.get("TIPO", "-"))
            sev = str(row.get("NIVEL_SEVERIDAD", "-"))
            elem = str(row.get("ELEMENTO", "-"))
            fecha = str(row.get("FECHA", "-"))

            self.table_incidents.setItem(r, 0, QTableWidgetItem(inc_code))
            self.table_incidents.setItem(r, 1, QTableWidgetItem(tipo))

            if sev not in ("-", "", "None"):
                self.table_incidents.setCellWidget(r, 2, StatusBadge(sev, self.table_incidents))
            else:
                self.table_incidents.setItem(r, 2, QTableWidgetItem("-"))

            self.table_incidents.setItem(r, 3, QTableWidgetItem(elem))
            self.table_incidents.setItem(r, 4, QTableWidgetItem(fecha))

        auto_fit_table_columns(self.table_incidents)

    def update_top_stations(self, stations: list):
        self.table_top_stations.clearContents()
        if not stations:
            self.table_top_stations.setRowCount(1)
            self.table_top_stations.setItem(0, 0, QTableWidgetItem("-"))
            self.table_top_stations.setItem(0, 1, QTableWidgetItem("Sin registros"))
            self.table_top_stations.setItem(0, 2, QTableWidgetItem("-"))
            self.table_top_stations.setItem(0, 3, QTableWidgetItem("0"))
            self.table_top_stations.setItem(0, 4, QTableWidgetItem("$0.00"))
            return

        self.table_top_stations.setRowCount(len(stations))
        for r, row in enumerate(stations):
            nom = str(row.get("NOMBRE", "-"))
            dist = str(row.get("DISTRITO", "-"))
            try:
                pasajes = f"{int(row.get('TOTAL_PASAJES', 0)):,}"
            except (ValueError, TypeError):
                pasajes = str(row.get("TOTAL_PASAJES", 0))

            try:
                monto = f"${float(row.get('TOTAL_MONTO', 0.0)):,.2f}"
            except (ValueError, TypeError):
                monto = f"${row.get('TOTAL_MONTO', 0.0)}"

            self.table_top_stations.setItem(r, 0, QTableWidgetItem(f"#{r + 1}"))
            self.table_top_stations.setItem(r, 1, QTableWidgetItem(nom))
            self.table_top_stations.setItem(r, 2, QTableWidgetItem(dist))
            self.table_top_stations.setItem(r, 3, QTableWidgetItem(pasajes))
            self.table_top_stations.setItem(r, 4, QTableWidgetItem(monto))

        auto_fit_table_columns(self.table_top_stations)

    def update_lines(self, lines: list):
        self._all_lines_data = list(lines)
        self.table_lines.clearContents()
        self.table_lines.setRowCount(len(lines))

        for r, row in enumerate(lines):
            self.table_lines.setItem(r, 0, QTableWidgetItem(str(row.get("CODIGO", "-"))))
            self.table_lines.setItem(r, 1, QTableWidgetItem(str(row.get("NOMBRE", "-"))))

            col_hex = str(row.get("COLOR", "#0039A6")).strip()
            chip = LineColorChip(col_hex, col_hex, "", self.table_lines)
            self.table_lines.setCellWidget(r, 2, chip)

            srv = str(row.get("TIPO_SERVICIO_PRINCIPAL", "-"))
            self.table_lines.setCellWidget(r, 3, StatusBadge(srv, self.table_lines))

            st = str(row.get("ESTADO_OPERATIVO", "-"))
            self.table_lines.setCellWidget(r, 4, StatusBadge(st, self.table_lines))

            self.table_lines.setItem(r, 5, QTableWidgetItem(f"{row.get('ESTACIONES', 0)} paradas"))

        auto_fit_table_columns(self.table_lines)
        self._filter_lines(self.search_lines.text())

    def _filter_lines(self, search_text: str):
        term = search_text.strip().lower()
        for row_idx in range(self.table_lines.rowCount()):
            if not term:
                self.table_lines.setRowHidden(row_idx, False)
                continue

            code_item = self.table_lines.item(row_idx, 0)
            name_item = self.table_lines.item(row_idx, 1)

            code_text = code_item.text().lower() if code_item is not None else ""
            name_text = name_item.text().lower() if name_item is not None else ""

            # Check service badge text if available
            srv_cell = self.table_lines.cellWidget(row_idx, 3)
            srv_text = str(getattr(srv_cell, "text_content", "")).lower()

            matched = (term in code_text) or (term in name_text) or (term in srv_text)
            self.table_lines.setRowHidden(row_idx, not matched)
