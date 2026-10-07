"""
Queries Interface - Centro de Reporteria Analitica y Extraccion de Datos.
Dynamic execution of the 15 executive SQL reports (REP-01 to REP-15).
Supports dynamic parameter injection, interactive in-memory pagination,
query copying to clipboard, and complete CSV export for Microsoft Excel.
"""
import os
import csv
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem,
    QFrame, QApplication, QFileDialog
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

from qfluentwidgets import (
    TitleLabel, SubtitleLabel, CaptionLabel, BodyLabel, StrongBodyLabel,
    CardWidget, ComboBox, LineEdit, PrimaryPushButton, PushButton, ToolButton,
    PlainTextEdit, TableWidget, DateEdit, InfoBar, InfoBarPosition,
    FluentIcon as FIF, isDarkTheme, qconfig
)

from services.queries_catalog import CONSULTAS_CATALOGO
from services import metro_service
from workers.query_worker import QueryWorker
from views.components import StatusBadge, configure_interactive_table, auto_fit_table_columns


class QueriesInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("queriesInterface")
        self.param_widgets = {}
        self.active_worker = None

        # Data & Pagination State
        self.all_columns = []
        self.all_rows = []
        self.current_page = 0
        self.page_size = 50

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # Header Module
        title = TitleLabel("Centro de Reporteria Analitica y Extraccion de Datos", self)
        subtitle = SubtitleLabel(
            "Genere sabanas de datos, audite la logica SQL subyacente y exporte reportes gerenciales de la red.", self
        )
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Control & Parameters Card
        card_controls = CardWidget(self)
        controls_layout = QVBoxLayout(card_controls)
        controls_layout.setContentsMargins(18, 16, 18, 16)
        controls_layout.setSpacing(12)

        # Query Selector Row
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        self.query_combo = ComboBox(self)
        for qid, q in CONSULTAS_CATALOGO.items():
            self.query_combo.addItem(f"{q['titulo']}", userData=qid)
        self.query_combo.currentIndexChanged.connect(self.on_query_changed)

        self.btn_run = PrimaryPushButton("Ejecutar Consulta", self, FIF.PLAY)
        self.btn_run.clicked.connect(self.run_query)

        self.btn_export = PushButton("Exportar a Excel (.csv)", self, FIF.DOCUMENT)
        self.btn_export.clicked.connect(self.export_to_csv)

        top_row.addWidget(self.query_combo, stretch=3)
        top_row.addWidget(self.btn_run, stretch=0)
        top_row.addWidget(self.btn_export, stretch=0)
        controls_layout.addLayout(top_row)

        # Description Label
        self.lbl_desc = BodyLabel(self)
        self._update_desc_style()
        qconfig.themeChanged.connect(self._update_desc_style)
        controls_layout.addWidget(self.lbl_desc)

        # Dynamic Parameters Container
        self.params_frame = QFrame(self)
        self.params_layout = QHBoxLayout(self.params_frame)
        self.params_layout.setContentsMargins(0, 4, 0, 4)
        self.params_layout.setSpacing(12)
        controls_layout.addWidget(self.params_frame)

        layout.addWidget(card_controls)

        # SQL Code Viewer Card
        card_sql = CardWidget(self)
        card_sql_layout = QVBoxLayout(card_sql)
        card_sql_layout.setContentsMargins(18, 12, 18, 12)
        card_sql_layout.setSpacing(8)

        sql_header_row = QHBoxLayout()
        lbl_sql_title = StrongBodyLabel("Logica de Extraccion (Oracle SQL)", self)
        self.btn_copy_sql = PushButton("Copiar Query", self, FIF.COPY)
        self.btn_copy_sql.clicked.connect(self.copy_sql_to_clipboard)

        sql_header_row.addWidget(lbl_sql_title)
        sql_header_row.addStretch(1)
        sql_header_row.addWidget(self.btn_copy_sql)
        card_sql_layout.addLayout(sql_header_row)

        self.sql_editor = PlainTextEdit(self)
        self.sql_editor.setReadOnly(True)
        self.sql_editor.setMaximumHeight(105)
        self.sql_editor.setFont(QFont("Consolas", 10))
        card_sql_layout.addWidget(self.sql_editor)

        layout.addWidget(card_sql)

        # Results & Pagination Card
        card_results = CardWidget(self)
        card_results_layout = QVBoxLayout(card_results)
        card_results_layout.setContentsMargins(18, 12, 18, 12)
        card_results_layout.setSpacing(10)

        results_header_row = QHBoxLayout()
        lbl_results_title = StrongBodyLabel("Vista Previa de Datos", self)
        self.lbl_timestamp = CaptionLabel("Ultima actualizacion: Sin ejecutar", self)
        results_header_row.addWidget(lbl_results_title)
        results_header_row.addStretch(1)
        results_header_row.addWidget(self.lbl_timestamp)
        card_results_layout.addLayout(results_header_row)

        # Results Table
        self.table_results = TableWidget(self)
        self.table_results.setBorderVisible(True)
        self.table_results.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_results.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        configure_interactive_table(self.table_results)
        card_results_layout.addWidget(self.table_results, stretch=1)

        # Pagination & Counter Footer Bar
        pagination_row = QHBoxLayout()
        pagination_row.setSpacing(10)

        self.lbl_pagination = CaptionLabel(
            "Selecciona un reporte, configura parametros y presiona 'Ejecutar Consulta'.", self
        )
        pagination_row.addWidget(self.lbl_pagination)
        pagination_row.addStretch(1)

        lbl_page_size = CaptionLabel("Mostrar:", self)
        pagination_row.addWidget(lbl_page_size)

        self.combo_page_size = ComboBox(self)
        self.combo_page_size.addItem("50 filas / pag", userData=50)
        self.combo_page_size.addItem("100 filas / pag", userData=100)
        self.combo_page_size.addItem("250 filas / pag", userData=250)
        self.combo_page_size.currentIndexChanged.connect(self.on_page_size_changed)
        pagination_row.addWidget(self.combo_page_size)

        self.btn_prev_page = ToolButton(FIF.PAGE_LEFT, self)
        self.btn_prev_page.setToolTip("Pagina Anterior")
        self.btn_prev_page.setEnabled(False)
        self.btn_prev_page.clicked.connect(self.prev_page)
        pagination_row.addWidget(self.btn_prev_page)

        self.btn_next_page = ToolButton(FIF.PAGE_RIGHT, self)
        self.btn_next_page.setToolTip("Pagina Siguiente")
        self.btn_next_page.setEnabled(False)
        self.btn_next_page.clicked.connect(self.next_page)
        pagination_row.addWidget(self.btn_next_page)

        card_results_layout.addLayout(pagination_row)
        layout.addWidget(card_results, stretch=1)

        # Load initial query
        self.on_query_changed(0)

    def _update_desc_style(self):
        dark = isDarkTheme()
        color = "#4da6ff" if dark else "#0039A6"
        self.lbl_desc.setStyleSheet(f"color: {color}; font-weight: 600;")

    def on_query_changed(self, index: int):
        qid = self.query_combo.currentData()
        if not qid or qid not in CONSULTAS_CATALOGO:
            return

        qinfo = CONSULTAS_CATALOGO[qid]
        self.lbl_desc.setText(f"Area: {qinfo.get('area', 'General')} | Objetivo: {qinfo['descripcion']}")

        # Clear existing dynamic parameters
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            if item is None:
                continue

            widget = item.widget()
            if widget is not None:
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

                elif p["type"] == "date":
                    date_edit = DateEdit(self.params_frame)
                    raw_default = str(p.get("default", "2026-09-01"))
                    try:
                        d_parts = [int(x) for x in raw_default.split("-")]
                        date_edit.setDate(QDate(d_parts[0], d_parts[1], d_parts[2]))
                    except (ValueError, IndexError):
                        date_edit.setDate(QDate(2026, 9, 1))

                    date_edit.dateChanged.connect(self.update_sql_preview)
                    self.params_layout.addWidget(date_edit, stretch=1)
                    self.param_widgets[p["key"]] = ("date", date_edit)

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
            elif widget_type == "date":
                values[key] = widget.date().toString("yyyy-MM-dd")
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
            preview_text += f"\n\n-- [Parametros Dinamicos: {bind_params}]"
        self.sql_editor.setPlainText(preview_text)

    def copy_sql_to_clipboard(self):
        sql_text = self.sql_editor.toPlainText().strip()
        if not sql_text:
            return

        cb = QApplication.clipboard()
        if cb is not None:
            cb.setText(sql_text)
            InfoBar.success(
                title="Query copiada",
                content="El codigo SQL de extraccion se ha copiado al portapapeles.",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )

    def run_query(self):
        qid = self.query_combo.currentData()
        if not qid or qid not in CONSULTAS_CATALOGO:
            return

        qinfo = CONSULTAS_CATALOGO[qid]
        param_values = self.get_current_param_values()
        sql, bind_params = qinfo["sql_generator"](param_values)

        self.btn_run.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.lbl_pagination.setText("Ejecutando extraccion analitica en Oracle Database...")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        self.active_worker = QueryWorker(sql, bind_params, self)
        self.active_worker.data_loaded.connect(self.on_data_loaded)
        self.active_worker.error_occurred.connect(self.on_error_occurred)
        self.active_worker.finished.connect(self.on_worker_finished)
        self.active_worker.start()

    def on_data_loaded(self, columns: list, rows: list, pdb: str):
        self.all_columns = list(columns)
        self.all_rows = list(rows)
        self.current_page = 0

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.lbl_timestamp.setText(f"Ultima actualizacion: {now_str} ({pdb})")

        self.render_current_page()

        InfoBar.success(
            title="Extraccion Completada",
            content=f"Se recuperaron {len(rows)} filas en tiempo real.",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000
        )

    def on_page_size_changed(self, index: int):
        val = self.combo_page_size.currentData()
        if val is not None:
            self.page_size = int(val)
            self.current_page = 0
            self.render_current_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_current_page()

    def next_page(self):
        total = len(self.all_rows)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.render_current_page()

    def render_current_page(self):
        self.table_results.clear()
        total_records = len(self.all_rows)
        self.table_results.setColumnCount(len(self.all_columns))
        self.table_results.setHorizontalHeaderLabels(self.all_columns)

        if total_records == 0:
            self.table_results.setRowCount(0)
            self.lbl_pagination.setText("0 registros devueltos por Oracle.")
            self.btn_prev_page.setEnabled(False)
            self.btn_next_page.setEnabled(False)
            return

        total_pages = max(1, (total_records + self.page_size - 1) // self.page_size)
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, total_records)
        page_rows = self.all_rows[start_idx:end_idx]

        self.table_results.setRowCount(len(page_rows))

        for r, row in enumerate(page_rows):
            for c, col in enumerate(self.all_columns):
                raw_val = row.get(col)
                if raw_val is None:
                    str_val = "-"
                else:
                    str_val = str(raw_val).strip()
                    if str_val == "" or str_val.lower() == "none":
                        str_val = "-"

                col_upper = col.upper()
                if any(k in col_upper for k in ("ESTADO", "SEVERIDAD", "PRIORIDAD", "ACTIVO", "OPERAT")) and str_val not in ("-", "", "None"):
                    self.table_results.setCellWidget(r, c, StatusBadge(str_val, self.table_results))
                else:
                    self.table_results.setItem(r, c, QTableWidgetItem(str_val))

        auto_fit_table_columns(self.table_results)

        self.lbl_pagination.setText(
            f"Pagina {self.current_page + 1} de {total_pages} (Mostrando {start_idx + 1}-{end_idx} de {total_records} registros)"
        )
        self.btn_prev_page.setEnabled(self.current_page > 0)
        self.btn_next_page.setEnabled(self.current_page < total_pages - 1)

    def export_to_csv(self):
        if not self.all_rows:
            InfoBar.warning(
                title="Sin datos para exportar",
                content="Ejecute primero un reporte antes de generar el archivo CSV.",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3500
            )
            return

        qid = self.query_combo.currentData()
        rep_code = "REPORTE"
        if qid in CONSULTAS_CATALOGO:
            rep_code = CONSULTAS_CATALOGO[qid].get("codigo", f"REP-{qid:02d}")

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"{rep_code}_{timestamp_str}.csv"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Reporte a CSV",
            default_filename,
            "Archivos CSV (*.csv);;Todos los Archivos (*.*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as csv_file:
                writer = csv.writer(csv_file, delimiter=",")
                writer.writerow(self.all_columns)
                for row in self.all_rows:
                    row_vals = []
                    for col in self.all_columns:
                        v = row.get(col)
                        row_vals.append("" if v is None else str(v))
                    writer.writerow(row_vals)

            InfoBar.success(
                title="Exportacion Exitosa",
                content=f"Se exportaron {len(self.all_rows)} filas a '{os.path.basename(file_path)}'.",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000
            )
        except Exception as ex:
            InfoBar.error(
                title="Error de Exportacion",
                content=f"No se pudo escribir el archivo CSV: {ex}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000
            )

    def on_error_occurred(self, error_msg: str):
        self.lbl_pagination.setText(f"Error al consultar Oracle: {error_msg}")
        InfoBar.error(
            title="Error de Oracle",
            content=error_msg,
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=5000
        )

    def on_worker_finished(self):
        self.btn_run.setEnabled(True)
        self.btn_export.setEnabled(True)
        if QApplication.overrideCursor() is not None:
            QApplication.restoreOverrideCursor()
