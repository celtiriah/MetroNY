"""
m3_fleet_interface.py - Vista principal para el Módulo 3: Flota, Trenes y Material Rodante.
Cumple estrictamente con los 8 requerimientos del enunciado y las reglas de negocio 8, 11, 12 y 25:
1. Registrar trenes y vagones.
2. Armar la composición de un tren (acoplar vagones en orden de posición y recalcular capacidad).
3. Conservar el historial de vagones asignados (auditoría en TREN_VAGON sin borrado físico - Regla 25).
4. Cambiar el estado de un tren (auditado automáticamente en BITACORA por TRG_TREN_CAMBIO_ESTADO).
5. Consultar disponibilidad operativa (evaluación con FN_TREN_DISPONIBLE e inspecciones técnicas).
6. Asignar un tren a un viaje programado.
7. Impedir asignaciones simultáneas solapadas (Regla de negocio 8).
8. Impedir el uso de trenes en mantenimiento o fuera de servicio (Regla 11 y TRG_TREN_MANTENIMIENTO_NO_ASIGNAR).
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QHeaderView, QFormLayout, QTableWidgetItem, QGridLayout
)

from qfluentwidgets import (
    TitleLabel, SubtitleLabel, CaptionLabel, BodyLabel, StrongBodyLabel,
    CardWidget, ComboBox, LineEdit, SearchLineEdit, DoubleSpinBox, SpinBox,
    PrimaryPushButton, PushButton, TableWidget, InfoBar, InfoBarPosition,
    SegmentedWidget, MessageBoxBase, MessageBox, FluentIcon as FIF
)

from services import m3_fleet_service, actions_service


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
# DIALOGOS MODALES FLUENT (MODULO 3)
# ==============================================================================

class TrenDialog(MessageBoxBase):
    """Diálogo modal Fluent para registrar o modificar datos de un tren."""
    def __init__(self, parent=None, tren_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.tren_data = tren_data
        self.es_edicion = tren_data is not None

        titulo = "Modificar Tren" if self.es_edicion else "Registrar Nuevo Tren"
        self.titleLabel = SubtitleLabel(titulo, self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        # 1. Código Interno
        self.txt_codigo = LineEdit(self)
        self.txt_codigo.setPlaceholderText("p.ej. TR-501")
        if self.es_edicion and self.tren_data:
            self.txt_codigo.setText(_safe_str(self.tren_data.get("CODIGO_INTERNO", "")))
        form.addRow("Código Interno:", self.txt_codigo)

        # 2. Modelo de Tren
        self.combo_modelo = ComboBox(self)
        modelos = m3_fleet_service.get_modelos_combo()
        target_mod_idx = 0
        current_mod_id = _safe_int(self.tren_data.get("MODELO_ID")) if self.es_edicion and self.tren_data else None
        for i, m in enumerate(modelos):
            m_id = _safe_int(m.get("ID_MODELO", 0))
            label = f"{m.get('NOMBRE_MODELO', '')} ({m.get('FABRICANTE', '')})"
            self.combo_modelo.addItem(label, userData=m_id)
            if current_mod_id and m_id == current_mod_id:
                target_mod_idx = i
        if modelos:
            self.combo_modelo.setCurrentIndex(target_mod_idx)
        form.addRow("Modelo de Tren:", self.combo_modelo)

        # 3. Año de Fabricación
        self.spin_anio = SpinBox(self)
        self.spin_anio.setRange(1980, 2035)
        anio_val = _safe_int(self.tren_data.get("ANIO_FABRICACION")) if self.es_edicion and self.tren_data else datetime.now().year
        self.spin_anio.setValue(anio_val if anio_val > 1980 else datetime.now().year)
        form.addRow("Año Fabricación:", self.spin_anio)

        # 4. Depósito Base
        self.combo_deposito = ComboBox(self)
        self.combo_deposito.addItem("(Sin Depósito Asignado)", userData=None)
        depositos = m3_fleet_service.get_depositos_combo()
        target_dep_idx = 0
        current_dep_id = _safe_int(self.tren_data.get("DEPOSITO_ID")) if self.es_edicion and self.tren_data else None
        for i, d in enumerate(depositos, start=1):
            d_id = _safe_int(d.get("ID_DEPOSITO", 0))
            self.combo_deposito.addItem(f"{d.get('NOMBRE', '')} ({d.get('CODIGO', '')})", userData=d_id)
            if current_dep_id and d_id == current_dep_id:
                target_dep_idx = i
        self.combo_deposito.setCurrentIndex(target_dep_idx)
        form.addRow("Depósito Base:", self.combo_deposito)

        # 5. Kilometraje Acumulado
        self.spin_km = DoubleSpinBox(self)
        self.spin_km.setRange(0.0, 9999999.0)
        self.spin_km.setDecimals(1)
        self.spin_km.setSuffix(" km")
        km_val = _safe_float(self.tren_data.get("KILOMETRAJE_ACUMULADO")) if self.es_edicion and self.tren_data else 0.0
        self.spin_km.setValue(km_val)
        form.addRow("Kilometraje:", self.spin_km)

        # 6. Fechas de Inspección Técnica
        self.txt_ult_insp = LineEdit(self)
        self.txt_ult_insp.setPlaceholderText("YYYY-MM-DD")
        ult_insp_str = _safe_str(self.tren_data.get("FECHA_ULTIMA_INSPECCION", "")) if self.es_edicion and self.tren_data else ""
        if ult_insp_str != "-":
            self.txt_ult_insp.setText(ult_insp_str)
        form.addRow("Última Inspección:", self.txt_ult_insp)

        self.txt_prox_insp = LineEdit(self)
        self.txt_prox_insp.setPlaceholderText("YYYY-MM-DD")
        prox_insp_str = _safe_str(self.tren_data.get("FECHA_PROXIMA_INSPECCION", "")) if self.es_edicion and self.tren_data else ""
        if prox_insp_str != "-":
            self.txt_prox_insp.setText(prox_insp_str)
        form.addRow("Próxima Inspección:", self.txt_prox_insp)

        # 7. Estado Operativo (solo al crear)
        if not self.es_edicion:
            self.combo_estado = ComboBox(self)
            self.combo_estado.addItems(["Disponible", "En Mantenimiento", "Fuera de Servicio", "Retirado"])
            form.addRow("Estado Inicial:", self.combo_estado)

        self.viewLayout.addLayout(form)

        # Botones
        self.yesButton.setText("Guardar Tren" if self.es_edicion else "Registrar Tren")
        self.cancelButton.setText("Cancelar")

    def get_data(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "codigo_interno": self.txt_codigo.text().strip(),
            "modelo_id": self.combo_modelo.currentData(),
            "anio_fabricacion": self.spin_anio.value(),
            "deposito_id": self.combo_deposito.currentData(),
            "kilometraje_acumulado": self.spin_km.value(),
            "fecha_ultima_inspeccion": self.txt_ult_insp.text().strip() or None,
            "fecha_proxima_inspeccion": self.txt_prox_insp.text().strip() or None,
        }
        if not self.es_edicion and hasattr(self, "combo_estado"):
            data["estado_operativo"] = self.combo_estado.currentText()
        return data


class VagonDialog(MessageBoxBase):
    """Diálogo modal Fluent para registrar o modificar datos de un vagón."""
    def __init__(self, parent=None, vagon_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.vagon_data = vagon_data
        self.es_edicion = vagon_data is not None

        titulo = "Modificar Vagón" if self.es_edicion else "Registrar Nuevo Vagón"
        self.titleLabel = SubtitleLabel(titulo, self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        # 1. Número de Serie
        self.txt_serie = LineEdit(self)
        self.txt_serie.setPlaceholderText("p.ej. VG-2001")
        if self.es_edicion and self.vagon_data:
            self.txt_serie.setText(_safe_str(self.vagon_data.get("NUMERO_SERIE", "")))
        form.addRow("Número de Serie:", self.txt_serie)

        # 2. Tipo de Vagón
        self.combo_tipo = ComboBox(self)
        self.combo_tipo.addItems(["Pasajero Regular", "Cabina Conductor", "Mixto", "Especial PMR"])
        if self.es_edicion and self.vagon_data:
            idx = self.combo_tipo.findText(_safe_str(self.vagon_data.get("TIPO_VAGON", "Pasajero Regular")))
            if idx >= 0:
                self.combo_tipo.setCurrentIndex(idx)
        form.addRow("Tipo de Vagón:", self.combo_tipo)

        # 3. Capacidad Sentados
        self.spin_sentados = SpinBox(self)
        self.spin_sentados.setRange(0, 300)
        sent_val = _safe_int(self.vagon_data.get("CAPACIDAD_SENTADOS")) if self.es_edicion and self.vagon_data else 40
        self.spin_sentados.setValue(sent_val)
        form.addRow("Capacidad Sentados:", self.spin_sentados)

        # 4. Capacidad De Pie
        self.spin_pie = SpinBox(self)
        self.spin_pie.setRange(0, 500)
        pie_val = _safe_int(self.vagon_data.get("CAPACIDAD_DE_PIE")) if self.es_edicion and self.vagon_data else 160
        self.spin_pie.setValue(pie_val)
        form.addRow("Capacidad De Pie:", self.spin_pie)

        # 5. Año Fabricación
        self.spin_anio = SpinBox(self)
        self.spin_anio.setRange(1980, 2035)
        anio_val = _safe_int(self.vagon_data.get("ANIO_FABRICACION")) if self.es_edicion and self.vagon_data else datetime.now().year
        self.spin_anio.setValue(anio_val if anio_val > 1980 else datetime.now().year)
        form.addRow("Año Fabricación:", self.spin_anio)

        # 6. Accesibilidad PMR
        self.combo_acc = ComboBox(self)
        self.combo_acc.addItem("Sí (PMR Accesible)", userData="S")
        self.combo_acc.addItem("No (Estándar)", userData="N")
        if self.es_edicion and self.vagon_data:
            acc_val = _safe_str(self.vagon_data.get("ACCESIBILIDAD", "S"))
            self.combo_acc.setCurrentIndex(0 if acc_val == "S" else 1)
        form.addRow("Accesibilidad:", self.combo_acc)

        # 7. Estado Inicial (solo al crear)
        if not self.es_edicion:
            self.combo_estado = ComboBox(self)
            self.combo_estado.addItems(["Disponible", "Fuera de Servicio", "Mantenimiento"])
            form.addRow("Estado Inicial:", self.combo_estado)

        self.viewLayout.addLayout(form)

        # Botones
        self.yesButton.setText("Guardar Vagón" if self.es_edicion else "Registrar Vagón")
        self.cancelButton.setText("Cancelar")

    def get_data(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "numero_serie": self.txt_serie.text().strip(),
            "tipo_vagon": self.combo_tipo.currentText(),
            "capacidad_sentados": self.spin_sentados.value(),
            "capacidad_de_pie": self.spin_pie.value(),
            "anio_fabricacion": self.spin_anio.value(),
            "accesibilidad": self.combo_acc.currentData(),
        }
        if not self.es_edicion and hasattr(self, "combo_estado"):
            data["estado"] = self.combo_estado.currentText()
        return data


class AcoplarVagonDialog(MessageBoxBase):
    """Diálogo modal para acoplar un vagón libre a la formación activa de un tren."""
    def __init__(self, cod_tren: str, proxima_pos: int, vagones_disponibles: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(f"Acoplar Vagón a Tren {cod_tren}", self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        self.viewLayout.addWidget(CaptionLabel(
            "Seleccione un vagón libre del inventario para incorporarlo a la formación del tren.\n"
            "El estado del vagón pasará automáticamente a 'En Uso' y se recalculará la capacidad total del tren.",
            self
        ))

        form = QFormLayout()
        form.setSpacing(8)

        self.combo_vagon = ComboBox(self)
        if not vagones_disponibles:
            self.combo_vagon.addItem("(No hay vagones disponibles para acoplar)", userData=None)
        else:
            for v in vagones_disponibles:
                v_id = _safe_int(v.get("ID_VAGON", 0))
                serie = v.get("NUMERO_SERIE", "")
                tipo = v.get("TIPO_VAGON", "")
                cap = _safe_int(v.get("CAPACIDAD_TOTAL", 0))
                self.combo_vagon.addItem(f"{serie} - {tipo} (Cap: {cap} pax)", userData=v_id)
        form.addRow("Vagón a Acoplar:", self.combo_vagon)

        self.spin_pos = SpinBox(self)
        self.spin_pos.setRange(1, 20)
        self.spin_pos.setValue(proxima_pos)
        form.addRow("Posición en Formación:", self.spin_pos)

        self.viewLayout.addLayout(form)

        self.yesButton.setText("Acoplar Vagón")
        self.cancelButton.setText("Cancelar")
        if not vagones_disponibles:
            self.yesButton.setEnabled(False)

    def get_selected_vagon_id(self) -> Optional[int]:
        return self.combo_vagon.currentData()

    def get_posicion(self) -> int:
        return self.spin_pos.value()


class CambiarEstadoTrenDialog(MessageBoxBase):
    """Diálogo modal para cambiar el estado operativo de un tren."""
    def __init__(self, cod_tren: str, estado_actual: str, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(f"Cambiar Estado de Tren {cod_tren}", self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        self.viewLayout.addWidget(CaptionLabel(
            "El cambio de estado operativo será auditado automáticamente en la tabla BITACORA\n"
            "mediante el trigger TRG_TREN_CAMBIO_ESTADO de Oracle.", self
        ))

        form = QFormLayout()
        form.setSpacing(8)

        self.lbl_actual = StrongBodyLabel(estado_actual, self)
        form.addRow("Estado Actual:", self.lbl_actual)

        self.combo_nuevo = ComboBox(self)
        estados = ["Disponible", "En Operación", "En Mantenimiento", "Fuera de Servicio", "Retirado"]
        self.combo_nuevo.addItems(estados)
        idx = self.combo_nuevo.findText(estado_actual)
        if idx >= 0:
            self.combo_nuevo.setCurrentIndex(idx)
        form.addRow("Nuevo Estado:", self.combo_nuevo)

        self.viewLayout.addLayout(form)

        self.yesButton.setText("Actualizar Estado")
        self.cancelButton.setText("Cancelar")

    def get_nuevo_estado(self) -> str:
        return self.combo_nuevo.currentText()


class CambiarEstadoVagonDialog(MessageBoxBase):
    """Diálogo modal para cambiar el estado de un vagón desacoplado."""
    def __init__(self, num_serie: str, estado_actual: str, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(f"Cambiar Estado de Vagón {num_serie}", self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        form.addRow("Estado Actual:", StrongBodyLabel(estado_actual, self))

        self.combo_nuevo = ComboBox(self)
        self.combo_nuevo.addItems(["Disponible", "Fuera de Servicio", "Mantenimiento"])
        idx = self.combo_nuevo.findText(estado_actual)
        if idx >= 0:
            self.combo_nuevo.setCurrentIndex(idx)
        form.addRow("Nuevo Estado:", self.combo_nuevo)

        self.viewLayout.addLayout(form)

        self.yesButton.setText("Actualizar Estado")
        self.cancelButton.setText("Cancelar")

    def get_nuevo_estado(self) -> str:
        return self.combo_nuevo.currentText()


class AsignarTrenViajeDialog(MessageBoxBase):
    """Diálogo modal para asignar o reasignar un tren a un viaje programado."""
    def __init__(self, id_viaje: int, num_viaje: str, trenes_disponibles: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.id_viaje = id_viaje
        self.titleLabel = SubtitleLabel(f"Asignar Tren a Viaje {num_viaje}", self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        self.viewLayout.addWidget(CaptionLabel(
            "Reglas de Negocio Validadas:\n"
            "- Regla 11: Trenes en mantenimiento o fuera de servicio no pueden asignarse.\n"
            "- Regla 8: Un tren no puede estar asignado a dos viajes simultáneos.",
            self
        ))

        form = QFormLayout()
        form.setSpacing(8)

        self.combo_tren = ComboBox(self)
        if not trenes_disponibles:
            self.combo_tren.addItem("(No hay trenes aptos para servicio)", userData=None)
        else:
            for t in trenes_disponibles:
                t_id = _safe_int(t.get("ID_TREN", 0))
                cod = t.get("CODIGO_INTERNO", "")
                mod = t.get("NOMBRE_MODELO", "")
                cap = _safe_int(t.get("CAPACIDAD_TOTAL", 0))
                self.combo_tren.addItem(f"{cod} - {mod} (Cap: {cap} pax)", userData=t_id)
        form.addRow("Tren a Asignar:", self.combo_tren)

        self.viewLayout.addLayout(form)

        self.yesButton.setText("Asignar Tren")
        self.cancelButton.setText("Cancelar")
        if not trenes_disponibles:
            self.yesButton.setEnabled(False)

    def get_selected_tren_id(self) -> Optional[int]:
        return self.combo_tren.currentData()


class CrearOrdenMantenimientoDialog(MessageBoxBase):
    """
    Diálogo modal Fluent para enviar material rodante o equipos a taller de mantenimiento.
    Preservado y perfeccionado para compatibilidad operativa con el módulo de talleres.
    """
    def __init__(self, preselected_equipo_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("Crear Orden de Mantenimiento / Taller", self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        # 1. Equipo / Tren a Intervenir
        self.combo_equipo = ComboBox(self)
        equipos = actions_service.get_equipos_combo()
        target_idx = 0
        for i, (eq_id, label) in enumerate(equipos):
            self.combo_equipo.addItem(label, userData=eq_id)
            if preselected_equipo_id and eq_id == preselected_equipo_id:
                target_idx = i
        if equipos:
            self.combo_equipo.setCurrentIndex(target_idx)
        form.addRow("Unidad / Activo a Intervenir:", self.combo_equipo)

        # 2. Tipo de Mantenimiento
        self.combo_tipo = ComboBox(self)
        self.combo_tipo.addItems(["Preventivo", "Correctivo", "Predictivo", "Inspección de Seguridad"])
        form.addRow("Tipo de Mantenimiento:", self.combo_tipo)

        # 3. Prioridad
        self.combo_prioridad = ComboBox(self)
        self.combo_prioridad.addItems(["Media", "Alta", "Urgente", "Baja"])
        form.addRow("Nivel de Prioridad:", self.combo_prioridad)

        # 4. Técnico Líder Responsable
        self.combo_tecnico = ComboBox(self)
        tecnicos = actions_service.get_tecnicos_combo()
        for tec_id, label in tecnicos:
            self.combo_tecnico.addItem(label, userData=tec_id)
        form.addRow("Técnico Asignado:", self.combo_tecnico)

        # 5. Descripción del Trabajo
        self.txt_desc = LineEdit(self)
        self.txt_desc.setPlaceholderText("p.ej. Torneado de ruedas, revisión de tracción y frenos...")
        form.addRow("Descripción del Trabajo:", self.txt_desc)

        self.viewLayout.addLayout(form)

        # Botones
        self.yesButton.setText("Crear Orden de Taller")
        self.cancelButton.setText("Cancelar")


# ==============================================================================
# VISTA PRINCIPAL (MODULO 3: FLOTA Y TRENES)
# ==============================================================================

class FleetInterface(QWidget):
    """
    Vista principal para el Módulo 3: Flota, Trenes y Material Rodante.
    Dispone el título en su propio CardWidget y las pestañas en un contenedor independiente.
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("fleetInterface")

        self.selected_tren_id: Optional[int] = None
        self.selected_tren_codigo: str = ""
        self.selected_vagon_id: Optional[int] = None
        self.trenes_cache: List[Dict[str, Any]] = []
        self.vagones_cache: List[Dict[str, Any]] = []

        self.init_ui()
        self.load_all_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # ----------------------------------------------------------------------
        # 1. CONTENEDOR EXCLUSIVO DE TITULO Y SUBTITULO (SIN TABS EN ESTE CONTENEDOR)
        # ----------------------------------------------------------------------
        header_card = CardWidget(self)
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(18, 14, 18, 14)
        header_layout.setSpacing(4)

        title = TitleLabel("Flota, Trenes y Material Rodante", header_card)
        subtitle = SubtitleLabel("Modulo 3: Gestion de trenes, composicion de vagones, historial de formaciones y asignacion", header_card)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        main_layout.addWidget(header_card)

        # ----------------------------------------------------------------------
        # 2. CONTENEDOR INDEPENDIENTE DE PESTANAS (SEGMENTED WIDGET)
        # ----------------------------------------------------------------------
        tabs_layout = QHBoxLayout()
        self.segmented_tabs = SegmentedWidget(self)
        self.segmented_tabs.addItem("tab_trenes", "Flota y Formación de Trenes")
        self.segmented_tabs.addItem("tab_vagones", "Inventario de Vagones")
        self.segmented_tabs.addItem("tab_historial", "Historial de Composición")
        self.segmented_tabs.addItem("tab_disponibilidad", "Disponibilidad y Asignaciones")

        # Seleccionar explícitamente la primera pestaña al inicio
        self.segmented_tabs.setCurrentItem("tab_trenes")
        self.segmented_tabs.currentItemChanged.connect(self.on_tab_changed)

        tabs_layout.addWidget(self.segmented_tabs)
        # tabs_layout.addStretch(1)
        main_layout.addLayout(tabs_layout)

        # ----------------------------------------------------------------------
        # 3. STACKED WIDGET PARA LAS VISTAS
        # ----------------------------------------------------------------------
        self.stack_views = QStackedWidget(self)

        self.init_tab_trenes()
        self.init_tab_vagones()
        self.init_tab_historial()
        self.init_tab_disponibilidad()

        main_layout.addWidget(self.stack_views, stretch=1)

    # ==========================================================================
    # PESTANA 1: FLOTA Y FORMACION DE TRENES
    # ==========================================================================

    def init_tab_trenes(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(10)

        # Barra de Acciones y Filtros de Trenes
        bar_actions = QHBoxLayout()
        bar_actions.setSpacing(8)

        self.search_trenes = SearchLineEdit(tab_widget)
        self.search_trenes.setPlaceholderText("Buscar por código de tren o modelo...")
        self.search_trenes.textChanged.connect(self.apply_trenes_filter)
        bar_actions.addWidget(self.search_trenes, stretch=3)

        bar_actions.addWidget(CaptionLabel("Estado:", tab_widget))
        self.combo_filtro_estado = ComboBox(tab_widget)
        self.combo_filtro_estado.addItems(["(Todos)", "Disponible", "En Operación", "En Mantenimiento", "Fuera de Servicio", "Retirado"])
        self.combo_filtro_estado.currentTextChanged.connect(self.refresh_trenes)
        bar_actions.addWidget(self.combo_filtro_estado, stretch=2)

        bar_actions.addWidget(CaptionLabel("Depósito:", tab_widget))
        self.combo_filtro_deposito = ComboBox(tab_widget)
        self.combo_filtro_deposito.addItem("(Todos)", userData=None)
        depositos = m3_fleet_service.get_depositos_combo()
        for d in depositos:
            self.combo_filtro_deposito.addItem(d.get("NOMBRE", ""), userData=_safe_int(d.get("ID_DEPOSITO", 0)))
        self.combo_filtro_deposito.currentIndexChanged.connect(self.refresh_trenes)
        bar_actions.addWidget(self.combo_filtro_deposito, stretch=2)

        self.btn_nuevo_tren = PrimaryPushButton("Nuevo Tren", tab_widget, FIF.ADD)
        self.btn_nuevo_tren.clicked.connect(self.handle_nuevo_tren)
        bar_actions.addWidget(self.btn_nuevo_tren)

        self.btn_modificar_tren = PushButton("Modificar Tren", tab_widget, FIF.EDIT)
        self.btn_modificar_tren.clicked.connect(self.handle_modificar_tren)
        bar_actions.addWidget(self.btn_modificar_tren)

        self.btn_estado_tren = PushButton("Cambiar Estado", tab_widget, FIF.SYNC)
        self.btn_estado_tren.clicked.connect(self.handle_cambiar_estado_tren)
        bar_actions.addWidget(self.btn_estado_tren)

        self.btn_enviar_taller = PushButton("Enviar a Taller", tab_widget, FIF.SETTING)
        self.btn_enviar_taller.clicked.connect(self.open_maintenance_dialog)
        bar_actions.addWidget(self.btn_enviar_taller)

        self.btn_eliminar_tren = PushButton("Eliminar", tab_widget, FIF.DELETE)
        self.btn_eliminar_tren.clicked.connect(self.handle_eliminar_tren)
        bar_actions.addWidget(self.btn_eliminar_tren)

        v_layout.addLayout(bar_actions)

        # Tabla Maestra de Trenes
        self.table_trenes = TableWidget(tab_widget)
        self.table_trenes.setBorderVisible(True)
        self.table_trenes.setColumnCount(11)
        self.table_trenes.setHorizontalHeaderLabels([
            "Código", "Modelo", "Fabricante", "Depósito Base", "Año Fab.",
            "Capacidad Total", "Kilometraje", "Estado Operativo",
            "Última Insp.", "Próxima Insp.", "Disponibilidad"
        ])
        ht = self.table_trenes.horizontalHeader()
        if ht is not None:
            ht.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_trenes.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_trenes.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table_trenes.itemSelectionChanged.connect(self.on_tren_selected)
        v_layout.addWidget(self.table_trenes, stretch=4)

        # Panel Inferior: Composición Activa del Tren Seleccionado (TREN_VAGON)
        card_comp = CardWidget(tab_widget)
        comp_layout = QVBoxLayout(card_comp)
        comp_layout.setContentsMargins(16, 12, 16, 12)
        comp_layout.setSpacing(8)

        bar_comp = QHBoxLayout()
        self.lbl_comp_title = StrongBodyLabel("Composición Activa del Tren Seleccionado (Vagones Acoplados)", card_comp)
        bar_comp.addWidget(self.lbl_comp_title)
        bar_comp.addStretch(1)

        self.btn_acoplar_vagon = PrimaryPushButton("Acoplar Vagón", card_comp, FIF.ADD)
        self.btn_acoplar_vagon.clicked.connect(self.handle_acoplar_vagon)
        bar_comp.addWidget(self.btn_acoplar_vagon)

        self.btn_desacoplar_vagon = PushButton("Desacoplar Vagón", card_comp, FIF.REMOVE)
        self.btn_desacoplar_vagon.clicked.connect(self.handle_desacoplar_vagon)
        bar_comp.addWidget(self.btn_desacoplar_vagon)

        self.btn_pos_up = PushButton("Subir Posición", card_comp, FIF.UP)
        self.btn_pos_up.clicked.connect(lambda: self.handle_cambiar_posicion(-1))
        bar_comp.addWidget(self.btn_pos_up)

        self.btn_pos_down = PushButton("Bajar Posición", card_comp, FIF.DOWN)
        self.btn_pos_down.clicked.connect(lambda: self.handle_cambiar_posicion(1))
        bar_comp.addWidget(self.btn_pos_down)

        comp_layout.addLayout(bar_comp)

        self.table_composicion = TableWidget(card_comp)
        self.table_composicion.setBorderVisible(True)
        self.table_composicion.setColumnCount(8)
        self.table_composicion.setHorizontalHeaderLabels([
            "Posición", "N° Serie Vagón", "Tipo de Vagón", "Cap. Sentados",
            "Cap. De Pie", "Capacidad Total", "Accesible PMR", "Fecha Acople"
        ])
        hc = self.table_composicion.horizontalHeader()
        if hc is not None:
            hc.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_composicion.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_composicion.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        comp_layout.addWidget(self.table_composicion)

        v_layout.addWidget(card_comp, stretch=3)
        self.stack_views.addWidget(tab_widget)

    # ==========================================================================
    # PESTANA 2: INVENTARIO DE VAGONES
    # ==========================================================================

    def init_tab_vagones(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(10)

        bar_actions = QHBoxLayout()
        bar_actions.setSpacing(8)

        self.search_vagones = SearchLineEdit(tab_widget)
        self.search_vagones.setPlaceholderText("Buscar por número de serie o tipo de vagón...")
        self.search_vagones.textChanged.connect(self.apply_vagones_filter)
        bar_actions.addWidget(self.search_vagones, stretch=3)

        bar_actions.addWidget(CaptionLabel("Estado:", tab_widget))
        self.combo_vag_estado = ComboBox(tab_widget)
        self.combo_vag_estado.addItems(["(Todos)", "Disponible", "En Uso", "Mantenimiento", "Fuera de Servicio"])
        self.combo_vag_estado.currentTextChanged.connect(self.refresh_vagones)
        bar_actions.addWidget(self.combo_vag_estado, stretch=2)

        bar_actions.addWidget(CaptionLabel("Tipo:", tab_widget))
        self.combo_vag_tipo = ComboBox(tab_widget)
        self.combo_vag_tipo.addItems(["(Todos)", "Pasajero Regular", "Cabina Conductor", "Mixto", "Especial PMR"])
        self.combo_vag_tipo.currentTextChanged.connect(self.refresh_vagones)
        bar_actions.addWidget(self.combo_vag_tipo, stretch=2)

        self.btn_nuevo_vagon = PrimaryPushButton("Nuevo Vagón", tab_widget, FIF.ADD)
        self.btn_nuevo_vagon.clicked.connect(self.handle_nuevo_vagon)
        bar_actions.addWidget(self.btn_nuevo_vagon)

        self.btn_modificar_vagon = PushButton("Modificar Vagón", tab_widget, FIF.EDIT)
        self.btn_modificar_vagon.clicked.connect(self.handle_modificar_vagon)
        bar_actions.addWidget(self.btn_modificar_vagon)

        self.btn_estado_vagon = PushButton("Cambiar Estado", tab_widget, FIF.SYNC)
        self.btn_estado_vagon.clicked.connect(self.handle_cambiar_estado_vagon)
        bar_actions.addWidget(self.btn_estado_vagon)

        self.btn_eliminar_vagon = PushButton("Eliminar", tab_widget, FIF.DELETE)
        self.btn_eliminar_vagon.clicked.connect(self.handle_eliminar_vagon)
        bar_actions.addWidget(self.btn_eliminar_vagon)

        v_layout.addLayout(bar_actions)

        # Tabla Maestra de Vagones
        self.table_vagones = TableWidget(tab_widget)
        self.table_vagones.setBorderVisible(True)
        self.table_vagones.setColumnCount(10)
        self.table_vagones.setHorizontalHeaderLabels([
            "N° Serie", "Tipo de Vagón", "Cap. Sentados", "Cap. De Pie",
            "Capacidad Total", "Año Fab.", "Estado", "Accesibilidad PMR",
            "Tren Acoplado", "Posición"
        ])
        hv = self.table_vagones.horizontalHeader()
        if hv is not None:
            hv.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_vagones.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_vagones.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        v_layout.addWidget(self.table_vagones)

        self.stack_views.addWidget(tab_widget)

    # ==========================================================================
    # PESTANA 3: HISTORIAL DE COMPOSICION
    # ==========================================================================

    def init_tab_historial(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(10)

        # Barra de Filtros de Historial
        bar_filters = QHBoxLayout()
        bar_filters.setSpacing(8)

        bar_filters.addWidget(CaptionLabel("Filtrar Tren:", tab_widget))
        self.combo_hist_tren = ComboBox(tab_widget)
        self.combo_hist_tren.addItem("(Todos los Trenes)", userData=None)
        self.combo_hist_tren.currentIndexChanged.connect(self.refresh_historial)
        bar_filters.addWidget(self.combo_hist_tren, stretch=2)

        bar_filters.addWidget(CaptionLabel("Asociación:", tab_widget))
        self.combo_hist_estado = ComboBox(tab_widget)
        self.combo_hist_estado.addItems(["(Todos)", "Activos", "Históricos"])
        self.combo_hist_estado.currentTextChanged.connect(self.refresh_historial)
        bar_filters.addWidget(self.combo_hist_estado, stretch=2)

        bar_filters.addStretch(1)

        self.btn_refresh_hist = PushButton("Actualizar Historial", tab_widget, FIF.SYNC)
        self.btn_refresh_hist.clicked.connect(self.refresh_historial)
        bar_filters.addWidget(self.btn_refresh_hist)

        v_layout.addLayout(bar_filters)

        # Tabla de Historial (TREN_VAGON)
        self.table_historial = TableWidget(tab_widget)
        self.table_historial.setBorderVisible(True)
        self.table_historial.setColumnCount(9)
        self.table_historial.setHorizontalHeaderLabels([
            "ID Registro", "Tren", "N° Serie Vagón", "Tipo Vagón",
            "Posición", "Capacidad", "Fecha Inicio (Acople)",
            "Fecha Fin (Desacople)", "Estado Asociación"
        ])
        hh = self.table_historial.horizontalHeader()
        if hh is not None:
            hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_historial.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_historial.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        v_layout.addWidget(self.table_historial)

        self.stack_views.addWidget(tab_widget)

    # ==========================================================================
    # PESTANA 4: DISPONIBILIDAD Y ASIGNACIONES A VIAJES
    # ==========================================================================

    def init_tab_disponibilidad(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(12)

        # Tarjeta 1: KPIs y Métricas de la Flota
        card_kpis = CardWidget(tab_widget)
        kpi_layout = QHBoxLayout(card_kpis)
        kpi_layout.setContentsMargins(16, 12, 16, 12)
        kpi_layout.setSpacing(20)

        self.lbl_kpi_total = StrongBodyLabel("Total Trenes: -", card_kpis)
        self.lbl_kpi_disp = StrongBodyLabel("Disponibles: -", card_kpis)
        self.lbl_kpi_oper = StrongBodyLabel("En Operación: -", card_kpis)
        self.lbl_kpi_maint = StrongBodyLabel("En Taller: -", card_kpis)
        self.lbl_kpi_vencidas = StrongBodyLabel("Insp. Vencidas: -", card_kpis)

        kpi_layout.addWidget(self.lbl_kpi_total)
        kpi_layout.addWidget(self.lbl_kpi_disp)
        kpi_layout.addWidget(self.lbl_kpi_oper)
        kpi_layout.addWidget(self.lbl_kpi_maint)
        kpi_layout.addWidget(self.lbl_kpi_vencidas)
        kpi_layout.addStretch(1)

        v_layout.addWidget(card_kpis)

        # Tarjeta 2: Diagnóstico Operativo en Tiempo Real del Tren
        card_diag = CardWidget(tab_widget)
        diag_layout = QVBoxLayout(card_diag)
        diag_layout.setContentsMargins(16, 12, 16, 12)
        diag_layout.setSpacing(8)

        bar_sel_tren = QHBoxLayout()
        bar_sel_tren.addWidget(CaptionLabel("Seleccionar Tren para Diagnóstico de Disponibilidad:", card_diag))
        self.combo_disp_tren = ComboBox(card_diag)
        self.combo_disp_tren.currentIndexChanged.connect(self.on_disp_tren_selected)
        bar_sel_tren.addWidget(self.combo_disp_tren, stretch=2)
        bar_sel_tren.addStretch(2)
        diag_layout.addLayout(bar_sel_tren)

        self.lbl_diag_resultado = StrongBodyLabel("Estado Operativo: Seleccione una unidad para evaluar", card_diag)
        self.lbl_diag_detalle = CaptionLabel("Detalle de aptitud técnica y órdenes de trabajo", card_diag)
        diag_layout.addWidget(self.lbl_diag_resultado)
        diag_layout.addWidget(self.lbl_diag_detalle)

        v_layout.addWidget(card_diag)

        # Tarjeta 3: Asignación de Trenes a Viajes Programados
        card_viajes = CardWidget(tab_widget)
        viajes_layout = QVBoxLayout(card_viajes)
        viajes_layout.setContentsMargins(16, 12, 16, 12)
        viajes_layout.setSpacing(8)

        bar_viajes_acts = QHBoxLayout()
        bar_viajes_acts.addWidget(StrongBodyLabel("Viajes Programados y Material Rodante Asignado", card_viajes))
        bar_viajes_acts.addStretch(1)

        self.btn_asignar_tren_viaje = PrimaryPushButton("Asignar Tren a Viaje", card_viajes, FIF.SEND)
        self.btn_asignar_tren_viaje.clicked.connect(self.handle_asignar_tren_viaje)
        bar_viajes_acts.addWidget(self.btn_asignar_tren_viaje)

        self.btn_desasignar_tren_viaje = PushButton("Desasignar Tren", card_viajes, FIF.CANCEL)
        self.btn_desasignar_tren_viaje.clicked.connect(self.handle_desasignar_tren_viaje)
        bar_viajes_acts.addWidget(self.btn_desasignar_tren_viaje)

        self.btn_refresh_viajes = PushButton("Actualizar Viajes", card_viajes, FIF.SYNC)
        self.btn_refresh_viajes.clicked.connect(self.refresh_viajes_flota)
        bar_viajes_acts.addWidget(self.btn_refresh_viajes)

        viajes_layout.addLayout(bar_viajes_acts)

        self.table_viajes_flota = TableWidget(card_viajes)
        self.table_viajes_flota.setBorderVisible(True)
        self.table_viajes_flota.setColumnCount(9)
        self.table_viajes_flota.setHorizontalHeaderLabels([
            "N° Viaje", "Ruta", "Línea", "Fecha", "Salida Prog.",
            "Llegada Prog.", "Tren Asignado", "Conductor", "Estado Viaje"
        ])
        hvf = self.table_viajes_flota.horizontalHeader()
        if hvf is not None:
            hvf.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_viajes_flota.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_viajes_flota.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        viajes_layout.addWidget(self.table_viajes_flota)

        v_layout.addWidget(card_viajes, stretch=4)
        self.stack_views.addWidget(tab_widget)

    # ==========================================================================
    # CONTROL DE PESTANAS Y CARGA GENERAL
    # ==========================================================================

    def on_tab_changed(self, key: str):
        if key == "tab_trenes":
            self.stack_views.setCurrentIndex(0)
            self.refresh_trenes()
        elif key == "tab_vagones":
            self.stack_views.setCurrentIndex(1)
            self.refresh_vagones()
        elif key == "tab_historial":
            self.stack_views.setCurrentIndex(2)
            self.refresh_historial()
        else:
            self.stack_views.setCurrentIndex(3)
            self.refresh_disponibilidad()

    def load_all_data(self):
        """Punto de entrada para sincronización general de datos del módulo."""
        self.refresh_trenes()
        self.populate_trenes_combos()
        self.refresh_vagones()
        self.refresh_historial()
        self.refresh_disponibilidad()

    def update_fleet(self, fleet: Optional[List] = None):
        """Compatibilidad con main_window.load_all_data."""
        self.load_all_data()

    def populate_trenes_combos(self):
        """Llena los combos que dependen de la lista de trenes activos."""
        trenes = m3_fleet_service.get_trenes()

        # Combo en Historial
        self.combo_hist_tren.blockSignals(True)
        self.combo_hist_tren.clear()
        self.combo_hist_tren.addItem("(Todos los Trenes)", userData=None)
        for t in trenes:
            t_id = _safe_int(t.get("ID_TREN", 0))
            self.combo_hist_tren.addItem(f"{t.get('CODIGO_INTERNO', '')} - {t.get('NOMBRE_MODELO', '')}", userData=t_id)
        self.combo_hist_tren.blockSignals(False)

        # Combo en Diagnóstico
        self.combo_disp_tren.blockSignals(True)
        self.combo_disp_tren.clear()
        for t in trenes:
            t_id = _safe_int(t.get("ID_TREN", 0))
            self.combo_disp_tren.addItem(f"{t.get('CODIGO_INTERNO', '')} - {t.get('NOMBRE_MODELO', '')}", userData=t_id)
        self.combo_disp_tren.blockSignals(False)

    # ==========================================================================
    # LOGICA PESTANA 1: FLOTA Y TRENES
    # ==========================================================================

    def refresh_trenes(self):
        estado = self.combo_filtro_estado.currentText()
        deposito_id = self.combo_filtro_deposito.currentData()
        self.trenes_cache = m3_fleet_service.get_trenes(
            estado_filter=estado if estado != "(Todos)" else None,
            deposito_id=deposito_id
        )
        self.apply_trenes_filter()

    def apply_trenes_filter(self):
        txt = self.search_trenes.text().strip().lower()
        filtered = self.trenes_cache
        if txt:
            filtered = [
                t for t in filtered
                if txt in str(t.get("CODIGO_INTERNO", "")).lower() or
                   txt in str(t.get("NOMBRE_MODELO", "")).lower() or
                   txt in str(t.get("FABRICANTE", "")).lower()
            ]

        self.table_trenes.setRowCount(len(filtered))
        for r, row in enumerate(filtered):
            self.table_trenes.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("CODIGO_INTERNO"))))
            self.table_trenes.setItem(r, 1, QTableWidgetItem(_safe_str(row.get("NOMBRE_MODELO"))))
            self.table_trenes.setItem(r, 2, QTableWidgetItem(_safe_str(row.get("FABRICANTE"))))
            self.table_trenes.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("NOMBRE_DEPOSITO"))))
            self.table_trenes.setItem(r, 4, QTableWidgetItem(_safe_str(row.get("ANIO_FABRICACION"))))
            self.table_trenes.setItem(r, 5, QTableWidgetItem(f"{_safe_int(row.get('CAPACIDAD_TOTAL')):,} pax"))
            self.table_trenes.setItem(r, 6, QTableWidgetItem(f"{_safe_float(row.get('KILOMETRAJE_ACUMULADO')):,} km"))

            estado_item = QTableWidgetItem(_safe_str(row.get("ESTADO_OPERATIVO")))
            self.table_trenes.setItem(r, 7, estado_item)

            self.table_trenes.setItem(r, 8, QTableWidgetItem(_safe_str(row.get("FECHA_ULTIMA_INSPECCION"))))

            prox_insp_str = _safe_str(row.get("FECHA_PROXIMA_INSPECCION"))
            prox_item = QTableWidgetItem(prox_insp_str)
            if _safe_int(row.get("INSPECCION_VENCIDA")) == 1:
                prox_item.setText(f"{prox_insp_str} (Vencida)")
            self.table_trenes.setItem(r, 9, prox_item)

            disp_str = "Apto (FN=1)" if _safe_int(row.get("DISPONIBLE_FN")) == 1 else "No Apto (FN=0)"
            self.table_trenes.setItem(r, 10, QTableWidgetItem(disp_str))

        if filtered and self.table_trenes.rowCount() > 0:
            self.table_trenes.selectRow(0)
        else:
            self.table_composicion.setRowCount(0)
            self.lbl_comp_title.setText("Composición Activa (Ningún tren seleccionado)")

    def on_tren_selected(self):
        selected_items = self.table_trenes.selectedItems()
        if not selected_items:
            return
        row = selected_items[0].row()
        cod_item = self.table_trenes.item(row, 0)
        if cod_item is None:
            return

        cod_tren = cod_item.text()
        tren = next((t for t in self.trenes_cache if t.get("CODIGO_INTERNO") == cod_tren), None)
        if not tren:
            return

        self.selected_tren_id = _safe_int(tren.get("ID_TREN", 0))
        self.selected_tren_codigo = cod_tren
        self.lbl_comp_title.setText(f"Composición Activa del Tren {cod_tren} ({tren.get('NOMBRE_MODELO', '')})")

        self.refresh_composicion()

    def refresh_composicion(self):
        if not self.selected_tren_id:
            self.table_composicion.setRowCount(0)
            return

        vagones_comp = m3_fleet_service.get_composicion_activa(self.selected_tren_id)
        self.table_composicion.setRowCount(len(vagones_comp))

        for r, row in enumerate(vagones_comp):
            self.table_composicion.setItem(r, 0, QTableWidgetItem(f"Posición {_safe_int(row.get('POSICION'))}"))
            self.table_composicion.setItem(r, 1, QTableWidgetItem(_safe_str(row.get("NUMERO_SERIE"))))
            self.table_composicion.setItem(r, 2, QTableWidgetItem(_safe_str(row.get("TIPO_VAGON"))))
            self.table_composicion.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("CAPACIDAD_SENTADOS"))))
            self.table_composicion.setItem(r, 4, QTableWidgetItem(_safe_str(row.get("CAPACIDAD_DE_PIE"))))
            self.table_composicion.setItem(r, 5, QTableWidgetItem(f"{_safe_int(row.get('CAPACIDAD_TOTAL')):,} pax"))
            acc_str = "Sí" if _safe_str(row.get("ACCESIBILIDAD")) == "S" else "No"
            self.table_composicion.setItem(r, 6, QTableWidgetItem(acc_str))
            self.table_composicion.setItem(r, 7, QTableWidgetItem(_safe_str(row.get("FECHA_INICIO"))))

    def handle_nuevo_tren(self):
        dlg = TrenDialog(parent=self.window())
        if dlg.exec():
            datos = dlg.get_data()
            if not datos.get("codigo_interno"):
                InfoBar.warning(title="Campo Obligatorio", content="El código interno es requerido.", parent=self.window(), duration=3500)
                return

            res = m3_fleet_service.crear_tren(datos)
            if res.get("success"):
                InfoBar.success(
                    title="Tren Registrado",
                    content=f"Tren {datos['codigo_interno']} registrado exitosamente en Oracle.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.load_all_data()
            else:
                InfoBar.error(
                    title="Error al Registrar Tren",
                    content=res.get("error", "No se pudo crear el tren."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )

    def handle_modificar_tren(self):
        if not self.selected_tren_id:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un tren en la tabla.", parent=self.window(), duration=3000)
            return

        tren_data = m3_fleet_service.get_tren_by_id(self.selected_tren_id)
        if not tren_data:
            return

        dlg = TrenDialog(parent=self.window(), tren_data=tren_data)
        if dlg.exec():
            datos = dlg.get_data()
            res = m3_fleet_service.modificar_tren(self.selected_tren_id, datos)
            if res.get("success"):
                InfoBar.success(
                    title="Tren Actualizado",
                    content="Los datos técnicos del tren se actualizaron correctamente.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.refresh_trenes()
            else:
                InfoBar.error(
                    title="Error al Modificar",
                    content=res.get("error", "No se pudo actualizar el tren."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )

    def handle_cambiar_estado_tren(self):
        if not self.selected_tren_id:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un tren de la tabla.", parent=self.window(), duration=3000)
            return

        tren = next((t for t in self.trenes_cache if _safe_int(t.get("ID_TREN")) == self.selected_tren_id), None)
        if not tren:
            return

        est_actual = _safe_str(tren.get("ESTADO_OPERATIVO"))
        dlg = CambiarEstadoTrenDialog(self.selected_tren_codigo, est_actual, parent=self.window())
        if dlg.exec():
            nuevo_estado = dlg.get_nuevo_estado()
            res = m3_fleet_service.cambiar_estado_tren(self.selected_tren_id, nuevo_estado)
            if res.get("success"):
                InfoBar.success(
                    title="Estado Actualizado",
                    content=f"Estado del tren {self.selected_tren_codigo} cambiado a '{nuevo_estado}' (Auditado en BITACORA).",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.load_all_data()
            else:
                InfoBar.error(
                    title="Error al Cambiar Estado",
                    content=res.get("error", "No se pudo cambiar el estado."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )

    def handle_eliminar_tren(self):
        if not self.selected_tren_id:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un tren para eliminar.", parent=self.window(), duration=3000)
            return

        box = MessageBox(
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar el tren {self.selected_tren_codigo} del sistema?",
            self.window()
        )
        if box.exec():
            res = m3_fleet_service.eliminar_tren(self.selected_tren_id)
            if res.get("success"):
                InfoBar.success(
                    title="Tren Eliminado",
                    content=f"Tren {self.selected_tren_codigo} eliminado del sistema.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.selected_tren_id = None
                self.load_all_data()
            else:
                InfoBar.error(
                    title="Error al Eliminar",
                    content=res.get("error", "No se pudo eliminar el tren."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )

    def open_maintenance_dialog(self):
        """Abre el diálogo para crear una orden de trabajo de taller."""
        pre_id = None
        if self.selected_tren_id:
            from services.db import execute_query
            sql = "SELECT id_equipo FROM EQUIPO WHERE tipo_referencia = 'TREN' AND referencia_id = :tid"
            rows = execute_query(sql, {"tid": self.selected_tren_id})["rows"]
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
                    content=f"Orden {res.get('numero_orden')} creada exitosamente. Estado actualizado en Oracle.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.load_all_data()
            else:
                InfoBar.error(
                    title="Error al Crear Orden",
                    content=res.get("error", "No se pudo crear la orden."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4000
                )

    # --------------------------------------------------------------------------
    # COMPOSICION DE TRENES (TREN_VAGON)
    # --------------------------------------------------------------------------

    def handle_acoplar_vagon(self):
        if not self.selected_tren_id:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un tren para acoplar vagones.", parent=self.window(), duration=3000)
            return

        vagones_disponibles = m3_fleet_service.get_vagones_disponibles_combo()
        proxima_pos = self.table_composicion.rowCount() + 1

        dlg = AcoplarVagonDialog(self.selected_tren_codigo, proxima_pos, vagones_disponibles, parent=self.window())
        if dlg.exec():
            vagon_id = dlg.get_selected_vagon_id()
            if not vagon_id:
                return

            pos = dlg.get_posicion()
            res = m3_fleet_service.acoplar_vagon(self.selected_tren_id, vagon_id, pos)
            if res.get("success"):
                InfoBar.success(
                    title="Vagón Acoplado",
                    content=res.get("mensaje", "Vagón acoplado exitosamente."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.refresh_composicion()
                self.refresh_trenes()
                self.refresh_vagones()
            else:
                InfoBar.error(
                    title="Error al Acoplar",
                    content=res.get("error", "No se pudo acoplar el vagón."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )

    def handle_desacoplar_vagon(self):
        selected = self.table_composicion.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un vagón de la composición activa.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        if self.selected_tren_id is None:
            return

        if self.selected_tren_id is None:
            return

        comp_activa = m3_fleet_service.get_composicion_activa(self.selected_tren_id)
        if row >= len(comp_activa):
            return

        item_tv = comp_activa[row]
        tv_id = _safe_int(item_tv.get("ID_TREN_VAGON", 0))
        num_serie = item_tv.get("NUMERO_SERIE", "")

        box = MessageBox(
            "Confirmar Desacople",
            f"¿Desea desacoplar el vagón {num_serie} de la formación?\n"
            f"El registro de acoplamiento se conservará en el historial con fecha de finalización (Regla 25).",
            self.window()
        )
        if box.exec():
            res = m3_fleet_service.desacoplar_vagon(tv_id)
            if res.get("success"):
                InfoBar.success(
                    title="Vagón Desacoplado",
                    content=res.get("mensaje", "Vagón desacoplado y liberado al inventario."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.refresh_composicion()
                self.refresh_trenes()
                self.refresh_vagones()
            else:
                InfoBar.error(
                    title="Error al Desacoplar",
                    content=res.get("error", "No se pudo desacoplar."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )

    def handle_cambiar_posicion(self, delta: int):
        selected = self.table_composicion.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        if self.selected_tren_id is None:
            return

        comp_activa = m3_fleet_service.get_composicion_activa(self.selected_tren_id)
        if row >= len(comp_activa):
            return

        item_tv = comp_activa[row]
        tv_id = _safe_int(item_tv.get("ID_TREN_VAGON", 0))
        pos_actual = _safe_int(item_tv.get("POSICION", 0))
        nueva_pos = pos_actual + delta

        if nueva_pos < 1 or nueva_pos > len(comp_activa):
            return

        res = m3_fleet_service.reordenar_posicion(tv_id, nueva_pos)
        if res.get("success"):
            self.refresh_composicion()
            # Mantener selección en la nueva fila
            new_row = row + delta
            if 0 <= new_row < self.table_composicion.rowCount():
                self.table_composicion.selectRow(new_row)

    # ==========================================================================
    # LOGICA PESTANA 2: INVENTARIO DE VAGONES
    # ==========================================================================

    def refresh_vagones(self):
        est = self.combo_vag_estado.currentText()
        tip = self.combo_vag_tipo.currentText()
        self.vagones_cache = m3_fleet_service.get_vagones(
            estado_filter=est if est != "(Todos)" else None,
            tipo_filter=tip if tip != "(Todos)" else None
        )
        self.apply_vagones_filter()

    def apply_vagones_filter(self):
        txt = self.search_vagones.text().strip().lower()
        filtered = self.vagones_cache
        if txt:
            filtered = [
                v for v in filtered
                if txt in str(v.get("NUMERO_SERIE", "")).lower() or
                   txt in str(v.get("TIPO_VAGON", "")).lower()
            ]

        self.table_vagones.setRowCount(len(filtered))
        for r, row in enumerate(filtered):
            self.table_vagones.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("NUMERO_SERIE"))))
            self.table_vagones.setItem(r, 1, QTableWidgetItem(_safe_str(row.get("TIPO_VAGON"))))
            self.table_vagones.setItem(r, 2, QTableWidgetItem(_safe_str(row.get("CAPACIDAD_SENTADOS"))))
            self.table_vagones.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("CAPACIDAD_DE_PIE"))))
            self.table_vagones.setItem(r, 4, QTableWidgetItem(f"{_safe_int(row.get('CAPACIDAD_TOTAL')):,} pax"))
            self.table_vagones.setItem(r, 5, QTableWidgetItem(_safe_str(row.get("ANIO_FABRICACION"))))
            self.table_vagones.setItem(r, 6, QTableWidgetItem(_safe_str(row.get("ESTADO"))))
            acc_str = "Sí (PMR)" if _safe_str(row.get("ACCESIBILIDAD")) == "S" else "No"
            self.table_vagones.setItem(r, 7, QTableWidgetItem(acc_str))

            tren_acop = _safe_str(row.get("TREN_ACOPLADO"))
            self.table_vagones.setItem(r, 8, QTableWidgetItem(tren_acop))

            pos_str = f"Pos. {_safe_int(row.get('POSICION_EN_TREN'))}" if row.get("POSICION_EN_TREN") else "-"
            self.table_vagones.setItem(r, 9, QTableWidgetItem(pos_str))

    def handle_nuevo_vagon(self):
        dlg = VagonDialog(parent=self.window())
        if dlg.exec():
            datos = dlg.get_data()
            if not datos.get("numero_serie"):
                InfoBar.warning(title="Campo Obligatorio", content="El número de serie es requerido.", parent=self.window(), duration=3500)
                return

            res = m3_fleet_service.crear_vagon(datos)
            if res.get("success"):
                InfoBar.success(
                    title="Vagón Registrado",
                    content=f"Vagón {datos['numero_serie']} agregado exitosamente al inventario.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.refresh_vagones()
            else:
                InfoBar.error(
                    title="Error al Crear Vagón",
                    content=res.get("error", "No se pudo registrar el vagón."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )

    def handle_modificar_vagon(self):
        selected = self.table_vagones.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un vagón de la tabla.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item = self.table_vagones.item(row, 0)
        if not item:
            return

        serie = item.text()
        vagon = next((v for v in self.vagones_cache if v.get("NUMERO_SERIE") == serie), None)
        if not vagon:
            return

        v_id = _safe_int(vagon.get("ID_VAGON", 0))
        dlg = VagonDialog(parent=self.window(), vagon_data=vagon)
        if dlg.exec():
            datos = dlg.get_data()
            res = m3_fleet_service.modificar_vagon(v_id, datos)
            if res.get("success"):
                InfoBar.success(
                    title="Vagón Actualizado",
                    content=f"Vagón {serie} actualizado correctamente.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.refresh_vagones()
                self.refresh_composicion()
                self.refresh_trenes()
            else:
                InfoBar.error(
                    title="Error al Modificar",
                    content=res.get("error", "No se pudo modificar."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )

    def handle_cambiar_estado_vagon(self):
        selected = self.table_vagones.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un vagón de la tabla.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item = self.table_vagones.item(row, 0)
        if not item:
            return

        serie = item.text()
        vagon = next((v for v in self.vagones_cache if v.get("NUMERO_SERIE") == serie), None)
        if not vagon:
            return

        v_id = _safe_int(vagon.get("ID_VAGON", 0))
        est_actual = _safe_str(vagon.get("ESTADO"))

        dlg = CambiarEstadoVagonDialog(serie, est_actual, parent=self.window())
        if dlg.exec():
            nuevo_estado = dlg.get_nuevo_estado()
            res = m3_fleet_service.cambiar_estado_vagon(v_id, nuevo_estado)
            if res.get("success"):
                InfoBar.success(
                    title="Estado Actualizado",
                    content=f"Estado del vagón {serie} cambiado a '{nuevo_estado}'.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.refresh_vagones()
            else:
                InfoBar.error(
                    title="Error al Cambiar Estado",
                    content=res.get("error", "No se pudo actualizar el estado."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )

    def handle_eliminar_vagon(self):
        selected = self.table_vagones.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un vagón para eliminar.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item = self.table_vagones.item(row, 0)
        if not item:
            return

        serie = item.text()
        vagon = next((v for v in self.vagones_cache if v.get("NUMERO_SERIE") == serie), None)
        if not vagon:
            return

        v_id = _safe_int(vagon.get("ID_VAGON", 0))

        box = MessageBox(
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar el vagón {serie} del inventario?",
            self.window()
        )
        if box.exec():
            res = m3_fleet_service.eliminar_vagon(v_id)
            if res.get("success"):
                InfoBar.success(
                    title="Vagón Eliminado",
                    content=f"Vagón {serie} eliminado del inventario.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.refresh_vagones()
            else:
                InfoBar.error(
                    title="Error al Eliminar",
                    content=res.get("error", "No se pudo eliminar el vagón."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )

    # ==========================================================================
    # LOGICA PESTANA 3: HISTORIAL DE COMPOSICION
    # ==========================================================================

    def refresh_historial(self):
        tren_id = self.combo_hist_tren.currentData()
        est_filtro = self.combo_hist_estado.currentText()
        if est_filtro == "(Todos)":
            est_filtro = None

        hist = m3_fleet_service.get_historial_composicion(tren_id=tren_id, estado_filtro=est_filtro)
        self.table_historial.setRowCount(len(hist))

        for r, row in enumerate(hist):
            self.table_historial.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("ID_TREN_VAGON"))))
            self.table_historial.setItem(r, 1, QTableWidgetItem(_safe_str(row.get("CODIGO_TREN"))))
            self.table_historial.setItem(r, 2, QTableWidgetItem(_safe_str(row.get("NUMERO_VAGON"))))
            self.table_historial.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("TIPO_VAGON"))))
            self.table_historial.setItem(r, 4, QTableWidgetItem(f"Pos. {_safe_int(row.get('POSICION'))}"))
            self.table_historial.setItem(r, 5, QTableWidgetItem(f"{_safe_int(row.get('CAPACIDAD_VAGON')):,} pax"))
            self.table_historial.setItem(r, 6, QTableWidgetItem(_safe_str(row.get("FECHA_INICIO"))))

            fecha_fin = _safe_str(row.get("FECHA_FIN"))
            fin_str = fecha_fin if fecha_fin != "-" else "(Actualmente Acoplado)"
            self.table_historial.setItem(r, 7, QTableWidgetItem(fin_str))

            est_asoc = _safe_str(row.get("ESTADO_ASOCIACION"))
            self.table_historial.setItem(r, 8, QTableWidgetItem(est_asoc))

    # ==========================================================================
    # LOGICA PESTANA 4: DISPONIBILIDAD Y VIAJES
    # ==========================================================================

    def refresh_disponibilidad(self):
        # 1. KPIs
        kpis = m3_fleet_service.get_kpis_flota()
        self.lbl_kpi_total.setText(f"Total Trenes: {kpis.get('total_trenes', 0)}")
        self.lbl_kpi_disp.setText(f"Disponibles: {kpis.get('disponibles', 0)}")
        self.lbl_kpi_oper.setText(f"En Operación: {kpis.get('en_operacion', 0)}")
        self.lbl_kpi_maint.setText(f"En Taller: {kpis.get('en_mantenimiento', 0)}")
        self.lbl_kpi_vencidas.setText(f"Insp. Vencidas: {kpis.get('inspecciones_vencidas', 0)}")

        # 2. Diagnóstico del tren seleccionado en el combo
        self.on_disp_tren_selected()

        # 3. Viajes de la flota
        self.refresh_viajes_flota()

    def on_disp_tren_selected(self):
        t_id = self.combo_disp_tren.currentData()
        if not t_id:
            return

        diag = m3_fleet_service.verificar_disponibilidad_tren(t_id)
        if not diag.get("success"):
            return

        cod = diag.get("codigo_interno", "")
        apto = diag.get("apto_para_servicio", False)
        fn_val = diag.get("disponible_fn", False)
        estado = diag.get("estado_operativo", "")
        dias_insp = diag.get("dias_para_inspeccion", "-")
        prox_insp = diag.get("fecha_proxima_inspeccion", "-")
        ordenes = diag.get("ordenes_mantenimiento_activas", 0)
        viajes_curso = diag.get("viajes_en_curso", 0)

        if apto:
            self.lbl_diag_resultado.setText(
                f"Resultado: Tren {cod} está APTO PARA SERVICIO (FN_TREN_DISPONIBLE = 1, Inspección Vigente)"
            )
        else:
            motivos_str = " | ".join(diag.get("motivos", ["No disponible"]))
            self.lbl_diag_resultado.setText(
                f"Resultado: Tren {cod} NO DISPONIBLE PARA SERVICIO - Causa: {motivos_str}"
            )

        self.lbl_diag_detalle.setText(
            f"Estado Operativo: {estado} | FN_TREN_DISPONIBLE: {'1 (Disponible)' if fn_val else '0 (No Disponible)'} | "
            f"Próxima Inspección: {prox_insp} ({dias_insp} días) | Órdenes Taller Activas: {ordenes} | "
            f"Viajes en Curso: {viajes_curso}"
        )

    def refresh_viajes_flota(self):
        viajes = m3_fleet_service.get_viajes_asignados_tren()
        self.table_viajes_flota.setRowCount(len(viajes))

        for r, row in enumerate(viajes):
            self.table_viajes_flota.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("NUMERO_VIAJE"))))
            self.table_viajes_flota.setItem(r, 1, QTableWidgetItem(f"Ruta {_safe_str(row.get('CODIGO_RUTA'))}"))
            self.table_viajes_flota.setItem(r, 2, QTableWidgetItem(f"Línea {_safe_str(row.get('CODIGO_LINEA'))}"))
            self.table_viajes_flota.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("FECHA"))))
            self.table_viajes_flota.setItem(r, 4, QTableWidgetItem(_safe_str(row.get("SALIDA_PROG"))))
            self.table_viajes_flota.setItem(r, 5, QTableWidgetItem(_safe_str(row.get("LLEGADA_PROG"))))

            cod_tren = _safe_str(row.get("CODIGO_TREN"))
            tren_str = cod_tren if cod_tren != "-" else "(Sin Asignar)"
            self.table_viajes_flota.setItem(r, 6, QTableWidgetItem(tren_str))

            self.table_viajes_flota.setItem(r, 7, QTableWidgetItem(_safe_str(row.get("CONDUCTOR"))))
            self.table_viajes_flota.setItem(r, 8, QTableWidgetItem(_safe_str(row.get("ESTADO_VIAJE"))))

    def handle_asignar_tren_viaje(self):
        selected = self.table_viajes_flota.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un viaje de la tabla.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item_num = self.table_viajes_flota.item(row, 0)
        if not item_num:
            return

        num_viaje = item_num.text()
        viajes = m3_fleet_service.get_viajes_asignados_tren()
        viaje = next((v for v in viajes if v.get("NUMERO_VIAJE") == num_viaje), None)
        if not viaje:
            return

        v_id = _safe_int(viaje.get("ID_VIAJE", 0))

        # Obtener trenes aptos para asignación
        trenes = m3_fleet_service.get_trenes()
        trenes_aptos = [t for t in trenes if _safe_str(t.get("ESTADO_OPERATIVO")) == "Disponible"]

        dlg = AsignarTrenViajeDialog(v_id, num_viaje, trenes_aptos, parent=self.window())
        if dlg.exec():
            tren_id = dlg.get_selected_tren_id()
            if not tren_id:
                return

            res = m3_fleet_service.asignar_tren_a_viaje(v_id, tren_id)
            if res.get("success"):
                InfoBar.success(
                    title="Tren Asignado",
                    content=res.get("mensaje", "Tren asignado exitosamente."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.refresh_viajes_flota()
                self.refresh_trenes()
            else:
                InfoBar.error(
                    title="Conflicto de Asignación",
                    content=res.get("error", "No se pudo asignar el tren."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=5000
                )

    def handle_desasignar_tren_viaje(self):
        selected = self.table_viajes_flota.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un viaje de la tabla.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item_num = self.table_viajes_flota.item(row, 0)
        if not item_num:
            return

        num_viaje = item_num.text()
        viajes = m3_fleet_service.get_viajes_asignados_tren()
        viaje = next((v for v in viajes if v.get("NUMERO_VIAJE") == num_viaje), None)
        if not viaje:
            return

        v_id = _safe_int(viaje.get("ID_VIAJE", 0))

        box = MessageBox(
            "Confirmar Desasignación",
            f"¿Desea desvincular el tren asignado al viaje {num_viaje}?",
            self.window()
        )
        if box.exec():
            res = m3_fleet_service.desasignar_tren_de_viaje(v_id)
            if res.get("success"):
                InfoBar.success(
                    title="Tren Desasignado",
                    content=res.get("mensaje", "Tren desasignado del viaje."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.refresh_viajes_flota()
            else:
                InfoBar.error(
                    title="Error al Desasignar",
                    content=res.get("error", "No se pudo desasignar el tren."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )
