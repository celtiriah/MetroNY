"""
m6_maintenance_interface.py - Vista principal del Modulo 6: Mantenimiento y Control de Activos.
Cumple estrictamente con los 9 requerimientos oficiales y las Reglas de Negocio 19 y 25:
1. Registrar equipos de infraestructura (vias, senales, andenes, elevadores, escaleras, trenes, vagones).
2. Generar ordenes de trabajo vinculadas al procedimiento canonico SP_CREAR_ORDEN_MANTENIMIENTO.
3. Asignacion de tecnicos y cuadrillas a ordenes de trabajo (ORDEN_TECNICO).
4. Registrar repuestos utilizados con calculo automatico de costos (REPUESTO, ORDEN_REPUESTO).
5. Gestionar el ciclo de vida de las ordenes (Solicitada, Programada, En Ejecucion, Suspendida, Completada, Cancelada).
6. Actualizar fecha de ultima revision y programar fecha de proxima inspeccion.
7. Consultar equipos fuera de servicio y alertas de inspecciones tecnicas vencidas.
8. Bloqueo de asignacion de trenes en mantenimiento a viajes (Regla 19).
9. Integridad y auditoria historica de ordenes (Regla 25).
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QHeaderView, QFormLayout, QTableWidgetItem, QGridLayout,
    QLabel, QSplitter
)

from qfluentwidgets import (
    TitleLabel, SubtitleLabel, CaptionLabel, BodyLabel, StrongBodyLabel,
    CardWidget, ComboBox, LineEdit, SearchLineEdit, DoubleSpinBox, SpinBox,
    PrimaryPushButton, PushButton, TableWidget, InfoBar, InfoBarPosition,
    SegmentedWidget, MessageBoxBase, MessageBox, IconWidget,
    FluentIcon as FIF
)

from services import m6_maintenance_service


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
# DIALOGOS MODALES (MessageBoxBase)
# ==============================================================================

class NuevaOrdenDialog(MessageBoxBase):
    """Dialogo modal para generar una nueva orden de mantenimiento con SP_CREAR_ORDEN_MANTENIMIENTO."""
    def __init__(self, equipos: List[Dict[str, Any]], tecnicos: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.equipos = equipos
        self.tecnicos = tecnicos
        self.init_ui()

    def init_ui(self):
        self.titleLabel = TitleLabel("Generar Orden de Mantenimiento", self)
        self.viewLayout.addWidget(self.titleLabel)

        form = QFormLayout()
        form.setSpacing(10)

        # 1. Selector de Equipo
        self.combo_equipo = ComboBox(self)
        for eq in self.equipos:
            codigo = _safe_str(eq.get("CODIGO_EQUIPO"))
            tipo = _safe_str(eq.get("TIPO_EQUIPO"))
            ubic = _safe_str(eq.get("UBICACION"))
            id_eq = _safe_int(eq.get("ID_EQUIPO"))
            self.combo_equipo.addItem(f"{codigo} ({tipo}) - {ubic}", userData=id_eq)
        form.addRow("Activo / Equipo:", self.combo_equipo)

        # 2. Tipo de Mantenimiento
        self.combo_tipo = ComboBox(self)
        self.combo_tipo.addItems(["Preventivo", "Correctivo", "Predictivo", "Inspección de Seguridad"])
        form.addRow("Tipo de Trabajo:", self.combo_tipo)

        # 3. Prioridad
        self.combo_prioridad = ComboBox(self)
        self.combo_prioridad.addItems(["Baja", "Media", "Alta", "Urgente"])
        self.combo_prioridad.setCurrentText("Media")
        form.addRow("Nivel de Prioridad:", self.combo_prioridad)

        # 4. Tecnico Lider
        self.combo_tecnico = ComboBox(self)
        self.combo_tecnico.addItem("(Sin asignar líder inicialmente)", userData=None)
        for tec in self.tecnicos:
            nom = _safe_str(tec.get("NOMBRE_COMPLETO"))
            num = _safe_str(tec.get("NUMERO_EMPLEADO"))
            id_emp = _safe_int(tec.get("ID_EMPLEADO"))
            self.combo_tecnico.addItem(f"{nom} ({num})", userData=id_emp)
        form.addRow("Técnico Responsable:", self.combo_tecnico)

        # 5. Descripcion
        self.txt_descripcion = LineEdit(self)
        self.txt_descripcion.setPlaceholderText("Detalle de las tareas tecnicas a realizar...")
        form.addRow("Descripción:", self.txt_descripcion)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Generar Orden")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(520)

    def validate(self) -> bool:
        if not self.txt_descripcion.text().strip():
            self.txt_descripcion.setFocus()
            return False
        return True


class CompletarOrdenDialog(MessageBoxBase):
    """Dialogo modal para finalizar formalmente una orden de trabajo."""
    def __init__(self, orden: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.orden = orden
        self.init_ui()

    def init_ui(self):
        self.titleLabel = TitleLabel("Finalizar Orden de Mantenimiento", self)
        self.viewLayout.addWidget(self.titleLabel)

        form = QFormLayout()
        form.setSpacing(10)

        num_orden = _safe_str(self.orden.get("NUMERO_ORDEN"))
        codigo_eq = _safe_str(self.orden.get("CODIGO_EQUIPO"))
        tipo_eq = _safe_str(self.orden.get("TIPO_EQUIPO"))

        lbl_info = BodyLabel(f"Orden: {num_orden} | Activo: {codigo_eq} ({tipo_eq})", self)
        form.addRow("Identificación:", lbl_info)

        # Costo final
        costo_base = _safe_float(self.orden.get("COSTO_TOTAL_CALCULADO"))
        self.spin_costo = DoubleSpinBox(self)
        self.spin_costo.setRange(0.0, 999999.99)
        self.spin_costo.setValue(costo_base)
        form.addRow("Costo Final Auditado ($):", self.spin_costo)

        # Fecha de finalizacion
        self.txt_fecha_fin = LineEdit(self)
        self.txt_fecha_fin.setText(datetime.now().strftime("%Y-%m-%d %H:%M"))
        form.addRow("Fecha / Hora Cierre:", self.txt_fecha_fin)

        # Proxima revision en dias
        self.spin_dias = SpinBox(self)
        self.spin_dias.setRange(1, 730)
        self.spin_dias.setValue(90)
        form.addRow("Próxima Revisión (Días):", self.spin_dias)

        lbl_notice = CaptionLabel(
            "Al completar la orden, el estado del activo (y del tren, si aplica) se restablecerá a 'Disponible' "
            "y se actualizarán las fechas de inspección técnica reglamentarias.",
            self
        )
        lbl_notice.setWordWrap(True)
        form.addRow(lbl_notice)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Confirmar Finalización")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(500)


class CambiarEstadoOrdenDialog(MessageBoxBase):
    """Dialogo modal para alternar el estado operativo de una orden."""
    def __init__(self, estado_actual: str, parent=None):
        super().__init__(parent)
        self.estado_actual = estado_actual
        self.init_ui()

    def init_ui(self):
        self.titleLabel = TitleLabel("Cambiar Estado de la Orden", self)
        self.viewLayout.addWidget(self.titleLabel)

        form = QFormLayout()
        form.setSpacing(10)

        lbl_actual = StrongBodyLabel(f"Estado Actual: {self.estado_actual}", self)
        form.addRow("Estado:", lbl_actual)

        self.combo_estado = ComboBox(self)
        estados = ["Solicitada", "Programada", "En Ejecución", "Suspendida", "Cancelada"]
        for est in estados:
            if est != self.estado_actual:
                self.combo_estado.addItem(est)
        form.addRow("Nuevo Estado:", self.combo_estado)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Actualizar Estado")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(400)


class EquipoDialog(MessageBoxBase):
    """Dialogo modal para crear o editar un activo de infraestructura en EQUIPO."""
    def __init__(self, equipo: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.equipo = equipo
        self.is_edit = equipo is not None
        self.init_ui()

    def init_ui(self):
        titulo = "Editar Activo de Infraestructura" if self.is_edit else "Registrar Nuevo Activo"
        self.titleLabel = TitleLabel(titulo, self)
        self.viewLayout.addWidget(self.titleLabel)

        form = QFormLayout()
        form.setSpacing(8)

        # 1. Codigo
        self.txt_codigo = LineEdit(self)
        self.txt_codigo.setPlaceholderText("Ej: EQ-TRK-201, EQ-SIG-305")
        if self.equipo:
            self.txt_codigo.setText(_safe_str(self.equipo.get("CODIGO_EQUIPO")))
        form.addRow("Código Único:", self.txt_codigo)

        # 2. Tipo de Equipo
        self.combo_tipo = ComboBox(self)
        tipos = ["Vía", "Señal", "Plataforma", "Elevador", "Escalera Eléctrica", "Tren", "Vagón"]
        self.combo_tipo.addItems(tipos)
        if self.equipo:
            self.combo_tipo.setCurrentText(_safe_str(self.equipo.get("TIPO_EQUIPO"), "Vía"))
        form.addRow("Tipo de Equipo:", self.combo_tipo)

        # 3. Referencia Polimorfica
        self.combo_tipo_ref = ComboBox(self)
        self.combo_tipo_ref.addItems(["NINGUNO", "ESTACION", "PLATAFORMA", "TREN", "VAGON"])
        if self.equipo:
            self.combo_tipo_ref.setCurrentText(_safe_str(self.equipo.get("TIPO_REFERENCIA"), "NINGUNO"))
        form.addRow("Tipo de Referencia:", self.combo_tipo_ref)

        self.spin_ref_id = SpinBox(self)
        self.spin_ref_id.setRange(0, 999999)
        if self.equipo:
            self.spin_ref_id.setValue(_safe_int(self.equipo.get("REFERENCIA_ID"), 0))
        form.addRow("ID de Referencia:", self.spin_ref_id)

        # 4. Ubicacion
        self.txt_ubicacion = LineEdit(self)
        self.txt_ubicacion.setPlaceholderText("Ej: Vía 1 Norte - Times Sq")
        if self.equipo:
            self.txt_ubicacion.setText(_safe_str(self.equipo.get("UBICACION")))
        form.addRow("Ubicación Física:", self.txt_ubicacion)

        # 5. Fabricante y Modelo
        self.txt_fabricante = LineEdit(self)
        if self.equipo:
            self.txt_fabricante.setText(_safe_str(self.equipo.get("FABRICANTE")))
        form.addRow("Fabricante:", self.txt_fabricante)

        self.txt_modelo = LineEdit(self)
        if self.equipo:
            self.txt_modelo.setText(_safe_str(self.equipo.get("MODELO")))
        form.addRow("Modelo:", self.txt_modelo)

        # 6. Serie
        self.txt_serie = LineEdit(self)
        if self.equipo:
            self.txt_serie.setText(_safe_str(self.equipo.get("NUMERO_SERIE")))
        form.addRow("Número de Serie:", self.txt_serie)

        # 7. Estado
        self.combo_estado = ComboBox(self)
        self.combo_estado.addItems(["Disponible", "En Mantenimiento", "Fuera de Servicio"])
        if self.equipo:
            self.combo_estado.setCurrentText(_safe_str(self.equipo.get("ESTADO"), "Disponible"))
        form.addRow("Estado Operativo:", self.combo_estado)

        # 8. Fechas
        self.txt_fecha_prox = LineEdit(self)
        self.txt_fecha_prox.setPlaceholderText("YYYY-MM-DD")
        if self.equipo and self.equipo.get("FECHA_PROXIMA_REVISION") != "-":
            self.txt_fecha_prox.setText(_safe_str(self.equipo.get("FECHA_PROXIMA_REVISION")))
        form.addRow("Próxima Revisión:", self.txt_fecha_prox)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Guardar Activo")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(500)

    def validate(self) -> bool:
        if not self.txt_codigo.text().strip():
            self.txt_codigo.setFocus()
            return False
        return True


class AsignarTecnicoDialog(MessageBoxBase):
    """Dialogo modal para asignar un tecnico de mantenimiento a una orden."""
    def __init__(self, tecnicos: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.tecnicos = tecnicos
        self.init_ui()

    def init_ui(self):
        self.titleLabel = TitleLabel("Asignar Técnico a la Orden", self)
        self.viewLayout.addWidget(self.titleLabel)

        form = QFormLayout()
        form.setSpacing(10)

        # Selector de Tecnico
        self.combo_tecnico = ComboBox(self)
        for tec in self.tecnicos:
            nom = _safe_str(tec.get("NOMBRE_COMPLETO"))
            num = _safe_str(tec.get("NUMERO_EMPLEADO"))
            id_emp = _safe_int(tec.get("ID_EMPLEADO"))
            self.combo_tecnico.addItem(f"{nom} ({num})", userData=id_emp)
        form.addRow("Técnico Especialista:", self.combo_tecnico)

        # Rol
        self.combo_rol = ComboBox(self)
        self.combo_rol.addItems([
            "Técnico Especialista",
            "Líder de Reparación",
            "Técnico Mecánico Principal",
            "Inspector de Vía y Señales",
            "Auxiliar Técnico"
        ])
        form.addRow("Rol en la Orden:", self.combo_rol)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Asignar a Cuadrilla")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(440)


class ConsumoRepuestoDialog(MessageBoxBase):
    """Dialogo modal para registrar el consumo de una pieza de repuesto en una orden."""
    def __init__(self, repuestos: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.repuestos = repuestos
        self.init_ui()

    def init_ui(self):
        self.titleLabel = TitleLabel("Registrar Consumo de Repuesto", self)
        self.viewLayout.addWidget(self.titleLabel)

        form = QFormLayout()
        form.setSpacing(10)

        # Selector de Repuesto
        self.combo_repuesto = ComboBox(self)
        for rep in self.repuestos:
            cod = _safe_str(rep.get("CODIGO"))
            nom = _safe_str(rep.get("NOMBRE"))
            costo = _safe_float(rep.get("COSTO_UNITARIO"))
            id_rep = _safe_int(rep.get("ID_REPUESTO"))
            self.combo_repuesto.addItem(f"{cod} - {nom} (${costo:.2f})", userData=id_rep)
        self.combo_repuesto.currentIndexChanged.connect(self.update_subtotal)
        form.addRow("Pieza / Repuesto:", self.combo_repuesto)

        # Cantidad
        self.spin_cantidad = SpinBox(self)
        self.spin_cantidad.setRange(1, 500)
        self.spin_cantidad.setValue(1)
        self.spin_cantidad.valueChanged.connect(self.update_subtotal)
        form.addRow("Cantidad Utilizada:", self.spin_cantidad)

        # Subtotal estimado
        self.lbl_subtotal = StrongBodyLabel("Subtotal Estimado: $0.00", self)
        form.addRow("Impacto en Costo:", self.lbl_subtotal)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Registrar Pieza")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(480)
        self.update_subtotal()

    def update_subtotal(self):
        idx = self.combo_repuesto.currentIndex()
        if idx >= 0 and idx < len(self.repuestos):
            costo_u = _safe_float(self.repuestos[idx].get("COSTO_UNITARIO"))
            cant = self.spin_cantidad.value()
            self.lbl_subtotal.setText(f"Subtotal Estimado: ${cant * costo_u:.2f}")


class RepuestoDialog(MessageBoxBase):
    """Dialogo modal para crear o editar un repuesto en el catalogo general."""
    def __init__(self, repuesto: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.repuesto = repuesto
        self.is_edit = repuesto is not None
        self.init_ui()

    def init_ui(self):
        titulo = "Editar Repuesto de Catálogo" if self.is_edit else "Nuevo Repuesto en Catálogo"
        self.titleLabel = TitleLabel(titulo, self)
        self.viewLayout.addWidget(self.titleLabel)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_codigo = LineEdit(self)
        self.txt_codigo.setPlaceholderText("Ej: REP-TRK-10, REP-MOT-05")
        if self.repuesto:
            self.txt_codigo.setText(_safe_str(self.repuesto.get("CODIGO")))
        form.addRow("Código de Pieza:", self.txt_codigo)

        self.txt_nombre = LineEdit(self)
        self.txt_nombre.setPlaceholderText("Denominación técnica de la pieza...")
        if self.repuesto:
            self.txt_nombre.setText(_safe_str(self.repuesto.get("NOMBRE")))
        form.addRow("Denominación:", self.txt_nombre)

        self.spin_costo = DoubleSpinBox(self)
        self.spin_costo.setRange(0.01, 99999.99)
        if self.repuesto:
            self.spin_costo.setValue(_safe_float(self.repuesto.get("COSTO_UNITARIO"), 50.0))
        else:
            self.spin_costo.setValue(50.0)
        form.addRow("Costo Unitario ($):", self.spin_costo)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Guardar")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(440)

    def validate(self) -> bool:
        if not self.txt_codigo.text().strip() or not self.txt_nombre.text().strip():
            return False
        return True


# ==============================================================================
# VISTA PRINCIPAL: MaintenanceInterface
# ==============================================================================

class MaintenanceInterface(QWidget):
    """
    Vista principal del Modulo 6: Mantenimiento e Inspecciones Tecnicas.
    Disenada con 5 pestanas de ancho completo en un layout independiente.
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("maintenanceInterface")
        self.ordenes_cache: List[Dict[str, Any]] = []
        self.equipos_cache: List[Dict[str, Any]] = []
        self.tecnicos_cache: List[Dict[str, Any]] = []
        self.repuestos_cache: List[Dict[str, Any]] = []
        self.selected_orden_id: Optional[int] = None
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

        title = TitleLabel("Mantenimiento y Control de Activos", header_card)
        subtitle = SubtitleLabel("Modulo 6: Gestion de ordenes de trabajo, inventario de infraestructura, cuadrillas tecnicas y repuestos", header_card)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addWidget(header_card)

        # ----------------------------------------------------------------------
        # 2. CONTENEDOR INDEPENDIENTE DE PESTANAS (ANCHO COMPLETO)
        # ----------------------------------------------------------------------
        tabs_layout = QHBoxLayout()
        self.segmented_tabs = SegmentedWidget(self)
        self.segmented_tabs.addItem("tab_ordenes", "Órdenes de Mantenimiento")
        self.segmented_tabs.addItem("tab_equipos", "Inventario de Equipos")
        self.segmented_tabs.addItem("tab_cuadrillas", "Cuadrillas y Técnicos")
        self.segmented_tabs.addItem("tab_repuestos", "Repuestos y Costos")
        self.segmented_tabs.addItem("tab_alertas", "Alertas y Material en Taller")

        self.segmented_tabs.setCurrentItem("tab_ordenes")
        self.segmented_tabs.currentItemChanged.connect(self.on_tab_changed)

        tabs_layout.addWidget(self.segmented_tabs)
        main_layout.addLayout(tabs_layout)

        # ----------------------------------------------------------------------
        # 3. STACKED WIDGET DE VISTAS
        # ----------------------------------------------------------------------
        self.stack_views = QStackedWidget(self)

        self.init_tab_ordenes()
        self.init_tab_equipos()
        self.init_tab_cuadrillas()
        self.init_tab_repuestos()
        self.init_tab_alertas()

        main_layout.addWidget(self.stack_views, stretch=1)

    def showEvent(self, a0):
        super().showEvent(a0)
        if not self.segmented_tabs.currentItem():
            self.segmented_tabs.setCurrentItem("tab_ordenes")

    def on_tab_changed(self, key: str):
        if key == "tab_ordenes":
            self.stack_views.setCurrentIndex(0)
            self.refresh_ordenes()
        elif key == "tab_equipos":
            self.stack_views.setCurrentIndex(1)
            self.refresh_equipos()
        elif key == "tab_cuadrillas":
            self.stack_views.setCurrentIndex(2)
            self.refresh_cuadrillas()
        elif key == "tab_repuestos":
            self.stack_views.setCurrentIndex(3)
            self.refresh_repuestos()
        else:
            self.stack_views.setCurrentIndex(4)
            self.refresh_alertas()

    # ==========================================================================
    # PESTANA 1: ORDENES DE MANTENIMIENTO
    # ==========================================================================

    def init_tab_ordenes(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(12)

        # 1. KPIs
        card_kpis = CardWidget(tab_widget)
        kpi_layout = QHBoxLayout(card_kpis)
        kpi_layout.setContentsMargins(16, 12, 16, 12)
        kpi_layout.setSpacing(18)

        self.lbl_kpi_total = StrongBodyLabel("Total Órdenes: -", card_kpis)
        self.lbl_kpi_ejecucion = StrongBodyLabel("En Ejecución: -", card_kpis)
        self.lbl_kpi_prog = StrongBodyLabel("Programadas: -", card_kpis)
        self.lbl_kpi_comp = StrongBodyLabel("Completadas: -", card_kpis)
        self.lbl_kpi_costo = StrongBodyLabel("Inversión Total: -", card_kpis)

        kpi_layout.addWidget(self.lbl_kpi_total)
        kpi_layout.addWidget(self.lbl_kpi_ejecucion)
        kpi_layout.addWidget(self.lbl_kpi_prog)
        kpi_layout.addWidget(self.lbl_kpi_comp)
        kpi_layout.addWidget(self.lbl_kpi_costo)
        kpi_layout.addStretch(1)
        v_layout.addWidget(card_kpis)

        # 2. Barra de Filtros y Acciones
        bar_card = CardWidget(tab_widget)
        bar_layout = QHBoxLayout(bar_card)
        bar_layout.setContentsMargins(14, 10, 14, 10)
        bar_layout.setSpacing(10)

        self.search_ordenes = SearchLineEdit(bar_card)
        self.search_ordenes.setPlaceholderText("Buscar por orden, activo o descripción...")
        self.search_ordenes.textChanged.connect(self.refresh_ordenes)
        bar_layout.addWidget(self.search_ordenes, stretch=1)

        self.combo_filtro_estado = ComboBox(bar_card)
        self.combo_filtro_estado.addItems(["(Todos)", "Solicitada", "Programada", "En Ejecución", "Suspendida", "Completada", "Cancelada"])
        self.combo_filtro_estado.currentIndexChanged.connect(self.refresh_ordenes)
        bar_layout.addWidget(self.combo_filtro_estado)

        self.combo_filtro_tipo = ComboBox(bar_card)
        self.combo_filtro_tipo.addItems(["(Todos)", "Preventivo", "Correctivo", "Predictivo", "Inspección de Seguridad"])
        self.combo_filtro_tipo.currentIndexChanged.connect(self.refresh_ordenes)
        bar_layout.addWidget(self.combo_filtro_tipo)

        self.btn_nueva_orden = PrimaryPushButton("Nueva Orden", bar_card, FIF.ADD)
        self.btn_nueva_orden.clicked.connect(self.handle_nueva_orden)
        bar_layout.addWidget(self.btn_nueva_orden)

        self.btn_cambiar_estado = PushButton("Cambiar Estado", bar_card, FIF.SYNC)
        self.btn_cambiar_estado.clicked.connect(self.handle_cambiar_estado)
        bar_layout.addWidget(self.btn_cambiar_estado)

        self.btn_completar_orden = PushButton("Finalizar Trabajo", bar_card, FIF.COMPLETED)
        self.btn_completar_orden.clicked.connect(self.handle_completar_orden)
        bar_layout.addWidget(self.btn_completar_orden)

        self.btn_cancelar_orden = PushButton("Cancelar", bar_card, FIF.CANCEL)
        self.btn_cancelar_orden.clicked.connect(self.handle_cancelar_orden)
        bar_layout.addWidget(self.btn_cancelar_orden)

        v_layout.addWidget(bar_card)

        # 3. Tabla de Ordenes
        self.table_ordenes = TableWidget(tab_widget)
        self.table_ordenes.setColumnCount(9)
        self.table_ordenes.setHorizontalHeaderLabels([
            "Nº Orden", "Activo", "Tipo Trabajo", "Descripción",
            "Prioridad", "Técnico Líder", "Programada", "Costo ($)", "Estado"
        ])
        self.table_ordenes.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table_ordenes.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)

        header = self.table_ordenes.horizontalHeader()
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

        self.table_ordenes.itemSelectionChanged.connect(self.on_orden_selected)
        v_layout.addWidget(self.table_ordenes, stretch=1)

        self.stack_views.addWidget(tab_widget)

    def refresh_ordenes(self):
        est = self.combo_filtro_estado.currentText()
        tipo = self.combo_filtro_tipo.currentText()
        st = self.search_ordenes.text().strip()

        self.ordenes_cache = m6_maintenance_service.get_ordenes(
            estado_filter=est if est != "(Todos)" else None,
            tipo_filter=tipo if tipo != "(Todos)" else None,
            search_text=st if st else None
        )

        self.table_ordenes.blockSignals(True)
        self.table_ordenes.setRowCount(len(self.ordenes_cache))
        for r, row in enumerate(self.ordenes_cache):
            num = _safe_str(row.get("NUMERO_ORDEN"))
            cod_eq = _safe_str(row.get("CODIGO_EQUIPO"))
            tipo_trab = _safe_str(row.get("TIPO_MANTENIMIENTO"))
            desc = _safe_str(row.get("DESCRIPCION_TRABAJO"))
            prio = _safe_str(row.get("PRIORIDAD"))
            tec = _safe_str(row.get("TECNICO_LIDER"))
            f_prog = _safe_str(row.get("FECHA_PROGRAMADA"))
            costo = _safe_float(row.get("COSTO_TOTAL_CALCULADO"))
            estado = _safe_str(row.get("ESTADO"))

            self.table_ordenes.setItem(r, 0, QTableWidgetItem(num))
            self.table_ordenes.setItem(r, 1, QTableWidgetItem(cod_eq))
            self.table_ordenes.setItem(r, 2, QTableWidgetItem(tipo_trab))
            self.table_ordenes.setItem(r, 3, QTableWidgetItem(desc))
            self.table_ordenes.setItem(r, 4, QTableWidgetItem(prio))
            self.table_ordenes.setItem(r, 5, QTableWidgetItem(tec))
            self.table_ordenes.setItem(r, 6, QTableWidgetItem(f_prog))
            self.table_ordenes.setItem(r, 7, QTableWidgetItem(f"${costo:.2f}"))
            self.table_ordenes.setItem(r, 8, QTableWidgetItem(estado))

        self.table_ordenes.blockSignals(False)
        self.refresh_kpis()

    def refresh_kpis(self):
        kpis = m6_maintenance_service.get_kpis_mantenimiento()
        self.lbl_kpi_total.setText(f"Total Órdenes: {kpis['total_ordenes']}")
        self.lbl_kpi_ejecucion.setText(f"En Ejecución: {kpis['en_ejecucion']}")
        self.lbl_kpi_prog.setText(f"Programadas: {kpis['programadas']}")
        self.lbl_kpi_comp.setText(f"Completadas: {kpis['completadas']}")
        self.lbl_kpi_costo.setText(f"Inversión Total: ${kpis['inversion_total']:,.2f}")

    def on_orden_selected(self):
        selected = self.table_ordenes.selectedItems()
        if selected:
            r = selected[0].row()
            if r < len(self.ordenes_cache):
                self.selected_orden_id = _safe_int(self.ordenes_cache[r].get("ID_ORDEN"))
        else:
            self.selected_orden_id = None

    def handle_nueva_orden(self):
        equipos = m6_maintenance_service.get_equipos()
        tecnicos = m6_maintenance_service.get_tecnicos_disponibles()
        if not equipos:
            InfoBar.warning("Sin Equipos", "No hay activos de infraestructura registrados.", parent=self.window(), duration=3000)
            return

        dialog = NuevaOrdenDialog(equipos, tecnicos, self.window())
        if dialog.exec():
            if not dialog.validate():
                InfoBar.warning("Validación", "Complete la descripción de la orden.", parent=self.window(), duration=3000)
                return

            id_eq = dialog.combo_equipo.currentData()
            if id_eq is None:
                return
            tipo = dialog.combo_tipo.currentText()
            prio = dialog.combo_prioridad.currentText()
            tec_id = dialog.combo_tecnico.currentData()
            desc = dialog.txt_descripcion.text()

            res = m6_maintenance_service.crear_orden(
                equipo_id=int(id_eq),
                tipo_mantenimiento=tipo,
                descripcion=desc,
                prioridad=prio,
                tecnico_id=int(tec_id) if tec_id is not None else None
            )

            if res.get("success"):
                InfoBar.success(
                    "Orden Generada",
                    f"Orden {res.get('numero_orden')} creada exitosamente. El activo fue colocado en mantenimiento.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4000
                )
                self.refresh_ordenes()
            else:
                InfoBar.error("Error al Crear Orden", res.get("error", ""), parent=self.window(), duration=4500)

    def handle_cambiar_estado(self):
        if not self.selected_orden_id:
            InfoBar.warning("Selección Requerida", "Seleccione una orden de trabajo de la tabla.", parent=self.window(), duration=3000)
            return

        orden = next((o for o in self.ordenes_cache if _safe_int(o.get("ID_ORDEN")) == self.selected_orden_id), None)
        if not orden:
            return

        dialog = CambiarEstadoOrdenDialog(_safe_str(orden.get("ESTADO")), self.window())
        if dialog.exec():
            nuevo_est = dialog.combo_estado.currentText()
            res = m6_maintenance_service.cambiar_estado_orden(self.selected_orden_id, nuevo_est)
            if res.get("success"):
                InfoBar.success("Estado Actualizado", res.get("mensaje", ""), parent=self.window(), duration=3000)
                self.refresh_ordenes()
            else:
                InfoBar.error("Error", res.get("error", ""), parent=self.window(), duration=4000)

    def handle_completar_orden(self):
        if not self.selected_orden_id:
            InfoBar.warning("Selección Requerida", "Seleccione la orden de trabajo que desea finalizar.", parent=self.window(), duration=3000)
            return

        orden = next((o for o in self.ordenes_cache if _safe_int(o.get("ID_ORDEN")) == self.selected_orden_id), None)
        if not orden:
            return

        dialog = CompletarOrdenDialog(orden, self.window())
        if dialog.exec():
            costo = dialog.spin_costo.value()
            f_fin = dialog.txt_fecha_fin.text().strip()
            dias = dialog.spin_dias.value()

            res = m6_maintenance_service.completar_orden(
                id_orden=self.selected_orden_id,
                costo_final=costo,
                fecha_fin=f_fin if f_fin else None,
                dias_proxima_revision=dias
            )

            if res.get("success"):
                InfoBar.success("Trabajo Finalizado", res.get("mensaje", ""), parent=self.window(), duration=4000)
                self.refresh_ordenes()
            else:
                InfoBar.error("Error al Finalizar", res.get("error", ""), parent=self.window(), duration=4000)

    def handle_cancelar_orden(self):
        if not self.selected_orden_id:
            InfoBar.warning("Selección Requerida", "Seleccione la orden que desea cancelar.", parent=self.window(), duration=3000)
            return

        box = MessageBox("Cancelar Orden", "¿Está seguro de que desea cancelar esta orden de mantenimiento? Esta acción restaurará la disponibilidad del activo si no existen otros trabajos activos.", self.window())
        if box.exec():
            res = m6_maintenance_service.cancelar_orden(self.selected_orden_id)
            if res.get("success"):
                InfoBar.success("Orden Cancelada", res.get("mensaje", ""), parent=self.window(), duration=3000)
                self.refresh_ordenes()
            else:
                InfoBar.error("Error", res.get("error", ""), parent=self.window(), duration=4000)

    # ==========================================================================
    # PESTANA 2: INVENTARIO DE EQUIPOS Y ACTIVOS
    # ==========================================================================

    def init_tab_equipos(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(12)

        # Barra de Filtros
        bar_card = CardWidget(tab_widget)
        bar_layout = QHBoxLayout(bar_card)
        bar_layout.setContentsMargins(14, 10, 14, 10)
        bar_layout.setSpacing(10)

        self.search_equipos = SearchLineEdit(bar_card)
        self.search_equipos.setPlaceholderText("Buscar por código, ubicación o fabricante...")
        self.search_equipos.textChanged.connect(self.refresh_equipos)
        bar_layout.addWidget(self.search_equipos, stretch=1)

        self.combo_filtro_eq_tipo = ComboBox(bar_card)
        self.combo_filtro_eq_tipo.addItems(["(Todos)", "Vía", "Señal", "Plataforma", "Elevador", "Escalera Eléctrica", "Tren", "Vagón"])
        self.combo_filtro_eq_tipo.currentIndexChanged.connect(self.refresh_equipos)
        bar_layout.addWidget(self.combo_filtro_eq_tipo)

        self.combo_filtro_eq_estado = ComboBox(bar_card)
        self.combo_filtro_eq_estado.addItems(["(Todos)", "Disponible", "En Mantenimiento", "Fuera de Servicio"])
        self.combo_filtro_eq_estado.currentIndexChanged.connect(self.refresh_equipos)
        bar_layout.addWidget(self.combo_filtro_eq_estado)

        self.btn_nuevo_equipo = PrimaryPushButton("Registrar Activo", bar_card, FIF.ADD)
        self.btn_nuevo_equipo.clicked.connect(self.handle_nuevo_equipo)
        bar_layout.addWidget(self.btn_nuevo_equipo)

        self.btn_editar_equipo = PushButton("Editar", bar_card, FIF.EDIT)
        self.btn_editar_equipo.clicked.connect(self.handle_editar_equipo)
        bar_layout.addWidget(self.btn_editar_equipo)

        self.btn_eliminar_equipo = PushButton("Eliminar", bar_card, FIF.DELETE)
        self.btn_eliminar_equipo.clicked.connect(self.handle_eliminar_equipo)
        bar_layout.addWidget(self.btn_eliminar_equipo)

        v_layout.addWidget(bar_card)

        # Tabla de Equipos
        self.table_equipos = TableWidget(tab_widget)
        self.table_equipos.setColumnCount(9)
        self.table_equipos.setHorizontalHeaderLabels([
            "Código", "Tipo", "Ubicación Física", "Referencia",
            "Fabricante / Modelo", "Estado", "Última Rev.", "Próxima Insp.", "Alerta"
        ])
        self.table_equipos.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table_equipos.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)

        header = self.table_equipos.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)

        v_layout.addWidget(self.table_equipos, stretch=1)
        self.stack_views.addWidget(tab_widget)

    def refresh_equipos(self):
        tipo = self.combo_filtro_eq_tipo.currentText()
        est = self.combo_filtro_eq_estado.currentText()
        st = self.search_equipos.text().strip()

        self.equipos_cache = m6_maintenance_service.get_equipos(
            tipo_filter=tipo if tipo != "(Todos)" else None,
            estado_filter=est if est != "(Todos)" else None,
            search_text=st if st else None
        )

        self.table_equipos.blockSignals(True)
        self.table_equipos.setRowCount(len(self.equipos_cache))
        for r, row in enumerate(self.equipos_cache):
            cod = _safe_str(row.get("CODIGO_EQUIPO"))
            tipo_eq = _safe_str(row.get("TIPO_EQUIPO"))
            ubic = _safe_str(row.get("UBICACION"))
            ref_nom = _safe_str(row.get("REFERENCIA_NOMBRE"))
            fab = _safe_str(row.get("FABRICANTE"))
            mod = _safe_str(row.get("MODELO"))
            fab_mod = f"{fab} {mod}".strip()
            estado = _safe_str(row.get("ESTADO"))
            ult = _safe_str(row.get("FECHA_ULTIMA_REVISION"))
            prox = _safe_str(row.get("FECHA_PROXIMA_REVISION"))
            alerta = _safe_str(row.get("ALERTA_INSPECCION"))

            self.table_equipos.setItem(r, 0, QTableWidgetItem(cod))
            self.table_equipos.setItem(r, 1, QTableWidgetItem(tipo_eq))
            self.table_equipos.setItem(r, 2, QTableWidgetItem(ubic))
            self.table_equipos.setItem(r, 3, QTableWidgetItem(ref_nom))
            self.table_equipos.setItem(r, 4, QTableWidgetItem(fab_mod))
            self.table_equipos.setItem(r, 5, QTableWidgetItem(estado))
            self.table_equipos.setItem(r, 6, QTableWidgetItem(ult))
            self.table_equipos.setItem(r, 7, QTableWidgetItem(prox))
            self.table_equipos.setItem(r, 8, QTableWidgetItem(alerta))

        self.table_equipos.blockSignals(False)

    def handle_nuevo_equipo(self):
        dialog = EquipoDialog(None, self.window())
        if dialog.exec():
            if not dialog.validate():
                InfoBar.warning("Validación", "El código del equipo es obligatorio.", parent=self.window(), duration=3000)
                return

            res = m6_maintenance_service.crear_equipo(
                codigo_equipo=dialog.txt_codigo.text(),
                tipo_equipo=dialog.combo_tipo.currentText(),
                tipo_referencia=dialog.combo_tipo_ref.currentText(),
                referencia_id=dialog.spin_ref_id.value() if dialog.combo_tipo_ref.currentText() != "NINGUNO" else None,
                ubicacion=dialog.txt_ubicacion.text(),
                fabricante=dialog.txt_fabricante.text(),
                modelo=dialog.txt_modelo.text(),
                numero_serie=dialog.txt_serie.text(),
                estado=dialog.combo_estado.currentText(),
                fecha_proxima_revision=dialog.txt_fecha_prox.text() if dialog.txt_fecha_prox.text().strip() else None
            )

            if res.get("success"):
                InfoBar.success("Activo Registrado", res.get("mensaje", ""), parent=self.window(), duration=3000)
                self.refresh_equipos()
            else:
                InfoBar.error("Error", res.get("error", ""), parent=self.window(), duration=4000)

    def handle_editar_equipo(self):
        selected = self.table_equipos.selectedItems()
        if not selected:
            InfoBar.warning("Selección Requerida", "Seleccione un activo de la tabla para editar.", parent=self.window(), duration=3000)
            return

        r = selected[0].row()
        equipo = self.equipos_cache[r]
        id_eq = _safe_int(equipo.get("ID_EQUIPO"))

        dialog = EquipoDialog(equipo, self.window())
        if dialog.exec():
            if not dialog.validate():
                return

            res = m6_maintenance_service.modificar_equipo(
                id_equipo=id_eq,
                codigo_equipo=dialog.txt_codigo.text(),
                tipo_equipo=dialog.combo_tipo.currentText(),
                tipo_referencia=dialog.combo_tipo_ref.currentText(),
                referencia_id=dialog.spin_ref_id.value() if dialog.combo_tipo_ref.currentText() != "NINGUNO" else None,
                ubicacion=dialog.txt_ubicacion.text(),
                fabricante=dialog.txt_fabricante.text(),
                modelo=dialog.txt_modelo.text(),
                numero_serie=dialog.txt_serie.text(),
                estado=dialog.combo_estado.currentText(),
                fecha_proxima_revision=dialog.txt_fecha_prox.text() if dialog.txt_fecha_prox.text().strip() else None
            )

            if res.get("success"):
                InfoBar.success("Activo Actualizado", res.get("mensaje", ""), parent=self.window(), duration=3000)
                self.refresh_equipos()
            else:
                InfoBar.error("Error", res.get("error", ""), parent=self.window(), duration=4000)

    def handle_eliminar_equipo(self):
        selected = self.table_equipos.selectedItems()
        if not selected:
            InfoBar.warning("Selección Requerida", "Seleccione el activo que desea eliminar.", parent=self.window(), duration=3000)
            return

        r = selected[0].row()
        equipo = self.equipos_cache[r]
        id_eq = _safe_int(equipo.get("ID_EQUIPO"))
        cod_eq = _safe_str(equipo.get("CODIGO_EQUIPO"))

        box = MessageBox("Eliminar Activo", f"¿Confirma la eliminación del activo {cod_eq}? Solo será eliminado si no posee órdenes históricas asociadas.", self.window())
        if box.exec():
            res = m6_maintenance_service.eliminar_equipo(id_eq)
            if res.get("success"):
                InfoBar.success("Activo Eliminado", res.get("mensaje", ""), parent=self.window(), duration=3000)
                self.refresh_equipos()
            else:
                InfoBar.error("Integridad Referencial", res.get("error", ""), parent=self.window(), duration=5000)

    # ==========================================================================
    # PESTANA 3: ASIGNACION DE CUADRILLAS Y TECNICOS
    # ==========================================================================

    def init_tab_cuadrillas(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(12)

        # Splitter Horizontal: Izquierda = Selector Orden, Derecha = Tecnicos en Orden
        splitter = QSplitter(Qt.Orientation.Horizontal, tab_widget)

        # Panel Izquierdo: Resumen y seleccion de Orden
        left_widget = CardWidget(splitter)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(14, 12, 14, 12)
        left_layout.setSpacing(10)

        left_layout.addWidget(StrongBodyLabel("1. Seleccionar Orden de Trabajo", left_widget))
        self.combo_cuadrilla_orden = ComboBox(left_widget)
        self.combo_cuadrilla_orden.currentIndexChanged.connect(self.on_cuadrilla_orden_changed)
        left_layout.addWidget(self.combo_cuadrilla_orden)

        self.lbl_cuadrilla_orden_info = CaptionLabel("Seleccione una orden para gestionar sus técnicos asignados.", left_widget)
        self.lbl_cuadrilla_orden_info.setWordWrap(True)
        left_layout.addWidget(self.lbl_cuadrilla_orden_info)

        left_layout.addWidget(StrongBodyLabel("Plantilla de Técnicos Activos", left_widget))
        self.table_roster = TableWidget(left_widget)
        self.table_roster.setColumnCount(3)
        self.table_roster.setHorizontalHeaderLabels(["Nº Emp.", "Técnico de Mantenimiento", "Órdenes Activas"])
        self.table_roster.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        roster_header = self.table_roster.horizontalHeader()
        if roster_header is not None:
            roster_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            roster_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            roster_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        left_layout.addWidget(self.table_roster, stretch=1)

        splitter.addWidget(left_widget)

        # Panel Derecho: Tecnicos asignados a la orden
        right_widget = CardWidget(splitter)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(14, 12, 14, 12)
        right_layout.setSpacing(10)

        right_top = QHBoxLayout()
        right_top.addWidget(StrongBodyLabel("2. Cuadrilla Asignada a la Orden", right_widget))
        right_top.addStretch(1)

        self.btn_asignar_tec = PrimaryPushButton("Asignar Técnico", right_widget, FIF.ADD)
        self.btn_asignar_tec.clicked.connect(self.handle_asignar_tecnico)
        right_top.addWidget(self.btn_asignar_tec)

        self.btn_desasignar_tec = PushButton("Remover", right_widget, FIF.DELETE)
        self.btn_desasignar_tec.clicked.connect(self.handle_desasignar_tecnico)
        right_top.addWidget(self.btn_desasignar_tec)

        right_layout.addLayout(right_top)

        self.table_orden_tecnicos = TableWidget(right_widget)
        self.table_orden_tecnicos.setColumnCount(4)
        self.table_orden_tecnicos.setHorizontalHeaderLabels(["Nº Empleado", "Nombre Completo", "Teléfono", "Rol en la Orden"])
        self.table_orden_tecnicos.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table_orden_tecnicos.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)

        ord_tec_header = self.table_orden_tecnicos.horizontalHeader()
        if ord_tec_header is not None:
            ord_tec_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            ord_tec_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            ord_tec_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            ord_tec_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        right_layout.addWidget(self.table_orden_tecnicos, stretch=1)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        v_layout.addWidget(splitter, stretch=1)
        self.stack_views.addWidget(tab_widget)

    def refresh_cuadrillas(self):
        # 1. Llenar combo de ordenes activas
        ordenes = m6_maintenance_service.get_ordenes()
        self.combo_cuadrilla_orden.blockSignals(True)
        self.combo_cuadrilla_orden.clear()
        for o in ordenes:
            num = _safe_str(o.get("NUMERO_ORDEN"))
            eq = _safe_str(o.get("CODIGO_EQUIPO"))
            tipo = _safe_str(o.get("TIPO_MANTENIMIENTO"))
            est = _safe_str(o.get("ESTADO"))
            id_ord = _safe_int(o.get("ID_ORDEN"))
            self.combo_cuadrilla_orden.addItem(f"{num} - {eq} ({tipo}) [{est}]", userData=id_ord)
        self.combo_cuadrilla_orden.blockSignals(False)

        # 2. Roster general de tecnicos
        self.tecnicos_cache = m6_maintenance_service.get_tecnicos_disponibles()
        self.table_roster.blockSignals(True)
        self.table_roster.setRowCount(len(self.tecnicos_cache))
        for r, tec in enumerate(self.tecnicos_cache):
            num_emp = _safe_str(tec.get("NUMERO_EMPLEADO"))
            nom = _safe_str(tec.get("NOMBRE_COMPLETO"))
            ord_act = _safe_str(tec.get("ORDENES_ACTIVAS"))
            self.table_roster.setItem(r, 0, QTableWidgetItem(num_emp))
            self.table_roster.setItem(r, 1, QTableWidgetItem(nom))
            self.table_roster.setItem(r, 2, QTableWidgetItem(ord_act))
        self.table_roster.blockSignals(False)

        self.on_cuadrilla_orden_changed()

    def on_cuadrilla_orden_changed(self):
        id_ord = self.combo_cuadrilla_orden.currentData()
        if not id_ord:
            self.table_orden_tecnicos.setRowCount(0)
            self.lbl_cuadrilla_orden_info.setText("Sin orden seleccionada.")
            return

        tecnicos_orden = m6_maintenance_service.get_tecnicos_por_orden(int(id_ord))
        self.table_orden_tecnicos.blockSignals(True)
        self.table_orden_tecnicos.setRowCount(len(tecnicos_orden))
        for r, row in enumerate(tecnicos_orden):
            num = _safe_str(row.get("NUMERO_EMPLEADO"))
            nom = _safe_str(row.get("NOMBRE_COMPLETO"))
            tel = _safe_str(row.get("TELEFONO"))
            rol = _safe_str(row.get("ROL_EN_ORDEN"))
            id_ot = _safe_int(row.get("ID_ORDEN_TECNICO"))

            it_num = QTableWidgetItem(num)
            it_num.setData(Qt.ItemDataRole.UserRole, id_ot)
            self.table_orden_tecnicos.setItem(r, 0, it_num)
            self.table_orden_tecnicos.setItem(r, 1, QTableWidgetItem(nom))
            self.table_orden_tecnicos.setItem(r, 2, QTableWidgetItem(tel))
            self.table_orden_tecnicos.setItem(r, 3, QTableWidgetItem(rol))
        self.table_orden_tecnicos.blockSignals(False)

        self.lbl_cuadrilla_orden_info.setText(f"Mostrando {len(tecnicos_orden)} técnico(s) asignados a la orden ID {id_ord}.")

    def handle_asignar_tecnico(self):
        id_ord = self.combo_cuadrilla_orden.currentData()
        if not id_ord:
            InfoBar.warning("Orden Requerida", "Seleccione una orden de trabajo primero.", parent=self.window(), duration=3000)
            return

        dialog = AsignarTecnicoDialog(self.tecnicos_cache, self.window())
        if dialog.exec():
            emp_id = dialog.combo_tecnico.currentData()
            rol = dialog.combo_rol.currentText()
            if not emp_id:
                return

            res = m6_maintenance_service.asignar_tecnico_a_orden(int(id_ord), int(emp_id), rol)
            if res.get("success"):
                InfoBar.success("Técnico Asignado", res.get("mensaje", ""), parent=self.window(), duration=3000)
                self.on_cuadrilla_orden_changed()
            else:
                InfoBar.error("Error al Asignar", res.get("error", ""), parent=self.window(), duration=4000)

    def handle_desasignar_tecnico(self):
        selected = self.table_orden_tecnicos.selectedItems()
        if not selected:
            InfoBar.warning("Selección Requerida", "Seleccione un técnico asignado de la tabla para removerlo.", parent=self.window(), duration=3000)
            return

        r = selected[0].row()
        item = self.table_orden_tecnicos.item(r, 0)
        id_ot = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if not id_ot:
            return

        box = MessageBox("Remover Técnico", "¿Desea desasignar este técnico de la orden de trabajo?", self.window())
        if box.exec():
            res = m6_maintenance_service.desasignar_tecnico(int(id_ot))
            if res.get("success"):
                InfoBar.success("Técnico Removido", res.get("mensaje", ""), parent=self.window(), duration=3000)
                self.on_cuadrilla_orden_changed()
            else:
                InfoBar.error("Error", res.get("error", ""), parent=self.window(), duration=4000)

    # ==========================================================================
    # PESTANA 4: REPUESTOS Y COSTOS DE REPARACION
    # ==========================================================================

    def init_tab_repuestos(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Horizontal, tab_widget)

        # Panel Izquierdo: Catalogo General de Repuestos
        left_widget = CardWidget(splitter)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(14, 12, 14, 12)
        left_layout.setSpacing(10)

        left_top = QHBoxLayout()
        left_top.addWidget(StrongBodyLabel("Catálogo de Repuestos", left_widget))
        left_top.addStretch(1)

        self.btn_nuevo_repuesto = PrimaryPushButton("Nuevo", left_widget, FIF.ADD)
        self.btn_nuevo_repuesto.clicked.connect(self.handle_nuevo_repuesto)
        left_top.addWidget(self.btn_nuevo_repuesto)

        self.btn_editar_repuesto = PushButton("Editar", left_widget, FIF.EDIT)
        self.btn_editar_repuesto.clicked.connect(self.handle_editar_repuesto)
        left_top.addWidget(self.btn_editar_repuesto)

        self.btn_eliminar_repuesto = PushButton("Eliminar", left_widget, FIF.DELETE)
        self.btn_eliminar_repuesto.clicked.connect(self.handle_eliminar_repuesto)
        left_top.addWidget(self.btn_eliminar_repuesto)

        left_layout.addLayout(left_top)

        self.search_repuestos = SearchLineEdit(left_widget)
        self.search_repuestos.setPlaceholderText("Buscar por código o denominación...")
        self.search_repuestos.textChanged.connect(self.refresh_repuestos)
        left_layout.addWidget(self.search_repuestos)

        self.table_catalogo_repuestos = TableWidget(left_widget)
        self.table_catalogo_repuestos.setColumnCount(4)
        self.table_catalogo_repuestos.setHorizontalHeaderLabels(["Código", "Denominación de Pieza", "Costo ($)", "Uso Histórico"])
        self.table_catalogo_repuestos.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table_catalogo_repuestos.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)

        cat_header = self.table_catalogo_repuestos.horizontalHeader()
        if cat_header is not None:
            cat_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            cat_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            cat_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            cat_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        left_layout.addWidget(self.table_catalogo_repuestos, stretch=1)
        splitter.addWidget(left_widget)

        # Panel Derecho: Repuestos Utilizados en la Orden Seleccionada
        right_widget = CardWidget(splitter)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(14, 12, 14, 12)
        right_layout.setSpacing(10)

        right_top = QHBoxLayout()
        right_top.addWidget(StrongBodyLabel("Consumo de Repuestos por Orden", right_widget))
        right_top.addStretch(1)

        self.btn_consumir_repuesto = PrimaryPushButton("Registrar Consumo", right_widget, FIF.ADD)
        self.btn_consumir_repuesto.clicked.connect(self.handle_consumir_repuesto)
        right_top.addWidget(self.btn_consumir_repuesto)

        self.btn_eliminar_consumo = PushButton("Eliminar Partida", right_widget, FIF.DELETE)
        self.btn_eliminar_consumo.clicked.connect(self.handle_eliminar_consumo)
        right_top.addWidget(self.btn_eliminar_consumo)

        right_layout.addLayout(right_top)

        # Selector de orden
        right_sub = QHBoxLayout()
        right_sub.addWidget(BodyLabel("Orden:", right_widget))
        self.combo_rep_orden = ComboBox(right_widget)
        self.combo_rep_orden.currentIndexChanged.connect(self.on_rep_orden_changed)
        right_sub.addWidget(self.combo_rep_orden, stretch=1)
        right_layout.addLayout(right_sub)

        self.table_orden_repuestos = TableWidget(right_widget)
        self.table_orden_repuestos.setColumnCount(5)
        self.table_orden_repuestos.setHorizontalHeaderLabels(["Código", "Pieza", "Costo Unit.", "Cantidad", "Total ($)"])
        self.table_orden_repuestos.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table_orden_repuestos.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)

        ord_rep_header = self.table_orden_repuestos.horizontalHeader()
        if ord_rep_header is not None:
            ord_rep_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            ord_rep_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            ord_rep_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            ord_rep_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            ord_rep_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        right_layout.addWidget(self.table_orden_repuestos, stretch=1)

        self.lbl_costo_orden_consolidado = StrongBodyLabel("Costo Total Consolidado (Base + Repuestos): $0.00", right_widget)
        right_layout.addWidget(self.lbl_costo_orden_consolidado)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        v_layout.addWidget(splitter, stretch=1)
        self.stack_views.addWidget(tab_widget)

    def refresh_repuestos(self):
        # 1. Catalogo
        st = self.search_repuestos.text().strip()
        self.repuestos_cache = m6_maintenance_service.get_catalogo_repuestos(st if st else None)

        self.table_catalogo_repuestos.blockSignals(True)
        self.table_catalogo_repuestos.setRowCount(len(self.repuestos_cache))
        for r, row in enumerate(self.repuestos_cache):
            cod = _safe_str(row.get("CODIGO"))
            nom = _safe_str(row.get("NOMBRE"))
            costo = _safe_float(row.get("COSTO_UNITARIO"))
            total_c = _safe_str(row.get("TOTAL_CONSUMIDO"))

            it_cod = QTableWidgetItem(cod)
            it_cod.setData(Qt.ItemDataRole.UserRole, _safe_int(row.get("ID_REPUESTO")))
            self.table_catalogo_repuestos.setItem(r, 0, it_cod)
            self.table_catalogo_repuestos.setItem(r, 1, QTableWidgetItem(nom))
            self.table_catalogo_repuestos.setItem(r, 2, QTableWidgetItem(f"${costo:.2f}"))
            self.table_catalogo_repuestos.setItem(r, 3, QTableWidgetItem(total_c))
        self.table_catalogo_repuestos.blockSignals(False)

        # 2. Selector de orden
        ordenes = m6_maintenance_service.get_ordenes()
        prev_id = self.combo_rep_orden.currentData()
        self.combo_rep_orden.blockSignals(True)
        self.combo_rep_orden.clear()
        for o in ordenes:
            num = _safe_str(o.get("NUMERO_ORDEN"))
            eq = _safe_str(o.get("CODIGO_EQUIPO"))
            id_ord = _safe_int(o.get("ID_ORDEN"))
            self.combo_rep_orden.addItem(f"{num} - {eq}", userData=id_ord)
        if prev_id:
            for idx in range(self.combo_rep_orden.count()):
                if self.combo_rep_orden.itemData(idx) == prev_id:
                    self.combo_rep_orden.setCurrentIndex(idx)
                    break
        self.combo_rep_orden.blockSignals(False)

        self.on_rep_orden_changed()

    def on_rep_orden_changed(self):
        id_ord = self.combo_rep_orden.currentData()
        if not id_ord:
            self.table_orden_repuestos.setRowCount(0)
            self.lbl_costo_orden_consolidado.setText("Costo Total Consolidado: $0.00")
            return

        repuestos = m6_maintenance_service.get_repuestos_por_orden(int(id_ord))
        self.table_orden_repuestos.blockSignals(True)
        self.table_orden_repuestos.setRowCount(len(repuestos))
        for r, row in enumerate(repuestos):
            cod = _safe_str(row.get("CODIGO_REPUESTO"))
            nom = _safe_str(row.get("NOMBRE_REPUESTO"))
            costo_u = _safe_float(row.get("COSTO_UNITARIO"))
            cant = _safe_int(row.get("CANTIDAD"))
            costo_t = _safe_float(row.get("COSTO_TOTAL"))
            id_orp = _safe_int(row.get("ID_ORDEN_REPUESTO"))

            it_cod = QTableWidgetItem(cod)
            it_cod.setData(Qt.ItemDataRole.UserRole, id_orp)
            self.table_orden_repuestos.setItem(r, 0, it_cod)
            self.table_orden_repuestos.setItem(r, 1, QTableWidgetItem(nom))
            self.table_orden_repuestos.setItem(r, 2, QTableWidgetItem(f"${costo_u:.2f}"))
            self.table_orden_repuestos.setItem(r, 3, QTableWidgetItem(str(cant)))
            self.table_orden_repuestos.setItem(r, 4, QTableWidgetItem(f"${costo_t:.2f}"))
        self.table_orden_repuestos.blockSignals(False)

        costo_fn = m6_maintenance_service.calcular_costo_total_orden(int(id_ord))
        self.lbl_costo_orden_consolidado.setText(f"Costo Total Consolidado (Base + Repuestos): ${costo_fn:,.2f}")

    def handle_nuevo_repuesto(self):
        dialog = RepuestoDialog(None, self.window())
        if dialog.exec():
            if not dialog.validate():
                return
            res = m6_maintenance_service.crear_repuesto(
                codigo=dialog.txt_codigo.text(),
                nombre=dialog.txt_nombre.text(),
                costo_unitario=dialog.spin_costo.value()
            )
            if res.get("success"):
                InfoBar.success("Pieza Registrada", res.get("mensaje", ""), parent=self.window(), duration=3000)
                self.refresh_repuestos()
            else:
                InfoBar.error("Error", res.get("error", ""), parent=self.window(), duration=4000)

    def handle_editar_repuesto(self):
        selected = self.table_catalogo_repuestos.selectedItems()
        if not selected:
            InfoBar.warning("Selección Requerida", "Seleccione un repuesto para editar.", parent=self.window(), duration=3000)
            return

        r = selected[0].row()
        repuesto = self.repuestos_cache[r]
        id_rep = _safe_int(repuesto.get("ID_REPUESTO"))

        dialog = RepuestoDialog(repuesto, self.window())
        if dialog.exec():
            if not dialog.validate():
                return
            res = m6_maintenance_service.modificar_repuesto(
                id_repuesto=id_rep,
                codigo=dialog.txt_codigo.text(),
                nombre=dialog.txt_nombre.text(),
                costo_unitario=dialog.spin_costo.value()
            )
            if res.get("success"):
                InfoBar.success("Repuesto Actualizado", res.get("mensaje", ""), parent=self.window(), duration=3000)
                self.refresh_repuestos()
            else:
                InfoBar.error("Error", res.get("error", ""), parent=self.window(), duration=4000)

    def handle_eliminar_repuesto(self):
        selected = self.table_catalogo_repuestos.selectedItems()
        if not selected:
            InfoBar.warning("Selección Requerida", "Seleccione un repuesto para eliminar.", parent=self.window(), duration=3000)
            return

        r = selected[0].row()
        repuesto = self.repuestos_cache[r]
        id_rep = _safe_int(repuesto.get("ID_REPUESTO"))
        cod = _safe_str(repuesto.get("CODIGO"))

        box = MessageBox("Eliminar Repuesto", f"¿Confirma la eliminación del repuesto {cod} del catálogo?", self.window())
        if box.exec():
            res = m6_maintenance_service.eliminar_repuesto(id_rep)
            if res.get("success"):
                InfoBar.success("Repuesto Eliminado", res.get("mensaje", ""), parent=self.window(), duration=3000)
                self.refresh_repuestos()
            else:
                InfoBar.error("Restricción de Integridad", res.get("error", ""), parent=self.window(), duration=5000)

    def handle_consumir_repuesto(self):
        id_ord = self.combo_rep_orden.currentData()
        if not id_ord:
            InfoBar.warning("Orden Requerida", "Seleccione una orden de trabajo primero.", parent=self.window(), duration=3000)
            return

        if not self.repuestos_cache:
            InfoBar.warning("Sin Repuestos", "No hay repuestos registrados en el catálogo.", parent=self.window(), duration=3000)
            return

        dialog = ConsumoRepuestoDialog(self.repuestos_cache, self.window())
        if dialog.exec():
            rep_id = dialog.combo_repuesto.currentData()
            cant = dialog.spin_cantidad.value()
            if not rep_id:
                return

            res = m6_maintenance_service.registrar_consumo_repuesto(int(id_ord), int(rep_id), cant)
            if res.get("success"):
                InfoBar.success("Consumo Registrado", res.get("mensaje", ""), parent=self.window(), duration=3000)
                self.on_rep_orden_changed()
                self.refresh_kpis()
            else:
                InfoBar.error("Error", res.get("error", ""), parent=self.window(), duration=4000)

    def handle_eliminar_consumo(self):
        selected = self.table_orden_repuestos.selectedItems()
        if not selected:
            InfoBar.warning("Selección Requerida", "Seleccione una partida de repuesto para remover.", parent=self.window(), duration=3000)
            return

        r = selected[0].row()
        item = self.table_orden_repuestos.item(r, 0)
        id_orp = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if not id_orp:
            return

        box = MessageBox("Remover Repuesto", "¿Desea eliminar este consumo de repuesto de la orden?", self.window())
        if box.exec():
            res = m6_maintenance_service.eliminar_consumo_repuesto(int(id_orp))
            if res.get("success"):
                InfoBar.success("Partida Removida", res.get("mensaje", ""), parent=self.window(), duration=3000)
                self.on_rep_orden_changed()
                self.refresh_kpis()
            else:
                InfoBar.error("Error", res.get("error", ""), parent=self.window(), duration=4000)

    # ==========================================================================
    # PESTANA 5: ALERTAS Y MATERIAL EN TALLER
    # ==========================================================================

    def init_tab_alertas(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(12)

        # Seccion Superior: Trenes en Taller (VW_TRENES_MANTENIMIENTO)
        card_taller = CardWidget(tab_widget)
        taller_layout = QVBoxLayout(card_taller)
        taller_layout.setContentsMargins(14, 12, 14, 12)
        taller_layout.setSpacing(8)

        taller_layout.addWidget(StrongBodyLabel("Trenes en Mantenimiento en Taller (VW_TRENES_MANTENIMIENTO)", card_taller))
        self.table_taller = TableWidget(card_taller)
        self.table_taller.setColumnCount(8)
        self.table_taller.setHorizontalHeaderLabels([
            "Tren", "Modelo", "Depósito Base", "Nº Orden",
            "Tipo Trabajo", "Prioridad", "Técnico Responsable", "Ingreso a Taller"
        ])
        self.table_taller.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        taller_header = self.table_taller.horizontalHeader()
        if taller_header is not None:
            taller_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            taller_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            taller_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            taller_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            taller_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            taller_header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
            taller_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
            taller_header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        taller_layout.addWidget(self.table_taller, stretch=1)
        v_layout.addWidget(card_taller, stretch=1)

        # Seccion Inferior: Equipos Fuera de Servicio e Inspecciones Vencidas
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal, tab_widget)

        # Izquierda: Fuera de servicio
        card_fuera = CardWidget(bottom_splitter)
        fuera_layout = QVBoxLayout(card_fuera)
        fuera_layout.setContentsMargins(14, 12, 14, 12)
        fuera_layout.setSpacing(8)

        fuera_layout.addWidget(StrongBodyLabel("Equipos Fuera de Servicio o En Reparación", card_fuera))
        self.table_fuera = TableWidget(card_fuera)
        self.table_fuera.setColumnCount(4)
        self.table_fuera.setHorizontalHeaderLabels(["Código", "Tipo", "Ubicación", "Estado"])
        self.table_fuera.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        fuera_header = self.table_fuera.horizontalHeader()
        if fuera_header is not None:
            fuera_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            fuera_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            fuera_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            fuera_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        fuera_layout.addWidget(self.table_fuera, stretch=1)
        bottom_splitter.addWidget(card_fuera)

        # Derecha: Inspecciones vencidas
        card_vencidas = CardWidget(bottom_splitter)
        vencidas_layout = QVBoxLayout(card_vencidas)
        vencidas_layout.setContentsMargins(14, 12, 14, 12)
        vencidas_layout.setSpacing(8)

        vencidas_layout.addWidget(StrongBodyLabel("Inspecciones Técnicas Vencidas o Próximas", card_vencidas))
        self.table_vencidas = TableWidget(card_vencidas)
        self.table_vencidas.setColumnCount(4)
        self.table_vencidas.setHorizontalHeaderLabels(["Código", "Tipo", "Próxima Revisión", "Días Restantes"])
        self.table_vencidas.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        vencidas_header = self.table_vencidas.horizontalHeader()
        if vencidas_header is not None:
            vencidas_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            vencidas_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            vencidas_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            vencidas_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        vencidas_layout.addWidget(self.table_vencidas, stretch=1)
        bottom_splitter.addWidget(card_vencidas)

        bottom_splitter.setStretchFactor(0, 1)
        bottom_splitter.setStretchFactor(1, 1)
        v_layout.addWidget(bottom_splitter, stretch=1)

        self.stack_views.addWidget(tab_widget)

    def refresh_alertas(self):
        # 1. Trenes en Taller
        trenes = m6_maintenance_service.get_trenes_en_taller()
        self.table_taller.blockSignals(True)
        self.table_taller.setRowCount(len(trenes))
        for r, t in enumerate(trenes):
            self.table_taller.setItem(r, 0, QTableWidgetItem(_safe_str(t.get("CODIGO_TREN"))))
            self.table_taller.setItem(r, 1, QTableWidgetItem(_safe_str(t.get("NOMBRE_MODELO"))))
            self.table_taller.setItem(r, 2, QTableWidgetItem(_safe_str(t.get("DEPOSITO"))))
            self.table_taller.setItem(r, 3, QTableWidgetItem(_safe_str(t.get("NUMERO_ORDEN"))))
            self.table_taller.setItem(r, 4, QTableWidgetItem(_safe_str(t.get("TIPO_MANTENIMIENTO"))))
            self.table_taller.setItem(r, 5, QTableWidgetItem(_safe_str(t.get("PRIORIDAD"))))
            self.table_taller.setItem(r, 6, QTableWidgetItem(_safe_str(t.get("TECNICO_RESPONSABLE"))))
            self.table_taller.setItem(r, 7, QTableWidgetItem(_safe_str(t.get("FECHA_INGRESO_TALLER"))))
        self.table_taller.blockSignals(False)

        # 2. Equipos fuera de servicio
        equipos_fuera = m6_maintenance_service.get_equipos_fuera_servicio()
        self.table_fuera.blockSignals(True)
        self.table_fuera.setRowCount(len(equipos_fuera))
        for r, eq in enumerate(equipos_fuera):
            self.table_fuera.setItem(r, 0, QTableWidgetItem(_safe_str(eq.get("CODIGO_EQUIPO"))))
            self.table_fuera.setItem(r, 1, QTableWidgetItem(_safe_str(eq.get("TIPO_EQUIPO"))))
            self.table_fuera.setItem(r, 2, QTableWidgetItem(_safe_str(eq.get("UBICACION"))))
            self.table_fuera.setItem(r, 3, QTableWidgetItem(_safe_str(eq.get("ESTADO"))))
        self.table_fuera.blockSignals(False)

        # 3. Inspecciones vencidas
        vencidas = m6_maintenance_service.get_equipos_inspeccion_vencida()
        self.table_vencidas.blockSignals(True)
        self.table_vencidas.setRowCount(len(vencidas))
        for r, v in enumerate(vencidas):
            dias = _safe_int(v.get("DIAS_RESTANTES"))
            dias_str = f"VENCIDA ({abs(dias)} días de atraso)" if dias < 0 else f"{dias} días restantes"
            self.table_vencidas.setItem(r, 0, QTableWidgetItem(_safe_str(v.get("CODIGO_EQUIPO"))))
            self.table_vencidas.setItem(r, 1, QTableWidgetItem(_safe_str(v.get("TIPO_EQUIPO"))))
            self.table_vencidas.setItem(r, 2, QTableWidgetItem(_safe_str(v.get("FECHA_PROXIMA_REVISION"), "Sin Programar")))
            self.table_vencidas.setItem(r, 3, QTableWidgetItem(dias_str))
        self.table_vencidas.blockSignals(False)

    # ==========================================================================
    # CARGA GLOBAL DESDE MAIN WINDOW
    # ==========================================================================

    def load_maintenance_data(self):
        """Metodo de enlace invocado por load_all_data() en MetroFluentApp."""
        current_idx = self.stack_views.currentIndex()
        if current_idx == 0:
            self.refresh_ordenes()
        elif current_idx == 1:
            self.refresh_equipos()
        elif current_idx == 2:
            self.refresh_cuadrillas()
        elif current_idx == 3:
            self.refresh_repuestos()
        else:
            self.refresh_alertas()
