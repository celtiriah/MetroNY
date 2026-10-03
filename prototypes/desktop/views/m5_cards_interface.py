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
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QHeaderView, QFormLayout, QTableWidgetItem, QGridLayout,
    QSizePolicy
)

from qfluentwidgets import (
    TitleLabel, SubtitleLabel, CaptionLabel, BodyLabel, StrongBodyLabel,
    CardWidget, ComboBox, LineEdit, SearchLineEdit, DoubleSpinBox, SpinBox,
    PrimaryPushButton, PushButton, TableWidget, InfoBar, InfoBarPosition,
    SegmentedWidget, CheckBox, MessageBoxBase, MessageBox, IconWidget,
    SingleDirectionScrollArea, FluentIcon as FIF, CalendarPicker
)

from services import m5_cards_service
from views.components import (
    StatusBadge, LineColorChip, configure_interactive_table, auto_fit_table_columns,
    to_qdate, qdate_to_iso, create_calendar_picker
)


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
    Representación visual estilizada del medio de acceso al sistema:
    - Tarjeta OMNY: Gradiente oficial MTA Navy Blue, tipografía blanca y contactless indicator.
    - Boleto de Uso Único: Formato ticket MTA Single-Ride con banda magnética superior y cuerpo ámbar/dorado.
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(380, 205)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)

        # Fila superior: Logo MTA y OMNY Contactless o Tipo de Medio
        top_layout = QHBoxLayout()
        self.lbl_logo = CaptionLabel("MTA NYCT • SUBWAY", self)
        self.lbl_logo.setStyleSheet("color: rgba(255, 255, 255, 0.85); font-weight: bold;")

        self.lbl_tech = CaptionLabel("(((•))) OMNY", self)
        self.lbl_tech.setStyleSheet("color: #FFCC00; font-weight: bold; font-size: 13px;")

        top_layout.addWidget(self.lbl_logo)
        top_layout.addStretch(1)
        top_layout.addWidget(self.lbl_tech)
        layout.addLayout(top_layout)

        layout.addStretch(1)

        # Número de tarjeta o identificador de boleto
        self.lbl_card_num = TitleLabel("OMNY-0000-0000", self)
        self.lbl_card_num.setStyleSheet("color: #FFFFFF; font-family: 'Consolas', monospace; font-size: 18px; font-weight: bold;")
        layout.addWidget(self.lbl_card_num)

        # Fila inferior: Titular, Tarifa y Saldo / Estado
        bottom_layout = QHBoxLayout()

        col_info = QVBoxLayout()
        col_info.setSpacing(2)
        self.lbl_titular = BodyLabel("Cargando titular...", self)
        self.lbl_titular.setStyleSheet("color: #FFFFFF; font-weight: 600; font-size: 13px;")
        self.lbl_tarifa = CaptionLabel("Tarifa OMNY Asignada", self)
        self.lbl_tarifa.setStyleSheet("color: rgba(255, 255, 255, 0.75); font-size: 11px;")
        col_info.addWidget(self.lbl_titular)
        col_info.addWidget(self.lbl_tarifa)

        bottom_layout.addLayout(col_info)
        bottom_layout.addStretch(1)

        col_saldo = QVBoxLayout()
        col_saldo.setSpacing(2)
        col_saldo.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_saldo_tag = CaptionLabel("SALDO DISPONIBLE", self)
        self.lbl_saldo_tag.setStyleSheet("color: rgba(255, 255, 255, 0.75); font-size: 9px; font-weight: bold;")
        self.lbl_saldo = TitleLabel("$0.00", self)
        self.lbl_saldo.setStyleSheet("color: #00E676; font-size: 20px; font-weight: bold;")
        col_saldo.addWidget(self.lbl_saldo_tag, alignment=Qt.AlignmentFlag.AlignRight)
        col_saldo.addWidget(self.lbl_saldo, alignment=Qt.AlignmentFlag.AlignRight)

        bottom_layout.addLayout(col_saldo)
        layout.addLayout(bottom_layout)

        # Aplicar estilo inicial de Tarjeta OMNY
        self._apply_card_style()

    def _apply_card_style(self):
        self.setStyleSheet("""
            VisualOmnyCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0039A6, stop:1 #001B4D);
                border-radius: 14px;
                border: 1px solid rgba(255, 255, 255, 0.25);
            }
        """)

    def _apply_ticket_style(self):
        self.setStyleSheet("""
            VisualOmnyCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1F2023, stop:0.25 #1F2023, stop:0.251 #F5A623, stop:1 #D48806);
                border-radius: 12px;
                border: 2px dashed rgba(255, 255, 255, 0.45);
            }
        """)

    def set_card_data(self, numero: str, titular: str, tarifa: str, saldo: float, estado: str, is_boleto: bool = False):
        if is_boleto:
            self._apply_ticket_style()
            self.lbl_logo.setText("MTA NYCT • SINGLE-RIDE TICKET")
            self.lbl_logo.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px;")

            self.lbl_tech.setText("[ 1 SOLO USO ]")
            self.lbl_tech.setStyleSheet("color: #FFD54F; font-weight: bold; font-size: 11px;")

            self.lbl_card_num.setText(numero)
            self.lbl_card_num.setStyleSheet("color: #111111; font-family: 'Consolas', monospace; font-size: 18px; font-weight: bold;")

            tit_text = titular if titular and titular != "Anónima" else "Al Portador (Sin Titular)"
            self.lbl_titular.setText(tit_text)
            self.lbl_titular.setStyleSheet("color: #222222; font-weight: bold; font-size: 13px;")

            self.lbl_tarifa.setText(f"{tarifa} • No Recargable")
            self.lbl_tarifa.setStyleSheet("color: #333333; font-size: 11px; font-weight: 600;")

            self.lbl_saldo_tag.setText("ESTADO DEL BOLETO")
            self.lbl_saldo_tag.setStyleSheet("color: #333333; font-size: 9px; font-weight: bold;")

            if estado == "Activa":
                self.lbl_saldo.setText("1 USO ($2.90)")
                self.lbl_saldo.setStyleSheet("color: #006622; font-size: 16px; font-weight: bold;")
            elif estado in ("Emisión Inmediata", "Nuevo"):
                self.lbl_saldo.setText("EMISIÓN ($2.90)")
                self.lbl_saldo.setStyleSheet("color: #004D40; font-size: 15px; font-weight: bold;")
            elif estado == "Usado":
                self.lbl_saldo.setText("USADO (0 USOS)")
                self.lbl_saldo.setStyleSheet("color: #B71C1C; font-size: 14px; font-weight: bold;")
            else:
                self.lbl_saldo.setText(f"{estado.upper()} (0 USOS)")
                self.lbl_saldo.setStyleSheet("color: #B71C1C; font-size: 14px; font-weight: bold;")
        else:
            self._apply_card_style()
            self.lbl_logo.setText("MTA NYCT • SUBWAY")
            self.lbl_logo.setStyleSheet("color: rgba(255, 255, 255, 0.85); font-weight: bold;")

            if numero.startswith("MC-"):
                self.lbl_tech.setText("MetroCard")
            else:
                self.lbl_tech.setText("(((•))) OMNY")
            self.lbl_tech.setStyleSheet("color: #FFCC00; font-weight: bold; font-size: 13px;")

            self.lbl_card_num.setText(numero)
            self.lbl_card_num.setStyleSheet("color: #FFFFFF; font-family: 'Consolas', monospace; font-size: 18px; font-weight: bold;")

            self.lbl_titular.setText(titular)
            self.lbl_titular.setStyleSheet("color: #FFFFFF; font-weight: 600; font-size: 13px;")

            self.lbl_tarifa.setText(f"{tarifa} [{estado}]")
            self.lbl_tarifa.setStyleSheet("color: rgba(255, 255, 255, 0.75); font-size: 11px;")

            self.lbl_saldo_tag.setText("SALDO DISPONIBLE")
            self.lbl_saldo_tag.setStyleSheet("color: rgba(255, 255, 255, 0.75); font-size: 9px; font-weight: bold;")

            self.lbl_saldo.setText(f"${saldo:.2f}")
            if estado == "Activa":
                self.lbl_saldo.setStyleSheet("color: #00E676; font-size: 20px; font-weight: bold;")
            elif estado in ("Bloqueada", "Cancelada", "Reportada Perdida", "Usado"):
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
        fnac_val = self.pas_data.get("FECHA_NACIMIENTO") if self.es_edicion and self.pas_data else None
        self.picker_fnac = create_calendar_picker(self, initial_date=fnac_val, allow_reset=True)
        form.addRow("Fecha Nacimiento:", self.picker_fnac)

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

        # Label de validación
        self.lbl_error = CaptionLabel("", self)
        self.lbl_error.setStyleSheet("color: #FF5252; font-weight: bold;")
        self.lbl_error.hide()
        form.addRow("", self.lbl_error)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Guardar Cambios" if self.es_edicion else "Registrar Pasajero")
        self.cancelButton.setText("Cancelar")

        self.yesButton.clicked.disconnect()
        self.yesButton.clicked.connect(self._on_confirm)

    def validate(self) -> bool:
        nom = self.txt_nombre.text().strip()
        if not nom or len(nom) < 3:
            self.lbl_error.setText("El nombre del pasajero es obligatorio (mínimo 3 caracteres).")
            self.lbl_error.show()
            self.txt_nombre.setFocus()
            return False

        q_nac = self.picker_fnac.getDate()
        if q_nac.isValid():
            hoy = date.today()
            if (q_nac.year(), q_nac.month(), q_nac.day()) > (hoy.year, hoy.month, hoy.day):
                self.lbl_error.setText("La fecha de nacimiento no puede ser futura.")
                self.lbl_error.show()
                self.picker_fnac.setFocus()
                return False

        correo = self.txt_correo.text().strip()
        if correo and ("@" not in correo or "." not in correo):
            self.lbl_error.setText("Formato de correo electrónico inválido.")
            self.lbl_error.show()
            self.txt_correo.setFocus()
            return False

        self.lbl_error.hide()
        return True

    def _on_confirm(self):
        if self.validate():
            self.accept()

    def get_data(self) -> Dict[str, Any]:
        return {
            "nombre": self.txt_nombre.text().strip(),
            "identificador": self.txt_ident.text().strip(),
            "tipo_pasajero": self.combo_tipo.currentText(),
            "fecha_nacimiento": qdate_to_iso(self.picker_fnac.getDate()),
            "telefono": self.txt_tel.text().strip() or None,
            "correo_electronico": self.txt_correo.text().strip() or None,
            "estado": self.combo_estado.currentText()
        }


class EmitirTarjetaDialog(MessageBoxBase):
    """Diálogo modal para emitir una nueva tarjeta OMNY (nominal o anónima) o un boleto de uso único."""
    def __init__(self, parent=None, pasajeros_list: Optional[List[Dict[str, Any]]] = None):
        super().__init__(parent)
        self.pasajeros_list = pasajeros_list or []

        self.titleLabel = SubtitleLabel("Emitir Medio de Acceso OMNY", self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        # 0. Tipo de Soporte
        self.combo_tipo_soporte = ComboBox(self)
        self.combo_tipo_soporte.addItem("Tarjeta OMNY / MetroCard", userData="Tarjeta")
        self.combo_tipo_soporte.addItem("Boleto de Uso Único (Single-Ride)", userData="Boleto")
        self.combo_tipo_soporte.currentIndexChanged.connect(self._on_soporte_changed)
        form.addRow("Tipo de Soporte:", self.combo_tipo_soporte)

        # 1. Número de Tarjeta (Opcional)
        self.txt_numero = LineEdit(self)
        self.txt_numero.setPlaceholderText("p.ej. OMNY-1001-0050 (Autogenerado si vacío)")
        form.addRow("N° Identificador:", self.txt_numero)

        # 2. Pasajero Titular (Opcional - Regla 13: puede ser anónima)
        self.combo_pasajero = ComboBox(self)
        self.combo_pasajero.addItem("(Tarjeta Anónima / Al Portador)", userData=None)
        for p in self.pasajeros_list:
            p_id = _safe_int(p.get("ID_PASAJERO", 0))
            nom = p.get("NOMBRE", "")
            tipo = p.get("TIPO_PASAJERO", "Regular")
            self.combo_pasajero.addItem(f"{nom} ({tipo})", userData=p_id)
        self.combo_pasajero.currentIndexChanged.connect(self._on_pasajero_changed)
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
        # 5. Fecha de Vencimiento
        default_venc = date.today().replace(year=date.today().year + 5)
        self.picker_fvenc = create_calendar_picker(self, initial_date=default_venc, allow_reset=False)
        form.addRow("Vencimiento:", self.picker_fvenc)

        # Label de validación
        self.lbl_error = CaptionLabel("", self)
        self.lbl_error.setStyleSheet("color: #FF5252; font-weight: bold;")
        self.lbl_error.hide()
        form.addRow("", self.lbl_error)

        self._update_placeholder_numero()

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Emitir")
        self.cancelButton.setText("Cancelar")

        self.yesButton.clicked.disconnect()
        self.yesButton.clicked.connect(self._on_confirm)

    def set_fecha_vencimiento(self, val: Any):
        qd = to_qdate(val)
        if qd is not None:
            self.picker_fvenc.setDate(qd)

    def _update_placeholder_numero(self):
        soporte = self.combo_tipo_soporte.currentData()
        if soporte == "Boleto":
            self.txt_numero.setPlaceholderText("p.ej. BOL-2026-XXXX (Autogenerado si vacío)")
        elif self.combo_pasajero.currentData() is None:
            self.txt_numero.setPlaceholderText("p.ej. MC-ANON-2026-XXXX (Autogenerado si vacío)")
        else:
            self.txt_numero.setPlaceholderText("p.ej. OMNY-2026-XXXX (Autogenerado si vacío)")

    def _on_pasajero_changed(self, index: int):
        self._update_placeholder_numero()

    def _on_soporte_changed(self, index: int):
        soporte = self.combo_tipo_soporte.currentData()
        if soporte == "Boleto":
            self.combo_pasajero.setCurrentIndex(0)
            self.combo_pasajero.setEnabled(False)

            # Para boletos la tarifa es fija ($2.90) y no es aplicable seleccionar tipo de tarifa
            self.combo_tarifa.setEnabled(False)
            self.combo_tarifa.setToolTip("Los boletos de uso único tienen tarifa fija ($2.90) y no admiten otras tarifas ni descuentos.")
            for i in range(self.combo_tarifa.count()):
                text = self.combo_tarifa.itemText(i)
                if "2.90" in text and ("Base" in text or "Regular" in text):
                    self.combo_tarifa.setCurrentIndex(i)
                    break

            self.spin_saldo.setValue(2.90)
            self.spin_saldo.setEnabled(False)
            venc_boleto = date.today() + timedelta(days=1)
            qd = to_qdate(venc_boleto)
            if qd is not None:
                self.picker_fvenc.setDate(qd)
        else:
            self.combo_pasajero.setEnabled(True)
            self.combo_tarifa.setEnabled(True)
            self.combo_tarifa.setToolTip("")
            self.spin_saldo.setEnabled(True)
            self.spin_saldo.setValue(10.00)
            default_venc = date.today().replace(year=date.today().year + 5)
            qd = to_qdate(default_venc)
            if qd is not None:
                self.picker_fvenc.setDate(qd)

        self._update_placeholder_numero()

    def validate(self) -> bool:
        if self.spin_saldo.value() < 0:
            self.lbl_error.setText("El saldo inicial no puede ser negativo.")
            self.lbl_error.show()
            return False

        q_venc = self.picker_fvenc.getDate()
        if not q_venc.isValid():
            self.lbl_error.setText("La fecha de vencimiento es obligatoria.")
            self.lbl_error.show()
            self.picker_fvenc.setFocus()
            return False

        hoy = date.today()
        if (q_venc.year(), q_venc.month(), q_venc.day()) < (hoy.year, hoy.month, hoy.day):
            self.lbl_error.setText("La fecha de vencimiento no puede ser anterior a hoy.")
            self.lbl_error.show()
            self.picker_fvenc.setFocus()
            return False

        # Validación estricta del prefijo si se ingresa número manualmente
        if self.txt_numero.isEnabled():
            num = self.txt_numero.text().strip().upper()
            soporte = self.combo_tipo_soporte.currentData()
            pasajero = self.combo_pasajero.currentData()

            if num:
                if soporte == "Boleto":
                    if not num.startswith("BOL-"):
                        self.lbl_error.setText("Los boletos de uso único deben comenzar con el prefijo BOL- (p.ej. BOL-2026-0001).")
                        self.lbl_error.show()
                        self.txt_numero.setFocus()
                        return False
                elif pasajero is None:
                    # Al Portador: no debe usar el prefijo de tarjetas registradas OMNY
                    if num.startswith("OMNY-") and not num.startswith("OMNY-ANON-"):
                        self.lbl_error.setText(
                            "Las tarjetas al portador no pueden usar el prefijo de tarjetas registradas (OMNY-). "
                            "Use el prefijo MC-ANON- (p.ej. MC-ANON-2026-0001) o déjelo vacío para autogenerar."
                        )
                        self.lbl_error.show()
                        self.txt_numero.setFocus()
                        return False
                    valid_bearer = (
                        num.startswith("MC-ANON-") or
                        num.startswith("MC-") or
                        num.startswith("ANON-") or
                        num.startswith("OMNY-ANON-")
                    )
                    if not valid_bearer:
                        self.lbl_error.setText(
                            "Las tarjetas al portador deben tener el prefijo MC-ANON- (p.ej. MC-ANON-2026-0001)."
                        )
                        self.lbl_error.show()
                        self.txt_numero.setFocus()
                        return False
                else:
                    # Tarjeta Registrada con pasajero asignado
                    if num.startswith("BOL-") or num.startswith("MC-ANON-") or num.startswith("ANON-"):
                        self.lbl_error.setText(
                            "Las tarjetas registradas deben comenzar con el prefijo OMNY- (p.ej. OMNY-2026-0001)."
                        )
                        self.lbl_error.show()
                        self.txt_numero.setFocus()
                        return False
                    if not num.startswith("OMNY-"):
                        self.lbl_error.setText(
                            "Las tarjetas registradas deben comenzar con el prefijo OMNY- (p.ej. OMNY-2026-0001)."
                        )
                        self.lbl_error.show()
                        self.txt_numero.setFocus()
                        return False

        self.lbl_error.hide()
        return True

    def _on_confirm(self):
        if self.validate():
            self.accept()

    def get_data(self) -> Dict[str, Any]:
        soporte = self.combo_tipo_soporte.currentData() or "Tarjeta"
        return {
            "numero_tarjeta": self.txt_numero.text().strip(),
            "tipo_soporte": soporte,
            "pasajero_id": None if soporte == "Boleto" else self.combo_pasajero.currentData(),
            "tarifa_id": self.combo_tarifa.currentData(),
            "saldo_disponible": 2.90 if soporte == "Boleto" else self.spin_saldo.value(),
            "fecha_vencimiento": qdate_to_iso(self.picker_fvenc.getDate()),
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
        estados = ["Activa", "Bloqueada", "Reportada Perdida", "Cancelada", "Vencida", "Usado"]
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


class RecargaTarjetaDialog(MessageBoxBase):
    """
    Diálogo modal para recargar saldo de forma explícita a una tarjeta OMNY / MetroCard.
    Muestra con claridad el titular, saldo actual y proyección de nuevo saldo.
    """
    def __init__(self, parent=None, tarjetas_list: Optional[List[Dict[str, Any]]] = None, preselected_numero: Optional[str] = None):
        super().__init__(parent)
        self.tarjetas_list = tarjetas_list or []
        self.preselected_numero = preselected_numero

        self.titleLabel = SubtitleLabel("Recarga de Saldo OMNY / MetroCard", self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        # 1. Selector de Tarjeta Destino
        self.combo_tarjeta = ComboBox(self)
        sel_idx = 0
        for i, t in enumerate(self.tarjetas_list):
            num = _safe_str(t.get("NUMERO_TARJETA"))
            tit = _safe_str(t.get("PASAJERO"))
            sal = _safe_float(t.get("SALDO_DISPONIBLE"))
            est = _safe_str(t.get("ESTADO"))
            self.combo_tarjeta.addItem(f"{num} - {tit} (${sal:.2f}) [{est}]", userData=num)
            if preselected_numero and num == preselected_numero:
                sel_idx = i
        if self.tarjetas_list:
            self.combo_tarjeta.setCurrentIndex(sel_idx)
        form.addRow("Tarjeta a Recargar:", self.combo_tarjeta)

        # 2. Resumen de Saldo Actual y Titular
        self.lbl_info_titular = BodyLabel("-", self)
        self.lbl_info_saldo_actual = BodyLabel("$0.00", self)
        self.lbl_info_saldo_actual.setStyleSheet("font-weight: bold; color: #00E676;")
        form.addRow("Titular Asignado:", self.lbl_info_titular)
        form.addRow("Saldo Actual:", self.lbl_info_saldo_actual)

        # 3. Monto a Recargar (monto > 0)
        self.spin_monto = DoubleSpinBox(self)
        self.spin_monto.setRange(0.00, 500.00)
        self.spin_monto.setValue(10.00)
        self.spin_monto.setSingleStep(5.00)
        self.spin_monto.setPrefix("$ ")
        form.addRow("Monto a Abonar ($):", self.spin_monto)

        # Botones de monto rápido
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(6)
        for amt in [5, 10, 20, 50]:
            btn_q = PushButton(f"+${amt}", self)
            btn_q.clicked.connect(lambda ch, a=amt: self.spin_monto.setValue(float(a)))
            quick_layout.addWidget(btn_q)
        form.addRow("Montos Rápidos:", quick_layout)

        # 4. Medio de Pago
        self.combo_medio = ComboBox(self)
        self.combo_medio.addItems(["Efectivo", "Tarjeta Débito", "Tarjeta Crédito", "App Móvil", "Transferencia"])
        form.addRow("Medio de Pago:", self.combo_medio)

        # 5. Canal o Estación
        self.txt_canal = LineEdit(self)
        self.txt_canal.setText("Taquilla Central Estación")
        form.addRow("Estación / Canal:", self.txt_canal)

        # 6. Saldo Posterior Proyectado
        self.lbl_saldo_proyectado = StrongBodyLabel("$10.00", self)
        self.lbl_saldo_proyectado.setStyleSheet("font-size: 15px; font-weight: bold; color: #00E676;")
        form.addRow("Nuevo Saldo Estimado:", self.lbl_saldo_proyectado)

        # Label de error
        self.lbl_error = CaptionLabel("", self)
        self.lbl_error.setStyleSheet("color: #FF5252; font-weight: bold;")
        self.lbl_error.hide()
        form.addRow("", self.lbl_error)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Confirmar Recarga")
        self.cancelButton.setText("Cancelar")

        self.combo_tarjeta.currentIndexChanged.connect(self._actualizar_proyeccion)
        self.spin_monto.valueChanged.connect(self._actualizar_proyeccion)
        self._actualizar_proyeccion()

        self.yesButton.clicked.disconnect()
        self.yesButton.clicked.connect(self._on_confirm)

    def _actualizar_proyeccion(self):
        card_num = self.combo_tarjeta.currentData()
        saldo_actual = 0.0
        titular = "Al Portador"
        for t in self.tarjetas_list:
            if _safe_str(t.get("NUMERO_TARJETA")) == card_num:
                saldo_actual = _safe_float(t.get("SALDO_DISPONIBLE"))
                titular = _safe_str(t.get("PASAJERO"))
                break
        self.lbl_info_titular.setText(titular)
        self.lbl_info_saldo_actual.setText(f"${saldo_actual:.2f}")
        monto_abono = self.spin_monto.value()
        nuevo_saldo = saldo_actual + monto_abono
        self.lbl_saldo_proyectado.setText(f"${nuevo_saldo:.2f}")

    def validate(self) -> bool:
        card_num = self.combo_tarjeta.currentData()
        if not card_num:
            self.lbl_error.setText("Debe seleccionar una tarjeta a recargar.")
            self.lbl_error.show()
            return False
        if self.spin_monto.value() <= 0:
            self.lbl_error.setText("El monto a recargar debe ser estrictamente positivo (> 0).")
            self.lbl_error.show()
            return False
        self.lbl_error.hide()
        return True

    def _on_confirm(self):
        if self.validate():
            self.accept()

    def get_data(self) -> Dict[str, Any]:
        return {
            "numero_tarjeta": self.combo_tarjeta.currentData(),
            "monto": self.spin_monto.value(),
            "medio_pago": self.combo_medio.currentText(),
            "estacion_canal": self.txt_canal.text().strip() or "Torniquete Estacion"
        }


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
        fini_val = self.tarifa_data.get("FECHA_INICIO") if self.es_edicion and self.tarifa_data else date.today()
        self.picker_fini = create_calendar_picker(self, initial_date=fini_val, allow_reset=False)
        form.addRow("Inicio Vigencia:", self.picker_fini)

        ffin_val = self.tarifa_data.get("FECHA_FIN") if self.es_edicion and self.tarifa_data else None
        self.picker_ffin = create_calendar_picker(self, initial_date=ffin_val, allow_reset=True)
        form.addRow("Fin Vigencia:", self.picker_ffin)

        # 6. Estado
        self.combo_estado = ComboBox(self)
        self.combo_estado.addItems(["Vigente", "Suspendida", "Vencida"])
        if self.es_edicion and self.tarifa_data:
            idx = self.combo_estado.findText(_safe_str(self.tarifa_data.get("ESTADO", "")))
            if idx >= 0:
                self.combo_estado.setCurrentIndex(idx)
        form.addRow("Estado:", self.combo_estado)

        # Label de validación
        self.lbl_error = CaptionLabel("", self)
        self.lbl_error.setStyleSheet("color: #FF5252; font-weight: bold;")
        self.lbl_error.hide()
        form.addRow("", self.lbl_error)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Guardar Tarifa")
        self.cancelButton.setText("Cancelar")

        self.yesButton.clicked.disconnect()
        self.yesButton.clicked.connect(self._on_confirm)

    def validate(self) -> bool:
        cod = self.txt_cod.text().strip()
        if not cod:
            self.lbl_error.setText("El código de tarifa es obligatorio.")
            self.lbl_error.show()
            self.txt_cod.setFocus()
            return False

        nom = self.txt_nom.text().strip()
        if not nom:
            self.lbl_error.setText("El nombre de la tarifa es obligatorio.")
            self.lbl_error.show()
            self.txt_nom.setFocus()
            return False

        if self.spin_monto.value() < 0:
            self.lbl_error.setText("El costo por viaje no puede ser negativo.")
            self.lbl_error.show()
            return False

        d_ini = self.picker_fini.getDate()
        if not d_ini.isValid():
            self.lbl_error.setText("La fecha de inicio de vigencia es obligatoria.")
            self.lbl_error.show()
            self.picker_fini.setFocus()
            return False

        d_fin = self.picker_ffin.getDate()
        if d_fin.isValid() and d_fin < d_ini:
            self.lbl_error.setText("La fecha de fin de vigencia no puede ser anterior al inicio.")
            self.lbl_error.show()
            self.picker_ffin.setFocus()
            return False

        self.lbl_error.hide()
        return True

    def _on_confirm(self):
        if self.validate():
            self.accept()

    def get_data(self) -> Dict[str, Any]:
        return {
            "codigo": self.txt_cod.text().strip().upper(),
            "nombre": self.txt_nom.text().strip(),
            "monto": self.spin_monto.value(),
            "tipo_pasajero": self.combo_tipo.currentText(),
            "fecha_inicio_vigencia": qdate_to_iso(self.picker_fini.getDate()),
            "fecha_fin_vigencia": qdate_to_iso(self.picker_ffin.getDate()),
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
        self.combo_recarga_tarjeta: Optional[ComboBox] = None

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
        self.stack_views.setStyleSheet("background: transparent;")

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
        try:
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
        except Exception as exc:
            InfoBar.error(
                title="Error al Cargar Vista",
                content=f"Error en consulta de datos: {exc}. Asegúrese de haber ejecutado 'dbconfigurar.bat' y 'dbprogramar.bat'.",
                parent=self.window(),
                duration=6000
            )

    # ==========================================================================
    # PESTANA 1: TORNIQUETES Y TARJETA OMNY
    # ==========================================================================

    def init_tab_torniquetes(self):
        tab_widget = QWidget()
        tab_widget.setObjectName("tabTorniquetes")
        tab_widget.setStyleSheet("#tabTorniquetes { background: transparent; }")
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(0)

        # Contenedor de desplazamiento para garantizar adaptación en todas las pantallas
        scroll = SingleDirectionScrollArea(tab_widget, Qt.Orientation.Vertical)
        scroll.setWidgetResizable(True)

        content_widget = QWidget()
        content_widget.setObjectName("tabTorniquetesContent")

        # Layout centrado con ancho ergonomico para evitar estiramiento excesivo en pantallas anchas
        outer_layout = QHBoxLayout(content_widget)
        outer_layout.setContentsMargins(20, 8, 20, 24)
        outer_layout.setAlignment(Qt.AlignmentFlag(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop))

        center_container = QWidget(content_widget)
        center_container.setObjectName("tabTorniquetesCenterContainer")
        center_container.setStyleSheet("#tabTorniquetesCenterContainer { background: transparent; }")
        center_container.setMaximumWidth(820)
        center_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        content_layout = QVBoxLayout(center_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)
        outer_layout.addWidget(center_container)

        # 1. Tarjetas Métricas (KPIs)
        card_kpis = CardWidget(center_container)
        kpi_layout = QHBoxLayout(card_kpis)
        kpi_layout.setContentsMargins(16, 12, 16, 12)
        kpi_layout.setSpacing(14)

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
        content_layout.addWidget(card_kpis)

        # 2. Representación Visual del Medio de Transporte (ARRIBA)
        card_visual_box = CardWidget(center_container)
        visual_box_layout = QVBoxLayout(card_visual_box)
        visual_box_layout.setContentsMargins(16, 14, 16, 14)
        visual_box_layout.setSpacing(8)

        visual_header = QHBoxLayout()
        visual_header.addWidget(StrongBodyLabel("Visualización del Medio de Acceso", card_visual_box))
        visual_header.addStretch(1)
        self.lbl_medio_tipo_tag = CaptionLabel("TARJETA OMNY", card_visual_box)
        self.lbl_medio_tipo_tag.setStyleSheet("color: #64B5F6; font-weight: bold;")
        visual_header.addWidget(self.lbl_medio_tipo_tag)
        visual_box_layout.addLayout(visual_header)

        self.visual_card = VisualOmnyCard(card_visual_box)
        visual_box_layout.addWidget(self.visual_card, alignment=Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(card_visual_box)

        # 3. Panel Unificado: Torniquete, Tarifas y Operaciones
        card_ops = CardWidget(center_container)
        ops_layout = QVBoxLayout(card_ops)
        ops_layout.setContentsMargins(16, 14, 16, 14)
        ops_layout.setSpacing(10)

        ops_layout.addWidget(StrongBodyLabel("Gestión Operativa de Torniquetes y Tarifas OMNY", card_ops))

        # Fila de selectores
        row_sel = QHBoxLayout()
        row_sel.setSpacing(12)

        col_sel_card = QVBoxLayout()
        col_sel_card.setSpacing(3)
        col_sel_card.addWidget(CaptionLabel("Medio de Acceso a Operar (Tarjeta / Boleto):", card_ops))
        self.combo_tarjetas = ComboBox(card_ops)
        self.combo_tarjetas.currentIndexChanged.connect(self.on_card_combo_selected)
        col_sel_card.addWidget(self.combo_tarjetas)
        row_sel.addLayout(col_sel_card, stretch=6)

        # Mantener referencia compatible a combo_recarga_tarjeta
        self.combo_recarga_tarjeta = self.combo_tarjetas

        col_sel_est = QVBoxLayout()
        col_sel_est.setSpacing(3)
        col_sel_est.addWidget(CaptionLabel("Estación donde se ubica el torniquete:", card_ops))
        self.combo_estaciones = ComboBox(card_ops)
        col_sel_est.addWidget(self.combo_estaciones)
        row_sel.addLayout(col_sel_est, stretch=4)

        ops_layout.addLayout(row_sel)

        # Panel de desglose dinámico de tarifa asociada
        self.card_tarifa_info = CardWidget(card_ops)
        tar_info_layout = QHBoxLayout(self.card_tarifa_info)
        tar_info_layout.setContentsMargins(14, 10, 14, 10)
        tar_info_layout.setSpacing(12)

        col_t1 = QVBoxLayout()
        col_t1.setSpacing(2)
        col_t1.addWidget(CaptionLabel("TARIFA ASOCIADA", self.card_tarifa_info))
        self.lbl_sim_tarifa_nom = StrongBodyLabel("Tarifa Base Estándar", self.card_tarifa_info)
        col_t1.addWidget(self.lbl_sim_tarifa_nom)
        tar_info_layout.addLayout(col_t1, stretch=4)

        col_t2 = QVBoxLayout()
        col_t2.setSpacing(2)
        col_t2.addWidget(CaptionLabel("TARIFA A DEBITAR", self.card_tarifa_info))
        self.lbl_sim_tarifa_monto = StrongBodyLabel("$2.90", self.card_tarifa_info)
        self.lbl_sim_tarifa_monto.setStyleSheet("font-size: 14px; font-weight: bold;")
        col_t2.addWidget(self.lbl_sim_tarifa_monto)
        tar_info_layout.addLayout(col_t2, stretch=3)

        col_t3 = QVBoxLayout()
        col_t3.setSpacing(2)
        col_t3.addWidget(CaptionLabel("SALDO POST-VALIDACIÓN", self.card_tarifa_info))
        self.lbl_sim_saldo_proy = StrongBodyLabel("$0.00", self.card_tarifa_info)
        col_t3.addWidget(self.lbl_sim_saldo_proy)
        tar_info_layout.addLayout(col_t3, stretch=3)

        ops_layout.addWidget(self.card_tarifa_info)

        # Botón de paso por torniquete - Centrado y ajustado al ancho ergonómico del medio visual (380px)
        self.btn_tap = PrimaryPushButton("Validar Paso en Torniquete ($2.90)", card_ops, FIF.QRCODE)
        self.btn_tap.setFixedHeight(40)
        self.btn_tap.setFixedWidth(380)
        self.btn_tap.clicked.connect(self.handle_turnstile_tap)
        ops_layout.addWidget(self.btn_tap, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Sección de Recargas y Pases
        self.card_recharge = CardWidget(card_ops)
        rec_layout = QVBoxLayout(self.card_recharge)
        rec_layout.setContentsMargins(14, 12, 14, 12)
        rec_layout.setSpacing(8)

        rec_layout.addWidget(CaptionLabel("GESTIÓN FINANCIERA (RECARGAS Y ACTIVACIÓN DE PASES)", self.card_recharge))

        # Aviso cuando se selecciona un boleto
        self.lbl_boleto_no_recharge = StrongBodyLabel("Los boletos de uso único son al portador y no admiten recargas de saldo (Regla 14).", self.card_recharge)
        self.lbl_boleto_no_recharge.setStyleSheet("color: #FFB74D; font-weight: bold;")
        self.lbl_boleto_no_recharge.hide()
        rec_layout.addWidget(self.lbl_boleto_no_recharge)

        # Contenedor de inputs de recarga (solo para tarjetas)
        self.box_recharge_inputs = QWidget(self.card_recharge)
        box_rec_layout = QVBoxLayout(self.box_recharge_inputs)
        box_rec_layout.setContentsMargins(0, 0, 0, 0)
        box_rec_layout.setSpacing(8)

        # Proyección de Saldo Actual y Nuevo
        proj_card = CardWidget(self.box_recharge_inputs)
        proj_layout = QHBoxLayout(proj_card)
        proj_layout.setContentsMargins(14, 8, 14, 8)
        self.lbl_rec_saldo_actual = CaptionLabel("Saldo actual: $0.00", proj_card)
        self.lbl_rec_saldo_nuevo = StrongBodyLabel("Saldo posterior: $10.00", proj_card)
        self.lbl_rec_saldo_nuevo.setStyleSheet("color: #00E676; font-size: 13px; font-weight: bold;")
        proj_layout.addWidget(self.lbl_rec_saldo_actual)
        proj_layout.addStretch(1)
        proj_layout.addWidget(self.lbl_rec_saldo_nuevo)
        box_rec_layout.addWidget(proj_card)

        rec_inputs = QHBoxLayout()
        rec_inputs.setSpacing(12)
        col_m = QVBoxLayout()
        col_m.addWidget(CaptionLabel("Monto ($):", self.box_recharge_inputs))
        self.spin_monto_rec = DoubleSpinBox(self.box_recharge_inputs)
        self.spin_monto_rec.setRange(1.0, 500.0)
        self.spin_monto_rec.setValue(10.0)
        self.spin_monto_rec.setSingleStep(5.0)
        self.spin_monto_rec.setPrefix("$ ")
        self.spin_monto_rec.valueChanged.connect(self.update_tab1_recharge_projection)
        col_m.addWidget(self.spin_monto_rec)
        rec_inputs.addLayout(col_m, stretch=1)

        col_p = QVBoxLayout()
        col_p.addWidget(CaptionLabel("Medio de Pago:", self.box_recharge_inputs))
        self.combo_medio_pago = ComboBox(self.box_recharge_inputs)
        self.combo_medio_pago.addItems(["Efectivo", "Tarjeta Débito", "Tarjeta Crédito", "App Móvil", "Transferencia"])
        col_p.addWidget(self.combo_medio_pago)
        rec_inputs.addLayout(col_p, stretch=1)
        box_rec_layout.addLayout(rec_inputs)

        self.quick_row = QHBoxLayout()
        self.quick_row.setSpacing(8)
        self.quick_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        for amt in [5, 10, 20, 50]:
            b = PushButton(f"+${amt}", self.box_recharge_inputs)
            b.setFixedSize(74, 30)
            b.clicked.connect(lambda ch, a=amt: self.spin_monto_rec.setValue(float(a)))
            self.quick_row.addWidget(b)
        box_rec_layout.addLayout(self.quick_row)

        btns_recharge = QHBoxLayout()
        btns_recharge.setSpacing(10)
        btns_recharge.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.btn_ejecutar_recarga = PrimaryPushButton("Abonar Saldo a la Tarjeta", self.box_recharge_inputs, FIF.ADD)
        self.btn_ejecutar_recarga.setFixedHeight(36)
        self.btn_ejecutar_recarga.setFixedWidth(280)
        self.btn_ejecutar_recarga.clicked.connect(self.handle_recharge)
        btns_recharge.addWidget(self.btn_ejecutar_recarga)

        self.btn_pagar_pase = PushButton("Pagar / Activar Pase Ilimitado", self.box_recharge_inputs, FIF.SYNC)
        self.btn_pagar_pase.setFixedHeight(36)
        self.btn_pagar_pase.setFixedWidth(280)
        self.btn_pagar_pase.clicked.connect(self.handle_pagar_pase)
        self.btn_pagar_pase.setVisible(False)
        btns_recharge.addWidget(self.btn_pagar_pase)
        box_rec_layout.addLayout(btns_recharge)

        rec_layout.addWidget(self.box_recharge_inputs)
        ops_layout.addWidget(self.card_recharge)

        content_layout.addWidget(card_ops)

        # 4. Tabla de últimos pasos por torniquete de esta tarjeta
        card_log = CardWidget(center_container)
        log_layout = QVBoxLayout(card_log)
        log_layout.setContentsMargins(16, 12, 16, 12)
        log_layout.setSpacing(6)

        log_layout.addWidget(StrongBodyLabel("Últimas Transacciones Registradas en Torniquete", card_log))
        self.table_recent_taps = TableWidget(card_log)
        self.table_recent_taps.setBorderVisible(True)
        self.table_recent_taps.setColumnCount(6)
        self.table_recent_taps.setHorizontalHeaderLabels([
            "N° Transacción", "Medio", "Tarifa Aplicada", "Estación", "Hora Ingreso", "Cobro"
        ])
        configure_interactive_table(self.table_recent_taps)
        self.table_recent_taps.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_recent_taps.setMinimumHeight(180)
        self.table_recent_taps.setMaximumHeight(260)
        header_taps = self.table_recent_taps.horizontalHeader()
        if header_taps is not None:
            self.table_recent_taps.setColumnWidth(0, 160)
            self.table_recent_taps.setColumnWidth(1, 115)
            self.table_recent_taps.setColumnWidth(2, 140)
            self.table_recent_taps.setColumnWidth(4, 135)
            self.table_recent_taps.setColumnWidth(5, 75)
            header_taps.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        log_layout.addWidget(self.table_recent_taps)

        content_layout.addWidget(card_log)

        scroll.setWidget(content_widget)
        scroll.enableTransparentBackground()
        vp = scroll.viewport()
        if vp is not None:
            vp.setStyleSheet("background: transparent;")
        content_widget.setAutoFillBackground(False)
        content_widget.setStyleSheet("#tabTorniquetesContent { background: transparent; }")
        v_layout.addWidget(scroll)
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
        self.combo_filtro_estado.addItems(["(Todos)", "Activa", "Bloqueada", "Reportada Perdida", "Cancelada", "Vencida", "Usado"])
        self.combo_filtro_estado.currentTextChanged.connect(self.refresh_cards_list)
        bar_actions.addWidget(self.combo_filtro_estado, stretch=2)

        self.btn_emitir_tarjeta = PrimaryPushButton("Emitir Medio", tab_widget, FIF.ADD)
        self.btn_emitir_tarjeta.clicked.connect(self.handle_emitir_tarjeta)
        bar_actions.addWidget(self.btn_emitir_tarjeta)

        self.btn_modificar_tarjeta = PushButton("Modificar Tarjeta", tab_widget, FIF.EDIT)
        self.btn_modificar_tarjeta.clicked.connect(self.handle_modificar_tarjeta)
        bar_actions.addWidget(self.btn_modificar_tarjeta)

        self.btn_bloquear_tarjeta = PushButton("Bloquear / Estado", tab_widget, FIF.SYNC)
        self.btn_bloquear_tarjeta.clicked.connect(self.handle_bloquear_tarjeta)
        bar_actions.addWidget(self.btn_bloquear_tarjeta)

        self.btn_recargar_tarjeta = PushButton("Recargar Saldo", tab_widget, FIF.SHOPPING_CART)
        self.btn_recargar_tarjeta.clicked.connect(self.handle_recargar_tarjeta_dialog)
        bar_actions.addWidget(self.btn_recargar_tarjeta)

        self.btn_eliminar_tarjeta = PushButton("Eliminar", tab_widget, FIF.DELETE)
        self.btn_eliminar_tarjeta.clicked.connect(self.handle_eliminar_tarjeta)
        bar_actions.addWidget(self.btn_eliminar_tarjeta)

        v_layout.addLayout(bar_actions)

        # Tabla de Tarjetas
        self.table_cards = TableWidget(tab_widget)
        self.table_cards.setBorderVisible(True)
        self.table_cards.setColumnCount(10)
        self.table_cards.setHorizontalHeaderLabels([
            "N° Tarjeta / Boleto", "Soporte", "Titular / Pasajero", "Tipo Pasajero", "Tarifa",
            "Saldo Disponible", "Fecha Emisión", "Vencimiento", "Días Rest.", "Estado"
        ])
        configure_interactive_table(self.table_cards)
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
        configure_interactive_table(self.table_viajes_tarjeta)
        self.table_viajes_tarjeta.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.stack_sub_hist.addWidget(self.table_viajes_tarjeta)

        # Tabla 2: Recargas
        self.table_recargas_tarjeta = TableWidget(self.stack_sub_hist)
        self.table_recargas_tarjeta.setBorderVisible(True)
        self.table_recargas_tarjeta.setColumnCount(7)
        self.table_recargas_tarjeta.setHorizontalHeaderLabels([
            "N° Transacción", "Monto", "Medio Pago", "Estación / Canal", "Saldo Ant.", "Saldo Post.", "Fecha y Hora"
        ])
        configure_interactive_table(self.table_recargas_tarjeta)
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
        configure_interactive_table(self.table_pasajeros)
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
        configure_interactive_table(self.table_pasajero_tarjetas)
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
        configure_interactive_table(self.table_tarifas)
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
            InfoBar.warning(title="Selección Requerida", content="Seleccione una tarjeta o boleto para validar en el torniquete.", parent=self.window(), duration=3000)
            return

        est_id = self.combo_estaciones.currentData()
        if not est_id:
            InfoBar.warning(title="Estación Requerida", content="Seleccione la estación del torniquete.", parent=self.window(), duration=3000)
            return

        if str(num_tarjeta) == "__EMITIR_BOLETO_INMEDIATO__":
            res = m5_cards_service.emitir_y_validar_boleto_inmediato(int(est_id))
            if res.get("success"):
                bol_num = res.get("numero_tarjeta", "Boleto")
                monto = _safe_float(res.get("monto_cobrado", 2.90))
                InfoBar.success(
                    title="Paso Autorizado con Boleto Único",
                    content=f"Boleto {bol_num} emitido y validado exitosamente. Tarifa cobrada: ${monto:.2f}. Estado final: Usado.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )
            else:
                InfoBar.error(
                    title="Paso Rechazado",
                    content=res.get("mensaje", "No se pudo emitir y validar el boleto de uso único."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )
        else:
            res = m5_cards_service.validar_ingreso_torniquete(str(num_tarjeta), int(est_id))
            if res.get("success"):
                monto_cobrado = _safe_float(res.get("monto_cobrado"))
                nuevo_saldo = _safe_float(res.get("nuevo_saldo"))
                msg = res.get("mensaje", "Paso validado correctamente.")
                card_data = m5_cards_service.get_tarjeta_by_numero(str(num_tarjeta))
                es_bol = card_data and (card_data.get("TIPO_SOPORTE") == "Boleto" or _safe_int(card_data.get("ES_BOLETO"), 0) == 1)
                
                extra_info = " | Boleto Consumido (1 solo uso)" if es_bol else f" | Saldo restante: ${nuevo_saldo:.2f}"
                InfoBar.success(
                    title="Paso Autorizado",
                    content=f"{msg} (Cobro aplicado: ${monto_cobrado:.2f}{extra_info})",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4000
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

        res = m5_cards_service.emitir_y_validar_boleto_inmediato(int(est_id))
        if res.get("success"):
            bol_num = res.get("numero_tarjeta", "Boleto")
            InfoBar.success(
                title="Paso con Boleto Único",
                content=f"Boleto {bol_num} emitido y validado exitosamente. Tarifa cobrada: ${res.get('monto_cobrado', 2.90):.2f}.",
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
                duration=3500
            )
        else:
            InfoBar.error(title="Paso Rechazado", content=res.get("mensaje", ""), parent=self.window(), duration=4500)

        self.refresh_cards_list()
        self.refresh_kpis()
        self.refresh_recent_taps()

    def handle_recharge(self):
        combo = self.combo_recarga_tarjeta if self.combo_recarga_tarjeta is not None else self.combo_tarjetas
        num_tarjeta = combo.currentData()
        if not num_tarjeta or str(num_tarjeta) == "__EMITIR_BOLETO_INMEDIATO__":
            InfoBar.warning(title="Selección Requerida", content="Seleccione una tarjeta válida que admita recarga.", parent=self.window(), duration=3000)
            return

        card_chk = m5_cards_service.get_tarjeta_by_numero(str(num_tarjeta))
        if card_chk and (card_chk.get("TIPO_SOPORTE") == "Boleto" or _safe_int(card_chk.get("ES_BOLETO"), 0) == 1):
            InfoBar.warning(
                title="Operación No Permitida",
                content="Los boletos de uso único no admiten recargas de saldo (Regla 14 / Modelo OMNY).",
                parent=self.window(),
                duration=3500
            )
            return

        monto = self.spin_monto_rec.value()
        if monto <= 0:
            InfoBar.error(title="Monto Inválido", content="El monto a recargar debe ser estrictamente positivo (> 0).", parent=self.window(), duration=3500)
            return

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
            self.update_tab1_recharge_projection()
        else:
            InfoBar.error(title="Error en Recarga", content=res.get("error", ""), parent=self.window(), duration=4000)

    def handle_pagar_pase(self):
        combo = self.combo_recarga_tarjeta if self.combo_recarga_tarjeta is not None else self.combo_tarjetas
        num_tarjeta = combo.currentData()
        if not num_tarjeta:
            InfoBar.warning(title="Selección Requerida", content="Seleccione la tarjeta para pagar el pase.", parent=self.window(), duration=3000)
            return

        medio = self.combo_medio_pago.currentText()
        est_nombre = self.combo_estaciones.currentText().split(" - ")[-1]

        res = m5_cards_service.pagar_o_renovar_pase(str(num_tarjeta), medio, f"Taquilla {est_nombre}")
        if res.get("success"):
            InfoBar.success(
                title="Pase Pagado y Activado",
                content=res.get("mensaje", "Pase activado exitosamente."),
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000
            )
            self.refresh_cards_list()
            self.refresh_kpis()
            self.update_tab1_recharge_projection()
        else:
            InfoBar.error(title="Error al Pagar Pase", content=res.get("error", ""), parent=self.window(), duration=4000)

    def refresh_recent_taps(self):
        viajes = m5_cards_service.get_historial_viajes(limit=8)
        self.table_recent_taps.setRowCount(len(viajes))
        for r, row in enumerate(viajes):
            self.table_recent_taps.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("NUMERO_TRANSACCION"))))
            self.table_recent_taps.setItem(r, 1, QTableWidgetItem(_safe_str(row.get("NUMERO_TARJETA"))))
            tar_nom = _safe_str(row.get("TARIFA_APLICADA", "-"))
            self.table_recent_taps.setCellWidget(r, 2, StatusBadge(tar_nom, self.table_recent_taps))
            self.table_recent_taps.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("ESTACION_INGRESO"))))
            self.table_recent_taps.setItem(r, 4, QTableWidgetItem(_safe_str(row.get("FECHA_HORA_INGRESO"))))
            cobro = _safe_float(row.get("MONTO_COBRADO"))
            self.table_recent_taps.setItem(r, 5, QTableWidgetItem(f"${cobro:.2f}"))
        header_taps = self.table_recent_taps.horizontalHeader()
        if header_taps is not None:
            self.table_recent_taps.setColumnWidth(0, 160)
            self.table_recent_taps.setColumnWidth(1, 115)
            self.table_recent_taps.setColumnWidth(2, 140)
            self.table_recent_taps.setColumnWidth(4, 135)
            self.table_recent_taps.setColumnWidth(5, 75)
            header_taps.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_recent_taps.updateEditorGeometries()

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
        self.table_cards.clearContents()
        self.table_cards.setRowCount(len(self.tarjetas_cache))
        for r, row in enumerate(self.tarjetas_cache):
            num = _safe_str(row.get("NUMERO_TARJETA"))
            soporte = _safe_str(row.get("TIPO_SOPORTE"), "Tarjeta")
            saldo = _safe_float(row.get("SALDO_DISPONIBLE"))
            dias = _safe_str(row.get("DIAS_RESTANTES"))

            self.table_cards.setItem(r, 0, QTableWidgetItem(num))
            self.table_cards.setCellWidget(r, 1, StatusBadge(soporte, self.table_cards))
            self.table_cards.setItem(r, 2, QTableWidgetItem(_safe_str(row.get("PASAJERO"))))
            
            tipo_p = _safe_str(row.get("TIPO_PASAJERO"))
            self.table_cards.setCellWidget(r, 3, StatusBadge(tipo_p, self.table_cards))

            tar_nom = _safe_str(row.get("TARIFA_NOMBRE"))
            tar_mto = _safe_float(row.get("TARIFA_MONTO"))
            es_pase = _safe_int(row.get("ES_PASE_ILIMITADO"), 0) == 1
            pase_vig = _safe_int(row.get("PASE_VIGENTE"), 0) == 1
            pase_fin = _safe_str(row.get("PASE_FECHA_FIN"))
            es_bol = soporte == "Boleto" or _safe_int(row.get("ES_BOLETO"), 0) == 1

            if es_bol:
                tar_display = f"Boleto Único (${tar_mto:.2f})"
            elif es_pase:
                if pase_vig:
                    tar_display = f"{tar_nom} (Vigente hasta {pase_fin})"
                else:
                    tar_display = f"{tar_nom} (Vencido / Requiere Pago)"
            else:
                tar_display = f"{tar_nom} (${tar_mto:.2f})"

            self.table_cards.setCellWidget(r, 4, StatusBadge(tar_display, self.table_cards))

            self.table_cards.setItem(r, 5, QTableWidgetItem(f"${saldo:.2f}"))
            self.table_cards.setItem(r, 6, QTableWidgetItem(_safe_str(row.get("FECHA_EMISION"))))
            self.table_cards.setItem(r, 7, QTableWidgetItem(_safe_str(row.get("FECHA_VENCIMIENTO"))))
            self.table_cards.setItem(r, 8, QTableWidgetItem(dias))

            est_card = _safe_str(row.get("ESTADO"))
            self.table_cards.setCellWidget(r, 9, StatusBadge(est_card, self.table_cards))

        self.table_cards.blockSignals(False)
        auto_fit_table_columns(self.table_cards)

        # Llenar combo de tarjetas de la pestaña 1 (simulador y recarga)
        self.combo_tarjetas.blockSignals(True)
        self.combo_tarjetas.clear()
        combo_rec = self.combo_recarga_tarjeta
        if combo_rec is not None:
            combo_rec.blockSignals(True)
            combo_rec.clear()

        # Opción para emisión y validación inmediata de boletos de un solo viaje
        self.combo_tarjetas.addItem("[Boleto] Emitir y Validar Boleto de Uso Único ($2.90)", userData="__EMITIR_BOLETO_INMEDIATO__")

        target_idx = 0
        all_cards = m5_cards_service.get_tarjetas()
        for i, t in enumerate(all_cards):
            c_num = _safe_str(t.get("NUMERO_TARJETA"))
            tit = _safe_str(t.get("PASAJERO"))
            sal = _safe_float(t.get("SALDO_DISPONIBLE"))
            est = _safe_str(t.get("ESTADO"))
            tar_nom = _safe_str(t.get("TARIFA_NOMBRE"))
            tar_mto = _safe_float(t.get("TARIFA_MONTO"))
            t_es_pase = _safe_int(t.get("ES_PASE_ILIMITADO"), 0) == 1
            t_pase_vig = _safe_int(t.get("PASE_VIGENTE"), 0) == 1
            t_pase_fin = _safe_str(t.get("PASE_FECHA_FIN"))
            t_soporte = _safe_str(t.get("TIPO_SOPORTE"), "Tarjeta")
            t_es_boleto = _safe_int(t.get("ES_BOLETO"), 0) == 1 or t_soporte == "Boleto"

            if t_es_boleto:
                if est == "Activa":
                    item_text = f"[Boleto] {c_num} - Al Portador (${sal:.2f}) [1 Solo Uso]"
                else:
                    item_text = f"[Boleto] {c_num} - Al Portador (${sal:.2f}) [{est} / Consumido]"
            elif c_num.startswith("MC-") or "Portador" in tit or "Anónima" in tit:
                item_text = f"[Tarjeta Al Portador] {c_num} (${sal:.2f}) - {tar_nom} (${tar_mto:.2f}) [{est}]"
            elif t_es_pase:
                if t_pase_vig:
                    item_text = f"[Tarjeta] {c_num} - {tit} (${sal:.2f}) - {tar_nom} [Vigente hasta {t_pase_fin}]"
                else:
                    item_text = f"[Tarjeta] {c_num} - {tit} (${sal:.2f}) - {tar_nom} [Pase Vencido / No Pagado]"
            else:
                item_text = f"[Tarjeta] {c_num} - {tit} (${sal:.2f}) - {tar_nom} (${tar_mto:.2f}) [{est}]"

            self.combo_tarjetas.addItem(item_text, userData=c_num)

            if combo_rec is not None and combo_rec is not self.combo_tarjetas:
                if t_es_boleto:
                    item_text_rec = f"[Boleto] {c_num} - Al Portador (${sal:.2f}) [No Recargable]"
                else:
                    item_text_rec = item_text
                combo_rec.addItem(item_text_rec, userData=c_num)

            if c_num == prev_card:
                target_idx = i + 1

        if prev_card == "__EMITIR_BOLETO_INMEDIATO__":
            target_idx = 0
        elif not prev_card and len(all_cards) > 0:
            target_idx = 1

        self.combo_tarjetas.setCurrentIndex(target_idx)
        self.combo_tarjetas.blockSignals(False)

        if combo_rec is not None and combo_rec is not self.combo_tarjetas:
            if prev_card:
                idx_rec = combo_rec.findData(prev_card)
                combo_rec.setCurrentIndex(idx_rec if idx_rec >= 0 else 0)
            else:
                combo_rec.setCurrentIndex(0)
            combo_rec.blockSignals(False)

        # Actualizar visual card y proyección
        active_num = self.combo_tarjetas.currentData()
        if active_num:
            self.set_active_card(str(active_num))

        self.update_tab1_recharge_projection()
        self.refresh_recent_taps()

    def on_card_combo_selected(self, index: int):
        card_num = self.combo_tarjetas.currentData()
        if not card_num:
            return
        if str(card_num) == "__EMITIR_BOLETO_INMEDIATO__":
            self.set_active_card("__EMITIR_BOLETO_INMEDIATO__")
            self.update_tab1_recharge_projection()
            return

        self.set_active_card(str(card_num))
        self.update_tab1_recharge_projection()

    def on_recarga_card_combo_selected(self, index: int):
        combo_rec = self.combo_recarga_tarjeta
        if combo_rec is None:
            return
        card_num = combo_rec.currentData()
        if card_num:
            self.combo_tarjetas.blockSignals(True)
            idx = self.combo_tarjetas.findData(card_num)
            if idx >= 0:
                self.combo_tarjetas.setCurrentIndex(idx)
            self.combo_tarjetas.blockSignals(False)
            self.set_active_card(str(card_num))
            self.update_tab1_recharge_projection()

    def update_tab1_recharge_projection(self):
        if not hasattr(self, "lbl_rec_saldo_actual") or not hasattr(self, "lbl_rec_saldo_nuevo"):
            return

        # Si el simulador tiene seleccionada la opción de emisión inmediata
        if getattr(self, "selected_card_num", None) == "__EMITIR_BOLETO_INMEDIATO__":
            self.lbl_rec_saldo_actual.setText("Soporte: Boleto Único (Emisión Inmediata)")
            self.lbl_rec_saldo_nuevo.setText("No Admite Recargas")
            self.lbl_rec_saldo_nuevo.setStyleSheet("color: #FF5252; font-size: 13px; font-weight: bold;")
            if hasattr(self, "btn_ejecutar_recarga"):
                self.btn_ejecutar_recarga.setEnabled(False)
                self.btn_ejecutar_recarga.setText("Boletos No Admiten Recargas")
            return

        combo = self.combo_recarga_tarjeta if self.combo_recarga_tarjeta is not None else self.combo_tarjetas
        card_num = combo.currentData()
        saldo_actual = 0.0
        es_boleto = False
        if card_num and str(card_num) != "__EMITIR_BOLETO_INMEDIATO__":
            card = m5_cards_service.get_tarjeta_by_numero(str(card_num))
            if card:
                saldo_actual = _safe_float(card.get("SALDO_DISPONIBLE"))
                es_boleto = _safe_int(card.get("ES_BOLETO"), 0) == 1 or str(card.get("TIPO_SOPORTE")) == "Boleto"
        elif str(card_num) == "__EMITIR_BOLETO_INMEDIATO__":
            es_boleto = True

        monto_rec = self.spin_monto_rec.value()
        if es_boleto:
            self.lbl_rec_saldo_actual.setText("Soporte: Boleto Único")
            self.lbl_rec_saldo_nuevo.setText("No Admite Recargas")
            self.lbl_rec_saldo_nuevo.setStyleSheet("color: #FF5252; font-size: 13px; font-weight: bold;")
            if hasattr(self, "btn_ejecutar_recarga"):
                self.btn_ejecutar_recarga.setEnabled(False)
                self.btn_ejecutar_recarga.setText("Boletos No Admiten Recargas")
        else:
            self.lbl_rec_saldo_actual.setText(f"Saldo actual: ${saldo_actual:.2f}")
            self.lbl_rec_saldo_nuevo.setText(f"Saldo posterior: ${saldo_actual + monto_rec:.2f}")
            self.lbl_rec_saldo_nuevo.setStyleSheet("color: #00E676; font-size: 13px; font-weight: bold;")
            if hasattr(self, "btn_ejecutar_recarga"):
                self.btn_ejecutar_recarga.setEnabled(True)
                self.btn_ejecutar_recarga.setText("Abonar Saldo a la Tarjeta")

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
        if numero_tarjeta == "__EMITIR_BOLETO_INMEDIATO__":
            self.visual_card.set_card_data(
                numero="BOL-NUEVO",
                titular="Al Portador (Boleto Único)",
                tarifa="Tarifa Base Regular ($2.90)",
                saldo=2.90,
                estado="Emisión Inmediata",
                is_boleto=True
            )
            fake_card = {
                "NUMERO_TARJETA": "__EMITIR_BOLETO_INMEDIATO__",
                "TIPO_SOPORTE": "Boleto",
                "ES_BOLETO": 1,
                "TARIFA_NOMBRE": "Boleto de Uso Único",
                "TARIFA_MONTO": 2.90,
                "SALDO_DISPONIBLE": 2.90,
                "ESTADO": "Activa",
                "ES_PASE_ILIMITADO": 0,
                "PASE_VIGENTE": 0,
            }
            self.update_turnstile_fare_display(fake_card)
            return

        card = m5_cards_service.get_tarjeta_by_numero(numero_tarjeta)
        if not card:
            return

        tarifa_nom = str(card.get("TARIFA_NOMBRE", "Tarifa Base"))
        tarifa_monto = _safe_float(card.get("TARIFA_MONTO"))
        saldo_actual = _safe_float(card.get("SALDO_DISPONIBLE"))
        estado = str(card.get("ESTADO", "Activa"))
        soporte = str(card.get("TIPO_SOPORTE", "Tarjeta"))
        es_boleto = _safe_int(card.get("ES_BOLETO"), 0) == 1 or soporte == "Boleto"

        es_pase = _safe_int(card.get("ES_PASE_ILIMITADO"), 0) == 1
        pase_vigente = _safe_int(card.get("PASE_VIGENTE"), 0) == 1
        pase_fin = _safe_str(card.get("PASE_FECHA_FIN"), "")

        if es_boleto:
            uso_desc = "1 Uso Disponible" if estado == "Activa" else ("Usado" if estado == "Usado" else estado)
            tarifa_display = f"Boleto Único ($2.90) [{uso_desc}]"
        elif es_pase:
            if pase_vigente:
                tarifa_display = f"{tarifa_nom} [Vigente hasta {pase_fin}]"
            else:
                tarifa_display = f"{tarifa_nom} [Vencido / Requiere Pago]"
        else:
            tarifa_display = f"{tarifa_nom} (${tarifa_monto:.2f})"

        tit_raw = card.get("PASAJERO")
        if not tit_raw or "Anónima" in str(tit_raw) or "Portador" in str(tit_raw):
            titular_display = "Al Portador (Sin Titular)" if es_boleto else "Al Portador (Tarjeta Anónima)"
        else:
            titular_display = str(tit_raw)

        self.visual_card.set_card_data(
            numero=str(card.get("NUMERO_TARJETA", "-")),
            titular=titular_display,
            tarifa=tarifa_display,
            saldo=saldo_actual,
            estado=estado,
            is_boleto=es_boleto
        )

        # Sincronizar selección en combo si difiere
        if self.combo_tarjetas.currentData() != numero_tarjeta:
            idx = self.combo_tarjetas.findData(numero_tarjeta)
            if idx >= 0:
                self.combo_tarjetas.blockSignals(True)
                self.combo_tarjetas.setCurrentIndex(idx)
                self.combo_tarjetas.blockSignals(False)

        combo_rec = self.combo_recarga_tarjeta
        if combo_rec is not None and combo_rec is not self.combo_tarjetas and not es_boleto:
            if combo_rec.currentData() != numero_tarjeta:
                idx_rec = combo_rec.findData(numero_tarjeta)
                if idx_rec >= 0:
                    combo_rec.blockSignals(True)
                    combo_rec.setCurrentIndex(idx_rec)
                    combo_rec.blockSignals(False)

        self.update_turnstile_fare_display(card)
        self.load_card_sub_histories(numero_tarjeta)

    def update_turnstile_fare_display(self, card: dict):
        """
        Actualiza dinámicamente los controles del simulador de torniquete
        en función del medio seleccionado (Tarjeta OMNY, Pase Ilimitado o Boleto de Uso Único).
        """
        tarifa_nom = str(card.get("TARIFA_NOMBRE", "Tarifa Base Estándar"))
        tarifa_monto = _safe_float(card.get("TARIFA_MONTO", 2.90))
        saldo_actual = _safe_float(card.get("SALDO_DISPONIBLE", 0.0))
        estado = str(card.get("ESTADO", "Activa"))
        c_num = str(card.get("NUMERO_TARJETA", ""))
        soporte = str(card.get("TIPO_SOPORTE", "Tarjeta"))
        es_boleto = _safe_int(card.get("ES_BOLETO"), 0) == 1 or soporte == "Boleto"
        es_inmediato = (c_num == "__EMITIR_BOLETO_INMEDIATO__")

        es_pase = _safe_int(card.get("ES_PASE_ILIMITADO"), 0) == 1
        pase_vigente = _safe_int(card.get("PASE_VIGENTE"), 0) == 1
        pase_fin = _safe_str(card.get("PASE_FECHA_FIN"), "")
        dias_rest = card.get("PASE_DIAS_RESTANTES")
        dias_rest_int = _safe_int(dias_rest, 0) if dias_rest not in (None, "", "-") else 0

        # Actualizar indicador superior de tipo de medio
        if hasattr(self, "lbl_medio_tipo_tag"):
            if es_inmediato:
                self.lbl_medio_tipo_tag.setText("BOLETO DE USO ÚNICO (NUEVO)")
                self.lbl_medio_tipo_tag.setStyleSheet("color: #FFA726; font-weight: bold;")
            elif es_boleto:
                self.lbl_medio_tipo_tag.setText("BOLETO DE USO ÚNICO")
                self.lbl_medio_tipo_tag.setStyleSheet("color: #FFA726; font-weight: bold;")
            elif c_num.startswith("MC-") or c_num.startswith("ANON-"):
                self.lbl_medio_tipo_tag.setText("TARJETA AL PORTADOR")
                self.lbl_medio_tipo_tag.setStyleSheet("color: #81D4FA; font-weight: bold;")
            else:
                self.lbl_medio_tipo_tag.setText("TARJETA OMNY")
                self.lbl_medio_tipo_tag.setStyleSheet("color: #64B5F6; font-weight: bold;")

        # Controlar visibilidad del panel de recarga según sea boleto o tarjeta
        if es_inmediato or es_boleto:
            if hasattr(self, "box_recharge_inputs"):
                self.box_recharge_inputs.hide()
            if hasattr(self, "lbl_boleto_no_recharge"):
                self.lbl_boleto_no_recharge.show()
        else:
            if hasattr(self, "box_recharge_inputs"):
                self.box_recharge_inputs.show()
            if hasattr(self, "lbl_boleto_no_recharge"):
                self.lbl_boleto_no_recharge.hide()

        # Botón de activación / pago de pase en panel de recargas
        if hasattr(self, "btn_pagar_pase"):
            if es_pase:
                self.btn_pagar_pase.setVisible(True)
                accion = "Renovar" if pase_vigente else "Pagar y Activar"
                self.btn_pagar_pase.setText(f"{accion} {tarifa_nom} (${tarifa_monto:.2f})")
            else:
                self.btn_pagar_pase.setVisible(False)

        if es_inmediato:
            self.btn_tap.setText("Emitir y Validar Boleto Único ($2.90)")
            self.btn_tap.setToolTip("Emite un nuevo boleto de uso único por $2.90 y valida el paso por torniquete de inmediato.")
            if hasattr(self, "lbl_sim_tarifa_nom"):
                self.lbl_sim_tarifa_nom.setText("Boleto de Uso Único (Emisión Inmediata)")
            if hasattr(self, "lbl_sim_tarifa_monto"):
                self.lbl_sim_tarifa_monto.setText("$2.90")
            if hasattr(self, "lbl_sim_saldo_proy"):
                self.lbl_sim_saldo_proy.setText("$0.00 (Consumo Inmediato)")
                self.lbl_sim_saldo_proy.setStyleSheet("color: #00E676; font-weight: bold;")
        elif es_boleto:
            if estado == "Activa" and saldo_actual >= 2.90:
                self.btn_tap.setText("Validar Paso con Boleto Único ($2.90 - 1 Solo Uso)")
                self.btn_tap.setToolTip("Boleto al portador de un solo viaje. Al validar, su estado pasará a Usado.")
                if hasattr(self, "lbl_sim_tarifa_nom"):
                    self.lbl_sim_tarifa_nom.setText("Boleto de Uso Único (Vigente)")
                if hasattr(self, "lbl_sim_tarifa_monto"):
                    self.lbl_sim_tarifa_monto.setText("$2.90")
                if hasattr(self, "lbl_sim_saldo_proy"):
                    self.lbl_sim_saldo_proy.setText("$0.00 (Consumo Inmediato)")
                    self.lbl_sim_saldo_proy.setStyleSheet("color: #00E676; font-weight: bold;")
            else:
                self.btn_tap.setText(f"Validar Paso con Boleto ({estado} - 0 Usos)")
                self.btn_tap.setToolTip(f"Boleto {estado}. Este boleto ya fue utilizado y no admite nuevos viajes.")
                if hasattr(self, "lbl_sim_tarifa_nom"):
                    self.lbl_sim_tarifa_nom.setText(f"Boleto Agotado ({estado})")
                if hasattr(self, "lbl_sim_tarifa_monto"):
                    self.lbl_sim_tarifa_monto.setText("$2.90")
                if hasattr(self, "lbl_sim_saldo_proy"):
                    self.lbl_sim_saldo_proy.setText(f"Rechazado ({estado})")
                    self.lbl_sim_saldo_proy.setStyleSheet("color: #FF5252; font-weight: bold;")
        elif es_pase:
            if pase_vigente:
                btn_text = "Validar Paso en Torniquete (Pase Vigente - $0.00)"
                self.btn_tap.setText(btn_text)
                self.btn_tap.setToolTip(
                    f"{tarifa_nom} activo y pagado. Válido hasta {pase_fin} "
                    f"({dias_rest_int} días restantes). Acceso ilimitado sin costo por viaje."
                )
                if hasattr(self, "lbl_sim_tarifa_nom"):
                    self.lbl_sim_tarifa_nom.setText(f"{tarifa_nom} (Vigente)")
                if hasattr(self, "lbl_sim_tarifa_monto"):
                    self.lbl_sim_tarifa_monto.setText("$0.00 (Ilimitado)")
                if hasattr(self, "lbl_sim_saldo_proy"):
                    self.lbl_sim_saldo_proy.setText(f"${saldo_actual:.2f} (Intacto)")
                    self.lbl_sim_saldo_proy.setStyleSheet("color: #00E676; font-weight: bold;")
            else:
                if pase_fin:
                    btn_text = f"Validar Paso en Torniquete (Pase Vencido - {pase_fin})"
                    desc_venc = f"Venció el {pase_fin}. Se requiere renovación (${tarifa_monto:.2f})."
                else:
                    btn_text = f"Validar Paso en Torniquete (Pase No Pagado - ${tarifa_monto:.2f})"
                    desc_venc = f"No activado. Requiere pago inicial de ${tarifa_monto:.2f}."

                self.btn_tap.setText(btn_text)
                self.btn_tap.setToolTip(
                    f"Acceso restringido: {desc_venc} Realice el pago del pase para activar viajes ilimitados."
                )
                if hasattr(self, "lbl_sim_tarifa_nom"):
                    self.lbl_sim_tarifa_nom.setText(f"{tarifa_nom} (Inactivo)")
                if hasattr(self, "lbl_sim_tarifa_monto"):
                    self.lbl_sim_tarifa_monto.setText(f"${tarifa_monto:.2f} (Pago requerido)")
                if hasattr(self, "lbl_sim_saldo_proy"):
                    self.lbl_sim_saldo_proy.setText("Bloqueado (Pase Vencido)")
                    self.lbl_sim_saldo_proy.setStyleSheet("color: #FF5252; font-weight: bold;")
        else:
            saldo_proy = saldo_actual - tarifa_monto
            if tarifa_monto == 0.0:
                btn_text = "Validar Paso en Torniquete (Gratuito - $0.00)"
            else:
                btn_text = f"Validar Paso en Torniquete (${tarifa_monto:.2f})"

            self.btn_tap.setText(btn_text)

            if estado != "Activa":
                self.btn_tap.setToolTip(f"Tarjeta {estado}. El torniquete rechazará el paso.")
            elif saldo_actual < tarifa_monto:
                self.btn_tap.setToolTip(
                    f"Saldo insuficiente (${saldo_actual:.2f} < ${tarifa_monto:.2f}). Se requiere recargar saldo."
                )
            else:
                self.btn_tap.setToolTip(
                    f"Aplica {tarifa_nom}: Cobro de ${tarifa_monto:.2f} sobre saldo disponible (${saldo_actual:.2f})."
                )

            if hasattr(self, "lbl_sim_tarifa_nom"):
                self.lbl_sim_tarifa_nom.setText(tarifa_nom)
            if hasattr(self, "lbl_sim_tarifa_monto"):
                self.lbl_sim_tarifa_monto.setText(f"${tarifa_monto:.2f}" if tarifa_monto > 0 else "Gratuito ($0.00)")
            if hasattr(self, "lbl_sim_saldo_proy"):
                if saldo_proy < 0:
                    self.lbl_sim_saldo_proy.setText(f"${saldo_actual:.2f} (Insuficiente)")
                    self.lbl_sim_saldo_proy.setStyleSheet("color: #FF5252; font-weight: bold;")
                else:
                    self.lbl_sim_saldo_proy.setText(f"${saldo_proy:.2f}")
                    self.lbl_sim_saldo_proy.setStyleSheet("color: #00E676; font-weight: bold;")

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
        self.table_viajes_tarjeta.clearContents()
        self.table_viajes_tarjeta.setRowCount(len(viajes))
        for r, row in enumerate(viajes):
            self.table_viajes_tarjeta.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("NUMERO_TRANSACCION"))))
            self.table_viajes_tarjeta.setItem(r, 1, QTableWidgetItem(_safe_str(row.get("ESTACION_INGRESO"))))
            self.table_viajes_tarjeta.setItem(r, 2, QTableWidgetItem(_safe_str(row.get("ESTACION_SALIDA"))))
            self.table_viajes_tarjeta.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("FECHA_HORA_INGRESO"))))
            self.table_viajes_tarjeta.setItem(r, 4, QTableWidgetItem(f"${_safe_float(row.get('MONTO_COBRADO')):.2f}"))
            est_tx = _safe_str(row.get("ESTADO_TRANSACCION"))
            self.table_viajes_tarjeta.setCellWidget(r, 5, StatusBadge(est_tx, self.table_viajes_tarjeta))
        auto_fit_table_columns(self.table_viajes_tarjeta)

        # 2. Recargas
        recargas = m5_cards_service.get_historial_recargas(numero_tarjeta=numero_tarjeta)
        self.table_recargas_tarjeta.clearContents()
        self.table_recargas_tarjeta.setRowCount(len(recargas))
        for r, row in enumerate(recargas):
            self.table_recargas_tarjeta.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("NUMERO_TRANSACCION"))))
            self.table_recargas_tarjeta.setItem(r, 1, QTableWidgetItem(f"${_safe_float(row.get('MONTO')):.2f}"))
            self.table_recargas_tarjeta.setItem(r, 2, QTableWidgetItem(_safe_str(row.get("MEDIO_PAGO"))))
            self.table_recargas_tarjeta.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("ESTACION_CANAL"))))
            self.table_recargas_tarjeta.setItem(r, 4, QTableWidgetItem(f"${_safe_float(row.get('SALDO_ANTERIOR')):.2f}"))
            self.table_recargas_tarjeta.setItem(r, 5, QTableWidgetItem(f"${_safe_float(row.get('SALDO_POSTERIOR')):.2f}"))
            self.table_recargas_tarjeta.setItem(r, 6, QTableWidgetItem(_safe_str(row.get("FECHA_HORA"))))
        auto_fit_table_columns(self.table_recargas_tarjeta)

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
        soporte = str(card.get("TIPO_SOPORTE", "Tarjeta"))
        idx_sop = dlg.combo_tipo_soporte.findData(soporte)
        if idx_sop >= 0:
            dlg.combo_tipo_soporte.setCurrentIndex(idx_sop)
        dlg.combo_tipo_soporte.setEnabled(False)

        pas_id = card.get("PASAJERO_ID")
        if pas_id:
            idx_p = dlg.combo_pasajero.findData(_safe_int(pas_id))
            if idx_p >= 0:
                dlg.combo_pasajero.setCurrentIndex(idx_p)
        else:
            dlg.combo_pasajero.setCurrentIndex(0)
            if num.startswith("MC-ANON-") or num.startswith("MC-") or soporte == "Boleto":
                dlg.combo_pasajero.setEnabled(False)

        tar_id = card.get("TARIFA_ID")
        if tar_id:
            idx_t = dlg.combo_tarifa.findData(_safe_int(tar_id))
            if idx_t >= 0:
                dlg.combo_tarifa.setCurrentIndex(idx_t)

        dlg.spin_saldo.setValue(_safe_float(card.get("SALDO_DISPONIBLE")))
        dlg.spin_saldo.setEnabled(False)
        dlg.set_fecha_vencimiento(card.get("FECHA_VENCIMIENTO"))
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
        if not item_num:
            return
        num = item_num.text()
        card = m5_cards_service.get_tarjeta_by_numero(num)
        if not card:
            return
        est_actual = str(card.get("ESTADO", "Activa"))

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

    def handle_recargar_tarjeta_dialog(self):
        selected = self.table_cards.selectedItems()
        preselected_num = None
        if selected:
            row = selected[0].row()
            item_num = self.table_cards.item(row, 0)
            if item_num:
                preselected_num = item_num.text()

        if preselected_num:
            card_chk = m5_cards_service.get_tarjeta_by_numero(preselected_num)
            if card_chk and (card_chk.get("TIPO_SOPORTE") == "Boleto" or _safe_int(card_chk.get("ES_BOLETO"), 0) == 1):
                InfoBar.warning(
                    title="Operación No Permitida",
                    content="Los boletos de uso único no admiten recargas de saldo (Regla 14 / Modelo OMNY).",
                    parent=self.window(),
                    duration=3500
                )
                return

        all_cards = [
            t for t in m5_cards_service.get_tarjetas()
            if t.get("TIPO_SOPORTE") != "Boleto" and _safe_int(t.get("ES_BOLETO"), 0) != 1
        ]
        if not all_cards:
            InfoBar.warning(title="Sin Tarjetas Recargables", content="No existen tarjetas recargables registradas en el sistema para recargar.", parent=self.window(), duration=3000)
            return

        dlg = RecargaTarjetaDialog(parent=self.window(), tarjetas_list=all_cards, preselected_numero=preselected_num)
        if dlg.exec():
            datos = dlg.get_data()
            res = m5_cards_service.recargar_tarjeta(
                numero_tarjeta=datos["numero_tarjeta"],
                monto=datos["monto"],
                medio_pago=datos["medio_pago"],
                estacion_canal=datos["estacion_canal"]
            )
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
                self.update_tab1_recharge_projection()
            else:
                InfoBar.error(title="Error al Recargar", content=res.get("error", ""), parent=self.window(), duration=4000)

    def handle_eliminar_tarjeta(self):
        selected = self.table_cards.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione una tarjeta o boleto para eliminar.", parent=self.window(), duration=3000)
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
        es_boleto = (card.get("TIPO_SOPORTE") == "Boleto") or bool(card.get("ES_BOLETO"))

        if es_boleto:
            box = MessageBox("Confirmar Eliminación", f"¿Está seguro de que desea eliminar definitivamente el boleto {num}?", self.window())
            if box.exec():
                res = m5_cards_service.eliminar_tarjeta(c_id)
                if res.get("success"):
                    InfoBar.success(title="Boleto Eliminado", content=f"Boleto {num} eliminado correctamente del sistema.", parent=self.window(), duration=3000)
                    self.refresh_cards_list()
                    self.refresh_kpis()
                else:
                    InfoBar.error(title="Error al Eliminar", content=res.get("error", ""), parent=self.window(), duration=4000)
            return

        deps = m5_cards_service.verificar_dependencias_tarjeta(c_id)
        if not deps.get("puede_eliminar", False):
            v_cnt = deps.get("total_viajes", 0)
            r_cnt = deps.get("total_recargas", 0)
            box = MessageBox(
                "Historial Financiero Detectado",
                f"La tarjeta {num} posee {v_cnt} viaje(s) y {r_cnt} recarga(s) registradas.\n\n"
                f"Por integridad de auditoría financiera (Regla 25), no es posible eliminarla físicamente.\n"
                f"¿Desea darla de baja lógica (marcarla como 'Cancelada')?",
                self.window()
            )
            if box.exec():
                res = m5_cards_service.dar_de_baja_tarjeta(c_id)
                if res.get("success"):
                    InfoBar.success(
                        title="Baja Lógica Exitosa",
                        content=f"La tarjeta {num} fue cancelada exitosamente.",
                        parent=self.window(),
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=3500
                    )
                    self.refresh_cards_list()
                    self.refresh_kpis()
                else:
                    InfoBar.error(title="Error", content=res.get("error", ""), parent=self.window(), duration=4000)
            return

        box = MessageBox("Confirmar Eliminación Física", f"¿Está seguro de que desea eliminar definitivamente la tarjeta {num}?", self.window())
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
            
            tipo_p = _safe_str(row.get("TIPO_PASAJERO"))
            self.table_pasajeros.setCellWidget(r, 2, StatusBadge(tipo_p, self.table_pasajeros))

            self.table_pasajeros.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("FECHA_NACIMIENTO"))))
            self.table_pasajeros.setItem(r, 4, QTableWidgetItem(_safe_str(row.get("TELEFONO"))))
            self.table_pasajeros.setItem(r, 5, QTableWidgetItem(_safe_str(row.get("CORREO_ELECTRONICO"))))
            self.table_pasajeros.setItem(r, 6, QTableWidgetItem(_safe_str(row.get("TOTAL_TARJETAS"))))
            
            est_p = _safe_str(row.get("ESTADO"))
            self.table_pasajeros.setCellWidget(r, 7, StatusBadge(est_p, self.table_pasajeros))

        self.table_pasajeros.blockSignals(False)
        auto_fit_table_columns(self.table_pasajeros)

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
        self.table_pasajero_tarjetas.clearContents()
        self.table_pasajero_tarjetas.setRowCount(len(tarjetas))
        for r, row in enumerate(tarjetas):
            self.table_pasajero_tarjetas.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("NUMERO_TARJETA"))))
            
            tar_n = _safe_str(row.get("TARIFA_NOMBRE"))
            self.table_pasajero_tarjetas.setCellWidget(r, 1, StatusBadge(tar_n, self.table_pasajero_tarjetas))

            self.table_pasajero_tarjetas.setItem(r, 2, QTableWidgetItem(f"${_safe_float(row.get('SALDO_DISPONIBLE')):.2f}"))
            self.table_pasajero_tarjetas.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("FECHA_VENCIMIENTO"))))
            
            est_t = _safe_str(row.get("ESTADO"))
            self.table_pasajero_tarjetas.setCellWidget(r, 4, StatusBadge(est_t, self.table_pasajero_tarjetas))
        auto_fit_table_columns(self.table_pasajero_tarjetas)

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
        deps = m5_cards_service.verificar_dependencias_pasajero(p_id)
        if not deps.get("puede_eliminar", False):
            t_cnt = deps.get("total_tarjetas", 0)
            sal_tot = deps.get("saldo_total", 0.0)
            box = MessageBox(
                "Tarjetas Vinculadas Detectadas",
                f"El pasajero {nom} ({ident}) posee {t_cnt} tarjeta(s) vinculada(s) con un saldo acumulado de ${sal_tot:.2f}.\n\n"
                f"No puede eliminarse físicamente sin antes desvincular sus tarjetas.\n"
                f"¿Desea cambiar el estado del pasajero a 'Inactivo'?",
                self.window()
            )
            if box.exec():
                res = m5_cards_service.dar_de_baja_pasajero(p_id)
                if res.get("success"):
                    InfoBar.success(
                        title="Baja Lógica Exitosa",
                        content=f"El pasajero {nom} fue marcado como 'Inactivo'.",
                        parent=self.window(),
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=3500
                    )
                    self.refresh_pasajeros()
                    self.refresh_kpis()
                else:
                    InfoBar.error(title="Error", content=res.get("error", ""), parent=self.window(), duration=4000)
            return

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
            tipo_pas = _safe_str(row.get("TIPO_PASAJERO"))
            self.table_tarifas.setCellWidget(r, 3, StatusBadge(tipo_pas, self.table_tarifas))

            self.table_tarifas.setItem(r, 4, QTableWidgetItem(_safe_str(row.get("FECHA_INICIO"))))
            self.table_tarifas.setItem(r, 5, QTableWidgetItem(_safe_str(row.get("FECHA_FIN"))))
            
            est_tar = _safe_str(row.get("ESTADO"))
            self.table_tarifas.setCellWidget(r, 6, StatusBadge(est_tar, self.table_tarifas))
        auto_fit_table_columns(self.table_tarifas)

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
