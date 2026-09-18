"""
m5_cards_interface.py - Vista principal para el Módulo 5: Pasajeros y Tarifas OMNY.
Cumple estrictamente con los 10 requerimientos del enunciado y las reglas de negocio 13, 14, 15, 16, 17, 18, 21 y 25:
1. Registrar pasajeros frecuentes con clasificación por categoría (Adulto Mayor, Estudiante, etc.).
2. Emitir tarjetas OMNY nominales y anónimas (Regla 13).
3. Recargar saldo mediante SP_RECARGAR_TARJETA (Regla 14).
4. Bloquear, reactivar y gestionar el ciclo de vida de las tarjetas (Regla 16).
5. Registrar el ingreso y salida en torniquetes respetando estaciones operativas (Regla 21).
6. Cobrar la tarifa aplicable preservando el monto histórico en VIAJE_PASAJERO (Regla 18).
7. Consultar saldo en tiempo real mediante la tarjeta gráfica VisualOmnyCard (Regla 15).
8. Consultar historiales detallados de viajes y recargas (Regla 25).
9. Registrar viajes anónimos directos en torniquete.
10. Detectar tarjetas vencidas o sin saldo.
11. Catálogo oficial de tarifas y visualización de OMNY Fare Capping.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QHeaderView, QFormLayout, QTableWidgetItem, QGridLayout
)

from qfluentwidgets import (
    TitleLabel, SubtitleLabel, CaptionLabel, BodyLabel, StrongBodyLabel,
    CardWidget, ComboBox, LineEdit, SearchLineEdit, DoubleSpinBox, SpinBox,
    PrimaryPushButton, PushButton, TableWidget, InfoBar, InfoBarPosition,
    SegmentedWidget, CheckBox, MessageBoxBase, MessageBox, IconWidget,
    FluentIcon as FIF
)

from services import m5_cards_service


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
# COMPONENTE VISUAL: TARJETA OMNY MTA BLUE
# ==============================================================================

class VisualOmnyCard(CardWidget):
    """
    Representación visual estilizada de la tarjeta física OMNY / MetroCard
    con gradiente oficial MTA Blue y tipografía de alta fidelidad.
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(360, 200)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            VisualOmnyCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0039A6, stop:1 #001B4D);
                border-radius: 14px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QLabel {
                color: #FFFFFF;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)

        # Fila superior: Logo MTA y OMNY Contactless
        top_layout = QHBoxLayout()
        self.lbl_logo = CaptionLabel("MTA NYCT • SUBWAY", self)
        self.lbl_logo.setStyleSheet("color: rgba(255, 255, 255, 0.85); font-weight: bold; letter-spacing: 1.5px;")

        self.lbl_tech = CaptionLabel("(((•))) OMNY", self)
        self.lbl_tech.setStyleSheet("color: #FFCC00; font-weight: bold; font-size: 13px;")

        top_layout.addWidget(self.lbl_logo)
        top_layout.addStretch(1)
        top_layout.addWidget(self.lbl_tech)
        layout.addLayout(top_layout)

        layout.addStretch(1)

        # Número de tarjeta
        self.lbl_card_num = TitleLabel("OMNY-0000-0000", self)
        self.lbl_card_num.setStyleSheet("color: #FFFFFF; font-family: 'Consolas', monospace; font-size: 18px; font-weight: bold; letter-spacing: 2px;")
        layout.addWidget(self.lbl_card_num)

        # Fila inferior: Titular, Tarifa y Saldo
        bottom_layout = QHBoxLayout()

        col_info = QVBoxLayout()
        col_info.setSpacing(2)
        self.lbl_titular = BodyLabel("Cargando titular...", self)
        self.lbl_titular.setStyleSheet("color: #FFFFFF; font-weight: 600; font-size: 13px;")
        self.lbl_tarifa = CaptionLabel("Tarifa Base Estándar ($2.90)", self)
        self.lbl_tarifa.setStyleSheet("color: rgba(255, 255, 255, 0.75); font-size: 11px;")
        col_info.addWidget(self.lbl_titular)
        col_info.addWidget(self.lbl_tarifa)

        bottom_layout.addLayout(col_info)
        bottom_layout.addStretch(1)

        col_saldo = QVBoxLayout()
        col_saldo.setSpacing(2)
        col_saldo.setAlignment(Qt.AlignmentFlag.AlignRight)
        lbl_saldo_tag = CaptionLabel("SALDO DISPONIBLE", self)
        lbl_saldo_tag.setStyleSheet("color: rgba(255, 255, 255, 0.75); font-size: 9px; font-weight: bold; letter-spacing: 0.8px;")
        self.lbl_saldo = TitleLabel("$0.00", self)
        self.lbl_saldo.setStyleSheet("color: #00E676; font-size: 20px; font-weight: bold;")
        col_saldo.addWidget(lbl_saldo_tag, alignment=Qt.AlignmentFlag.AlignRight)
        col_saldo.addWidget(self.lbl_saldo, alignment=Qt.AlignmentFlag.AlignRight)

        bottom_layout.addLayout(col_saldo)
        layout.addLayout(bottom_layout)

    def set_card_data(self, numero: str, titular: str, tarifa: str, saldo: float, estado: str):
        self.lbl_card_num.setText(numero)
        self.lbl_titular.setText(titular)
        self.lbl_tarifa.setText(f"{tarifa} [{estado}]")
        self.lbl_saldo.setText(f"${saldo:.2f}")
        if estado == "Activa":
            self.lbl_saldo.setStyleSheet("color: #00E676; font-size: 20px; font-weight: bold;")
        elif estado in ("Bloqueada", "Cancelada", "Reportada Perdida"):
            self.lbl_saldo.setStyleSheet("color: #FF5252; font-size: 20px; font-weight: bold;")
        else:
            self.lbl_saldo.setStyleSheet("color: #FFD600; font-size: 20px; font-weight: bold;")


# ==============================================================================
# DIALOGOS MODALES FLUENT (MODULO 5)
# ==============================================================================

class PasajeroDialog(MessageBoxBase):
    """Diálogo modal para registrar o modificar datos de un pasajero frecuente."""
    def __init__(self, parent=None, pas_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.pas_data = pas_data
        self.es_edicion = pas_data is not None

        titulo = "Modificar Pasajero Frecuente" if self.es_edicion else "Registrar Nuevo Pasajero"
        self.titleLabel = SubtitleLabel(titulo, self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        # 1. Nombre Completo
        self.txt_nombre = LineEdit(self)
        self.txt_nombre.setPlaceholderText("p.ej. Liam Noah Smith")
        if self.es_edicion and self.pas_data:
            self.txt_nombre.setText(_safe_str(self.pas_data.get("NOMBRE", "")))
        form.addRow("Nombre Completo:", self.txt_nombre)

        # 2. Identificador / Código
        self.txt_ident = LineEdit(self)
        self.txt_ident.setPlaceholderText("p.ej. PAS-001 (Autogenerado si vacío)")
        if self.es_edicion and self.pas_data:
            self.txt_ident.setText(_safe_str(self.pas_data.get("IDENTIFICADOR", "")))
        form.addRow("Identificador:", self.txt_ident)

        # 3. Tipo de Pasajero
        self.combo_tipo = ComboBox(self)
        tipos = ["Regular", "Estudiante", "Adulto Mayor", "Persona con Discapacidad", "Empleado Autorizado"]
        self.combo_tipo.addItems(tipos)
        if self.es_edicion and self.pas_data:
            idx = self.combo_tipo.findText(_safe_str(self.pas_data.get("TIPO_PASAJERO", "")))
            if idx >= 0:
                self.combo_tipo.setCurrentIndex(idx)
        form.addRow("Tipo de Pasajero:", self.combo_tipo)

        # 4. Fecha de Nacimiento
        self.txt_fnac = LineEdit(self)
        self.txt_fnac.setPlaceholderText("YYYY-MM-DD")
        if self.es_edicion and self.pas_data:
            self.txt_fnac.setText(_safe_str(self.pas_data.get("FECHA_NACIMIENTO", "")))
        form.addRow("Fecha Nacimiento:", self.txt_fnac)

        # 5. Teléfono y Correo Electrónico
        self.txt_tel = LineEdit(self)
        self.txt_tel.setPlaceholderText("+1 (555) 000-0000")
        if self.es_edicion and self.pas_data:
            self.txt_tel.setText(_safe_str(self.pas_data.get("TELEFONO", "")))
        form.addRow("Teléfono:", self.txt_tel)

        self.txt_correo = LineEdit(self)
        self.txt_correo.setPlaceholderText("usuario@gmail.com")
        if self.es_edicion and self.pas_data:
            self.txt_correo.setText(_safe_str(self.pas_data.get("CORREO_ELECTRONICO", "")))
        form.addRow("Correo Electrónico:", self.txt_correo)

        # 6. Estado
        self.combo_estado = ComboBox(self)
        self.combo_estado.addItems(["Activo", "Inactivo"])
        if self.es_edicion and self.pas_data:
            idx = self.combo_estado.findText(_safe_str(self.pas_data.get("ESTADO", "")))
            if idx >= 0:
                self.combo_estado.setCurrentIndex(idx)
        form.addRow("Estado:", self.combo_estado)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Guardar Cambios" if self.es_edicion else "Registrar Pasajero")
        self.cancelButton.setText("Cancelar")

    def get_data(self) -> Dict[str, Any]:
        return {
            "nombre": self.txt_nombre.text().strip(),
            "identificador": self.txt_ident.text().strip(),
            "tipo_pasajero": self.combo_tipo.currentText(),
            "fecha_nacimiento": self.txt_fnac.text().strip() or None,
            "telefono": self.txt_tel.text().strip() or None,
            "correo_electronico": self.txt_correo.text().strip() or None,
            "estado": self.combo_estado.currentText()
        }


class EmitirTarjetaDialog(MessageBoxBase):
    """Diálogo modal para emitir una nueva tarjeta OMNY (nominal o anónima)."""
    def __init__(self, parent=None, pasajeros_list: Optional[List[Dict[str, Any]]] = None):
        super().__init__(parent)
        self.pasajeros_list = pasajeros_list or []

        self.titleLabel = SubtitleLabel("Emitir Nueva Tarjeta OMNY", self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        # 1. Número de Tarjeta (Opcional)
        self.txt_numero = LineEdit(self)
        self.txt_numero.setPlaceholderText("p.ej. OMNY-1001-0050 (Autogenerado si vacío)")
        form.addRow("N° de Tarjeta:", self.txt_numero)

        # 2. Pasajero Titular (Opcional - Regla 13: puede ser anónima)
        self.combo_pasajero = ComboBox(self)
        self.combo_pasajero.addItem("(Tarjeta Anónima / Al Portador)", userData=None)
        for p in self.pasajeros_list:
            p_id = _safe_int(p.get("ID_PASAJERO", 0))
            nom = p.get("NOMBRE", "")
            tipo = p.get("TIPO_PASAJERO", "Regular")
            self.combo_pasajero.addItem(f"{nom} ({tipo})", userData=p_id)
        form.addRow("Titular Asignado:", self.combo_pasajero)

        # 3. Tarifa Asignada
        self.combo_tarifa = ComboBox(self)
        tarifas = m5_cards_service.get_tarifas_combo()
        for t in tarifas:
            t_id = _safe_int(t.get("ID_TARIFA", 0))
            nom = t.get("NOMBRE", "")
            monto = _safe_float(t.get("MONTO", 0.0))
            self.combo_tarifa.addItem(f"{nom} (${monto:.2f})", userData=t_id)
        form.addRow("Tarifa de Aplicación:", self.combo_tarifa)

        # 4. Saldo Inicial (Regla 15: no negativo)
        self.spin_saldo = DoubleSpinBox(self)
        self.spin_saldo.setRange(0.00, 500.00)
        self.spin_saldo.setValue(10.00)
        self.spin_saldo.setSingleStep(5.00)
        self.spin_saldo.setPrefix("$ ")
        form.addRow("Saldo Inicial:", self.spin_saldo)

        # 5. Fecha de Vencimiento
        self.txt_fvenc = LineEdit(self)
        default_venc = (date.today().replace(year=date.today().year + 5)).strftime("%Y-%m-%d")
        self.txt_fvenc.setText(default_venc)
        form.addRow("Vencimiento:", self.txt_fvenc)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Emitir Tarjeta")
        self.cancelButton.setText("Cancelar")

    def get_data(self) -> Dict[str, Any]:
        return {
            "numero_tarjeta": self.txt_numero.text().strip(),
            "pasajero_id": self.combo_pasajero.currentData(),
            "tarifa_id": self.combo_tarifa.currentData(),
            "saldo_disponible": self.spin_saldo.value(),
            "fecha_vencimiento": self.txt_fvenc.text().strip() or None,
            "estado": "Activa"
        }


class BloquearTarjetaDialog(MessageBoxBase):
    """Diálogo modal para cambiar el estado operativo o bloquear una tarjeta."""
    def __init__(self, numero_tarjeta: str, estado_actual: str, parent=None):
        super().__init__(parent)
        self.numero_tarjeta = numero_tarjeta

        self.titleLabel = SubtitleLabel(f"Gestión de Estado: {numero_tarjeta}", self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        self.combo_estado = ComboBox(self)
        estados = ["Activa", "Bloqueada", "Reportada Perdida", "Cancelada", "Vencida"]
        self.combo_estado.addItems(estados)
        idx = self.combo_estado.findText(estado_actual)
        if idx >= 0:
            self.combo_estado.setCurrentIndex(idx)
        form.addRow("Nuevo Estado:", self.combo_estado)

        self.txt_motivo = LineEdit(self)
        self.txt_motivo.setPlaceholderText("p.ej. Reporte de extravío por el usuario")
        form.addRow("Motivo / Observación:", self.txt_motivo)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Actualizar Estado")
        self.cancelButton.setText("Cancelar")

    def get_nuevo_estado(self) -> str:
        return self.combo_estado.currentText()


class TarifaDialog(MessageBoxBase):
    """Diálogo modal para crear o modificar una tarifa comercial de la MTA."""
    def __init__(self, parent=None, tarifa_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.tarifa_data = tarifa_data
        self.es_edicion = tarifa_data is not None

        titulo = "Modificar Tarifa Comercial" if self.es_edicion else "Nueva Tarifa MTA"
        self.titleLabel = SubtitleLabel(titulo, self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        # 1. Código
        self.txt_cod = LineEdit(self)
        self.txt_cod.setPlaceholderText("p.ej. TAR-REG")
        if self.es_edicion and self.tarifa_data:
            self.txt_cod.setText(_safe_str(self.tarifa_data.get("CODIGO", "")))
            self.txt_cod.setEnabled(False)
        form.addRow("Código:", self.txt_cod)

        # 2. Nombre
        self.txt_nom = LineEdit(self)
        self.txt_nom.setPlaceholderText("p.ej. Tarifa Base Estándar")
        if self.es_edicion and self.tarifa_data:
            self.txt_nom.setText(_safe_str(self.tarifa_data.get("NOMBRE", "")))
        form.addRow("Nombre de Tarifa:", self.txt_nom)

        # 3. Monto
        self.spin_monto = DoubleSpinBox(self)
        self.spin_monto.setRange(0.00, 500.00)
        self.spin_monto.setDecimals(2)
        self.spin_monto.setPrefix("$ ")
        monto_val = _safe_float(self.tarifa_data.get("MONTO")) if self.es_edicion and self.tarifa_data else 2.90
        self.spin_monto.setValue(monto_val)
        form.addRow("Costo por Viaje:", self.spin_monto)

        # 4. Tipo de Pasajero
        self.combo_tipo = ComboBox(self)
        tipos = ["Regular", "Estudiante", "Adulto Mayor", "Persona con Discapacidad", "Empleado Autorizado"]
        self.combo_tipo.addItems(tipos)
        if self.es_edicion and self.tarifa_data:
            idx = self.combo_tipo.findText(_safe_str(self.tarifa_data.get("TIPO_PASAJERO", "")))
            if idx >= 0:
                self.combo_tipo.setCurrentIndex(idx)
        form.addRow("Perfil Beneficiario:", self.combo_tipo)

        # 5. Vigencia
        self.txt_fini = LineEdit(self)
        self.txt_fini.setPlaceholderText("YYYY-MM-DD")
        if self.es_edicion and self.tarifa_data:
            self.txt_fini.setText(_safe_str(self.tarifa_data.get("FECHA_INICIO", "")))
        else:
            self.txt_fini.setText(date.today().strftime("%Y-%m-%d"))
        form.addRow("Inicio Vigencia:", self.txt_fini)

        self.txt_ffin = LineEdit(self)
        self.txt_ffin.setPlaceholderText("YYYY-MM-DD (Opcional)")
        if self.es_edicion and self.tarifa_data:
            self.txt_ffin.setText(_safe_str(self.tarifa_data.get("FECHA_FIN", "")))
        form.addRow("Fin Vigencia:", self.txt_ffin)

        # 6. Estado
        self.combo_estado = ComboBox(self)
        self.combo_estado.addItems(["Vigente", "Suspendida", "Vencida"])
        if self.es_edicion and self.tarifa_data:
            idx = self.combo_estado.findText(_safe_str(self.tarifa_data.get("ESTADO", "")))
            if idx >= 0:
                self.combo_estado.setCurrentIndex(idx)
        form.addRow("Estado:", self.combo_estado)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Guardar Tarifa")
        self.cancelButton.setText("Cancelar")

    def get_data(self) -> Dict[str, Any]:
        return {
            "codigo": self.txt_cod.text().strip().upper(),
            "nombre": self.txt_nom.text().strip(),
            "monto": self.spin_monto.value(),
            "tipo_pasajero": self.combo_tipo.currentText(),
            "fecha_inicio_vigencia": self.txt_fini.text().strip() or None,
            "fecha_fin_vigencia": self.txt_ffin.text().strip() or None,
            "estado": self.combo_estado.currentText()
        }


# ==============================================================================
# VISTA PRINCIPAL FLUENT (MODULO 5: PASAJEROS Y TARIFAS OMNY)
# ==============================================================================

class CardsInterface(QWidget):
    """
    Vista principal para el Módulo 5: Pasajeros, Tarifas y Torniquetes OMNY.
    Estructura desacoplada: Título en su propio CardWidget y pestañas en
    SegmentedWidget de ancho completo.
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("cardsInterface")

        self.selected_card_num: Optional[str] = None
        self.selected_pasajero_id: Optional[int] = None
        self.tarjetas_cache: List[Dict[str, Any]] = []
        self.pasajeros_cache: List[Dict[str, Any]] = []

        self.init_ui()
        self.load_cards_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # ----------------------------------------------------------------------
        # 1. CONTENEDOR EXCLUSIVO DE TITULO Y SUBTITULO
        # ----------------------------------------------------------------------
        header_card = CardWidget(self)
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(18, 14, 18, 14)
        header_layout.setSpacing(4)

        title = TitleLabel("Pasajeros, Tarifas y Torniquetes OMNY", header_card)
        subtitle = SubtitleLabel("Modulo 5: Gestion de usuarios frecuentes, emision de tarjetas OMNY, cobro de tarifas y simulador de torniquetes", header_card)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        main_layout.addWidget(header_card)

        # ----------------------------------------------------------------------
        # 2. CONTENEDOR INDEPENDIENTE DE PESTANAS (SEGMENTED WIDGET DE ANCHO COMPLETO)
        # ----------------------------------------------------------------------
        tabs_layout = QHBoxLayout()
        self.segmented_tabs = SegmentedWidget(self)
        self.segmented_tabs.addItem("tab_torniquetes", "Torniquetes y Tarjeta OMNY")
        self.segmented_tabs.addItem("tab_tarjetas", "Directorio de Tarjetas")
        self.segmented_tabs.addItem("tab_pasajeros", "Padrón de Pasajeros")
        self.segmented_tabs.addItem("tab_tarifas", "Catálogo de Tarifas y Fare Capping")

        self.segmented_tabs.setCurrentItem("tab_torniquetes")
        self.segmented_tabs.currentItemChanged.connect(self.on_tab_changed)

        tabs_layout.addWidget(self.segmented_tabs)
        main_layout.addLayout(tabs_layout)

        # ----------------------------------------------------------------------
        # 3. STACKED WIDGET PARA LAS VISTAS
        # ----------------------------------------------------------------------
        self.stack_views = QStackedWidget(self)

        self.init_tab_torniquetes()
        self.init_tab_tarjetas()
        self.init_tab_pasajeros()
        self.init_tab_tarifas()

        main_layout.addWidget(self.stack_views, stretch=1)

    def showEvent(self, a0):
        super().showEvent(a0)
        if not self.segmented_tabs.currentItem():
            self.segmented_tabs.setCurrentItem("tab_torniquetes")

    def on_tab_changed(self, key: str):
        if key == "tab_torniquetes":
            self.stack_views.setCurrentIndex(0)
            self.refresh_kpis()
        elif key == "tab_tarjetas":
            self.stack_views.setCurrentIndex(1)
            self.refresh_cards_list()
        elif key == "tab_pasajeros":
            self.stack_views.setCurrentIndex(2)
            self.refresh_pasajeros()
        else:
            self.stack_views.setCurrentIndex(3)
            self.refresh_tarifas()

    # ==========================================================================
    # PESTANA 1: TORNIQUETES Y TARJETA OMNY
    # ==========================================================================

    def init_tab_torniquetes(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(12)

        # 1. Tarjetas Métricas (KPIs)
        card_kpis = CardWidget(tab_widget)
        kpi_layout = QHBoxLayout(card_kpis)
        kpi_layout.setContentsMargins(16, 12, 16, 12)
        kpi_layout.setSpacing(18)

        self.lbl_kpi_tarjetas = StrongBodyLabel("Total Tarjetas: -", card_kpis)
        self.lbl_kpi_activas = StrongBodyLabel("Tarjetas Activas: -", card_kpis)
        self.lbl_kpi_saldo = StrongBodyLabel("Saldo en Circulación: -", card_kpis)
        self.lbl_kpi_viajes = StrongBodyLabel("Viajes Hoy: -", card_kpis)
        self.lbl_kpi_recaudo = StrongBodyLabel("Recaudación Hoy: -", card_kpis)

        kpi_layout.addWidget(self.lbl_kpi_tarjetas)
        kpi_layout.addWidget(self.lbl_kpi_activas)
        kpi_layout.addWidget(self.lbl_kpi_saldo)
        kpi_layout.addWidget(self.lbl_kpi_viajes)
        kpi_layout.addWidget(self.lbl_kpi_recaudo)
        kpi_layout.addStretch(1)
        v_layout.addWidget(card_kpis)

        # 2. Contenedor Interactivo en 2 Columnas
        row_content = QHBoxLayout()
        row_content.setSpacing(14)

        # Columna Izquierda: Tarjeta Visual + Recarga Express
        col_izq = QVBoxLayout()
        col_izq.setSpacing(12)

        self.visual_card = VisualOmnyCard(tab_widget)
        col_izq.addWidget(self.visual_card, alignment=Qt.AlignmentFlag.AlignCenter)

        # Caja de Recarga Express
        card_recharge = CardWidget(tab_widget)
        rec_layout = QVBoxLayout(card_recharge)
        rec_layout.setContentsMargins(16, 14, 16, 14)
        rec_layout.setSpacing(8)

        rec_layout.addWidget(StrongBodyLabel("Recarga de Saldo OMNY / MetroCard", card_recharge))

        rec_inputs = QHBoxLayout()
        col_m = QVBoxLayout()
        col_m.addWidget(CaptionLabel("Monto ($):", card_recharge))
        self.spin_monto_rec = DoubleSpinBox(card_recharge)
        self.spin_monto_rec.setRange(1.0, 500.0)
        self.spin_monto_rec.setValue(10.0)
        self.spin_monto_rec.setSingleStep(5.0)
        self.spin_monto_rec.setPrefix("$ ")
        col_m.addWidget(self.spin_monto_rec)
        rec_inputs.addLayout(col_m)

        col_p = QVBoxLayout()
        col_p.addWidget(CaptionLabel("Medio de Pago:", card_recharge))
        self.combo_medio_pago = ComboBox(card_recharge)
        self.combo_medio_pago.addItems(["Efectivo", "Tarjeta Débito", "Tarjeta Crédito", "App Móvil", "Transferencia"])
        col_p.addWidget(self.combo_medio_pago)
        rec_inputs.addLayout(col_p)
        rec_layout.addLayout(rec_inputs)

        quick_row = QHBoxLayout()
        quick_row.setSpacing(6)
        for amt in [5, 10, 20, 50]:
            b = PushButton(f"+${amt}", card_recharge)
            b.clicked.connect(lambda ch, a=amt: self.spin_monto_rec.setValue(float(a)))
            quick_row.addWidget(b)
        rec_layout.addLayout(quick_row)

        self.btn_ejecutar_recarga = PrimaryPushButton("Abonar Saldo a la Tarjeta", card_recharge, FIF.ADD)
        self.btn_ejecutar_recarga.clicked.connect(self.handle_recharge)
        rec_layout.addWidget(self.btn_ejecutar_recarga)

        col_izq.addWidget(card_recharge)
        col_izq.addStretch(1)
        row_content.addLayout(col_izq, stretch=4)

        # Columna Derecha: Simulador de Torniquete y Actividad Reciente
        col_der = QVBoxLayout()
        col_der.setSpacing(12)

        card_sim = CardWidget(tab_widget)
        sim_layout = QVBoxLayout(card_sim)
        sim_layout.setContentsMargins(16, 14, 16, 14)
        sim_layout.setSpacing(8)

        sim_layout.addWidget(StrongBodyLabel("Simulador de Paso en Torniquete (SP_REGISTRAR_INGRESO)", card_sim))

        sim_layout.addWidget(CaptionLabel("Estación donde se ubica el torniquete:", card_sim))
        self.combo_estaciones = ComboBox(card_sim)
        sim_layout.addWidget(self.combo_estaciones)

        sim_layout.addWidget(CaptionLabel("Tarjeta a aproximar al lector OMNY:", card_sim))
        self.combo_tarjetas = ComboBox(card_sim)
        self.combo_tarjetas.currentIndexChanged.connect(self.on_card_combo_selected)
        sim_layout.addWidget(self.combo_tarjetas)

        btns_tap = QHBoxLayout()
        btns_tap.setSpacing(8)
        self.btn_tap = PrimaryPushButton("Validar Paso en Torniquete ($2.90)", card_sim, FIF.QRCODE)
        self.btn_tap.clicked.connect(self.handle_turnstile_tap)
        btns_tap.addWidget(self.btn_tap, stretch=3)

        self.btn_tap_anon = PushButton("Paso Anónimo Contactless", card_sim, FIF.SEND)
        self.btn_tap_anon.clicked.connect(self.handle_anonymous_tap)
        btns_tap.addWidget(self.btn_tap_anon, stretch=2)
        sim_layout.addLayout(btns_tap)

        col_der.addWidget(card_sim)

        # Tabla de últimos pasos por torniquete de esta tarjeta
        card_log = CardWidget(tab_widget)
        log_layout = QVBoxLayout(card_log)
        log_layout.setContentsMargins(16, 12, 16, 12)
        log_layout.setSpacing(6)

        log_layout.addWidget(StrongBodyLabel("Últimas Transacciones Registradas en Torniquete", card_log))
        self.table_recent_taps = TableWidget(card_log)
        self.table_recent_taps.setBorderVisible(True)
        self.table_recent_taps.setColumnCount(5)
        self.table_recent_taps.setHorizontalHeaderLabels(["N° Transacción", "Tarjeta", "Estación", "Hora Ingreso", "Cobro"])
        ht = self.table_recent_taps.horizontalHeader()
        if ht is not None:
            ht.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_recent_taps.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        log_layout.addWidget(self.table_recent_taps)

        col_der.addWidget(card_log, stretch=3)
        row_content.addLayout(col_der, stretch=6)

        v_layout.addLayout(row_content, stretch=1)
        self.stack_views.addWidget(tab_widget)

    # ==========================================================================
    # PESTANA 2: DIRECTORIO DE TARJETAS
    # ==========================================================================

    def init_tab_tarjetas(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(10)

        bar_actions = QHBoxLayout()
        bar_actions.setSpacing(8)

        self.search_tarjetas = SearchLineEdit(tab_widget)
        self.search_tarjetas.setPlaceholderText("Buscar por número de tarjeta o titular...")
        self.search_tarjetas.textChanged.connect(self.refresh_cards_list)
        bar_actions.addWidget(self.search_tarjetas, stretch=3)

        bar_actions.addWidget(CaptionLabel("Estado:", tab_widget))
        self.combo_filtro_estado = ComboBox(tab_widget)
        self.combo_filtro_estado.addItems(["(Todos)", "Activa", "Bloqueada", "Reportada Perdida", "Cancelada", "Vencida"])
        self.combo_filtro_estado.currentTextChanged.connect(self.refresh_cards_list)
        bar_actions.addWidget(self.combo_filtro_estado, stretch=2)

        self.btn_emitir_tarjeta = PrimaryPushButton("Emitir Tarjeta", tab_widget, FIF.ADD)
        self.btn_emitir_tarjeta.clicked.connect(self.handle_emitir_tarjeta)
        bar_actions.addWidget(self.btn_emitir_tarjeta)

        self.btn_modificar_tarjeta = PushButton("Modificar Tarjeta", tab_widget, FIF.EDIT)
        self.btn_modificar_tarjeta.clicked.connect(self.handle_modificar_tarjeta)
        bar_actions.addWidget(self.btn_modificar_tarjeta)

        self.btn_bloquear_tarjeta = PushButton("Bloquear / Estado", tab_widget, FIF.SYNC)
        self.btn_bloquear_tarjeta.clicked.connect(self.handle_bloquear_tarjeta)
        bar_actions.addWidget(self.btn_bloquear_tarjeta)

        self.btn_eliminar_tarjeta = PushButton("Eliminar", tab_widget, FIF.DELETE)
        self.btn_eliminar_tarjeta.clicked.connect(self.handle_eliminar_tarjeta)
        bar_actions.addWidget(self.btn_eliminar_tarjeta)

        v_layout.addLayout(bar_actions)

        # Tabla de Tarjetas
        self.table_cards = TableWidget(tab_widget)
        self.table_cards.setBorderVisible(True)
        self.table_cards.setColumnCount(9)
        self.table_cards.setHorizontalHeaderLabels([
            "N° Tarjeta", "Titular / Pasajero", "Tipo Pasajero", "Tarifa",
            "Saldo Disponible", "Fecha Emisión", "Vencimiento", "Días Rest.", "Estado"
        ])
        hc = self.table_cards.horizontalHeader()
        if hc is not None:
            hc.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_cards.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_cards.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table_cards.itemSelectionChanged.connect(self.on_card_table_selected)
        v_layout.addWidget(self.table_cards, stretch=5)

        # Historiales Subordinados (Pestañas de la tarjeta seleccionada)
        card_sub_hist = CardWidget(tab_widget)
        sub_layout = QVBoxLayout(card_sub_hist)
        sub_layout.setContentsMargins(14, 10, 14, 10)
        sub_layout.setSpacing(6)

        self.sub_tabs_hist = SegmentedWidget(card_sub_hist)
        self.sub_tabs_hist.addItem("sub_viajes", "Historial de Pasos por Torniquete")
        self.sub_tabs_hist.addItem("sub_recargas", "Historial de Recargas Realizadas")
        self.sub_tabs_hist.setCurrentItem("sub_viajes")
        self.sub_tabs_hist.currentItemChanged.connect(self.on_sub_hist_tab_changed)
        sub_layout.addWidget(self.sub_tabs_hist)

        self.stack_sub_hist = QStackedWidget(card_sub_hist)

        # Tabla 1: Pasos por Torniquete
        self.table_viajes_tarjeta = TableWidget(self.stack_sub_hist)
        self.table_viajes_tarjeta.setBorderVisible(True)
        self.table_viajes_tarjeta.setColumnCount(6)
        self.table_viajes_tarjeta.setHorizontalHeaderLabels([
            "N° Transacción", "Estación Ingreso", "Estación Salida", "Fecha y Hora", "Monto Cobrado", "Estado"
        ])
        hv = self.table_viajes_tarjeta.horizontalHeader()
        if hv is not None:
            hv.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_viajes_tarjeta.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.stack_sub_hist.addWidget(self.table_viajes_tarjeta)

        # Tabla 2: Recargas
        self.table_recargas_tarjeta = TableWidget(self.stack_sub_hist)
        self.table_recargas_tarjeta.setBorderVisible(True)
        self.table_recargas_tarjeta.setColumnCount(7)
        self.table_recargas_tarjeta.setHorizontalHeaderLabels([
            "N° Transacción", "Monto", "Medio Pago", "Estación / Canal", "Saldo Ant.", "Saldo Post.", "Fecha y Hora"
        ])
        hr = self.table_recargas_tarjeta.horizontalHeader()
        if hr is not None:
            hr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_recargas_tarjeta.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.stack_sub_hist.addWidget(self.table_recargas_tarjeta)

        sub_layout.addWidget(self.stack_sub_hist)
        v_layout.addWidget(card_sub_hist, stretch=4)

        self.stack_views.addWidget(tab_widget)

    # ==========================================================================
    # PESTANA 3: PADRON DE PASAJEROS
    # ==========================================================================

    def init_tab_pasajeros(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(10)

        bar_actions = QHBoxLayout()
        bar_actions.setSpacing(8)

        self.search_pasajeros = SearchLineEdit(tab_widget)
        self.search_pasajeros.setPlaceholderText("Buscar por nombre, código, correo o teléfono...")
        self.search_pasajeros.textChanged.connect(self.refresh_pasajeros)
        bar_actions.addWidget(self.search_pasajeros, stretch=3)

        bar_actions.addWidget(CaptionLabel("Tipo:", tab_widget))
        self.combo_filtro_tipo_pas = ComboBox(tab_widget)
        self.combo_filtro_tipo_pas.addItems(["(Todos)", "Regular", "Estudiante", "Adulto Mayor", "Persona con Discapacidad", "Empleado Autorizado"])
        self.combo_filtro_tipo_pas.currentTextChanged.connect(self.refresh_pasajeros)
        bar_actions.addWidget(self.combo_filtro_tipo_pas, stretch=2)

        self.btn_nuevo_pas = PrimaryPushButton("Nuevo Pasajero", tab_widget, FIF.ADD)
        self.btn_nuevo_pas.clicked.connect(self.handle_nuevo_pasajero)
        bar_actions.addWidget(self.btn_nuevo_pas)

        self.btn_modificar_pas = PushButton("Modificar Pasajero", tab_widget, FIF.EDIT)
        self.btn_modificar_pas.clicked.connect(self.handle_modificar_pasajero)
        bar_actions.addWidget(self.btn_modificar_pas)

        self.btn_estado_pas = PushButton("Cambiar Estado", tab_widget, FIF.SYNC)
        self.btn_estado_pas.clicked.connect(self.handle_cambiar_estado_pasajero)
        bar_actions.addWidget(self.btn_estado_pas)

        self.btn_eliminar_pas = PushButton("Eliminar", tab_widget, FIF.DELETE)
        self.btn_eliminar_pas.clicked.connect(self.handle_eliminar_pasajero)
        bar_actions.addWidget(self.btn_eliminar_pas)

        v_layout.addLayout(bar_actions)

        # Tabla Maestra de Pasajeros
        self.table_pasajeros = TableWidget(tab_widget)
        self.table_pasajeros.setBorderVisible(True)
        self.table_pasajeros.setColumnCount(8)
        self.table_pasajeros.setHorizontalHeaderLabels([
            "Identificador", "Nombre Completo", "Categoría / Perfil", "Fecha Nac.",
            "Teléfono", "Correo Electrónico", "Total Tarjetas", "Estado"
        ])
        hp = self.table_pasajeros.horizontalHeader()
        if hp is not None:
            hp.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_pasajeros.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_pasajeros.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table_pasajeros.itemSelectionChanged.connect(self.on_pasajero_table_selected)
        v_layout.addWidget(self.table_pasajeros, stretch=5)

        # Panel de Tarjetas del Pasajero Seleccionado
        card_pas_tar = CardWidget(tab_widget)
        pas_tar_layout = QVBoxLayout(card_pas_tar)
        pas_tar_layout.setContentsMargins(14, 10, 14, 10)
        pas_tar_layout.setSpacing(6)

        self.lbl_pas_tar_title = StrongBodyLabel("Tarjetas OMNY Asociadas al Pasajero Seleccionado", card_pas_tar)
        pas_tar_layout.addWidget(self.lbl_pas_tar_title)

        self.table_pasajero_tarjetas = TableWidget(card_pas_tar)
        self.table_pasajero_tarjetas.setBorderVisible(True)
        self.table_pasajero_tarjetas.setColumnCount(5)
        self.table_pasajero_tarjetas.setHorizontalHeaderLabels([
            "N° Tarjeta", "Tarifa Asignada", "Saldo Disponible", "Vencimiento", "Estado"
        ])
        hpt = self.table_pasajero_tarjetas.horizontalHeader()
        if hpt is not None:
            hpt.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_pasajero_tarjetas.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        pas_tar_layout.addWidget(self.table_pasajero_tarjetas)

        v_layout.addWidget(card_pas_tar, stretch=3)
        self.stack_views.addWidget(tab_widget)

    # ==========================================================================
    # PESTANA 4: CATALOGO DE TARIFAS Y FARE CAPPING
    # ==========================================================================

    def init_tab_tarifas(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(12)

        # Banner Explicativo OMNY Fare Capping
        card_capping = CardWidget(tab_widget)
        cap_layout = QVBoxLayout(card_capping)
        cap_layout.setContentsMargins(16, 12, 16, 12)
        cap_layout.setSpacing(4)

        cap_title = StrongBodyLabel("Regla de Fare Capping Oficial MTA (OMNY)", card_capping)
        cap_desc = CaptionLabel(
            "La MTA aplica un tope tarifario automático semanal de 7 días: cada usuario paga $2.90 por viaje "
            "hasta alcanzar un máximo de $34.00 (12 viajes). A partir de la doceava validación, todos los viajes "
            "adicionales dentro del ciclo son 100% gratuitos para la misma tarjeta. Tarifas reducidas ($1.45) "
            "aplica tope de $17.00 semanal.", card_capping
        )
        cap_layout.addWidget(cap_title)
        cap_layout.addWidget(cap_desc)
        v_layout.addWidget(card_capping)

        # Barra de Acciones de Tarifas
        bar_actions = QHBoxLayout()
        bar_actions.addWidget(StrongBodyLabel("Catálogo Oficial de Tarifas MTA (TARIFA)", tab_widget))
        bar_actions.addStretch(1)

        self.btn_nueva_tarifa = PrimaryPushButton("Nueva Tarifa", tab_widget, FIF.ADD)
        self.btn_nueva_tarifa.clicked.connect(self.handle_nueva_tarifa)
        bar_actions.addWidget(self.btn_nueva_tarifa)

        self.btn_modificar_tarifa = PushButton("Modificar Tarifa", tab_widget, FIF.EDIT)
        self.btn_modificar_tarifa.clicked.connect(self.handle_modificar_tarifa)
        bar_actions.addWidget(self.btn_modificar_tarifa)

        self.btn_refresh_tarifas = PushButton("Actualizar", tab_widget, FIF.SYNC)
        self.btn_refresh_tarifas.clicked.connect(self.refresh_tarifas)
        bar_actions.addWidget(self.btn_refresh_tarifas)

        v_layout.addLayout(bar_actions)

        # Tabla de Tarifas
        self.table_tarifas = TableWidget(tab_widget)
        self.table_tarifas.setBorderVisible(True)
        self.table_tarifas.setColumnCount(7)
        self.table_tarifas.setHorizontalHeaderLabels([
            "Código", "Nombre de Tarifa", "Costo por Viaje", "Perfil Beneficiario",
            "Inicio Vigencia", "Fin Vigencia", "Estado"
        ])
        ht = self.table_tarifas.horizontalHeader()
        if ht is not None:
            ht.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_tarifas.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_tarifas.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        v_layout.addWidget(self.table_tarifas, stretch=1)

        self.stack_views.addWidget(tab_widget)

    # ==========================================================================
    # LOGICA DE SINCRONIZACION Y CARGA GENERAL
    # ==========================================================================

    def load_cards_data(self):
        """Carga y actualiza todos los datos del módulo de tarjetas y torniquetes."""
        try:
            self.refresh_estaciones_combo()
            self.refresh_cards_list()
            self.refresh_pasajeros()
            self.refresh_tarifas()
            self.refresh_kpis()
        except Exception as exc:
            print(f"Error al sincronizar datos del Módulo 5: {exc}")

    def refresh_kpis(self):
        kpis = m5_cards_service.get_kpis_omny()
        self.lbl_kpi_tarjetas.setText(f"Total Tarjetas: {kpis.get('total_tarjetas', 0)}")
        self.lbl_kpi_activas.setText(f"Tarjetas Activas: {kpis.get('tarjetas_activas', 0)}")
        self.lbl_kpi_saldo.setText(f"Saldo en Circulación: ${kpis.get('saldo_total_circulacion', 0.0):.2f}")
        self.lbl_kpi_viajes.setText(f"Viajes Hoy: {kpis.get('viajes_hoy', 0)}")
        self.lbl_kpi_recaudo.setText(f"Recaudación Hoy: ${kpis.get('recaudacion_hoy', 0.0):.2f}")

    def refresh_estaciones_combo(self):
        estaciones = m5_cards_service.get_estaciones_combo()
        self.combo_estaciones.clear()
        for est_id, label in estaciones:
            self.combo_estaciones.addItem(label, userData=est_id)

    # ==========================================================================
    # LOGICA PESTANA 1: TORNIQUETE Y RECARGA
    # ==========================================================================

    def handle_turnstile_tap(self):
        num_tarjeta = self.combo_tarjetas.currentData()
        if not num_tarjeta:
            InfoBar.warning(title="Selección Requerida", content="Seleccione una tarjeta para validar en el torniquete.", parent=self.window(), duration=3000)
            return

        est_id = self.combo_estaciones.currentData()
        if not est_id:
            InfoBar.warning(title="Estación Requerida", content="Seleccione la estación del torniquete.", parent=self.window(), duration=3000)
            return

        res = m5_cards_service.validar_ingreso_torniquete(str(num_tarjeta), int(est_id))
        if res.get("success"):
            InfoBar.success(
                title="Paso Autorizado",
                content=res.get("mensaje", "Paso validado correctamente."),
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
                duration=3500
            )
        else:
            InfoBar.error(
                title="Paso Rechazado",
                content=res.get("mensaje", "No se pudo validar el paso por torniquete."),
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
                duration=4500
            )

        self.refresh_cards_list()
        self.refresh_kpis()
        self.refresh_recent_taps()

    def handle_anonymous_tap(self):
        est_id = self.combo_estaciones.currentData()
        if not est_id:
            InfoBar.warning(title="Estación Requerida", content="Seleccione la estación del torniquete.", parent=self.window(), duration=3000)
            return

        res = m5_cards_service.registrar_viaje_anonimo(int(est_id))
        if res.get("success"):
            InfoBar.success(
                title="Paso Anónimo Contactless Autorizado",
                content=f"Viaje anónimo validado exitosamente. Tarifa cobrada: ${res.get('monto_cobrado', 2.90):.2f}.",
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
                duration=3500
            )
        else:
            InfoBar.error(title="Paso Anónimo Rechazado", content=res.get("mensaje", ""), parent=self.window(), duration=4500)

        self.refresh_cards_list()
        self.refresh_kpis()
        self.refresh_recent_taps()

    def handle_recharge(self):
        num_tarjeta = self.combo_tarjetas.currentData()
        if not num_tarjeta:
            InfoBar.warning(title="Selección Requerida", content="Seleccione la tarjeta que desea recargar.", parent=self.window(), duration=3000)
            return

        monto = self.spin_monto_rec.value()
        medio = self.combo_medio_pago.currentText()
        est_nombre = self.combo_estaciones.currentText().split(" - ")[-1]

        res = m5_cards_service.recargar_tarjeta(str(num_tarjeta), monto, medio, f"Torniquete {est_nombre}")
        if res.get("success"):
            InfoBar.success(
                title="Recarga Exitosa",
                content=res.get("mensaje", "Saldo abonado exitosamente."),
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
                duration=3500
            )
            self.refresh_cards_list()
            self.refresh_kpis()
        else:
            InfoBar.error(title="Error en Recarga", content=res.get("error", ""), parent=self.window(), duration=4000)

    def refresh_recent_taps(self):
        viajes = m5_cards_service.get_historial_viajes(limit=8)
        self.table_recent_taps.setRowCount(len(viajes))
        for r, row in enumerate(viajes):
            self.table_recent_taps.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("NUMERO_TRANSACCION"))))
            self.table_recent_taps.setItem(r, 1, QTableWidgetItem(_safe_str(row.get("NUMERO_TARJETA"))))
            self.table_recent_taps.setItem(r, 2, QTableWidgetItem(_safe_str(row.get("ESTACION_INGRESO"))))
            self.table_recent_taps.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("FECHA_HORA_INGRESO"))))
            self.table_recent_taps.setItem(r, 4, QTableWidgetItem(f"${_safe_float(row.get('MONTO_COBRADO')): .2f}"))

    # ==========================================================================
    # LOGICA PESTANA 2: DIRECTORIO DE TARJETAS
    # ==========================================================================

    def refresh_cards_list(self):
        prev_card = self.selected_card_num
        filtro_estado = self.combo_filtro_estado.currentText()
        st = self.search_tarjetas.text().strip()

        self.tarjetas_cache = m5_cards_service.get_tarjetas(
            estado_filter=filtro_estado if filtro_estado != "(Todos)" else None,
            search_text=st if st else None
        )

        # Llenar tabla de tarjetas
        self.table_cards.blockSignals(True)
        self.table_cards.setRowCount(len(self.tarjetas_cache))
        for r, row in enumerate(self.tarjetas_cache):
            num = _safe_str(row.get("NUMERO_TARJETA"))
            saldo = _safe_float(row.get("SALDO_DISPONIBLE"))
            dias = _safe_str(row.get("DIAS_RESTANTES"))

            self.table_cards.setItem(r, 0, QTableWidgetItem(num))
            self.table_cards.setItem(r, 1, QTableWidgetItem(_safe_str(row.get("PASAJERO"))))
            self.table_cards.setItem(r, 2, QTableWidgetItem(_safe_str(row.get("TIPO_PASAJERO"))))
            self.table_cards.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("TARIFA_NOMBRE"))))
            self.table_cards.setItem(r, 4, QTableWidgetItem(f"${saldo:.2f}"))
            self.table_cards.setItem(r, 5, QTableWidgetItem(_safe_str(row.get("FECHA_EMISION"))))
            self.table_cards.setItem(r, 6, QTableWidgetItem(_safe_str(row.get("FECHA_VENCIMIENTO"))))
            self.table_cards.setItem(r, 7, QTableWidgetItem(dias))
            self.table_cards.setItem(r, 8, QTableWidgetItem(_safe_str(row.get("ESTADO"))))

        self.table_cards.blockSignals(False)

        # Llenar combo de tarjetas de la pestaña 1
        self.combo_tarjetas.blockSignals(True)
        self.combo_tarjetas.clear()
        target_idx = 0
        all_cards = m5_cards_service.get_tarjetas()
        for i, t in enumerate(all_cards):
            c_num = _safe_str(t.get("NUMERO_TARJETA"))
            tit = _safe_str(t.get("PASAJERO"))
            sal = _safe_float(t.get("SALDO_DISPONIBLE"))
            est = _safe_str(t.get("ESTADO"))
            self.combo_tarjetas.addItem(f"{c_num} - {tit} (${sal:.2f}) [{est}]", userData=c_num)
            if c_num == prev_card:
                target_idx = i
        self.combo_tarjetas.setCurrentIndex(target_idx)
        self.combo_tarjetas.blockSignals(False)

        # Actualizar visual card
        if all_cards:
            active_num = self.combo_tarjetas.currentData() or all_cards[0].get("NUMERO_TARJETA")
            if active_num:
                self.set_active_card(str(active_num))

        self.refresh_recent_taps()

    def on_card_combo_selected(self, index: int):
        card_num = self.combo_tarjetas.currentData()
        if card_num:
            self.set_active_card(str(card_num))

    def on_card_table_selected(self):
        selected = self.table_cards.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        item_num = self.table_cards.item(row, 0)
        if item_num:
            self.set_active_card(item_num.text())

    def set_active_card(self, numero_tarjeta: str):
        self.selected_card_num = numero_tarjeta
        card = m5_cards_service.get_tarjeta_by_numero(numero_tarjeta)
        if not card:
            return

        self.visual_card.set_card_data(
            numero=card.get("NUMERO_TARJETA", "-"),
            titular=card.get("PASAJERO", "Anónima"),
            tarifa=card.get("TARIFA_NOMBRE", "Tarifa Base"),
            saldo=_safe_float(card.get("SALDO_DISPONIBLE")),
            estado=card.get("ESTADO", "Activa")
        )

        self.load_card_sub_histories(numero_tarjeta)

    def on_sub_hist_tab_changed(self, key: str):
        if key == "sub_viajes":
            self.stack_sub_hist.setCurrentIndex(0)
        else:
            self.stack_sub_hist.setCurrentIndex(1)
        if self.selected_card_num:
            self.load_card_sub_histories(self.selected_card_num)

    def load_card_sub_histories(self, numero_tarjeta: str):
        # 1. Viajes
        viajes = m5_cards_service.get_historial_viajes(numero_tarjeta=numero_tarjeta)
        self.table_viajes_tarjeta.setRowCount(len(viajes))
        for r, row in enumerate(viajes):
            self.table_viajes_tarjeta.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("NUMERO_TRANSACCION"))))
            self.table_viajes_tarjeta.setItem(r, 1, QTableWidgetItem(_safe_str(row.get("ESTACION_INGRESO"))))
            self.table_viajes_tarjeta.setItem(r, 2, QTableWidgetItem(_safe_str(row.get("ESTACION_SALIDA"))))
            self.table_viajes_tarjeta.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("FECHA_HORA_INGRESO"))))
            self.table_viajes_tarjeta.setItem(r, 4, QTableWidgetItem(f"${_safe_float(row.get('MONTO_COBRADO')):.2f}"))
            self.table_viajes_tarjeta.setItem(r, 5, QTableWidgetItem(_safe_str(row.get("ESTADO_TRANSACCION"))))

        # 2. Recargas
        recargas = m5_cards_service.get_historial_recargas(numero_tarjeta=numero_tarjeta)
        self.table_recargas_tarjeta.setRowCount(len(recargas))
        for r, row in enumerate(recargas):
            self.table_recargas_tarjeta.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("NUMERO_TRANSACCION"))))
            self.table_recargas_tarjeta.setItem(r, 1, QTableWidgetItem(f"${_safe_float(row.get('MONTO')):.2f}"))
            self.table_recargas_tarjeta.setItem(r, 2, QTableWidgetItem(_safe_str(row.get("MEDIO_PAGO"))))
            self.table_recargas_tarjeta.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("ESTACION_CANAL"))))
            self.table_recargas_tarjeta.setItem(r, 4, QTableWidgetItem(f"${_safe_float(row.get('SALDO_ANTERIOR')):.2f}"))
            self.table_recargas_tarjeta.setItem(r, 5, QTableWidgetItem(f"${_safe_float(row.get('SALDO_POSTERIOR')):.2f}"))
            self.table_recargas_tarjeta.setItem(r, 6, QTableWidgetItem(_safe_str(row.get("FECHA_HORA"))))

    def handle_emitir_tarjeta(self):
        pasajeros = m5_cards_service.get_pasajeros()
        dlg = EmitirTarjetaDialog(parent=self.window(), pasajeros_list=pasajeros)
        if dlg.exec():
            datos = dlg.get_data()
            res = m5_cards_service.emitir_tarjeta(datos)
            if res.get("success"):
                InfoBar.success(
                    title="Tarjeta Emitida",
                    content=f"Tarjeta {res.get('numero_tarjeta')} emitida exitosamente.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.refresh_cards_list()
                self.refresh_kpis()
            else:
                InfoBar.error(title="Error al Emitir", content=res.get("error", ""), parent=self.window(), duration=4000)

    def handle_modificar_tarjeta(self):
        selected = self.table_cards.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione una tarjeta de la tabla.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item_num = self.table_cards.item(row, 0)
        if not item_num:
            return
        num = item_num.text()
        card = m5_cards_service.get_tarjeta_by_numero(num)
        if not card:
            return

        c_id = _safe_int(card.get("ID_TARJETA", 0))
        pasajeros = m5_cards_service.get_pasajeros()
        dlg = EmitirTarjetaDialog(parent=self.window(), pasajeros_list=pasajeros)
        dlg.titleLabel.setText(f"Modificar Tarjeta: {num}")
        dlg.txt_numero.setText(num)
        dlg.txt_numero.setEnabled(False)
        dlg.spin_saldo.setValue(_safe_float(card.get("SALDO_DISPONIBLE")))
        dlg.spin_saldo.setEnabled(False)
        dlg.txt_fvenc.setText(_safe_str(card.get("FECHA_VENCIMIENTO", "")))
        dlg.yesButton.setText("Guardar Cambios")

        if dlg.exec():
            datos = dlg.get_data()
            res = m5_cards_service.modificar_tarjeta(c_id, datos)
            if res.get("success"):
                InfoBar.success(title="Tarjeta Actualizada", content="Datos actualizados.", parent=self.window(), duration=3000)
                self.refresh_cards_list()
            else:
                InfoBar.error(title="Error al Modificar", content=res.get("error", ""), parent=self.window(), duration=4000)

    def handle_bloquear_tarjeta(self):
        selected = self.table_cards.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione una tarjeta de la tabla.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item_num = self.table_cards.item(row, 0)
        item_est = self.table_cards.item(row, 8)
        if not item_num:
            return
        num = item_num.text()
        est_actual = item_est.text() if item_est else "Activa"

        card = m5_cards_service.get_tarjeta_by_numero(num)
        if not card:
            return

        c_id = _safe_int(card.get("ID_TARJETA", 0))
        dlg = BloquearTarjetaDialog(num, est_actual, parent=self.window())
        if dlg.exec():
            nuevo_est = dlg.get_nuevo_estado()
            res = m5_cards_service.cambiar_estado_tarjeta(c_id, nuevo_est)
            if res.get("success"):
                InfoBar.success(
                    title="Estado Actualizado",
                    content=f"La tarjeta {num} cambió a estado '{nuevo_est}'.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.refresh_cards_list()
                self.refresh_kpis()
            else:
                InfoBar.error(title="Error de Estado", content=res.get("error", ""), parent=self.window(), duration=4000)

    def handle_eliminar_tarjeta(self):
        selected = self.table_cards.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione una tarjeta para eliminar.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item_num = self.table_cards.item(row, 0)
        if not item_num:
            return
        num = item_num.text()
        card = m5_cards_service.get_tarjeta_by_numero(num)
        if not card:
            return

        c_id = _safe_int(card.get("ID_TARJETA", 0))
        box = MessageBox("Confirmar Eliminación", f"¿Está seguro de que desea eliminar la tarjeta {num}?", self.window())
        if box.exec():
            res = m5_cards_service.eliminar_tarjeta(c_id)
            if res.get("success"):
                InfoBar.success(title="Tarjeta Eliminada", content=f"Tarjeta {num} eliminada.", parent=self.window(), duration=3000)
                self.refresh_cards_list()
                self.refresh_kpis()
            else:
                InfoBar.error(title="Error al Eliminar", content=res.get("error", ""), parent=self.window(), duration=4000)

    # ==========================================================================
    # LOGICA PESTANA 3: PADRON DE PASAJEROS
    # ==========================================================================

    def refresh_pasajeros(self):
        tipo = self.combo_filtro_tipo_pas.currentText()
        st = self.search_pasajeros.text().strip()

        self.pasajeros_cache = m5_cards_service.get_pasajeros(
            tipo_filter=tipo if tipo != "(Todos)" else None,
            search_text=st if st else None
        )

        self.table_pasajeros.blockSignals(True)
        self.table_pasajeros.setRowCount(len(self.pasajeros_cache))
        for r, row in enumerate(self.pasajeros_cache):
            self.table_pasajeros.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("IDENTIFICADOR"))))
            self.table_pasajeros.setItem(r, 1, QTableWidgetItem(_safe_str(row.get("NOMBRE"))))
            self.table_pasajeros.setItem(r, 2, QTableWidgetItem(_safe_str(row.get("TIPO_PASAJERO"))))
            self.table_pasajeros.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("FECHA_NACIMIENTO"))))
            self.table_pasajeros.setItem(r, 4, QTableWidgetItem(_safe_str(row.get("TELEFONO"))))
            self.table_pasajeros.setItem(r, 5, QTableWidgetItem(_safe_str(row.get("CORREO_ELECTRONICO"))))
            self.table_pasajeros.setItem(r, 6, QTableWidgetItem(_safe_str(row.get("TOTAL_TARJETAS"))))
            self.table_pasajeros.setItem(r, 7, QTableWidgetItem(_safe_str(row.get("ESTADO"))))

        self.table_pasajeros.blockSignals(False)

    def on_pasajero_table_selected(self):
        selected = self.table_pasajeros.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        item_ident = self.table_pasajeros.item(row, 0)
        if not item_ident:
            return

        ident = item_ident.text()
        pas = next((p for p in self.pasajeros_cache if p.get("IDENTIFICADOR") == ident), None)
        if not pas:
            return

        p_id = _safe_int(pas.get("ID_PASAJERO", 0))
        self.selected_pasajero_id = p_id
        self.lbl_pas_tar_title.setText(f"Tarjetas OMNY Asociadas a {pas.get('NOMBRE', '')}")

        tarjetas = m5_cards_service.get_tarjetas(pasajero_id=p_id)
        self.table_pasajero_tarjetas.setRowCount(len(tarjetas))
        for r, row in enumerate(tarjetas):
            self.table_pasajero_tarjetas.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("NUMERO_TARJETA"))))
            self.table_pasajero_tarjetas.setItem(r, 1, QTableWidgetItem(_safe_str(row.get("TARIFA_NOMBRE"))))
            self.table_pasajero_tarjetas.setItem(r, 2, QTableWidgetItem(f"${_safe_float(row.get('SALDO_DISPONIBLE')):.2f}"))
            self.table_pasajero_tarjetas.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("FECHA_VENCIMIENTO"))))
            self.table_pasajero_tarjetas.setItem(r, 4, QTableWidgetItem(_safe_str(row.get("ESTADO"))))

    def handle_nuevo_pasajero(self):
        dlg = PasajeroDialog(parent=self.window())
        if dlg.exec():
            datos = dlg.get_data()
            res = m5_cards_service.crear_pasajero(datos)
            if res.get("success"):
                InfoBar.success(
                    title="Pasajero Registrado",
                    content=f"Pasajero {datos['nombre']} ({res.get('identificador')}) registrado exitosamente.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.refresh_pasajeros()
                self.refresh_kpis()
            else:
                InfoBar.error(title="Error al Registrar", content=res.get("error", ""), parent=self.window(), duration=4000)

    def handle_modificar_pasajero(self):
        selected = self.table_pasajeros.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un pasajero de la tabla.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item_id = self.table_pasajeros.item(row, 0)
        if not item_id:
            return
        ident = item_id.text()
        pas = next((p for p in self.pasajeros_cache if p.get("IDENTIFICADOR") == ident), None)
        if not pas:
            return

        p_id = _safe_int(pas.get("ID_PASAJERO", 0))
        dlg = PasajeroDialog(parent=self.window(), pas_data=pas)
        if dlg.exec():
            datos = dlg.get_data()
            res = m5_cards_service.modificar_pasajero(p_id, datos)
            if res.get("success"):
                InfoBar.success(title="Pasajero Actualizado", content="Datos guardados correctamente.", parent=self.window(), duration=3000)
                self.refresh_pasajeros()
            else:
                InfoBar.error(title="Error al Modificar", content=res.get("error", ""), parent=self.window(), duration=4000)

    def handle_cambiar_estado_pasajero(self):
        selected = self.table_pasajeros.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un pasajero de la tabla.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item_id = self.table_pasajeros.item(row, 0)
        item_est = self.table_pasajeros.item(row, 7)
        if not item_id:
            return
        ident = item_id.text()
        est_actual = item_est.text() if item_est else "Activo"
        nuevo_est = "Inactivo" if est_actual == "Activo" else "Activo"

        pas = next((p for p in self.pasajeros_cache if p.get("IDENTIFICADOR") == ident), None)
        if not pas:
            return

        p_id = _safe_int(pas.get("ID_PASAJERO", 0))
        res = m5_cards_service.cambiar_estado_pasajero(p_id, nuevo_est)
        if res.get("success"):
            InfoBar.success(title="Estado Actualizado", content=f"Estado de {ident} cambiado a '{nuevo_est}'.", parent=self.window(), duration=3000)
            self.refresh_pasajeros()
        else:
            InfoBar.error(title="Error de Estado", content=res.get("error", ""), parent=self.window(), duration=4000)

    def handle_eliminar_pasajero(self):
        selected = self.table_pasajeros.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un pasajero para eliminar.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item_id = self.table_pasajeros.item(row, 0)
        item_nom = self.table_pasajeros.item(row, 1)
        if not item_id:
            return
        ident = item_id.text()
        nom = item_nom.text() if item_nom else ident

        pas = next((p for p in self.pasajeros_cache if p.get("IDENTIFICADOR") == ident), None)
        if not pas:
            return

        p_id = _safe_int(pas.get("ID_PASAJERO", 0))
        box = MessageBox("Confirmar Eliminación", f"¿Está seguro de que desea eliminar al pasajero {nom} ({ident})?", self.window())
        if box.exec():
            res = m5_cards_service.eliminar_pasajero(p_id)
            if res.get("success"):
                InfoBar.success(title="Pasajero Eliminado", content=f"Pasajero {ident} eliminado.", parent=self.window(), duration=3000)
                self.refresh_pasajeros()
                self.refresh_kpis()
            else:
                InfoBar.error(title="Error al Eliminar", content=res.get("error", ""), parent=self.window(), duration=4000)

    # ==========================================================================
    # LOGICA PESTANA 4: CATALOGO DE TARIFAS
    # ==========================================================================

    def refresh_tarifas(self):
        tarifas = m5_cards_service.get_tarifas()
        self.table_tarifas.setRowCount(len(tarifas))
        for r, row in enumerate(tarifas):
            self.table_tarifas.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("CODIGO"))))
            self.table_tarifas.setItem(r, 1, QTableWidgetItem(_safe_str(row.get("NOMBRE"))))
            self.table_tarifas.setItem(r, 2, QTableWidgetItem(f"${_safe_float(row.get('MONTO')):.2f}"))
            self.table_tarifas.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("TIPO_PASAJERO"))))
            self.table_tarifas.setItem(r, 4, QTableWidgetItem(_safe_str(row.get("FECHA_INICIO"))))
            self.table_tarifas.setItem(r, 5, QTableWidgetItem(_safe_str(row.get("FECHA_FIN"))))
            self.table_tarifas.setItem(r, 6, QTableWidgetItem(_safe_str(row.get("ESTADO"))))

    def handle_nueva_tarifa(self):
        dlg = TarifaDialog(parent=self.window())
        if dlg.exec():
            datos = dlg.get_data()
            res = m5_cards_service.crear_tarifa(datos)
            if res.get("success"):
                InfoBar.success(title="Tarifa Creada", content=f"Tarifa {datos['nombre']} registrada.", parent=self.window(), duration=3000)
                self.refresh_tarifas()
            else:
                InfoBar.error(title="Error al Crear", content=res.get("error", ""), parent=self.window(), duration=4000)

    def handle_modificar_tarifa(self):
        selected = self.table_tarifas.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione una tarifa de la tabla.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item_cod = self.table_tarifas.item(row, 0)
        if not item_cod:
            return
        cod = item_cod.text()
        tarifas = m5_cards_service.get_tarifas()
        tar = next((t for t in tarifas if t.get("CODIGO") == cod), None)
        if not tar:
            return

        t_id = _safe_int(tar.get("ID_TARIFA", 0))
        dlg = TarifaDialog(parent=self.window(), tarifa_data=tar)
        if dlg.exec():
            datos = dlg.get_data()
            res = m5_cards_service.modificar_tarifa(t_id, datos)
            if res.get("success"):
                InfoBar.success(title="Tarifa Actualizada", content="Datos de tarifa guardados.", parent=self.window(), duration=3000)
                self.refresh_tarifas()
            else:
                InfoBar.error(title="Error al Modificar", content=res.get("error", ""), parent=self.window(), duration=4000)
