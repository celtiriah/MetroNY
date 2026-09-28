"""
m4_staff_interface.py - Vista principal para el Módulo 4: Personal y Turnos.
Cumple estrictamente con los 8 requerimientos del enunciado y las reglas de negocio 9 y 10:
1. Registrar empleados (altas, modificaciones, datos contractuales, salarios).
2. Asignar cargos y estructura jerárquica de supervisión.
3. Registrar certificaciones técnicas asociadas a modelos de tren (CERTIFICACION_MODELO).
4. Programar turnos laborales por fecha, horario, lugar y función operativa.
5. Asignar conductores a viajes programados (VIAJE_PROGRAMADO).
6. Controlar y auditar el vencimiento de certificaciones técnicas.
7. Detectar e impedir traslapes de turnos laborales para un mismo empleado.
8. Registrar ausencias y gestionar sustituciones de personal operativo.
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
    SegmentedWidget, CheckBox, MessageBoxBase, MessageBox, FluentIcon as FIF
)

from services import m4_staff_service
from views.components import (
    StatusBadge, LineColorChip, configure_interactive_table, auto_fit_table_columns
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
# DIALOGOS MODALES FLUENT (MODULO 4)
# ==============================================================================

class EmpleadoDialog(MessageBoxBase):
    """Diálogo modal para registrar o modificar un empleado."""
    def __init__(self, parent=None, emp_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.emp_data = emp_data
        self.es_edicion = emp_data is not None

        titulo = "Modificar Empleado" if self.es_edicion else "Registrar Nuevo Empleado"
        self.titleLabel = SubtitleLabel(titulo, self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        # 1. Nombre Completo
        self.txt_nombre = LineEdit(self)
        self.txt_nombre.setPlaceholderText("p.ej. Robert James Miller")
        if self.es_edicion and self.emp_data:
            self.txt_nombre.setText(_safe_str(self.emp_data.get("NOMBRE_COMPLETO", "")))
        form.addRow("Nombre Completo:", self.txt_nombre)

        # 2. Número de Nómina / Empleado
        self.txt_nomina = LineEdit(self)
        self.txt_nomina.setPlaceholderText("p.ej. EMP-2005 (Opcional, autogenerado si vacío)")
        if self.es_edicion and self.emp_data:
            self.txt_nomina.setText(_safe_str(self.emp_data.get("NUMERO_EMPLEADO", "")))
        form.addRow("N° de Nómina:", self.txt_nomina)

        # 3. Cargo Oficial
        self.combo_cargo = ComboBox(self)
        cargos = [
            "Conductor", "Operador de Control", "Supervisor de Estación",
            "Técnico de Mantenimiento", "Agente de Seguridad", "Personal de Atención al Pasajero"
        ]
        self.combo_cargo.addItems(cargos)
        if self.es_edicion and self.emp_data:
            idx = self.combo_cargo.findText(_safe_str(self.emp_data.get("CARGO", "")))
            if idx >= 0:
                self.combo_cargo.setCurrentIndex(idx)
        form.addRow("Cargo:", self.combo_cargo)

        # 4. Supervisor Directo
        self.combo_supervisor = ComboBox(self)
        self.combo_supervisor.addItem("(Sin Supervisor - Jefatura General)", userData=None)
        supervisores = m4_staff_service.get_supervisores_combo()
        current_sup_id = _safe_int(self.emp_data.get("SUPERVISOR_ID")) if self.es_edicion and self.emp_data else None
        current_emp_id = _safe_int(self.emp_data.get("ID_EMPLEADO")) if self.es_edicion and self.emp_data else None

        target_sup_idx = 0
        sup_counter = 1
        for s in supervisores:
            s_id = _safe_int(s.get("ID_EMPLEADO", 0))
            if current_emp_id and s_id == current_emp_id:
                continue  # No puede ser supervisor de sí mismo
            self.combo_supervisor.addItem(f"{s.get('NOMBRE_COMPLETO', '')} ({s.get('CARGO', '')})", userData=s_id)
            if current_sup_id and s_id == current_sup_id:
                target_sup_idx = sup_counter
            sup_counter += 1
        self.combo_supervisor.setCurrentIndex(target_sup_idx)
        form.addRow("Supervisor Directo:", self.combo_supervisor)

        # 5. Salario Anual (USD)
        self.spin_salario = DoubleSpinBox(self)
        self.spin_salario.setRange(20000.0, 300000.0)
        self.spin_salario.setDecimals(2)
        self.spin_salario.setPrefix("$ ")
        sal_val = _safe_float(self.emp_data.get("SALARIO")) if self.es_edicion and self.emp_data else 62000.0
        self.spin_salario.setValue(sal_val)
        form.addRow("Salario Anual:", self.spin_salario)

        # 6. Turno Habitual
        self.combo_turno = ComboBox(self)
        self.combo_turno.addItems(["Matutino", "Vespertino", "Nocturno", "Mixto"])
        if self.es_edicion and self.emp_data:
            idx = self.combo_turno.findText(_safe_str(self.emp_data.get("TURNO_HABITUAL", "")))
            if idx >= 0:
                self.combo_turno.setCurrentIndex(idx)
        form.addRow("Turno Habitual:", self.combo_turno)

        # 7. Teléfono y Correo Electrónico
        self.txt_tel = LineEdit(self)
        self.txt_tel.setPlaceholderText("+1 (555) 000-0000")
        if self.es_edicion and self.emp_data:
            self.txt_tel.setText(_safe_str(self.emp_data.get("TELEFONO", "")))
        form.addRow("Teléfono:", self.txt_tel)

        self.txt_correo = LineEdit(self)
        self.txt_correo.setPlaceholderText("nombre.apellido@mta.info")
        if self.es_edicion and self.emp_data:
            self.txt_correo.setText(_safe_str(self.emp_data.get("CORREO_ELECTRONICO", "")))
        form.addRow("Correo Electrónico:", self.txt_correo)

        # 8. Dirección
        self.txt_dir = LineEdit(self)
        self.txt_dir.setPlaceholderText("Dirección de residencia...")
        if self.es_edicion and self.emp_data:
            self.txt_dir.setText(_safe_str(self.emp_data.get("DIRECCION", "")))
        form.addRow("Dirección:", self.txt_dir)

        # 9. Fechas
        self.txt_fnac = LineEdit(self)
        self.txt_fnac.setPlaceholderText("YYYY-MM-DD")
        if self.es_edicion and self.emp_data:
            self.txt_fnac.setText(_safe_str(self.emp_data.get("FECHA_NACIMIENTO", "")))
        form.addRow("Fecha Nacimiento:", self.txt_fnac)

        self.txt_fcont = LineEdit(self)
        self.txt_fcont.setPlaceholderText("YYYY-MM-DD")
        if self.es_edicion and self.emp_data:
            self.txt_fcont.setText(_safe_str(self.emp_data.get("FECHA_CONTRATACION", "")))
        form.addRow("Fecha Contratación:", self.txt_fcont)

        # 10. Estado Laboral (solo en creación o visual)
        if not self.es_edicion:
            self.combo_estado = ComboBox(self)
            self.combo_estado.addItems(["Activo", "Permiso", "Vacaciones", "Suspendido"])
            form.addRow("Estado Inicial:", self.combo_estado)

        self.viewLayout.addLayout(form)

        # Etiqueta de aviso / error de validación
        self.lbl_error = CaptionLabel("", self)
        self.lbl_error.setStyleSheet("color: #cf1010; font-weight: 600; padding: 4px 0;")
        self.lbl_error.hide()
        self.viewLayout.addWidget(self.lbl_error)

        self.yesButton.setText("Guardar Empleado" if self.es_edicion else "Registrar Empleado")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(440)

    def validate(self) -> bool:
        """
        Valida rigurosamente los datos del empleado antes de procesar:
        - Nombre completo obligatorio
        - Teléfono de contacto obligatorio (comunicación operativa y de emergencia)
        - Mayoría de edad: fecha de nacimiento obligatoria y mínimo 18 años cumplidos
        - Salario positivo > 0
        - Formatos de fecha YYYY-MM-DD
        """
        nombre = self.txt_nombre.text().strip()
        if not nombre:
            self.lbl_error.setText("El nombre completo del empleado es obligatorio.")
            self.lbl_error.show()
            self.txt_nombre.setFocus()
            return False

        tel = self.txt_tel.text().strip()
        if not tel:
            self.lbl_error.setText("El teléfono de contacto es obligatorio para el personal operativo (emergencias).")
            self.lbl_error.show()
            self.txt_tel.setFocus()
            return False

        correo = self.txt_correo.text().strip()
        if correo and "@" not in correo:
            self.lbl_error.setText("El correo electrónico debe contener un formato válido con '@'.")
            self.lbl_error.show()
            self.txt_correo.setFocus()
            return False

        salario = self.spin_salario.value()
        if salario <= 0.0:
            self.lbl_error.setText("El salario anual debe ser un valor positivo mayor a 0.")
            self.lbl_error.show()
            self.spin_salario.setFocus()
            return False

        fnac_str = self.txt_fnac.text().strip()
        if not fnac_str:
            self.lbl_error.setText("La fecha de nacimiento es obligatoria (formato YYYY-MM-DD).")
            self.lbl_error.show()
            self.txt_fnac.setFocus()
            return False

        try:
            d_nac = datetime.strptime(fnac_str, "%Y-%m-%d").date()
            hoy = date.today()
            edad = hoy.year - d_nac.year - ((hoy.month, hoy.day) < (d_nac.month, d_nac.day))
            if edad < 18:
                self.lbl_error.setText(f"El empleado debe tener al menos 18 años cumplidos (edad calculada: {edad} años).")
                self.lbl_error.show()
                self.txt_fnac.setFocus()
                return False
        except ValueError:
            self.lbl_error.setText("Formato inválido en fecha de nacimiento. Utilice YYYY-MM-DD.")
            self.lbl_error.show()
            self.txt_fnac.setFocus()
            return False

        fcont_str = self.txt_fcont.text().strip()
        if fcont_str:
            try:
                datetime.strptime(fcont_str, "%Y-%m-%d")
            except ValueError:
                self.lbl_error.setText("Formato inválido en fecha de contratación. Utilice YYYY-MM-DD.")
                self.lbl_error.show()
                self.txt_fcont.setFocus()
                return False

        self.lbl_error.hide()
        return True

    def get_data(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "nombre_completo": self.txt_nombre.text().strip(),
            "numero_empleado": self.txt_nomina.text().strip() or None,
            "cargo": self.combo_cargo.currentText(),
            "supervisor_id": self.combo_supervisor.currentData(),
            "salario": self.spin_salario.value(),
            "turno_habitual": self.combo_turno.currentText(),
            "telefono": self.txt_tel.text().strip() or None,
            "correo_electronico": self.txt_correo.text().strip() or None,
            "direccion": self.txt_dir.text().strip() or None,
            "fecha_nacimiento": self.txt_fnac.text().strip() or None,
            "fecha_contratacion": self.txt_fcont.text().strip() or None,
        }
        if not self.es_edicion and hasattr(self, "combo_estado"):
            data["estado_laboral"] = self.combo_estado.currentText()
        return data


class CertificacionDialog(MessageBoxBase):
    """Diálogo modal para registrar o modificar una certificación técnica."""
    def __init__(self, parent=None, cert_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.cert_data = cert_data
        self.es_edicion = cert_data is not None

        titulo = "Modificar Certificación" if self.es_edicion else "Nueva Certificación Técnica"
        self.titleLabel = SubtitleLabel(titulo, self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        # 1. Empleado Titular
        self.combo_emp = ComboBox(self)
        empleados = m4_staff_service.get_empleados()
        current_emp_id = _safe_int(self.cert_data.get("EMPLEADO_ID")) if self.es_edicion and self.cert_data else None
        target_idx = 0
        for i, e in enumerate(empleados):
            e_id = _safe_int(e.get("ID_EMPLEADO", 0))
            label = f"{e.get('NOMBRE_COMPLETO', '')} ({e.get('CARGO', '')})"
            self.combo_emp.addItem(label, userData=e_id)
            if current_emp_id and e_id == current_emp_id:
                target_idx = i
        if empleados:
            self.combo_emp.setCurrentIndex(target_idx)
        form.addRow("Empleado Titular:", self.combo_emp)

        # 2. Tipo de Certificación
        self.combo_tipo = ComboBox(self)
        tipos_predef = [
            "Licencia Conducción Clase A Subterráneo",
            "Licencia Conducción Clase B Subterráneo",
            "Certificación en Señalización Ferroviaria CBTC",
            "Especialista en Sistemas Neumáticos y Frenos",
            "Certificación en Alta Tensión y Tercer Riel",
            "Inspector de Seguridad Operativa y Vías"
        ]
        self.combo_tipo.addItems(tipos_predef)
        if self.es_edicion and self.cert_data:
            idx = self.combo_tipo.findText(_safe_str(self.cert_data.get("TIPO_CERTIFICACION", "")))
            if idx >= 0:
                self.combo_tipo.setCurrentIndex(idx)
        form.addRow("Tipo de Certificación:", self.combo_tipo)

        # 3. Fechas de Emisión y Vencimiento
        self.txt_f_emi = LineEdit(self)
        self.txt_f_emi.setPlaceholderText("YYYY-MM-DD")
        emi_val = _safe_str(self.cert_data.get("FECHA_EMISION", "")) if self.es_edicion and self.cert_data else date.today().strftime("%Y-%m-%d")
        self.txt_f_emi.setText(emi_val)
        form.addRow("Fecha Emisión:", self.txt_f_emi)

        self.txt_f_venc = LineEdit(self)
        self.txt_f_venc.setPlaceholderText("YYYY-MM-DD")
        if self.es_edicion and self.cert_data:
            self.txt_f_venc.setText(_safe_str(self.cert_data.get("FECHA_VENCIMIENTO", "")))
        form.addRow("Fecha Vencimiento:", self.txt_f_venc)

        # 4. Institución Emisora
        self.txt_inst = LineEdit(self)
        self.txt_inst.setPlaceholderText("p.ej. MTA Training Academy")
        inst_val = _safe_str(self.cert_data.get("INSTITUCION_EMISORA", "MTA Training Academy")) if self.es_edicion and self.cert_data else "MTA Training Academy"
        self.txt_inst.setText(inst_val)
        form.addRow("Institución Emisora:", self.txt_inst)

        # 5. Estado
        self.combo_estado = ComboBox(self)
        self.combo_estado.addItems(["Vigente", "Vencida", "Revocada"])
        if self.es_edicion and self.cert_data:
            idx = self.combo_estado.findText(_safe_str(self.cert_data.get("ESTADO", "Vigente")))
            if idx >= 0:
                self.combo_estado.setCurrentIndex(idx)
        form.addRow("Estado:", self.combo_estado)

        self.viewLayout.addLayout(form)

        # 6. Modelos de Tren Habilitados (Checkboxes)
        self.viewLayout.addWidget(CaptionLabel("Modelos de Tren Habilitados (Para Maquinistas):", self))
        self.chk_modelos: Dict[int, CheckBox] = {}
        modelos_layout = QHBoxLayout()
        modelos = [
            (1, "R142 (Bombardier)"),
            (2, "R160 (Alstom/Kawasaki)"),
            (3, "R179 (Bombardier)"),
            (4, "R211 (Kawasaki)")
        ]
        mod_activos_str = _safe_str(self.cert_data.get("MODELOS_HABILITADOS", "")) if self.es_edicion and self.cert_data else ""
        for m_id, m_nombre in modelos:
            chk = CheckBox(m_nombre, self)
            if self.es_edicion and m_nombre.split(" ")[0] in mod_activos_str:
                chk.setChecked(True)
            self.chk_modelos[m_id] = chk
            modelos_layout.addWidget(chk)
        self.viewLayout.addLayout(modelos_layout)

        # Etiqueta de aviso / error de validación
        self.lbl_error = CaptionLabel("", self)
        self.lbl_error.setStyleSheet("color: #cf1010; font-weight: 600; padding: 4px 0;")
        self.lbl_error.hide()
        self.viewLayout.addWidget(self.lbl_error)

        self.yesButton.setText("Guardar Certificación" if self.es_edicion else "Registrar Certificación")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(440)

    def validate(self) -> bool:
        """
        Valida que la certificación cumpla con las reglas operativas y de integridad:
        - Empleado seleccionado
        - Fechas válidas y fecha_vencimiento >= fecha_emision
        - Inmutabilidad de fechas en certificaciones vencidas o revocadas
        """
        if self.combo_emp.currentData() is None:
            self.lbl_error.setText("Debe seleccionar un empleado titular de la certificación.")
            self.lbl_error.show()
            self.combo_emp.setFocus()
            return False

        tipo = self.combo_tipo.currentText().strip()
        if not tipo:
            self.lbl_error.setText("El tipo de certificación técnica es obligatorio.")
            self.lbl_error.show()
            return False

        f_emi_str = self.txt_f_emi.text().strip()
        f_venc_str = self.txt_f_venc.text().strip()

        if not f_emi_str:
            self.lbl_error.setText("La fecha de emisión es obligatoria (formato YYYY-MM-DD).")
            self.lbl_error.show()
            self.txt_f_emi.setFocus()
            return False

        if not f_venc_str:
            self.lbl_error.setText("La fecha de vencimiento es obligatoria (formato YYYY-MM-DD).")
            self.lbl_error.show()
            self.txt_f_venc.setFocus()
            return False

        try:
            d_emi = datetime.strptime(f_emi_str, "%Y-%m-%d").date()
        except ValueError:
            self.lbl_error.setText("Formato inválido en fecha de emisión. Utilice YYYY-MM-DD.")
            self.lbl_error.show()
            self.txt_f_emi.setFocus()
            return False

        try:
            d_venc = datetime.strptime(f_venc_str, "%Y-%m-%d").date()
        except ValueError:
            self.lbl_error.setText("Formato inválido en fecha de vencimiento. Utilice YYYY-MM-DD.")
            self.lbl_error.show()
            self.txt_f_venc.setFocus()
            return False

        if d_venc < d_emi:
            self.lbl_error.setText("La fecha de vencimiento no puede ser anterior a la fecha de emisión.")
            self.lbl_error.show()
            self.txt_f_venc.setFocus()
            return False

        # Inmutabilidad de fechas en histórico vencido o revocado
        if self.es_edicion and self.cert_data:
            est_orig = str(self.cert_data.get("ESTADO", ""))
            if est_orig in ("Vencida", "Revocada"):
                emi_orig = str(self.cert_data.get("FECHA_EMISION", ""))
                venc_orig = str(self.cert_data.get("FECHA_VENCIMIENTO", ""))
                if (f_emi_str != emi_orig) or (f_venc_str != venc_orig):
                    self.lbl_error.setText(
                        f"Operación rechazada: No se permite modificar las fechas de una certificación en estado '{est_orig}' (registro histórico inmutable)."
                    )
                    self.lbl_error.show()
                    return False

        self.lbl_error.hide()
        return True

    def get_data(self) -> Dict[str, Any]:
        return {
            "empleado_id": self.combo_emp.currentData(),
            "tipo_certificacion": self.combo_tipo.currentText(),
            "fecha_emision": self.txt_f_emi.text().strip() or None,
            "fecha_vencimiento": self.txt_f_venc.text().strip() or None,
            "institucion_emisora": self.txt_inst.text().strip(),
            "estado": self.combo_estado.currentText()
        }

    def get_modelos_ids(self) -> List[int]:
        return [m_id for m_id, chk in self.chk_modelos.items() if chk.isChecked()]


class TurnoDialog(MessageBoxBase):
    """Diálogo modal para programar o modificar un turno laboral."""
    def __init__(self, parent=None, turno_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.turno_data = turno_data
        self.es_edicion = turno_data is not None

        titulo = "Modificar Turno" if self.es_edicion else "Programar Turno Laboral"
        self.titleLabel = SubtitleLabel(titulo, self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        self.viewLayout.addWidget(CaptionLabel(
            "El sistema valida automáticamente que no existan traslapes horarios\n"
            "para el empleado seleccionado en la fecha establecida.", self
        ))

        form = QFormLayout()
        form.setSpacing(8)

        # 1. Empleado
        self.combo_emp = ComboBox(self)
        empleados = m4_staff_service.get_empleados(estado_filter="Activo")
        current_emp_id = _safe_int(self.turno_data.get("EMPLEADO_ID")) if self.es_edicion and self.turno_data else None
        target_idx = 0
        for i, e in enumerate(empleados):
            e_id = _safe_int(e.get("ID_EMPLEADO", 0))
            label = f"{e.get('NOMBRE_COMPLETO', '')} ({e.get('CARGO', '')})"
            self.combo_emp.addItem(label, userData=e_id)
            if current_emp_id and e_id == current_emp_id:
                target_idx = i
        if empleados:
            self.combo_emp.setCurrentIndex(target_idx)
        form.addRow("Empleado Asignado:", self.combo_emp)

        # 2. Fecha del Turno
        self.txt_fecha = LineEdit(self)
        self.txt_fecha.setPlaceholderText("YYYY-MM-DD")
        f_val = _safe_str(self.turno_data.get("FECHA", "")) if self.es_edicion and self.turno_data else date.today().strftime("%Y-%m-%d")
        self.txt_fecha.setText(f_val)
        form.addRow("Fecha del Turno:", self.txt_fecha)

        # 3. Horas de Inicio y Fin
        self.txt_h_ini = LineEdit(self)
        self.txt_h_ini.setPlaceholderText("HH:MI (p.ej. 06:00)")
        h_ini_val = _safe_str(self.turno_data.get("HORA_INICIO", "06:00")) if self.es_edicion and self.turno_data else "06:00"
        self.txt_h_ini.setText(h_ini_val)
        form.addRow("Hora Inicio:", self.txt_h_ini)

        self.txt_h_fin = LineEdit(self)
        self.txt_h_fin.setPlaceholderText("HH:MI (p.ej. 14:00)")
        h_fin_val = _safe_str(self.turno_data.get("HORA_FIN", "14:00")) if self.es_edicion and self.turno_data else "14:00"
        self.txt_h_fin.setText(h_fin_val)
        form.addRow("Hora Fin:", self.txt_h_fin)

        # 4. Tipo de Lugar y Función
        self.combo_lugar = ComboBox(self)
        lugares = ["Estación", "Depósito", "Tren", "Centro de Control", "Ruta"]
        self.combo_lugar.addItems(lugares)
        if self.es_edicion and self.turno_data:
            idx = self.combo_lugar.findText(_safe_str(self.turno_data.get("TIPO_LUGAR", "")))
            if idx >= 0:
                self.combo_lugar.setCurrentIndex(idx)
        form.addRow("Tipo de Lugar:", self.combo_lugar)

        self.txt_funcion = LineEdit(self)
        self.txt_funcion.setPlaceholderText("p.ej. Conducción Línea 1, Supervisión Andenes...")
        func_val = _safe_str(self.turno_data.get("FUNCION", "Servicio Operativo")) if self.es_edicion and self.turno_data else "Servicio Operativo"
        self.txt_funcion.setText(func_val)
        form.addRow("Función Operativa:", self.txt_funcion)

        # 5. Estado de Asistencia
        self.combo_asistencia = ComboBox(self)
        estados_asist = ["Programado", "Presente", "Ausente", "Permiso", "Vacaciones"]
        self.combo_asistencia.addItems(estados_asist)
        if self.es_edicion and self.turno_data:
            idx = self.combo_asistencia.findText(_safe_str(self.turno_data.get("ESTADO_ASISTENCIA", "Programado")))
            if idx >= 0:
                self.combo_asistencia.setCurrentIndex(idx)
        form.addRow("Estado Asistencia:", self.combo_asistencia)

        self.viewLayout.addLayout(form)

        # Etiqueta de aviso / error de validación
        self.lbl_error = CaptionLabel("", self)
        self.lbl_error.setStyleSheet("color: #cf1010; font-weight: 600; padding: 4px 0;")
        self.lbl_error.hide()
        self.viewLayout.addWidget(self.lbl_error)

        self.yesButton.setText("Guardar Turno" if self.es_edicion else "Programar Turno")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(440)

    def validate(self) -> bool:
        """
        Valida que el turno programado cumpla con los estándares de seguridad y descanso:
        - Empleado seleccionado
        - Fecha válida
        - Horas válidas y hora_fin > hora_inicio
        - Duración continua máxima de 16 horas
        - Ausencia de traslapes con otros turnos del mismo empleado
        """
        emp_id = self.combo_emp.currentData()
        if emp_id is None:
            self.lbl_error.setText("Debe seleccionar un empleado para programar el turno.")
            self.lbl_error.show()
            self.combo_emp.setFocus()
            return False

        f_str = self.txt_fecha.text().strip()
        if not f_str:
            self.lbl_error.setText("La fecha del turno es obligatoria (formato YYYY-MM-DD).")
            self.lbl_error.show()
            self.txt_fecha.setFocus()
            return False

        try:
            datetime.strptime(f_str, "%Y-%m-%d")
        except ValueError:
            self.lbl_error.setText("Formato inválido en fecha de turno. Utilice YYYY-MM-DD.")
            self.lbl_error.show()
            self.txt_fecha.setFocus()
            return False

        h_ini_str = self.txt_h_ini.text().strip()
        h_fin_str = self.txt_h_fin.text().strip()

        if not h_ini_str or not h_fin_str:
            self.lbl_error.setText("Las horas de inicio y fin son obligatorias (formato HH:MI).")
            self.lbl_error.show()
            return False

        try:
            t_ini = datetime.strptime(h_ini_str, "%H:%M")
            t_fin = datetime.strptime(h_fin_str, "%H:%M")
        except ValueError:
            self.lbl_error.setText("Formato inválido en horas del turno. Utilice formato HH:MI (ej. 08:30).")
            self.lbl_error.show()
            return False

        if t_fin <= t_ini:
            self.lbl_error.setText("La hora de fin debe ser posterior a la hora de inicio (no se permiten turnos invertidos).")
            self.lbl_error.show()
            self.txt_h_fin.setFocus()
            return False

        duracion_horas = (t_fin - t_ini).total_seconds() / 3600.0
        if duracion_horas > 16.0:
            self.lbl_error.setText(f"La duración ({duracion_horas:.1f} h) excede el límite máximo de 16 horas continuas (normativa MTA).")
            self.lbl_error.show()
            self.txt_h_fin.setFocus()
            return False

        excl_id = _safe_int(self.turno_data.get("ID_TURNO")) if self.es_edicion and self.turno_data else None
        conflicto = m4_staff_service.validar_traslape_turno(int(emp_id), f_str, h_ini_str, h_fin_str, excluir_id_turno=excl_id)
        if conflicto:
            self.lbl_error.setText(
                f"Conflicto de traslape: El empleado ya tiene asignado el turno {conflicto.get('CODIGO_TURNO', '')} "
                f"({conflicto.get('INI', '')} - {conflicto.get('FIN', '')}) en esa misma franja."
            )
            self.lbl_error.show()
            return False

        self.lbl_error.hide()
        return True

    def get_data(self) -> Dict[str, Any]:
        return {
            "empleado_id": self.combo_emp.currentData(),
            "fecha": self.txt_fecha.text().strip(),
            "hora_inicio": self.txt_h_ini.text().strip(),
            "hora_fin": self.txt_h_fin.text().strip(),
            "tipo_lugar": self.combo_lugar.currentText(),
            "funcion": self.txt_funcion.text().strip(),
            "estado_asistencia": self.combo_asistencia.currentText()
        }


class AsistenciaDialog(MessageBoxBase):
    """Diálogo modal para registrar asistencia rápida de un turno."""
    def __init__(self, cod_turno: str, nom_emp: str, est_actual: str, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(f"Registrar Asistencia: {cod_turno}", self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        form.addRow("Empleado:", StrongBodyLabel(nom_emp, self))
        form.addRow("Estado Actual:", CaptionLabel(est_actual, self))

        self.combo_nuevo = ComboBox(self)
        self.combo_nuevo.addItems(["Presente", "Ausente", "Permiso", "Vacaciones", "Programado"])
        idx = self.combo_nuevo.findText(est_actual)
        if idx >= 0:
            self.combo_nuevo.setCurrentIndex(idx)
        form.addRow("Nuevo Estado:", self.combo_nuevo)

        self.viewLayout.addLayout(form)

        self.yesButton.setText("Actualizar Asistencia")
        self.cancelButton.setText("Cancelar")

    def get_nuevo_estado(self) -> str:
        return self.combo_nuevo.currentText()


class SustitucionDialog(MessageBoxBase):
    """Diálogo modal para gestionar la sustitución de un empleado ausente."""
    def __init__(self, cod_turno: str, titular_nombre: str, fecha: str, horario: str, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(f"Gestionar Sustitución: {cod_turno}", self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        self.viewLayout.addWidget(CaptionLabel(
            f"Titular Ausente: {titular_nombre}\n"
            f"Fecha y Horario: {fecha} ({horario})\n"
            "El sistema validará que el sustituto esté activo y sin traslapes en ese horario.", self
        ))

        form = QFormLayout()
        form.setSpacing(8)

        self.combo_sustituto = ComboBox(self)
        empleados = m4_staff_service.get_empleados(estado_filter="Activo")
        for e in empleados:
            e_id = _safe_int(e.get("ID_EMPLEADO", 0))
            nom = e.get("NOMBRE_COMPLETO", "")
            cargo = e.get("CARGO", "")
            if nom != titular_nombre:
                self.combo_sustituto.addItem(f"{nom} ({cargo})", userData=e_id)
        form.addRow("Empleado Sustituto:", self.combo_sustituto)

        self.viewLayout.addLayout(form)

        self.yesButton.setText("Confirmar Sustitución")
        self.cancelButton.setText("Cancelar")

    def get_sustituto_id(self) -> Optional[int]:
        return self.combo_sustituto.currentData()


class AsignarConductorViajeDialog(MessageBoxBase):
    """Diálogo modal para asignar maquinista a un viaje cumpliendo Reglas 9 y 10."""
    def __init__(self, id_viaje: int, num_viaje: str, conductores_disponibles: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.id_viaje = id_viaje
        self.titleLabel = SubtitleLabel(f"Asignar Conductor a Viaje {num_viaje}", self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.setSpacing(10)

        self.viewLayout.addWidget(CaptionLabel(
            "Reglas Validadas:\n"
            "- Regla 10: Maquinistas con certificación técnica vigente (TRG_CERTIFICACION_ALERTA_VENCIDA).\n"
            "- Regla 9: Maquinistas sin viajes simultáneos solapados en esa fecha y horario.", self
        ))

        form = QFormLayout()
        form.setSpacing(8)

        self.combo_cond = ComboBox(self)
        if not conductores_disponibles:
            self.combo_cond.addItem("(No hay conductores certificados disponibles sin conflicto)", userData=None)
        else:
            for c in conductores_disponibles:
                c_id = _safe_int(c.get("ID_EMPLEADO", 0))
                nom = c.get("NOMBRE_COMPLETO", "")
                lic = c.get("TIPO_CERTIFICACION", "")
                vence = c.get("VENCE_LICENCIA", "")
                self.combo_cond.addItem(f"{nom} - Lic: {lic} (Vence: {vence})", userData=c_id)
        form.addRow("Conductor Habilitado:", self.combo_cond)

        self.viewLayout.addLayout(form)

        self.yesButton.setText("Asignar Conductor")
        self.cancelButton.setText("Cancelar")
        if not conductores_disponibles:
            self.yesButton.setEnabled(False)

    def get_selected_conductor_id(self) -> Optional[int]:
        return self.combo_cond.currentData()


# ==============================================================================
# VISTA PRINCIPAL (MODULO 4: PERSONAL Y TURNOS)
# ==============================================================================

class StaffInterface(QWidget):
    """
    Vista principal para el Módulo 4: Personal y Turnos.
    Dispone el título en su propio CardWidget y las pestañas en un contenedor independiente
    de ancho completo.
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("staffInterface")

        self.selected_empleado_id: Optional[int] = None
        self.selected_empleado_nombre: str = ""
        self.empleados_cache: List[Dict[str, Any]] = []
        self.certificaciones_cache: List[Dict[str, Any]] = []
        self.turnos_cache: List[Dict[str, Any]] = []

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

        title = TitleLabel("Personal Operativo y Turnos", header_card)
        subtitle = SubtitleLabel("Modulo 4: Gestion de empleados MTA, jerarquia, certificaciones tecnicas, turnos y despacho", header_card)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        main_layout.addWidget(header_card)

        # ----------------------------------------------------------------------
        # 2. CONTENEDOR INDEPENDIENTE DE PESTANAS (SEGMENTED WIDGET DE ANCHO COMPLETO)
        # ----------------------------------------------------------------------
        tabs_layout = QHBoxLayout()
        self.segmented_tabs = SegmentedWidget(self)
        self.segmented_tabs.addItem("tab_empleados", "Directorio y Gestión de Empleados")
        self.segmented_tabs.addItem("tab_certificaciones", "Certificaciones y Licencias Técnicas")
        self.segmented_tabs.addItem("tab_turnos", "Programación de Turnos y Asistencia")
        self.segmented_tabs.addItem("tab_viajes", "Asignación de Conductores a Viajes")

        self.segmented_tabs.setCurrentItem("tab_empleados")
        self.segmented_tabs.currentItemChanged.connect(self.on_tab_changed)

        tabs_layout.addWidget(self.segmented_tabs)
        main_layout.addLayout(tabs_layout)

        # ----------------------------------------------------------------------
        # 3. STACKED WIDGET PARA LAS VISTAS
        # ----------------------------------------------------------------------
        self.stack_views = QStackedWidget(self)

        self.init_tab_empleados()
        self.init_tab_certificaciones()
        self.init_tab_turnos()
        self.init_tab_viajes()

        main_layout.addWidget(self.stack_views, stretch=1)

    # ==========================================================================
    # PESTANA 1: DIRECTORIO Y GESTION DE EMPLEADOS
    # ==========================================================================

    def init_tab_empleados(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(10)

        bar_actions = QHBoxLayout()
        bar_actions.setSpacing(8)

        self.search_empleados = SearchLineEdit(tab_widget)
        self.search_empleados.setPlaceholderText("Buscar por nombre, nómina, teléfono o cargo...")
        self.search_empleados.textChanged.connect(self.apply_empleados_filter)
        bar_actions.addWidget(self.search_empleados, stretch=3)

        bar_actions.addWidget(CaptionLabel("Cargo:", tab_widget))
        self.combo_filtro_cargo = ComboBox(tab_widget)
        self.combo_filtro_cargo.addItems([
            "(Todos)", "Conductor", "Operador de Control", "Supervisor de Estación",
            "Técnico de Mantenimiento", "Agente de Seguridad", "Personal de Atención al Pasajero"
        ])
        self.combo_filtro_cargo.currentTextChanged.connect(self.refresh_empleados)
        bar_actions.addWidget(self.combo_filtro_cargo, stretch=2)

        bar_actions.addWidget(CaptionLabel("Estado Laboral:", tab_widget))
        self.combo_filtro_estado_lab = ComboBox(tab_widget)
        self.combo_filtro_estado_lab.addItems(["(Todos)", "Activo", "Permiso", "Vacaciones", "Suspendido", "Retirado"])
        self.combo_filtro_estado_lab.currentTextChanged.connect(self.refresh_empleados)
        bar_actions.addWidget(self.combo_filtro_estado_lab, stretch=2)

        self.btn_nuevo_emp = PrimaryPushButton("Nuevo Empleado", tab_widget, FIF.ADD)
        self.btn_nuevo_emp.clicked.connect(self.handle_nuevo_empleado)
        bar_actions.addWidget(self.btn_nuevo_emp)

        self.btn_modificar_emp = PushButton("Modificar", tab_widget, FIF.EDIT)
        self.btn_modificar_emp.clicked.connect(self.handle_modificar_empleado)
        bar_actions.addWidget(self.btn_modificar_emp)

        self.btn_estado_emp = PushButton("Cambiar Estado", tab_widget, FIF.SYNC)
        self.btn_estado_emp.clicked.connect(self.handle_cambiar_estado_empleado)
        bar_actions.addWidget(self.btn_estado_emp)

        self.btn_eliminar_emp = PushButton("Eliminar", tab_widget, FIF.DELETE)
        self.btn_eliminar_emp.clicked.connect(self.handle_eliminar_empleado)
        bar_actions.addWidget(self.btn_eliminar_emp)

        v_layout.addLayout(bar_actions)

        # Tabla Maestra de Empleados
        self.table_empleados = TableWidget(tab_widget)
        self.table_empleados.setBorderVisible(True)
        self.table_empleados.setColumnCount(10)
        self.table_empleados.setHorizontalHeaderLabels([
            "N° Nómina", "Nombre Completo", "Cargo", "Turno", "Supervisor Directo",
            "Salario", "Teléfono", "Correo MTA", "Estado Laboral", "Licencia / Certificación"
        ])
        configure_interactive_table(self.table_empleados, min_col_width=75)
        self.table_empleados.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_empleados.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table_empleados.itemSelectionChanged.connect(self.on_empleado_selected)
        v_layout.addWidget(self.table_empleados, stretch=4)

        # Panel Inferior: Historial de Actividades Operativas y Jerarquía
        card_bottom = CardWidget(tab_widget)
        bottom_layout = QVBoxLayout(card_bottom)
        bottom_layout.setContentsMargins(16, 12, 16, 12)
        bottom_layout.setSpacing(8)

        self.lbl_bottom_title = StrongBodyLabel("Historial Operativo y Jerarquía del Empleado Seleccionado", card_bottom)
        bottom_layout.addWidget(self.lbl_bottom_title)

        self.seg_emp_detail = SegmentedWidget(card_bottom)
        self.seg_emp_detail.addItem("subtab_actividades", "Historial de Actividades (Turnos y Viajes)")
        self.seg_emp_detail.addItem("subtab_subordinados", "Equipo de Subordinados Directos")
        self.seg_emp_detail.setCurrentItem("subtab_actividades")
        self.seg_emp_detail.currentItemChanged.connect(self.on_emp_detail_tab_changed)
        bottom_layout.addWidget(self.seg_emp_detail)

        self.stack_emp_detail = QStackedWidget(card_bottom)

        # Sub-pestaña 1: Actividades y turnos del empleado
        page_act = QWidget(self.stack_emp_detail)
        v_act = QVBoxLayout(page_act)
        v_act.setContentsMargins(0, 4, 0, 0)
        self.table_actividades = TableWidget(page_act)
        self.table_actividades.setBorderVisible(True)
        self.table_actividades.setColumnCount(6)
        self.table_actividades.setHorizontalHeaderLabels([
            "Tipo Actividad", "Identificador", "Fecha", "Horario", "Detalle / Asignación", "Estado"
        ])
        configure_interactive_table(self.table_actividades, min_col_width=75)
        self.table_actividades.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_actividades.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        v_act.addWidget(self.table_actividades)
        self.stack_emp_detail.addWidget(page_act)

        # Sub-pestaña 2: Subordinados directos
        page_sub = QWidget(self.stack_emp_detail)
        v_sub = QVBoxLayout(page_sub)
        v_sub.setContentsMargins(0, 4, 0, 0)
        self.table_subordinados = TableWidget(page_sub)
        self.table_subordinados.setBorderVisible(True)
        self.table_subordinados.setColumnCount(5)
        self.table_subordinados.setHorizontalHeaderLabels([
            "N° Nómina", "Nombre del Subordinado", "Cargo", "Estado Laboral", "Vínculo de Supervisión"
        ])
        configure_interactive_table(self.table_subordinados, min_col_width=75)
        self.table_subordinados.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_subordinados.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        v_sub.addWidget(self.table_subordinados)
        self.stack_emp_detail.addWidget(page_sub)

        bottom_layout.addWidget(self.stack_emp_detail)

        v_layout.addWidget(card_bottom, stretch=3)
        self.stack_views.addWidget(tab_widget)

    # ==========================================================================
    # PESTANA 2: CERTIFICACIONES Y LICENCIAS TECNICAS
    # ==========================================================================

    def init_tab_certificaciones(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(10)

        bar_actions = QHBoxLayout()
        bar_actions.setSpacing(8)

        bar_actions.addWidget(CaptionLabel("Filtrar Estado:", tab_widget))
        self.combo_filtro_cert_est = ComboBox(tab_widget)
        self.combo_filtro_cert_est.addItems(["(Todos)", "Vigente", "Vencida", "Revocada"])
        self.combo_filtro_cert_est.currentTextChanged.connect(self.refresh_certificaciones)
        bar_actions.addWidget(self.combo_filtro_cert_est, stretch=2)

        bar_actions.addWidget(CaptionLabel("Empleado:", tab_widget))
        self.combo_filtro_cert_emp = ComboBox(tab_widget)
        self.combo_filtro_cert_emp.addItem("(Todos los Empleados)", userData=None)
        self.combo_filtro_cert_emp.currentIndexChanged.connect(self.refresh_certificaciones)
        bar_actions.addWidget(self.combo_filtro_cert_emp, stretch=3)

        self.btn_nueva_cert = PrimaryPushButton("Nueva Certificación", tab_widget, FIF.ADD)
        self.btn_nueva_cert.clicked.connect(self.handle_nueva_certificacion)
        bar_actions.addWidget(self.btn_nueva_cert)

        self.btn_modificar_cert = PushButton("Modificar", tab_widget, FIF.EDIT)
        self.btn_modificar_cert.clicked.connect(self.handle_modificar_certificacion)
        bar_actions.addWidget(self.btn_modificar_cert)

        self.btn_auditar_venc = PushButton("Auditar Vencimientos", tab_widget, FIF.ACCEPT)
        self.btn_auditar_venc.clicked.connect(self.handle_auditar_vencimientos)
        bar_actions.addWidget(self.btn_auditar_venc)

        self.btn_eliminar_cert = PushButton("Eliminar", tab_widget, FIF.DELETE)
        self.btn_eliminar_cert.clicked.connect(self.handle_eliminar_certificacion)
        bar_actions.addWidget(self.btn_eliminar_cert)

        v_layout.addLayout(bar_actions)

        # Tabla Maestra de Certificaciones
        self.table_certificaciones = TableWidget(tab_widget)
        self.table_certificaciones.setBorderVisible(True)
        self.table_certificaciones.setColumnCount(9)
        self.table_certificaciones.setHorizontalHeaderLabels([
            "ID", "Nómina", "Empleado", "Cargo", "Tipo Certificación / Licencia",
            "Modelos de Tren Habilitados", "Fecha Emisión", "Fecha Vencimiento", "Estado"
        ])
        configure_interactive_table(self.table_certificaciones, min_col_width=75)
        self.table_certificaciones.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_certificaciones.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        v_layout.addWidget(self.table_certificaciones)

        self.stack_views.addWidget(tab_widget)

    # ==========================================================================
    # PESTANA 3: PROGRAMACION DE TURNOS Y ASISTENCIA
    # ==========================================================================

    def init_tab_turnos(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(10)

        # Fila 1: Filtros de consulta global
        bar_filters = QHBoxLayout()
        bar_filters.setSpacing(8)

        bar_filters.addWidget(CaptionLabel("Empleado:", tab_widget))
        self.combo_filtro_turno_emp = ComboBox(tab_widget)
        self.combo_filtro_turno_emp.addItem("(Todos los Empleados)", userData=None)
        self.combo_filtro_turno_emp.currentIndexChanged.connect(self.refresh_turnos)
        bar_filters.addWidget(self.combo_filtro_turno_emp, stretch=3)

        bar_filters.addWidget(CaptionLabel("Período:", tab_widget))
        self.combo_filtro_turno_tiempo = ComboBox(tab_widget)
        self.combo_filtro_turno_tiempo.addItems(["(Todos)", "Hoy", "Próximos 7 días", "Histórico (Pasados)"])
        self.combo_filtro_turno_tiempo.currentTextChanged.connect(self.refresh_turnos)
        bar_filters.addWidget(self.combo_filtro_turno_tiempo, stretch=2)

        bar_filters.addWidget(CaptionLabel("Lugar:", tab_widget))
        self.combo_filtro_turno_lugar = ComboBox(tab_widget)
        self.combo_filtro_turno_lugar.addItems(["(Todos)", "Estación", "Depósito", "Tren", "Centro de Control", "Ruta"])
        self.combo_filtro_turno_lugar.currentTextChanged.connect(self.refresh_turnos)
        bar_filters.addWidget(self.combo_filtro_turno_lugar, stretch=2)

        bar_filters.addWidget(CaptionLabel("Asistencia:", tab_widget))
        self.combo_filtro_turno_asist = ComboBox(tab_widget)
        self.combo_filtro_turno_asist.addItems(["(Todos)", "Programado", "Presente", "Ausente", "Permiso", "Vacaciones", "Sustituido"])
        self.combo_filtro_turno_asist.currentTextChanged.connect(self.refresh_turnos)
        bar_filters.addWidget(self.combo_filtro_turno_asist, stretch=2)

        v_layout.addLayout(bar_filters)

        # Fila 2: Acciones operativas
        bar_actions = QHBoxLayout()
        bar_actions.setSpacing(8)

        self.btn_nuevo_turno = PrimaryPushButton("Programar Turno", tab_widget, FIF.ADD)
        self.btn_nuevo_turno.clicked.connect(self.handle_nuevo_turno)
        bar_actions.addWidget(self.btn_nuevo_turno)

        self.btn_modificar_turno = PushButton("Modificar Turno", tab_widget, FIF.EDIT)
        self.btn_modificar_turno.clicked.connect(self.handle_modificar_turno)
        bar_actions.addWidget(self.btn_modificar_turno)

        self.btn_asistencia_turno = PushButton("Registrar Asistencia", tab_widget, FIF.COMPLETED)
        self.btn_asistencia_turno.clicked.connect(self.handle_registrar_asistencia)
        bar_actions.addWidget(self.btn_asistencia_turno)

        self.btn_sustitucion_turno = PushButton("Sustitución", tab_widget, FIF.PEOPLE)
        self.btn_sustitucion_turno.clicked.connect(self.handle_sustitucion_turno)
        bar_actions.addWidget(self.btn_sustitucion_turno)

        self.btn_auditar_traslapes = PushButton("Auditar Traslapes", tab_widget, FIF.SEARCH)
        self.btn_auditar_traslapes.clicked.connect(self.handle_auditar_traslapes)
        bar_actions.addWidget(self.btn_auditar_traslapes)

        self.btn_eliminar_turno = PushButton("Eliminar", tab_widget, FIF.DELETE)
        self.btn_eliminar_turno.clicked.connect(self.handle_eliminar_turno)
        bar_actions.addWidget(self.btn_eliminar_turno)

        bar_actions.addStretch(1)
        v_layout.addLayout(bar_actions)

        # Tabla Maestra de Turnos
        self.table_turnos = TableWidget(tab_widget)
        self.table_turnos.setBorderVisible(True)
        self.table_turnos.setColumnCount(8)
        self.table_turnos.setHorizontalHeaderLabels([
            "Código Turno", "Nómina", "Empleado", "Cargo", "Fecha",
            "Horario (Inicio - Fin)", "Lugar de Servicio", "Estado Asistencia"
        ])
        configure_interactive_table(self.table_turnos, min_col_width=75)
        self.table_turnos.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_turnos.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        v_layout.addWidget(self.table_turnos)

        self.stack_views.addWidget(tab_widget)

    # ==========================================================================
    # PESTANA 4: ASIGNACION DE CONDUCTORES A VIAJES
    # ==========================================================================

    def init_tab_viajes(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(12)

        # Tarjeta 1: KPIs Ejecutivos de Personal y Despacho
        card_kpis = CardWidget(tab_widget)
        kpi_layout = QHBoxLayout(card_kpis)
        kpi_layout.setContentsMargins(16, 12, 16, 12)
        kpi_layout.setSpacing(20)

        self.lbl_kpi_total = StrongBodyLabel("Total Personal: -", card_kpis)
        self.lbl_kpi_activos = StrongBodyLabel("Activos: -", card_kpis)
        self.lbl_kpi_conductores = StrongBodyLabel("Conductores: -", card_kpis)
        self.lbl_kpi_cert_vig = StrongBodyLabel("Licencias Vigentes: -", card_kpis)
        self.lbl_kpi_cert_venc = StrongBodyLabel("Licencias Vencidas: -", card_kpis)

        kpi_layout.addWidget(self.lbl_kpi_total)
        kpi_layout.addWidget(self.lbl_kpi_activos)
        kpi_layout.addWidget(self.lbl_kpi_conductores)
        kpi_layout.addWidget(self.lbl_kpi_cert_vig)
        kpi_layout.addWidget(self.lbl_kpi_cert_venc)
        kpi_layout.addStretch(1)

        v_layout.addWidget(card_kpis)

        # Tarjeta 2: Asignación de Maquinistas a Viajes (Reglas 9 y 10)
        card_viajes = CardWidget(tab_widget)
        viajes_layout = QVBoxLayout(card_viajes)
        viajes_layout.setContentsMargins(16, 12, 16, 12)
        viajes_layout.setSpacing(8)

        bar_viajes_acts = QHBoxLayout()
        bar_viajes_acts.addWidget(StrongBodyLabel("Despacho de Conductores y Viajes Programados", card_viajes))
        bar_viajes_acts.addStretch(1)

        self.btn_asignar_conductor = PrimaryPushButton("Asignar Conductor a Viaje", card_viajes, FIF.SEND)
        self.btn_asignar_conductor.clicked.connect(self.handle_asignar_conductor)
        bar_viajes_acts.addWidget(self.btn_asignar_conductor)

        self.btn_desasignar_conductor = PushButton("Desasignar Conductor", card_viajes, FIF.CANCEL)
        self.btn_desasignar_conductor.clicked.connect(self.handle_desasignar_conductor)
        bar_viajes_acts.addWidget(self.btn_desasignar_conductor)

        self.btn_refresh_viajes = PushButton("Actualizar Viajes", card_viajes, FIF.SYNC)
        self.btn_refresh_viajes.clicked.connect(self.refresh_viajes_staff)
        bar_viajes_acts.addWidget(self.btn_refresh_viajes)

        viajes_layout.addLayout(bar_viajes_acts)

        self.table_viajes_staff = TableWidget(card_viajes)
        self.table_viajes_staff.setBorderVisible(True)
        self.table_viajes_staff.setColumnCount(9)
        self.table_viajes_staff.setHorizontalHeaderLabels([
            "N° Viaje", "Ruta", "Línea", "Fecha", "Horario (Salida - Llegada)",
            "Tren Asignado", "Conductor Asignado", "Licencia Técnica", "Estado Viaje"
        ])
        configure_interactive_table(self.table_viajes_staff, min_col_width=75)
        self.table_viajes_staff.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_viajes_staff.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        viajes_layout.addWidget(self.table_viajes_staff)

        v_layout.addWidget(card_viajes, stretch=4)
        self.stack_views.addWidget(tab_widget)

    # ==========================================================================
    # CONTROL DE PESTANAS Y CARGA GENERAL
    # ==========================================================================

    def on_tab_changed(self, key: str):
        if key == "tab_empleados":
            self.stack_views.setCurrentIndex(0)
            self.refresh_empleados()
        elif key == "tab_certificaciones":
            self.stack_views.setCurrentIndex(1)
            self.refresh_certificaciones()
        elif key == "tab_turnos":
            self.stack_views.setCurrentIndex(2)
            self.refresh_turnos()
        else:
            self.stack_views.setCurrentIndex(3)
            self.refresh_viajes_staff()
            self.refresh_kpis()

    def load_all_data(self):
        """Punto de entrada para sincronización general de datos del módulo."""
        self.refresh_empleados()
        self.populate_staff_combos()
        self.refresh_certificaciones()
        self.refresh_turnos()
        self.refresh_viajes_staff()
        self.refresh_kpis()

    def update_staff(self, staff: Optional[List] = None):
        """Compatibilidad con main_window.load_all_data."""
        self.load_all_data()

    def populate_staff_combos(self):
        """Llena los combos que dependen de la lista de empleados."""
        emps = m4_staff_service.get_empleados()
        self.combo_filtro_cert_emp.blockSignals(True)
        self.combo_filtro_cert_emp.clear()
        self.combo_filtro_cert_emp.addItem("(Todos los Empleados)", userData=None)
        for e in emps:
            e_id = _safe_int(e.get("ID_EMPLEADO", 0))
            self.combo_filtro_cert_emp.addItem(f"{e.get('NOMBRE_COMPLETO', '')} ({e.get('CARGO', '')})", userData=e_id)
        self.combo_filtro_cert_emp.blockSignals(False)

        if hasattr(self, "combo_filtro_turno_emp"):
            self.combo_filtro_turno_emp.blockSignals(True)
            self.combo_filtro_turno_emp.clear()
            self.combo_filtro_turno_emp.addItem("(Todos los Empleados)", userData=None)
            for e in emps:
                e_id = _safe_int(e.get("ID_EMPLEADO", 0))
                self.combo_filtro_turno_emp.addItem(f"{e.get('NOMBRE_COMPLETO', '')} ({e.get('CARGO', '')})", userData=e_id)
            self.combo_filtro_turno_emp.blockSignals(False)

    def refresh_kpis(self):
        kpis = m4_staff_service.get_kpis_personal()
        self.lbl_kpi_total.setText(f"Total Personal: {kpis.get('total_empleados', 0)}")
        self.lbl_kpi_activos.setText(f"Activos: {kpis.get('empleados_activos', 0)}")
        self.lbl_kpi_conductores.setText(f"Conductores: {kpis.get('total_conductores', 0)}")
        self.lbl_kpi_cert_vig.setText(f"Licencias Vigentes: {kpis.get('cert_vigentes', 0)}")
        self.lbl_kpi_cert_venc.setText(f"Licencias Vencidas: {kpis.get('cert_vencidas', 0)}")

    # ==========================================================================
    # LOGICA PESTANA 1: EMPLEADOS Y JERARQUIA
    # ==========================================================================

    def refresh_empleados(self):
        cargo = self.combo_filtro_cargo.currentText()
        estado = self.combo_filtro_estado_lab.currentText()
        self.empleados_cache = m4_staff_service.get_empleados(
            cargo_filter=cargo if cargo != "(Todos)" else None,
            estado_filter=estado if estado != "(Todos)" else None
        )
        self.apply_empleados_filter()

    def apply_empleados_filter(self):
        txt = self.search_empleados.text().strip().lower()
        filtered = self.empleados_cache
        if txt:
            filtered = [
                e for e in filtered
                if txt in str(e.get("NOMBRE_COMPLETO", "")).lower() or
                   txt in str(e.get("NUMERO_EMPLEADO", "")).lower() or
                   txt in str(e.get("TELEFONO", "")).lower() or
                   txt in str(e.get("CARGO", "")).lower()
            ]

        self.table_empleados.setRowCount(len(filtered))
        for r, row in enumerate(filtered):
            self.table_empleados.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("NUMERO_EMPLEADO"))))
            self.table_empleados.setItem(r, 1, QTableWidgetItem(_safe_str(row.get("NOMBRE_COMPLETO"))))
            self.table_empleados.setItem(r, 2, QTableWidgetItem(_safe_str(row.get("CARGO"))))
            self.table_empleados.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("TURNO_HABITUAL"))))
            self.table_empleados.setItem(r, 4, QTableWidgetItem(_safe_str(row.get("NOMBRE_SUPERVISOR"))))
            self.table_empleados.setItem(r, 5, QTableWidgetItem(f"${_safe_float(row.get('SALARIO')):,} USD"))
            self.table_empleados.setItem(r, 6, QTableWidgetItem(_safe_str(row.get("TELEFONO"))))
            self.table_empleados.setItem(r, 7, QTableWidgetItem(_safe_str(row.get("CORREO_ELECTRONICO"))))
            est_lab = _safe_str(row.get("ESTADO_LABORAL"))
            self.table_empleados.setCellWidget(r, 8, StatusBadge(est_lab, self.table_empleados))

            cert_str = _safe_str(row.get("CERTIFICACION_PRINCIPAL"))
            if cert_str != "-":
                self.table_empleados.setCellWidget(r, 9, StatusBadge(cert_str, self.table_empleados))
            else:
                self.table_empleados.setItem(r, 9, QTableWidgetItem("-"))

        auto_fit_table_columns(self.table_empleados)

        if filtered and self.table_empleados.rowCount() > 0:
            self.table_empleados.selectRow(0)
        else:
            self.table_subordinados.setRowCount(0)
            self.table_actividades.setRowCount(0)
            self.lbl_bottom_title.setText("Historial Operativo y Jerarquía (Ningún empleado seleccionado)")

    def on_emp_detail_tab_changed(self, key: str):
        if key == "subtab_actividades":
            self.stack_emp_detail.setCurrentIndex(0)
            self.refresh_actividades_empleado()
        elif key == "subtab_subordinados":
            self.stack_emp_detail.setCurrentIndex(1)
            self.refresh_subordinados()

    def on_empleado_selected(self):
        selected_items = self.table_empleados.selectedItems()
        if not selected_items:
            return
        row = selected_items[0].row()
        num_item = self.table_empleados.item(row, 0)
        if num_item is None:
            return

        num_emp = num_item.text()
        emp = next((e for e in self.empleados_cache if e.get("NUMERO_EMPLEADO") == num_emp), None)
        if not emp:
            return

        self.selected_empleado_id = _safe_int(emp.get("ID_EMPLEADO", 0))
        self.selected_empleado_nombre = emp.get("NOMBRE_COMPLETO", "")
        sup_nom = emp.get("NOMBRE_SUPERVISOR") or "Jefatura General"
        self.lbl_bottom_title.setText(f"Historial Operativo y Jerarquía de {self.selected_empleado_nombre} ({emp.get('CARGO', '')} - Sup: {sup_nom})")

        self.refresh_actividades_empleado()
        self.refresh_subordinados()

    def refresh_actividades_empleado(self):
        if not self.selected_empleado_id:
            self.table_actividades.setRowCount(0)
            return

        acts = m4_staff_service.get_actividades_y_turnos_empleado(self.selected_empleado_id)
        self.table_actividades.setRowCount(len(acts))

        for r, row in enumerate(acts):
            tipo_act = _safe_str(row.get("TIPO_ACTIVIDAD"))
            self.table_actividades.setCellWidget(r, 0, StatusBadge(tipo_act, self.table_actividades))
            self.table_actividades.setItem(r, 1, QTableWidgetItem(_safe_str(row.get("IDENTIFICADOR"))))
            self.table_actividades.setItem(r, 2, QTableWidgetItem(_safe_str(row.get("FECHA"))))
            self.table_actividades.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("HORARIO"))))
            self.table_actividades.setItem(r, 4, QTableWidgetItem(_safe_str(row.get("DETALLE"))))
            st = _safe_str(row.get("ESTADO"))
            self.table_actividades.setCellWidget(r, 5, StatusBadge(st, self.table_actividades))

        auto_fit_table_columns(self.table_actividades)

    def refresh_subordinados(self):
        if not self.selected_empleado_id:
            self.table_subordinados.setRowCount(0)
            return

        subs = m4_staff_service.get_subordinados(self.selected_empleado_id)
        self.table_subordinados.setRowCount(len(subs))

        for r, row in enumerate(subs):
            self.table_subordinados.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("NUMERO_EMPLEADO"))))
            self.table_subordinados.setItem(r, 1, QTableWidgetItem(_safe_str(row.get("NOMBRE_COMPLETO"))))
            self.table_subordinados.setItem(r, 2, QTableWidgetItem(_safe_str(row.get("CARGO"))))
            est_sub = _safe_str(row.get("ESTADO_LABORAL"))
            self.table_subordinados.setCellWidget(r, 3, StatusBadge(est_sub, self.table_subordinados))
            self.table_subordinados.setCellWidget(r, 4, StatusBadge("Supervisión Directa", self.table_subordinados))

        auto_fit_table_columns(self.table_subordinados)

    def handle_nuevo_empleado(self):
        dlg = EmpleadoDialog(parent=self.window())
        if dlg.exec():
            if not dlg.validate():
                return
            datos = dlg.get_data()
            res = m4_staff_service.crear_empleado(datos)
            if res.get("success"):
                InfoBar.success(
                    title="Empleado Registrado",
                    content=f"Empleado {datos['nombre_completo']} registrado con nómina {res.get('numero_empleado')}.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.load_all_data()
            else:
                InfoBar.error(
                    title="Error al Registrar",
                    content=res.get("error", "No se pudo crear el empleado."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )

    def handle_modificar_empleado(self):
        if not self.selected_empleado_id:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un empleado de la tabla.", parent=self.window(), duration=3000)
            return

        emp_data = m4_staff_service.get_empleado_by_id(self.selected_empleado_id)
        if not emp_data:
            return

        dlg = EmpleadoDialog(parent=self.window(), emp_data=emp_data)
        if dlg.exec():
            if not dlg.validate():
                return
            datos = dlg.get_data()
            res = m4_staff_service.modificar_empleado(self.selected_empleado_id, datos)
            if res.get("success"):
                InfoBar.success(
                    title="Empleado Actualizado",
                    content="Los datos del empleado fueron actualizados exitosamente.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.refresh_empleados()
            else:
                InfoBar.error(
                    title="Error al Modificar",
                    content=res.get("error", "No se pudo actualizar."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )

    def handle_cambiar_estado_empleado(self):
        if not self.selected_empleado_id:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un empleado de la tabla.", parent=self.window(), duration=3000)
            return

        emp = next((e for e in self.empleados_cache if _safe_int(e.get("ID_EMPLEADO")) == self.selected_empleado_id), None)
        if not emp:
            return

        nuevo_est = "Activo" if emp.get("ESTADO_LABORAL") != "Activo" else "Permiso"
        res = m4_staff_service.cambiar_estado_laboral(self.selected_empleado_id, nuevo_est)
        if res.get("success"):
            InfoBar.success(
                title="Estado Laboral Actualizado",
                content=f"Estado de {self.selected_empleado_nombre} cambiado a '{nuevo_est}'.",
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
                duration=3500
            )
            self.refresh_empleados()
        else:
            InfoBar.error(title="Error al Cambiar Estado", content=res.get("error", ""), parent=self.window(), duration=4000)

    def handle_eliminar_empleado(self):
        if not self.selected_empleado_id:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un empleado para eliminar.", parent=self.window(), duration=3000)
            return

        dep = m4_staff_service.verificar_dependencias_empleado(self.selected_empleado_id)
        if not dep.get("success"):
            InfoBar.error(title="Error", content=dep.get("error", ""), parent=self.window(), duration=4000)
            return

        if dep.get("sub_cnt", 0) > 0:
            InfoBar.warning(
                title="Supervisor con Personal a Cargo",
                content=f"No se puede eliminar a {self.selected_empleado_nombre}: tiene {dep.get('sub_cnt')} subordinado(s) asignado(s). Reasigne su supervisión primero.",
                parent=self.window(),
                duration=4500
            )
            return

        if dep.get("tiene_dependencias", False):
            box = MessageBox(
                "Historial Operativo Detectado",
                f"El empleado {self.selected_empleado_nombre} no puede ser eliminado físicamente de la base de datos "
                f"porque posee registros vinculados ({dep.get('resumen')}).\n\n"
                f"Por integridad referencial, se debe aplicar una Baja Lógica (Estado: Retirado).\n"
                f"¿Desea cambiar el estado del empleado a 'Retirado'?",
                self.window()
            )
            if box.exec():
                res = m4_staff_service.dar_de_baja_empleado(self.selected_empleado_id)
                if res.get("success"):
                    InfoBar.success(
                        title="Baja Lógica Exitosa",
                        content=f"El empleado {self.selected_empleado_nombre} fue marcado como 'Retirado'.",
                        parent=self.window(),
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=3500
                    )
                    self.load_all_data()
                else:
                    InfoBar.error(title="Error al Retirar", content=res.get("error", ""), parent=self.window(), duration=4500)
            return

        # Sin dependencias operativas: eliminación física
        box = MessageBox(
            "Confirmar Eliminación Física",
            f"¿Está seguro de que desea eliminar definitivamente a {self.selected_empleado_nombre}?\n"
            "Esta acción borrará al empleado y sus licencias asociadas.",
            self.window()
        )
        if box.exec():
            res = m4_staff_service.eliminar_empleado(self.selected_empleado_id)
            if res.get("success"):
                InfoBar.success(
                    title="Empleado Eliminado",
                    content=f"Empleado {self.selected_empleado_nombre} eliminado del sistema.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.selected_empleado_id = None
                self.load_all_data()
            else:
                InfoBar.error(
                    title="Error al Eliminar",
                    content=res.get("error", "No se pudo eliminar el empleado."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )

    # ==========================================================================
    # LOGICA PESTANA 2: CERTIFICACIONES Y LICENCIAS TECNICAS
    # ==========================================================================

    def refresh_certificaciones(self):
        estado = self.combo_filtro_cert_est.currentText()
        emp_id = self.combo_filtro_cert_emp.currentData()
        self.certificaciones_cache = m4_staff_service.get_certificaciones(
            empleado_id=emp_id,
            estado_filter=estado if estado != "(Todos)" else None
        )
        self.table_certificaciones.setRowCount(len(self.certificaciones_cache))

        for r, row in enumerate(self.certificaciones_cache):
            self.table_certificaciones.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("ID_CERTIFICACION"))))
            self.table_certificaciones.setItem(r, 1, QTableWidgetItem(_safe_str(row.get("NUMERO_EMPLEADO"))))
            self.table_certificaciones.setItem(r, 2, QTableWidgetItem(_safe_str(row.get("NOMBRE_EMPLEADO"))))
            self.table_certificaciones.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("CARGO"))))
            tipo_cert = _safe_str(row.get("TIPO_CERTIFICACION"))
            self.table_certificaciones.setCellWidget(r, 4, StatusBadge(tipo_cert, self.table_certificaciones))

            mods_str = _safe_str(row.get("MODELOS_HABILITADOS"))
            self.table_certificaciones.setItem(r, 5, QTableWidgetItem(mods_str if mods_str != "-" else "General"))

            self.table_certificaciones.setItem(r, 6, QTableWidgetItem(_safe_str(row.get("FECHA_EMISION"))))

            venc_str = _safe_str(row.get("FECHA_VENCIMIENTO"))
            self.table_certificaciones.setItem(r, 7, QTableWidgetItem(venc_str))

            est_cert = _safe_str(row.get("ESTADO"))
            self.table_certificaciones.setCellWidget(r, 8, StatusBadge(est_cert, self.table_certificaciones))

        auto_fit_table_columns(self.table_certificaciones)

    def handle_nueva_certificacion(self):
        dlg = CertificacionDialog(parent=self.window())
        if dlg.exec():
            if not dlg.validate():
                return
            datos = dlg.get_data()
            modelos_ids = dlg.get_modelos_ids()
            res = m4_staff_service.crear_certificacion(datos, modelos_ids)
            if res.get("success"):
                InfoBar.success(
                    title="Certificación Registrada",
                    content="Licencia técnica registrada exitosamente en Oracle.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.refresh_certificaciones()
                self.refresh_empleados()
                self.refresh_kpis()
            else:
                InfoBar.error(
                    title="Error al Registrar",
                    content=res.get("error", "No se pudo registrar la certificación."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )

    def handle_modificar_certificacion(self):
        selected = self.table_certificaciones.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione una certificación de la tabla.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item_id = self.table_certificaciones.item(row, 0)
        if not item_id:
            return

        c_id = _safe_int(item_id.text())
        cert = next((c for c in self.certificaciones_cache if _safe_int(c.get("ID_CERTIFICACION")) == c_id), None)
        if not cert:
            return

        dlg = CertificacionDialog(parent=self.window(), cert_data=cert)
        if dlg.exec():
            if not dlg.validate():
                return
            datos = dlg.get_data()
            modelos_ids = dlg.get_modelos_ids()
            res = m4_staff_service.modificar_certificacion(c_id, datos, modelos_ids)
            if res.get("success"):
                InfoBar.success(
                    title="Certificación Actualizada",
                    content="Datos de la certificación actualizados correctamente.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.refresh_certificaciones()
                self.refresh_empleados()
                self.refresh_kpis()
            else:
                InfoBar.error(
                    title="Error al Modificar",
                    content=res.get("error", "No se pudo modificar."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )

    def handle_auditar_vencimientos(self):
        res = m4_staff_service.controlar_vencimientos_certificaciones()
        if res.get("success"):
            act = res.get("actualizadas", 0)
            InfoBar.success(
                title="Auditoría de Vencimientos",
                content=f"Auditoría ejecutada: {act} certificación(es) marcada(s) como 'Vencida'.",
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
                duration=3500
            )
            self.refresh_certificaciones()
            self.refresh_kpis()
        else:
            InfoBar.error(title="Error en Auditoría", content=res.get("error", ""), parent=self.window(), duration=4000)

    def handle_eliminar_certificacion(self):
        selected = self.table_certificaciones.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione una certificación para eliminar.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item_id = self.table_certificaciones.item(row, 0)
        if not item_id:
            return

        c_id = _safe_int(item_id.text())
        box = MessageBox("Confirmar Eliminación", f"¿Desea eliminar la certificación #{c_id}?", self.window())
        if box.exec():
            res = m4_staff_service.eliminar_certificacion(c_id)
            if res.get("success"):
                InfoBar.success(title="Certificación Eliminada", content="Registro eliminado.", parent=self.window(), duration=3000)
                self.refresh_certificaciones()
                self.refresh_empleados()
                self.refresh_kpis()
            else:
                InfoBar.error(title="Error al Eliminar", content=res.get("error", ""), parent=self.window(), duration=4000)

    # ==========================================================================
    # LOGICA PESTANA 3: PROGRAMACION DE TURNOS Y ASISTENCIA
    # ==========================================================================

    def refresh_turnos(self):
        lugar = self.combo_filtro_turno_lugar.currentText()
        asist = self.combo_filtro_turno_asist.currentText()
        emp_id = self.combo_filtro_turno_emp.currentData() if hasattr(self, "combo_filtro_turno_emp") else None
        tiempo = self.combo_filtro_turno_tiempo.currentText() if hasattr(self, "combo_filtro_turno_tiempo") else None

        self.turnos_cache = m4_staff_service.get_turnos(
            empleado_id=emp_id,
            tipo_lugar=lugar if lugar != "(Todos)" else None,
            estado_asistencia=asist if asist != "(Todos)" else None,
            filtro_tiempo=tiempo if tiempo != "(Todos)" else None
        )
        self.table_turnos.setRowCount(len(self.turnos_cache))

        for r, row in enumerate(self.turnos_cache):
            self.table_turnos.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("CODIGO_TURNO"))))
            self.table_turnos.setItem(r, 1, QTableWidgetItem(_safe_str(row.get("NUMERO_EMPLEADO"))))
            self.table_turnos.setItem(r, 2, QTableWidgetItem(_safe_str(row.get("NOMBRE_EMPLEADO"))))
            self.table_turnos.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("CARGO"))))
            self.table_turnos.setItem(r, 4, QTableWidgetItem(_safe_str(row.get("FECHA"))))

            horario_str = f"{row.get('HORA_INICIO', '')} - {row.get('HORA_FIN', '')}"
            self.table_turnos.setItem(r, 5, QTableWidgetItem(horario_str))

            lugar_str = f"{row.get('TIPO_LUGAR', '')} ({row.get('FUNCION', '')})"
            self.table_turnos.setItem(r, 6, QTableWidgetItem(lugar_str))

            est_asist = _safe_str(row.get("ESTADO_ASISTENCIA"))
            self.table_turnos.setCellWidget(r, 7, StatusBadge(est_asist, self.table_turnos))

        auto_fit_table_columns(self.table_turnos)

    def handle_nuevo_turno(self):
        dlg = TurnoDialog(parent=self.window())
        if dlg.exec():
            if not dlg.validate():
                return
            datos = dlg.get_data()
            res = m4_staff_service.crear_turno(datos)
            if res.get("success"):
                InfoBar.success(
                    title="Turno Programado",
                    content=f"Turno {res.get('codigo_turno')} programado exitosamente (Sin traslapes).",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.refresh_turnos()
                self.refresh_kpis()
            else:
                InfoBar.error(
                    title="Conflicto de Programación",
                    content=res.get("error", "No se pudo programar el turno."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=5000
                )

    def handle_modificar_turno(self):
        selected = self.table_turnos.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un turno de la tabla.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item_cod = self.table_turnos.item(row, 0)
        if not item_cod:
            return

        cod = item_cod.text()
        turno = next((t for t in self.turnos_cache if t.get("CODIGO_TURNO") == cod), None)
        if not turno:
            return

        t_id = _safe_int(turno.get("ID_TURNO", 0))
        dlg = TurnoDialog(parent=self.window(), turno_data=turno)
        if dlg.exec():
            if not dlg.validate():
                return
            datos = dlg.get_data()
            res = m4_staff_service.modificar_turno(t_id, datos)
            if res.get("success"):
                InfoBar.success(
                    title="Turno Actualizado",
                    content=f"Turno {cod} actualizado correctamente.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.refresh_turnos()
            else:
                InfoBar.error(
                    title="Error al Modificar Turno",
                    content=res.get("error", "No se pudo actualizar el turno."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )

    def handle_registrar_asistencia(self):
        selected = self.table_turnos.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un turno de la tabla.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item_cod = self.table_turnos.item(row, 0)
        if not item_cod:
            return

        cod = item_cod.text()
        turno = next((t for t in self.turnos_cache if t.get("CODIGO_TURNO") == cod), None)
        if not turno:
            return

        t_id = _safe_int(turno.get("ID_TURNO", 0))
        nom_emp = _safe_str(turno.get("NOMBRE_EMPLEADO"))
        est_actual = _safe_str(turno.get("ESTADO_ASISTENCIA"))

        dlg = AsistenciaDialog(cod, nom_emp, est_actual, parent=self.window())
        if dlg.exec():
            nuevo_est = dlg.get_nuevo_estado()
            res = m4_staff_service.registrar_asistencia(t_id, nuevo_est)
            if res.get("success"):
                InfoBar.success(
                    title="Asistencia Registrada",
                    content=f"Asistencia de {nom_emp} cambiada a '{nuevo_est}'.",
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000
                )
                self.refresh_turnos()
            else:
                InfoBar.error(title="Error al Registrar", content=res.get("error", ""), parent=self.window(), duration=4000)

    def handle_sustitucion_turno(self):
        selected = self.table_turnos.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione el turno a sustituir.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item_cod = self.table_turnos.item(row, 0)
        if not item_cod:
            return

        cod = item_cod.text()
        turno = next((t for t in self.turnos_cache if t.get("CODIGO_TURNO") == cod), None)
        if not turno:
            return

        t_id = _safe_int(turno.get("ID_TURNO", 0))
        nom_emp = _safe_str(turno.get("NOMBRE_EMPLEADO"))
        fecha = _safe_str(turno.get("FECHA"))
        horario = f"{turno.get('HORA_INICIO', '')} - {turno.get('HORA_FIN', '')}"

        dlg = SustitucionDialog(cod, nom_emp, fecha, horario, parent=self.window())
        if dlg.exec():
            sustituto_id = dlg.get_sustituto_id()
            if not sustituto_id:
                return

            res = m4_staff_service.registrar_sustitucion(t_id, sustituto_id)
            if res.get("success"):
                InfoBar.success(
                    title="Sustitución Exitosa",
                    content=res.get("mensaje", "Sustitución registrada."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4000
                )
                self.refresh_turnos()
            else:
                InfoBar.error(
                    title="Conflicto de Sustitución",
                    content=res.get("error", "No se pudo registrar la sustitución."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4500
                )

    def handle_auditar_traslapes(self):
        traslapes = m4_staff_service.detectar_traslapes_turnos()
        if not traslapes:
            InfoBar.success(
                title="Auditoría de Turnos Limpia",
                content="No se detectaron pares de turnos solapados en todo el sistema. Integridad 100%.",
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000
            )
        else:
            msg = f"Se detectaron {len(traslapes)} conflicto(s) de traslape:\n"
            for tr in traslapes[:3]:
                msg += f"- {tr['NOMBRE_COMPLETO']}: {tr['CODIGO_1']} ({tr['HORARIO_1']}) con {tr['CODIGO_2']} ({tr['HORARIO_2']})\n"
            InfoBar.warning(
                title="Traslapes Detectados",
                content=msg,
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
                duration=6000
            )

    def handle_eliminar_turno(self):
        selected = self.table_turnos.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un turno para eliminar.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item_cod = self.table_turnos.item(row, 0)
        if not item_cod:
            return

        cod = item_cod.text()
        turno = next((t for t in self.turnos_cache if t.get("CODIGO_TURNO") == cod), None)
        if not turno:
            return

        t_id = _safe_int(turno.get("ID_TURNO", 0))
        box = MessageBox("Confirmar Eliminación", f"¿Está seguro de que desea eliminar el turno {cod}?", self.window())
        if box.exec():
            res = m4_staff_service.eliminar_turno(t_id)
            if res.get("success"):
                InfoBar.success(title="Turno Eliminado", content=f"Turno {cod} eliminado.", parent=self.window(), duration=3000)
                self.refresh_turnos()
                self.refresh_kpis()
            else:
                InfoBar.error(title="Error al Eliminar", content=res.get("error", ""), parent=self.window(), duration=4000)

    # ==========================================================================
    # LOGICA PESTANA 4: ASIGNACION DE CONDUCTORES A VIAJES
    # ==========================================================================

    def refresh_viajes_staff(self):
        viajes = m4_staff_service.get_viajes_personal()
        self.table_viajes_staff.setRowCount(len(viajes))

        for r, row in enumerate(viajes):
            self.table_viajes_staff.setItem(r, 0, QTableWidgetItem(_safe_str(row.get("NUMERO_VIAJE"))))
            self.table_viajes_staff.setItem(r, 1, QTableWidgetItem(f"Ruta {_safe_str(row.get('CODIGO_RUTA'))}"))
            lin_cod = _safe_str(row.get('CODIGO_LINEA'))
            lin_col = _safe_str(row.get('COLOR_LINEA', '#0039A6'))
            chip = LineColorChip(lin_cod, lin_col, f"Línea {lin_cod}", self.table_viajes_staff)
            self.table_viajes_staff.setCellWidget(r, 2, chip)

            self.table_viajes_staff.setItem(r, 3, QTableWidgetItem(_safe_str(row.get("FECHA"))))

            horario_str = f"{row.get('HORA_SALIDA_CORTA', '')} - {row.get('HORA_LLEGADA_CORTA', '')}"
            self.table_viajes_staff.setItem(r, 4, QTableWidgetItem(horario_str))

            tren_str = f"{row.get('CODIGO_TREN', '')} ({row.get('NOMBRE_MODELO', '')})" if row.get("CODIGO_TREN") else "(Sin Tren)"
            self.table_viajes_staff.setItem(r, 5, QTableWidgetItem(tren_str))

            cond_str = _safe_str(row.get("CONDUCTOR"))
            self.table_viajes_staff.setItem(r, 6, QTableWidgetItem(cond_str if cond_str != "-" else "(Sin Conductor)"))

            lic_str = _safe_str(row.get("ESTADO_LICENCIA_CONDUCTOR"))
            self.table_viajes_staff.setCellWidget(r, 7, StatusBadge(lic_str, self.table_viajes_staff))

            st_viaje = _safe_str(row.get("ESTADO_VIAJE"))
            self.table_viajes_staff.setCellWidget(r, 8, StatusBadge(st_viaje, self.table_viajes_staff))

        auto_fit_table_columns(self.table_viajes_staff)

    def handle_asignar_conductor(self):
        selected = self.table_viajes_staff.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un viaje de la tabla.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item_num = self.table_viajes_staff.item(row, 0)
        if not item_num:
            return

        num_viaje = item_num.text()
        viajes = m4_staff_service.get_viajes_personal()
        viaje = next((v for v in viajes if v.get("NUMERO_VIAJE") == num_viaje), None)
        if not viaje:
            return

        v_id = _safe_int(viaje.get("ID_VIAJE", 0))
        f_str = _safe_str(viaje.get("FECHA"))
        h_sal = _safe_str(viaje.get("HORA_SALIDA_CORTA"))
        h_lleg = _safe_str(viaje.get("HORA_LLEGADA_CORTA"))

        conductores_aptos = m4_staff_service.get_conductores_disponibles(f_str, h_sal, h_lleg)

        dlg = AsignarConductorViajeDialog(v_id, num_viaje, conductores_aptos, parent=self.window())
        if dlg.exec():
            conductor_id = dlg.get_selected_conductor_id()
            if not conductor_id:
                return

            res = m4_staff_service.asignar_conductor_viaje(v_id, conductor_id)
            if res.get("success"):
                InfoBar.success(
                    title="Conductor Asignado",
                    content=res.get("mensaje", "Conductor asignado exitosamente."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3500
                )
                self.refresh_viajes_staff()
            else:
                InfoBar.error(
                    title="Conflicto de Asignación",
                    content=res.get("error", "No se pudo asignar el conductor."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=5000
                )

    def handle_desasignar_conductor(self):
        selected = self.table_viajes_staff.selectedItems()
        if not selected:
            InfoBar.warning(title="Selección Requerida", content="Seleccione un viaje de la tabla.", parent=self.window(), duration=3000)
            return

        row = selected[0].row()
        item_num = self.table_viajes_staff.item(row, 0)
        if not item_num:
            return

        num_viaje = item_num.text()
        viajes = m4_staff_service.get_viajes_personal()
        viaje = next((v for v in viajes if v.get("NUMERO_VIAJE") == num_viaje), None)
        if not viaje:
            return

        v_id = _safe_int(viaje.get("ID_VIAJE", 0))
        box = MessageBox("Confirmar Desasignación", f"¿Desea desvincular al conductor asignado al viaje {num_viaje}?", self.window())
        if box.exec():
            res = m4_staff_service.desasignar_conductor_viaje(v_id)
            if res.get("success"):
                InfoBar.success(
                    title="Conductor Desasignado",
                    content=res.get("mensaje", "Conductor desasignado del viaje."),
                    parent=self.window(),
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000
                )
                self.refresh_viajes_staff()
            else:
                InfoBar.error(title="Error al Desasignar", content=res.get("error", ""), parent=self.window(), duration=4000)
