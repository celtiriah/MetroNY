"""
m7_incidents_interface.py - Vista principal del Modulo 7: Incidentes Operativos y Contingencias de Red.
Cumple estrictamente con los 7 requerimientos del enunciado oficial y las reglas de negocio del sistema:
1. Registro de incidencias con tipologia estandarizada y clasificacion por severidad.
2. Asociacion de incidentes con elementos de red respetando la restriccion de Arco Exclusivo (CK_INCIDENTE_ELEMENTO_ARCO).
3. Ciclo de vida completo (Abierto, En Atencion, Cerrado) con resolucion tecnica y bitacora de acciones.
4. Despacho y cancelacion automatica de viajes afectados (SP_CANCELAR_VIAJES_AFECTADOS).
5. Monitoreo en tiempo real de la tabla de auditoria BITACORA alimentada por TRG_INCIDENTE_AUDITORIA.
6. Calculo exacto de duracion de eventos e impacto en pasajeros.
7. Metricas estadisticas agregadas de red.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QHeaderView, QFormLayout, QTableWidgetItem, QGridLayout,
    QLabel, QSplitter
)

from qfluentwidgets import (
    TitleLabel, SubtitleLabel, CaptionLabel, BodyLabel, StrongBodyLabel,
    CardWidget, ComboBox, LineEdit, SearchLineEdit, SpinBox,
    PrimaryPushButton, PushButton, TableWidget, InfoBar, InfoBarPosition,
    SegmentedWidget, MessageBoxBase, MessageBox,
    FluentIcon as FIF
)

from services import m7_incidents_service, actions_service


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        if val is None or val == "-" or val == "":
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


def _safe_int(val: Any, default: int = 0) -> int:
    try:
        if val is None or val == "-" or val == "":
            return default
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_str(val: Any, default: str = "-") -> str:
    if val is None or val == "":
        return default
    return str(val)


# ==============================================================================
# DIALOGOS MODALES
# ==============================================================================

class RegistrarIncidenteDialog(MessageBoxBase):
    """Dialogo modal para reportar un incidente con SP_REGISTRAR_INCIDENTE."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.titleLabel = TitleLabel("Reportar Nuevo Incidente Operativo", self)
        self.viewLayout.addWidget(self.titleLabel)

        form = QFormLayout()
        form.setSpacing(8)

        # 1. Tipo
        self.combo_tipo = ComboBox(self)
        self.combo_tipo.addItems([
            "Falla Mecánica", "Falla Eléctrica", "Falla de Señalización",
            "Emergencia Médica", "Accidente", "Problema de Seguridad",
            "Objeto en la Vía", "Inundación", "Incendio", "Congestión",
            "Mantenimiento no Programado"
        ])
        form.addRow("Tipo de Eventualidad:", self.combo_tipo)

        # 2. Severidad
        self.combo_severidad = ComboBox(self)
        self.combo_severidad.addItems(["Bajo", "Medio", "Alto", "Crítico"])
        self.combo_severidad.setCurrentText("Medio")
        form.addRow("Nivel de Severidad:", self.combo_severidad)

        # 3. Reportado Por
        self.combo_reportado = ComboBox(self)
        for emp_id, label in actions_service.get_empleados_combo():
            self.combo_reportado.addItem(label, userData=emp_id)
        form.addRow("Personal que Reporta:", self.combo_reportado)

        # 4. Tipo de Elemento Afectado (Arco Exclusivo)
        self.combo_tipo_elem = ComboBox(self)
        self.combo_tipo_elem.addItems(["ESTACION", "TREN", "RUTA", "LINEA", "EQUIPO", "VIAJE_PROGRAMADO"])
        self.combo_tipo_elem.currentTextChanged.connect(self.on_tipo_elem_changed)
        form.addRow("Tipo de Activo Afectado:", self.combo_tipo_elem)

        self.combo_elem = ComboBox(self)
        form.addRow("Elemento Específico:", self.combo_elem)

        # 5. Tipo de Afectacion
        self.combo_afectacion = ComboBox(self)
        self.combo_afectacion.addItems([
            "Retraso", "Cambio de Ruta", "Cancelación", "Cierre de Estación",
            "Cierre de Plataforma", "Retiro de Tren", "Suspensión de Tramo"
        ])
        form.addRow("Afectación Operativa:", self.combo_afectacion)

        # 6. Descripcion
        self.txt_desc = LineEdit(self)
        self.txt_desc.setPlaceholderText("Descripción técnica breve de la contingencia...")
        form.addRow("Descripción del Hecho:", self.txt_desc)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Registrar Incidente")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(520)

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
        elif tipo == "EQUIPO":
            for eq_id, label in actions_service.get_equipos_combo():
                self.combo_elem.addItem(label, userData=eq_id)
        elif tipo == "VIAJE_PROGRAMADO":
            from services.db import execute_query
            viajes = execute_query("SELECT id_viaje, numero_viaje, fecha, estado FROM VIAJE_PROGRAMADO WHERE estado IN ('Programado', 'En Abordaje', 'En Curso') ORDER BY id_viaje DESC FETCH FIRST 20 ROWS ONLY")["rows"]
            for v in viajes:
                self.combo_elem.addItem(f"Viaje {v['NUMERO_VIAJE']} ({v['FECHA']}) - [{v['ESTADO']}]", userData=int(v['ID_VIAJE']))

    def validate(self) -> bool:
        if not self.txt_desc.text().strip():
            self.txt_desc.setFocus()
            return False
        return True


