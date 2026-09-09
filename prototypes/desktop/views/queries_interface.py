"""
Queries Interface - Dynamic execution of the 15 mandatory SQL queries.
Allows user-specified parameters (stations, routes, dates, thresholds) for dynamic analysis.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidgetItem,
    QFrame, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from qfluentwidgets import (
    TitleLabel, SubtitleLabel, CaptionLabel, BodyLabel,
    CardWidget, ComboBox, LineEdit, PrimaryPushButton,
    PlainTextEdit, TableWidget, InfoBar, InfoBarPosition,
    FluentIcon as FIF
)

from services.queries_catalog import CONSULTAS_CATALOGO
from services import metro_service
from workers.query_worker import QueryWorker


class QueriesInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("queriesInterface")
        self.param_widgets = {}
        self.active_worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = TitleLabel("15 Consultas Mínimas Obligatorias", self)
        subtitle = SubtitleLabel(
            "Consultas dinámicas analíticas y operativas exigidas en el enunciado (con parámetros configurables)", self
        )
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Control & Parameters Card
        card = CardWidget(self)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(12)

        # Query Selector Row
        top_row = QHBoxLayout()
        self.query_combo = ComboBox(self)
        for qid, q in CONSULTAS_CATALOGO.items():
            self.query_combo.addItem(f"{q['titulo']}", userData=qid)
        self.query_combo.currentIndexChanged.connect(self.on_query_changed)

        self.btn_run = PrimaryPushButton("Ejecutar Consulta", self, FIF.PLAY)
        self.btn_run.clicked.connect(self.run_query)

        top_row.addWidget(self.query_combo, stretch=4)
        top_row.addWidget(self.btn_run, stretch=1)
        card_layout.addLayout(top_row)

        # Description Label
        self.lbl_desc = BodyLabel(self)
        self.lbl_desc.setStyleSheet("color: #0039A6; font-weight: 600;")
        card_layout.addWidget(self.lbl_desc)

        # Dynamic Parameters Container
        self.params_frame = QFrame(self)
        self.params_layout = QHBoxLayout(self.params_frame)
        self.params_layout.setContentsMargins(0, 4, 0, 4)
        self.params_layout.setSpacing(12)
        card_layout.addWidget(self.params_frame)

        # SQL Code Viewer
        self.sql_editor = PlainTextEdit(self)
        self.sql_editor.setReadOnly(True)
        self.sql_editor.setMaximumHeight(90)
        self.sql_editor.setFont(QFont("Consolas", 10))
        card_layout.addWidget(self.sql_editor)

        layout.addWidget(card)

        # Counter Banner
        self.lbl_counter = CaptionLabel(
            "Selecciona una consulta, ajusta los parámetros deseados y haz clic en 'Ejecutar Consulta'.", self
        )
        layout.addWidget(self.lbl_counter)

        # Results Table
        self.table_results = TableWidget(self)
        self.table_results.setBorderVisible(True)
        self.table_results.setEditTriggers(TableWidget.NoEditTriggers)
        self.table_results.setSelectionBehavior(TableWidget.SelectRows)
        layout.addWidget(self.table_results)

        # Load initial query
        self.on_query_changed(0)

    def on_query_changed(self, index: int):
        qid = self.query_combo.currentData()
        if not qid or qid not in CONSULTAS_CATALOGO:
            return

        qinfo = CONSULTAS_CATALOGO[qid]
        self.lbl_desc.setText(f"Objetivo: {qinfo['descripcion']}")

        # Clear existing dynamic parameters
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.param_widgets.clear()

        params = qinfo.get("params", [])
        if not params:
            self.params_frame.hide()
        else:
            self.params_frame.show()
            for p in params:
                lbl = CaptionLabel(p["label"], self.params_frame)
                lbl.setStyleSheet("font-weight: 600;")
                self.params_layout.addWidget(lbl)

                if p["type"] == "combo":
                    combo = ComboBox(self.params_frame)
                    source = p.get("source")
                    if source == "stations":
                        for code, text in metro_service.get_stations_lookup():
                            combo.addItem(text, userData=code)
                    elif source == "routes":
                        for code, text in metro_service.get_routes_lookup():
                            combo.addItem(text, userData=code)
                    elif source == "orders":
                        for num, text in metro_service.get_orders_lookup():
                            combo.addItem(text, userData=num)
                    elif p.get("options"):
                        for opt in p["options"]:
                            combo.addItem(opt, userData=opt)

                    # Set default
                    default_val = p.get("default", "")
                    for i in range(combo.count()):
                        if combo.itemData(i) == default_val or combo.itemText(i) == default_val:
                            combo.setCurrentIndex(i)
                            break

                    combo.currentIndexChanged.connect(self.update_sql_preview)
                    self.params_layout.addWidget(combo, stretch=1)
                    self.param_widgets[p["key"]] = ("combo", combo)

                elif p["type"] in ["text", "number"]:
                    line = LineEdit(self.params_frame)
                    line.setText(str(p.get("default", "")))
                    line.textChanged.connect(self.update_sql_preview)
                    self.params_layout.addWidget(line, stretch=1)
                    self.param_widgets[p["key"]] = ("text", line)

            self.params_layout.addStretch(1)

        self.update_sql_preview()

    def get_current_param_values(self) -> dict:
        values = {}
        for key, (widget_type, widget) in self.param_widgets.items():
            if widget_type == "combo":
                val = widget.currentData()
                values[key] = val if val is not None else widget.currentText()
            else:
                values[key] = widget.text().strip()
        return values

    def update_sql_preview(self):
        qid = self.query_combo.currentData()
        if not qid or qid not in CONSULTAS_CATALOGO:
            return
        qinfo = CONSULTAS_CATALOGO[qid]
        param_values = self.get_current_param_values()
        sql, bind_params = qinfo["sql_generator"](param_values)
        preview_text = sql.strip()
        if bind_params:
            preview_text += f"\n\n-- [Parámetros Dinámicos: {bind_params}]"
        self.sql_editor.setPlainText(preview_text)

    def run_query(self):
        qid = self.query_combo.currentData()
        if not qid or qid not in CONSULTAS_CATALOGO:
            return

        qinfo = CONSULTAS_CATALOGO[qid]
        param_values = self.get_current_param_values()
        sql, bind_params = qinfo["sql_generator"](param_values)

        self.btn_run.setEnabled(False)
        self.lbl_counter.setText("⏳ Ejecutando consulta dinámica en Oracle Database...")
        QApplication.setOverrideCursor(Qt.WaitCursor)

        self.active_worker = QueryWorker(sql, bind_params, self)
        self.active_worker.data_loaded.connect(self.on_data_loaded)
        self.active_worker.error_occurred.connect(self.on_error_occurred)
        self.active_worker.finished.connect(self.on_worker_finished)
        self.active_worker.start()

    def on_data_loaded(self, columns: list, rows: list, pdb: str):
        self.table_results.clear()
        self.table_results.setColumnCount(len(columns))
        self.table_results.setRowCount(len(rows))
        self.table_results.setHorizontalHeaderLabels(columns)

        for r, row in enumerate(rows):
            for c, col in enumerate(columns):
                val = str(row.get(col, "-"))
                self.table_results.setItem(r, c, QTableWidgetItem(val))

        self.table_results.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.lbl_counter.setText(f"✅ {len(rows)} filas devueltas por Oracle ({pdb})")

        InfoBar.success(
            title=f"Consulta Ejecutada",
            content=f"Se recuperaron {len(rows)} filas en tiempo real.",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2500
        )

    def on_error_occurred(self, error_msg: str):
        self.lbl_counter.setText(f"❌ Error al consultar Oracle: {error_msg}")
        InfoBar.error(
            title="Error de Oracle",
            content=error_msg,
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=4000
        )

    def on_worker_finished(self):
        self.btn_run.setEnabled(True)
        QApplication.restoreOverrideCursor()