class CerrarIncidenteDialog(MessageBoxBase):
    """Dialogo modal para resolver y cerrar formalmente un incidente operativo."""
    def __init__(self, incidente: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.incidente = incidente
        self.init_ui()

    def init_ui(self):
        self.titleLabel = TitleLabel("Cierre Técnico de Incidente", self)
        self.viewLayout.addWidget(self.titleLabel)

        form = QFormLayout()
        form.setSpacing(8)

        num = _safe_str(self.incidente.get("NUMERO_INCIDENTE"))
        tipo = _safe_str(self.incidente.get("TIPO"))
        sev = _safe_str(self.incidente.get("NIVEL_SEVERIDAD"))
        lbl_info = BodyLabel(f"Incidente: {num} ({tipo}) | Severidad: {sev}", self)
        form.addRow("Identificación:", lbl_info)

        self.txt_causa = LineEdit(self)
        self.txt_causa.setPlaceholderText("Causa raíz técnica determinada tras la inspección...")
        form.addRow("Causa Identificada:", self.txt_causa)

        self.txt_acciones = LineEdit(self)
        self.txt_acciones.setPlaceholderText("Acciones correctivas realizadas para restablecer el servicio...")
        form.addRow("Acciones Realizadas:", self.txt_acciones)

        self.spin_pasajeros = SpinBox(self)
        self.spin_pasajeros.setRange(0, 500000)
        self.spin_pasajeros.setValue(_safe_int(self.incidente.get("PASAJEROS_AFECTADOS_ESTIMADO"), 500))
        form.addRow("Pasajeros Impactados:", self.spin_pasajeros)

        self.txt_fecha_fin = LineEdit(self)
        self.txt_fecha_fin.setText(datetime.now().strftime("%Y-%m-%d %H:%M"))
        form.addRow("Fecha / Hora Cierre:", self.txt_fecha_fin)

        lbl_notice = CaptionLabel(
            "Al cerrar el incidente, su estado pasará a 'Cerrado' y la auditoría quedará registrada en BITACORA.",
            self
        )
        form.addRow(lbl_notice)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Confirmar Cierre")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(500)

    def validate(self) -> bool:
        if not self.txt_causa.text().strip() or not self.txt_acciones.text().strip():
            return False
        return True


class AsociarElementoDialog(MessageBoxBase):
    """Dialogo modal para asociar un nuevo elemento de red a un incidente respetando Arco Exclusivo."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.titleLabel = TitleLabel("Asociar Elemento Afectado", self)
        self.viewLayout.addWidget(self.titleLabel)

        form = QFormLayout()
        form.setSpacing(8)

        self.combo_tipo = ComboBox(self)
        self.combo_tipo.addItems(["ESTACION", "TREN", "RUTA", "LINEA", "EQUIPO", "VIAJE_PROGRAMADO"])
        self.combo_tipo.currentTextChanged.connect(self.on_tipo_changed)
        form.addRow("Tipo de Elemento:", self.combo_tipo)

        self.combo_entidad = ComboBox(self)
        form.addRow("Elemento de Red:", self.combo_entidad)

        self.combo_afectacion = ComboBox(self)
        self.combo_afectacion.addItems([
            "Retraso", "Cambio de Ruta", "Cancelación", "Cierre de Estación",
            "Cierre de Plataforma", "Retiro de Tren", "Suspensión de Tramo"
        ])
        form.addRow("Afectación Operativa:", self.combo_afectacion)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Vincular Elemento")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(480)

        self.on_tipo_changed("ESTACION")

    def on_tipo_changed(self, tipo: str):
        self.combo_entidad.clear()
        if tipo == "ESTACION":
            for est_id, label in actions_service.get_estaciones_combo():
                self.combo_entidad.addItem(label, userData=est_id)
        elif tipo == "TREN":
            for tren_id, label in actions_service.get_trenes_combo():
                self.combo_entidad.addItem(label, userData=tren_id)
        elif tipo == "RUTA":
            for ruta_id, label in actions_service.get_rutas_combo():
                self.combo_entidad.addItem(label, userData=ruta_id)
        elif tipo == "LINEA":
            for lin_id, label in actions_service.get_lineas_combo():
                self.combo_entidad.addItem(label, userData=lin_id)
        elif tipo == "EQUIPO":
            for eq_id, label in actions_service.get_equipos_combo():
                self.combo_entidad.addItem(label, userData=eq_id)
        elif tipo == "VIAJE_PROGRAMADO":
            from services.db import execute_query
            viajes = execute_query("SELECT id_viaje, numero_viaje, fecha, estado FROM VIAJE_PROGRAMADO WHERE estado IN ('Programado', 'En Abordaje', 'En Curso') ORDER BY id_viaje DESC FETCH FIRST 20 ROWS ONLY")["rows"]
            for v in viajes:
                self.combo_entidad.addItem(f"Viaje {v['NUMERO_VIAJE']} ({v['FECHA']}) - [{v['ESTADO']}]", userData=int(v['ID_VIAJE']))


class ModificarAfectacionDialog(MessageBoxBase):
    """Dialogo modal para cambiar la severidad u operacion de afectacion de un elemento."""
    def __init__(self, elemento_nombre: str, afectacion_actual: str, parent=None):
        super().__init__(parent)
        self.elemento_nombre = elemento_nombre
        self.afectacion_actual = afectacion_actual
        self.init_ui()

    def init_ui(self):
        self.titleLabel = TitleLabel("Modificar Afectación Operativa", self)
        self.viewLayout.addWidget(self.titleLabel)

        form = QFormLayout()
        form.setSpacing(10)

        lbl_elem = StrongBodyLabel(self.elemento_nombre, self)
        form.addRow("Activo Afectado:", lbl_elem)

        self.combo_afectacion = ComboBox(self)
        afectaciones = [
            "Retraso", "Cambio de Ruta", "Cancelación", "Cierre de Estación",
            "Cierre de Plataforma", "Retiro de Tren", "Suspensión de Tramo"
        ]
        self.combo_afectacion.addItems(afectaciones)
        self.combo_afectacion.setCurrentText(self.afectacion_actual)
        form.addRow("Nueva Afectación:", self.combo_afectacion)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Actualizar")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(440)


# ==============================================================================
# VISTA PRINCIPAL: IncidentsInterface
# ==============================================================================

class IncidentsInterface(QWidget):
    """
    Vista principal del Modulo 7: Incidentes Operativos y Contingencias de Red.
    Disenada con 5 pestanas de ancho completo en contenedor independiente.
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("incidentsInterface")
        self.incidents_cache: List[Dict[str, Any]] = []
        self.selected_incident_id: Optional[int] = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # ----------------------------------------------------------------------
        # 1. CONTENEDOR DE TITULO Y SUBTITULO (SEPARADO)
        # ----------------------------------------------------------------------
        header_card = CardWidget(self)
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(18, 14, 18, 14)
        header_layout.setSpacing(4)

        title = TitleLabel("Incidentes Operativos y Contingencias de Red", header_card)
        subtitle = SubtitleLabel("Modulo 7: Monitoreo de contingencias, gestion de elementos afectados con Arco Exclusivo, cancelacion de viajes y auditoria", header_card)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addWidget(header_card)

        # ----------------------------------------------------------------------
        # 2. CONTENEDOR INDEPENDIENTE DE PESTANAS (ANCHO COMPLETO)
        # ----------------------------------------------------------------------
        tabs_layout = QHBoxLayout()
        self.segmented_tabs = SegmentedWidget(self)
        self.segmented_tabs.addItem("tab_monitoreo", "Centro de Incidentes")
        self.segmented_tabs.addItem("tab_elementos", "Elementos Afectados (Arco Exclusivo)")
        self.segmented_tabs.addItem("tab_despacho", "Impacto y Cancelación de Viajes")
        self.segmented_tabs.addItem("tab_bitacora", "Bitácora de Auditoría")
        self.segmented_tabs.addItem("tab_metricas", "Métricas y Red")

        self.segmented_tabs.setCurrentItem("tab_monitoreo")
        self.segmented_tabs.currentItemChanged.connect(self.on_tab_changed)

        tabs_layout.addWidget(self.segmented_tabs)
        main_layout.addLayout(tabs_layout)

        # ----------------------------------------------------------------------
        # 3. STACKED WIDGET DE VISTAS
        # ----------------------------------------------------------------------
        self.stack_views = QStackedWidget(self)

        self.init_tab_monitoreo()
        self.init_tab_elementos()
        self.init_tab_despacho()
        self.init_tab_bitacora()
        self.init_tab_metricas()

        main_layout.addWidget(self.stack_views, stretch=1)

    def showEvent(self, a0):
        super().showEvent(a0)
        if not self.segmented_tabs.currentItem():
            self.segmented_tabs.setCurrentItem("tab_monitoreo")

    def on_tab_changed(self, key: str):
        if key == "tab_monitoreo":
            self.stack_views.setCurrentIndex(0)
            self.refresh_incidentes()
        elif key == "tab_elementos":
            self.stack_views.setCurrentIndex(1)
            self.refresh_elementos_view()
        elif key == "tab_despacho":
            self.stack_views.setCurrentIndex(2)
            self.refresh_despacho_view()
        elif key == "tab_bitacora":
            self.stack_views.setCurrentIndex(3)
            self.refresh_bitacora_view()
        else:
            self.stack_views.setCurrentIndex(4)
            self.refresh_metricas_view()

    # ==========================================================================
    # PESTANA 1: CENTRO DE INCIDENTES (MONITOREO)
    # ==========================================================================

    def init_tab_monitoreo(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(12)

        # 1. KPIs
        card_kpis = CardWidget(tab_widget)
        kpi_layout = QHBoxLayout(card_kpis)
        kpi_layout.setContentsMargins(16, 12, 16, 12)
        kpi_layout.setSpacing(18)

        self.lbl_kpi_activos = StrongBodyLabel("Incidentes Activos: -", card_kpis)
        self.lbl_kpi_en_atencion = StrongBodyLabel("En Atención: -", card_kpis)
        self.lbl_kpi_criticos = StrongBodyLabel("Críticos / Altos: -", card_kpis)
        self.lbl_kpi_pasajeros = StrongBodyLabel("Pasajeros Afectados: -", card_kpis)
        self.lbl_kpi_cancelados = StrongBodyLabel("Viajes Cancelados: -", card_kpis)

        kpi_layout.addWidget(self.lbl_kpi_activos)
        kpi_layout.addWidget(self.lbl_kpi_en_atencion)
        kpi_layout.addWidget(self.lbl_kpi_criticos)
        kpi_layout.addWidget(self.lbl_kpi_pasajeros)
        kpi_layout.addWidget(self.lbl_kpi_cancelados)
        kpi_layout.addStretch(1)
        v_layout.addWidget(card_kpis)

        # 2. Barra de Filtros y Acciones
        bar_card = CardWidget(tab_widget)
        bar_layout = QHBoxLayout(bar_card)
        bar_layout.setContentsMargins(14, 10, 14, 10)
        bar_layout.setSpacing(10)

        self.search_inc = SearchLineEdit(bar_card)
        self.search_inc.setPlaceholderText("Buscar por código, descripción o causa raíz...")
        self.search_inc.textChanged.connect(self.refresh_incidentes)
        bar_layout.addWidget(self.search_inc, stretch=1)

        self.combo_filtro_estado = ComboBox(bar_card)
        self.combo_filtro_estado.addItems(["(Todos)", "Abierto", "En Atención", "Cerrado"])
        self.combo_filtro_estado.currentIndexChanged.connect(self.refresh_incidentes)
        bar_layout.addWidget(self.combo_filtro_estado)

        self.combo_filtro_sev = ComboBox(bar_card)
        self.combo_filtro_sev.addItems(["(Todas)", "Bajo", "Medio", "Alto", "Crítico"])
        self.combo_filtro_sev.currentIndexChanged.connect(self.refresh_incidentes)
        bar_layout.addWidget(self.combo_filtro_sev)

        self.btn_nuevo_inc = PrimaryPushButton("Reportar Incidente", bar_card, FIF.ADD)
        self.btn_nuevo_inc.clicked.connect(self.handle_nuevo_incidente)
        bar_layout.addWidget(self.btn_nuevo_inc)

        self.btn_atender = PushButton("Atender Evento", bar_card, FIF.SYNC)
        self.btn_atender.clicked.connect(self.handle_atender_evento)
        bar_layout.addWidget(self.btn_atender)

        self.btn_cerrar_inc = PushButton("Resolver y Cerrar", bar_card, FIF.COMPLETED)
        self.btn_cerrar_inc.clicked.connect(self.handle_cerrar_incidente)
        bar_layout.addWidget(self.btn_cerrar_inc)

        self.btn_cancelar_viajes = PushButton("Despachar Cancelación", bar_card, FIF.CANCEL)
        self.btn_cancelar_viajes.clicked.connect(self.handle_cancelar_viajes_directo)
        bar_layout.addWidget(self.btn_cancelar_viajes)

        v_layout.addWidget(bar_card)

        # 3. Tabla de Incidentes
        self.table_incidentes = TableWidget(tab_widget)
        self.table_incidentes.setColumnCount(9)
        self.table_incidentes.setHorizontalHeaderLabels([
            "Nº Incidente", "Tipo", "Severidad", "Elementos Afectados",
            "Inicio", "Duración", "Estado", "Reportado Por", "Pasajeros Est."
        ])
        self.table_incidentes.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table_incidentes.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)

        header = self.table_incidentes.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)

        self.table_incidentes.itemSelectionChanged.connect(self.on_incidente_selected)
        v_layout.addWidget(self.table_incidentes, stretch=1)

        self.stack_views.addWidget(tab_widget)

    def refresh_incidentes(self):
        est = self.combo_filtro_estado.currentText()
        sev = self.combo_filtro_sev.currentText()
        st = self.search_inc.text().strip()

        self.incidents_cache = m7_incidents_service.get_incidentes(
            estado_filter=est if est != "(Todos)" else None,
            severidad_filter=sev if sev != "(Todas)" else None,
            search_text=st if st else None
        )

        self.table_incidentes.blockSignals(True)
        self.table_incidentes.setRowCount(len(self.incidents_cache))
        for r, row in enumerate(self.incidents_cache):
            num = _safe_str(row.get("NUMERO_INCIDENTE"))
            tipo = _safe_str(row.get("TIPO"))
            sev_val = _safe_str(row.get("NIVEL_SEVERIDAD"))
            elem = _safe_str(row.get("ELEMENTOS_AFECTADOS_STR"), "General")
            f_ini = _safe_str(row.get("FECHA_HORA_INICIO"))
            dur = _safe_int(row.get("DURACION_MINUTOS"))
            dur_str = f"{dur} min" if dur < 120 else f"{dur // 60} h {dur % 60} min"
            estado = _safe_str(row.get("ESTADO"))
            rep = _safe_str(row.get("REPORTADO_POR"))
            pax = _safe_str(row.get("PASAJEROS_AFECTADOS_ESTIMADO"))

            self.table_incidentes.setItem(r, 0, QTableWidgetItem(num))
            self.table_incidentes.setItem(r, 1, QTableWidgetItem(tipo))
            self.table_incidentes.setItem(r, 2, QTableWidgetItem(sev_val))
            self.table_incidentes.setItem(r, 3, QTableWidgetItem(elem))
            self.table_incidentes.setItem(r, 4, QTableWidgetItem(f_ini))
            self.table_incidentes.setItem(r, 5, QTableWidgetItem(dur_str))
            self.table_incidentes.setItem(r, 6, QTableWidgetItem(estado))
            self.table_incidentes.setItem(r, 7, QTableWidgetItem(rep))
            self.table_incidentes.setItem(r, 8, QTableWidgetItem(pax))

        self.table_incidentes.blockSignals(False)
        self.refresh_kpis()

    def refresh_kpis(self):
        kpis = m7_incidents_service.get_kpis_incidentes()
        self.lbl_kpi_activos.setText(f"Incidentes Activos: {kpis['activos']}")
        self.lbl_kpi_en_atencion.setText(f"En Atención: {kpis['en_atencion']}")
        self.lbl_kpi_criticos.setText(f"Críticos / Altos: {kpis['criticos_altos']}")
        self.lbl_kpi_pasajeros.setText(f"Pasajeros Afectados: {kpis['pasajeros_afectados']:,}")
        self.lbl_kpi_cancelados.setText(f"Viajes Cancelados: {kpis['viajes_cancelados']}")

    def on_incidente_selected(self):
        selected = self.table_incidentes.selectedItems()
        if selected:
            r = selected[0].row()
            if r < len(self.incidents_cache):
                self.selected_incident_id = _safe_int(self.incidents_cache[r].get("ID_INCIDENTE"))
        else:
            self.selected_incident_id = None

    def handle_nuevo_incidente(self):
        dialog = RegistrarIncidenteDialog(self.window())
        if dialog.exec():
            if not dialog.validate():
                InfoBar.warning("Validación", "Indique la descripción del incidente.", parent=self.window(), duration=3000)
                return

            tipo = dialog.combo_tipo.currentText()
            sev = dialog.combo_severidad.currentText()
            rep_id = dialog.combo_reportado.currentData()
            tipo_elem = dialog.combo_tipo_elem.currentText()
            elem_id = dialog.combo_elem.currentData()
            afectacion = dialog.combo_afectacion.currentText()
            desc = dialog.txt_desc.text().strip()

            res = m7_incidents_service.registrar_incidente(
                tipo=tipo,
                descripcion=desc,
                nivel_severidad=sev,
                reportado_por_id=int(rep_id) if rep_id is not None else 1,
                tipo_elemento=tipo_elem,
                elemento_id=int(elem_id) if elem_id is not None else None,
                tipo_afectacion=afectacion
            )

            if res.get("success"):
                InfoBar.success(
                    "Incidente Reportado",
                    f"Incidente {res.get('numero_incidente')} registrado exitosamente en Oracle.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4000
                )
                self.refresh_incidentes()
            else:
                InfoBar.error("Error al Registrar", res.get("error", ""), parent=self.window(), duration=4500)

    def handle_atender_evento(self):
        if not self.selected_incident_id:
            InfoBar.warning("Selección Requerida", "Seleccione un incidente de la tabla.", parent=self.window(), duration=3000)
            return

        res = m7_incidents_service.cambiar_estado(self.selected_incident_id, "En Atención")
        if res.get("success"):
            InfoBar.success("Estado Actualizado", "El incidente ha pasado a estado 'En Atención'.", parent=self.window(), duration=3000)
            self.refresh_incidentes()
        else:
            InfoBar.error("Error", res.get("error", ""), parent=self.window(), duration=4000)

    def handle_cerrar_incidente(self):
        if not self.selected_incident_id:
            InfoBar.warning("Selección Requerida", "Seleccione el incidente que desea resolver y cerrar.", parent=self.window(), duration=3000)
            return

        incidente = next((i for i in self.incidents_cache if _safe_int(i.get("ID_INCIDENTE")) == self.selected_incident_id), None)
        if not incidente:
            return

        dialog = CerrarIncidenteDialog(incidente, self.window())
        if dialog.exec():
            if not dialog.validate():
                InfoBar.warning("Validación", "Complete la causa identificada y las acciones realizadas.", parent=self.window(), duration=3000)
                return

            res = m7_incidents_service.cerrar_incidente(
                id_incidente=self.selected_incident_id,
                causa_identificada=dialog.txt_causa.text(),
                acciones_realizadas=dialog.txt_acciones.text(),
                pasajeros_afectados=dialog.spin_pasajeros.value(),
                fecha_fin=dialog.txt_fecha_fin.text().strip() if dialog.txt_fecha_fin.text().strip() else None
            )

            if res.get("success"):
                InfoBar.success("Incidente Cerrado", res.get("mensaje", ""), parent=self.window(), duration=4000)
                self.refresh_incidentes()
            else:
                InfoBar.error("Error al Cerrar", res.get("error", ""), parent=self.window(), duration=4500)

    def handle_cancelar_viajes_directo(self):
        if not self.selected_incident_id:
            InfoBar.warning("Selección Requerida", "Seleccione un incidente para cancelar sus viajes afectados.", parent=self.window(), duration=3000)
            return

        box = MessageBox(
            "Despacho de Cancelación",
            "¿Desea ejecutar el procedimiento canónico SP_CANCELAR_VIAJES_AFECTADOS para cancelar todos los viajes vinculados a las rutas o estaciones afectadas por este incidente?",
            self.window()
        )
        if box.exec():
            res = m7_incidents_service.despachar_cancelacion_viajes(self.selected_incident_id)
            if res.get("success"):
                tot = res.get("viajes_cancelados", 0)
                InfoBar.info("Cancelaciones Despachadas", f"Se cancelaron {tot} viaje(s) programados.", parent=self.window(), duration=4000)
                self.refresh_incidentes()
            else:
                InfoBar.error("Fallo al Cancelar", res.get("error", ""), parent=self.window(), duration=4500)

    # ==========================================================================
    # PESTANA 2: ELEMENTOS DE RED AFECTADOS (ARCO EXCLUSIVO)
    # ==========================================================================

    def init_tab_elementos(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(12)

        bar_card = CardWidget(tab_widget)
        bar_layout = QHBoxLayout(bar_card)
        bar_layout.setContentsMargins(14, 10, 14, 10)
        bar_layout.setSpacing(10)

        bar_layout.addWidget(BodyLabel("Incidente Activo:", bar_card))
        self.combo_elem_incidente = ComboBox(bar_card)
        self.combo_elem_incidente.currentIndexChanged.connect(self.on_elem_incidente_changed)
        bar_layout.addWidget(self.combo_elem_incidente, stretch=1)

        self.btn_asociar_elem = PrimaryPushButton("Asociar Elemento", bar_card, FIF.ADD)
        self.btn_asociar_elem.clicked.connect(self.handle_asociar_elemento)
        bar_layout.addWidget(self.btn_asociar_elem)

        self.btn_modificar_afectacion = PushButton("Modificar Afectación", bar_card, FIF.EDIT)
        self.btn_modificar_afectacion.clicked.connect(self.handle_modificar_afectacion)
        bar_layout.addWidget(self.btn_modificar_afectacion)

        self.btn_desvincular_elem = PushButton("Desvincular", bar_card, FIF.DELETE)
        self.btn_desvincular_elem.clicked.connect(self.handle_desvincular_elemento)
        bar_layout.addWidget(self.btn_desvincular_elem)

        v_layout.addWidget(bar_card)

        # Tabla de Elementos Afectados
        self.table_elementos = TableWidget(tab_widget)
        self.table_elementos.setColumnCount(4)
        self.table_elementos.setHorizontalHeaderLabels([
            "Tipo de Elemento (Arco)", "Elemento de Red Afectado", "Tipo de Afectación", "ID Asociación"
        ])
        self.table_elementos.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table_elementos.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)

        header = self.table_elementos.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        v_layout.addWidget(self.table_elementos, stretch=1)

        self.stack_views.addWidget(tab_widget)

    def refresh_elementos_view(self):
        incidentes = m7_incidents_service.get_incidentes()
        prev_id = self.combo_elem_incidente.currentData()

        self.combo_elem_incidente.blockSignals(True)
        self.combo_elem_incidente.clear()
        for inc in incidentes:
            num = _safe_str(inc.get("NUMERO_INCIDENTE"))
            tipo = _safe_str(inc.get("TIPO"))
            est = _safe_str(inc.get("ESTADO"))
            id_inc = _safe_int(inc.get("ID_INCIDENTE"))
            self.combo_elem_incidente.addItem(f"{num} - {tipo} [{est}]", userData=id_inc)

        if prev_id:
            for idx in range(self.combo_elem_incidente.count()):
                if self.combo_elem_incidente.itemData(idx) == prev_id:
                    self.combo_elem_incidente.setCurrentIndex(idx)
                    break
        self.combo_elem_incidente.blockSignals(False)

        self.on_elem_incidente_changed()

    def on_elem_incidente_changed(self):
        id_inc = self.combo_elem_incidente.currentData()
        if not id_inc:
            self.table_elementos.setRowCount(0)
            return

        elementos = m7_incidents_service.get_elementos_afectados(int(id_inc))
        self.table_elementos.blockSignals(True)
        self.table_elementos.setRowCount(len(elementos))
        for r, row in enumerate(elementos):
            tipo = _safe_str(row.get("TIPO_ELEMENTO"))
            nom = _safe_str(row.get("ELEMENTO_NOMBRE"))
            af = _safe_str(row.get("TIPO_AFECTACION"))
            id_ie = _safe_int(row.get("ID_INCIDENTE_ELEMENTO"))

            it_tipo = QTableWidgetItem(tipo)
            it_tipo.setData(Qt.ItemDataRole.UserRole, id_ie)
            self.table_elementos.setItem(r, 0, it_tipo)
            self.table_elementos.setItem(r, 1, QTableWidgetItem(nom))
            self.table_elementos.setItem(r, 2, QTableWidgetItem(af))
            self.table_elementos.setItem(r, 3, QTableWidgetItem(str(id_ie)))

        self.table_elementos.blockSignals(False)

    def handle_asociar_elemento(self):
        id_inc = self.combo_elem_incidente.currentData()
        if not id_inc:
            InfoBar.warning("Incidente Requerido", "Seleccione un incidente primero.", parent=self.window(), duration=3000)
            return

        dialog = AsociarElementoDialog(self.window())
        if dialog.exec():
            tipo_elem = dialog.combo_tipo.currentText()
            elem_id = dialog.combo_entidad.currentData()
            af = dialog.combo_afectacion.currentText()
            if not elem_id:
                return

            res = m7_incidents_service.asociar_elemento_afectado(int(id_inc), tipo_elem, int(elem_id), af)
            if res.get("success"):
                InfoBar.success("Elemento Asociado", res.get("mensaje", ""), parent=self.window(), duration=3000)
                self.on_elem_incidente_changed()
            else:
                InfoBar.error("Error Arco Exclusivo", res.get("error", ""), parent=self.window(), duration=5000)

    def handle_modificar_afectacion(self):
        selected = self.table_elementos.selectedItems()
        if not selected:
            InfoBar.warning("Selección Requerida", "Seleccione un elemento de la tabla para modificar su afectación.", parent=self.window(), duration=3000)
            return

        r = selected[0].row()
        item = self.table_elementos.item(r, 0)
        id_ie = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        item_nom = self.table_elementos.item(r, 1)
        nom = item_nom.text() if item_nom is not None else "Elemento"
        item_af = self.table_elementos.item(r, 2)
        af_actual = item_af.text() if item_af is not None else "Retraso"

        if not id_ie:
            return

        dialog = ModificarAfectacionDialog(nom, af_actual, self.window())
        if dialog.exec():
            nueva_af = dialog.combo_afectacion.currentText()
            res = m7_incidents_service.modificar_afectacion_elemento(int(id_ie), nueva_af)
            if res.get("success"):
                InfoBar.success("Afectación Actualizada", res.get("mensaje", ""), parent=self.window(), duration=3000)
                self.on_elem_incidente_changed()
            else:
                InfoBar.error("Error", res.get("error", ""), parent=self.window(), duration=4000)

    def handle_desvincular_elemento(self):
        selected = self.table_elementos.selectedItems()
        if not selected:
            InfoBar.warning("Selección Requerida", "Seleccione un elemento de la tabla para desvincular.", parent=self.window(), duration=3000)
            return

        r = selected[0].row()
        item = self.table_elementos.item(r, 0)
        id_ie = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if not id_ie:
            return

        box = MessageBox("Desvincular Elemento", "¿Confirma desvincular este elemento de red del incidente?", self.window())
        if box.exec():
            res = m7_incidents_service.desvincular_elemento(int(id_ie))
            if res.get("success"):
                InfoBar.success("Elemento Desvinculado", res.get("mensaje", ""), parent=self.window(), duration=3000)
                self.on_elem_incidente_changed()
            else:
                InfoBar.error("Error", res.get("error", ""), parent=self.window(), duration=4000)

    # ==========================================================================
    # PESTANA 3: IMPACTO Y CANCELACION DE VIAJES
    # ==========================================================================

    def init_tab_despacho(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(12)

        bar_card = CardWidget(tab_widget)
        bar_layout = QHBoxLayout(bar_card)
        bar_layout.setContentsMargins(14, 10, 14, 10)
        bar_layout.setSpacing(10)

        bar_layout.addWidget(BodyLabel("Incidente de Contingencia:", bar_card))
        self.combo_despacho_inc = ComboBox(bar_card)
        self.combo_despacho_inc.currentIndexChanged.connect(self.on_despacho_inc_changed)
        bar_layout.addWidget(self.combo_despacho_inc, stretch=1)

        self.btn_ejecutar_cancelacion = PrimaryPushButton("Despachar Cancelación (SP_CANCELAR_VIAJES_AFECTADOS)", bar_card, FIF.CANCEL)
        self.btn_ejecutar_cancelacion.clicked.connect(self.handle_ejecutar_cancelacion)
        bar_layout.addWidget(self.btn_ejecutar_cancelacion)

        v_layout.addWidget(bar_card)

        card_info = CardWidget(tab_widget)
        info_layout = QVBoxLayout(card_info)
        info_layout.setContentsMargins(14, 12, 14, 12)
        info_layout.setSpacing(6)

        self.lbl_despacho_summary = StrongBodyLabel("Viajes Programados que Intersectan con la Zona Afectada", card_info)
        info_layout.addWidget(self.lbl_despacho_summary)

        self.table_viajes_afectados = TableWidget(card_info)
        self.table_viajes_afectados.setColumnCount(8)
        self.table_viajes_afectados.setHorizontalHeaderLabels([
            "Nº Viaje", "Línea", "Ruta", "Tren Asignado", "Conductor", "Fecha", "Horario", "Estado Actual"
        ])
        self.table_viajes_afectados.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)

        header = self.table_viajes_afectados.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        info_layout.addWidget(self.table_viajes_afectados, stretch=1)
        v_layout.addWidget(card_info, stretch=1)

        self.stack_views.addWidget(tab_widget)

    def refresh_despacho_view(self):
        incidentes = m7_incidents_service.get_incidentes()
        prev_id = self.combo_despacho_inc.currentData()

        self.combo_despacho_inc.blockSignals(True)
        self.combo_despacho_inc.clear()
        for inc in incidentes:
            num = _safe_str(inc.get("NUMERO_INCIDENTE"))
            tipo = _safe_str(inc.get("TIPO"))
            sev = _safe_str(inc.get("NIVEL_SEVERIDAD"))
            id_inc = _safe_int(inc.get("ID_INCIDENTE"))
            self.combo_despacho_inc.addItem(f"{num} - {tipo} (Severidad {sev})", userData=id_inc)

        if prev_id:
            for idx in range(self.combo_despacho_inc.count()):
                if self.combo_despacho_inc.itemData(idx) == prev_id:
                    self.combo_despacho_inc.setCurrentIndex(idx)
                    break
        self.combo_despacho_inc.blockSignals(False)

        self.on_despacho_inc_changed()

    def on_despacho_inc_changed(self):
        id_inc = self.combo_despacho_inc.currentData()
        if not id_inc:
            self.table_viajes_afectados.setRowCount(0)
            self.lbl_despacho_summary.setText("Sin incidente seleccionado.")
            return

        viajes = m7_incidents_service.get_viajes_potencialmente_afectados(int(id_inc))
        self.table_viajes_afectados.blockSignals(True)
        self.table_viajes_afectados.setRowCount(len(viajes))
        for r, row in enumerate(viajes):
            num_v = _safe_str(row.get("NUMERO_VIAJE"))
            lin = f"Línea {_safe_str(row.get('LINEA_CODIGO'))}"
            rut = f"Ruta {_safe_str(row.get('RUTA_CODIGO'))}"
            tren = _safe_str(row.get("TREN_CODIGO"))
            cond = _safe_str(row.get("CONDUCTOR"))
            f = _safe_str(row.get("FECHA"))
            hor = f"{_safe_str(row.get('SALIDA'))} - {_safe_str(row.get('LLEGADA'))}"
            est = _safe_str(row.get("ESTADO"))

            self.table_viajes_afectados.setItem(r, 0, QTableWidgetItem(num_v))
            self.table_viajes_afectados.setItem(r, 1, QTableWidgetItem(lin))
            self.table_viajes_afectados.setItem(r, 2, QTableWidgetItem(rut))
            self.table_viajes_afectados.setItem(r, 3, QTableWidgetItem(tren))
            self.table_viajes_afectados.setItem(r, 4, QTableWidgetItem(cond))
            self.table_viajes_afectados.setItem(r, 5, QTableWidgetItem(f))
            self.table_viajes_afectados.setItem(r, 6, QTableWidgetItem(hor))
            self.table_viajes_afectados.setItem(r, 7, QTableWidgetItem(est))

        self.table_viajes_afectados.blockSignals(False)
        self.lbl_despacho_summary.setText(f"Se identificaron {len(viajes)} viaje(s) que intersectan con el sector afectado.")

    def handle_ejecutar_cancelacion(self):
        id_inc = self.combo_despacho_inc.currentData()
        if not id_inc:
            InfoBar.warning("Incidente Requerido", "Seleccione un incidente para despachar cancelaciones.", parent=self.window(), duration=3000)
            return

        box = MessageBox("Confirmar Cancelación", "¿Desea cancelar automáticamente todos los viajes intersectados mediante SP_CANCELAR_VIAJES_AFECTADOS?", self.window())
        if box.exec():
            res = m7_incidents_service.despachar_cancelacion_viajes(int(id_inc))
            if res.get("success"):
                tot = res.get("viajes_cancelados", 0)
                InfoBar.success("Despacho Ejecutado", f"Procedimiento completado. {tot} viaje(s) cancelados.", parent=self.window(), duration=4000)
                self.on_despacho_inc_changed()
                self.refresh_kpis()
            else:
                InfoBar.error("Fallo al Cancelar", res.get("error", ""), parent=self.window(), duration=4000)

    # ==========================================================================
    # PESTANA 4: BITACORA DE AUDITORIA EN TIEMPO REAL
    # ==========================================================================

    def init_tab_bitacora(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(12)

        bar_card = CardWidget(tab_widget)
        bar_layout = QHBoxLayout(bar_card)
        bar_layout.setContentsMargins(14, 10, 14, 10)
        bar_layout.setSpacing(10)

        self.search_bitacora = SearchLineEdit(bar_card)
        self.search_bitacora.setPlaceholderText("Buscar eventos en bitácora por descripción o usuario...")
        self.search_bitacora.textChanged.connect(self.refresh_bitacora_view)
        bar_layout.addWidget(self.search_bitacora, stretch=1)

        self.btn_sync_bitacora = PushButton("Actualizar Bitácora", bar_card, FIF.SYNC)
        self.btn_sync_bitacora.clicked.connect(self.refresh_bitacora_view)
        bar_layout.addWidget(self.btn_sync_bitacora)

        v_layout.addWidget(bar_card)

        self.table_bitacora = TableWidget(tab_widget)
        self.table_bitacora.setColumnCount(6)
        self.table_bitacora.setHorizontalHeaderLabels([
            "ID Bitácora", "Fecha / Hora", "Operación", "ID Incidente", "Usuario Oracle", "Descripción de Auditoría (Trigger)"
        ])
        self.table_bitacora.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)

        header = self.table_bitacora.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        v_layout.addWidget(self.table_bitacora, stretch=1)
        self.stack_views.addWidget(tab_widget)

    def refresh_bitacora_view(self):
        st = self.search_bitacora.text().strip()
        rows = m7_incidents_service.get_bitacora_incidentes(st if st else None)

        self.table_bitacora.blockSignals(True)
        self.table_bitacora.setRowCount(len(rows))
        for r, row in enumerate(rows):
            id_b = _safe_str(row.get("ID_BITACORA"))
            fh = _safe_str(row.get("FECHA_HORA"))
            op = _safe_str(row.get("OPERACION"))
            reg = _safe_str(row.get("REGISTRO_ID"))
            usr = _safe_str(row.get("USUARIO"))
            desc = _safe_str(row.get("DESCRIPCION"))

            self.table_bitacora.setItem(r, 0, QTableWidgetItem(id_b))
            self.table_bitacora.setItem(r, 1, QTableWidgetItem(fh))
            self.table_bitacora.setItem(r, 2, QTableWidgetItem(op))
            self.table_bitacora.setItem(r, 3, QTableWidgetItem(reg))
            self.table_bitacora.setItem(r, 4, QTableWidgetItem(usr))
            self.table_bitacora.setItem(r, 5, QTableWidgetItem(desc))

        self.table_bitacora.blockSignals(False)

    # ==========================================================================
    # PESTANA 5: METRICAS Y RED
    # ==========================================================================

    def init_tab_metricas(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Horizontal, tab_widget)

        # Panel 1: Por Severidad
        card_sev = CardWidget(splitter)
        sev_layout = QVBoxLayout(card_sev)
        sev_layout.setContentsMargins(14, 12, 14, 12)
        sev_layout.addWidget(StrongBodyLabel("Distribución por Nivel de Severidad", card_sev))
        self.table_stats_sev = TableWidget(card_sev)
        self.table_stats_sev.setColumnCount(2)
        self.table_stats_sev.setHorizontalHeaderLabels(["Severidad", "Total Incidentes"])
        self.table_stats_sev.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        h_sev = self.table_stats_sev.horizontalHeader()
        if h_sev is not None:
            h_sev.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            h_sev.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        sev_layout.addWidget(self.table_stats_sev)
        splitter.addWidget(card_sev)

        # Panel 2: Por Tipo
        card_tipo = CardWidget(splitter)
        tipo_layout = QVBoxLayout(card_tipo)
        tipo_layout.setContentsMargins(14, 12, 14, 12)
        tipo_layout.addWidget(StrongBodyLabel("Distribución por Tipo de Falla", card_tipo))
        self.table_stats_tipo = TableWidget(card_tipo)
        self.table_stats_tipo.setColumnCount(2)
        self.table_stats_tipo.setHorizontalHeaderLabels(["Tipo de Falla / Contingencia", "Total"])
        self.table_stats_tipo.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        h_tipo = self.table_stats_tipo.horizontalHeader()
        if h_tipo is not None:
            h_tipo.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            h_tipo.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        tipo_layout.addWidget(self.table_stats_tipo)
        splitter.addWidget(card_tipo)

        # Panel 3: Por Estado
        card_est = CardWidget(splitter)
        est_layout = QVBoxLayout(card_est)
        est_layout.setContentsMargins(14, 12, 14, 12)
        est_layout.addWidget(StrongBodyLabel("Distribución por Estado de Gestión", card_est))
        self.table_stats_est = TableWidget(card_est)
        self.table_stats_est.setColumnCount(2)
        self.table_stats_est.setHorizontalHeaderLabels(["Estado", "Total"])
        self.table_stats_est.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        h_est = self.table_stats_est.horizontalHeader()
        if h_est is not None:
            h_est.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            h_est.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        est_layout.addWidget(self.table_stats_est)
        splitter.addWidget(card_est)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)

        v_layout.addWidget(splitter, stretch=1)
        self.stack_views.addWidget(tab_widget)

    def refresh_metricas_view(self):
        stats = m7_incidents_service.get_estadisticas_incidentes()

        # Severidad
        self.table_stats_sev.blockSignals(True)
        self.table_stats_sev.setRowCount(len(stats["por_severidad"]))
        for r, row in enumerate(stats["por_severidad"]):
            self.table_stats_sev.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("NIVEL_SEVERIDAD"))))
            self.table_stats_sev.setItem(r, 1, QTableWidgetItem(str(row.get("TOTAL", 0))))
        self.table_stats_sev.blockSignals(False)

        # Tipo
        self.table_stats_tipo.blockSignals(True)
        self.table_stats_tipo.setRowCount(len(stats["por_tipo"]))
        for r, row in enumerate(stats["por_tipo"]):
            self.table_stats_tipo.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("TIPO"))))
            self.table_stats_tipo.setItem(r, 1, QTableWidgetItem(str(row.get("TOTAL", 0))))
        self.table_stats_tipo.blockSignals(False)

        # Estado
        self.table_stats_est.blockSignals(True)
        self.table_stats_est.setRowCount(len(stats["por_estado"]))
        for r, row in enumerate(stats["por_estado"]):
            self.table_stats_est.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("ESTADO"))))
            self.table_stats_est.setItem(r, 1, QTableWidgetItem(str(row.get("TOTAL", 0))))
        self.table_stats_est.blockSignals(False)

    # ==========================================================================
    # CARGA GLOBAL DESDE MAIN WINDOW
    # ==========================================================================

    def load_incidents_data(self):
        """Metodo invocado por load_all_data() en MetroFluentApp."""
        current_idx = self.stack_views.currentIndex()
        if current_idx == 0:
            self.refresh_incidentes()
        elif current_idx == 1:
            self.refresh_elementos_view()
        elif current_idx == 2:
            self.refresh_despacho_view()
        elif current_idx == 3:
            self.refresh_bitacora_view()
        else:
            self.refresh_metricas_view()

    def update_incidents(self, incidents: list):
        """Metodo de compatibilidad con versiones anteriores."""
        self.refresh_incidentes()
