"""
m2_routes_interface.py - Vista principal para el Módulo 2: Rutas y Horarios.
Cumple estrictamente con los 9 requerimientos del enunciado:
1. Crear rutas locales y expresas.
2. Establecer el sentido del recorrido.
3. Definir las paradas de cada ruta (parada local vs salto expreso).
4. Configurar horarios por dia.
5. Configurar frecuencias.
6. Generar viajes programados (SP_PROGRAMAR_VIAJE).
7. Cancelar o reprogramar viajes.
8. Consultar proximos viajes por estacion.
9. Identificar rutas afectadas por incidentes o cierres.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QHeaderView, QFormLayout, QTableWidgetItem
)

from qfluentwidgets import (
    TitleLabel, SubtitleLabel, CaptionLabel, BodyLabel, StrongBodyLabel,
    CardWidget, ComboBox, LineEdit, SearchLineEdit, DoubleSpinBox, SpinBox,
    PrimaryPushButton, PushButton, TableWidget, InfoBar, InfoBarPosition,
    SegmentedWidget, CheckBox, MessageBoxBase, MessageBox, FluentIcon as FIF
)

from services import m2_routes_service


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


# ==============================================================================
# DIALOGOS MODALES FLUENT (MODULO 2)
# ==============================================================================

class RutaDialog(MessageBoxBase):
    """Dialogo modal para crear o modificar una ruta."""
    def __init__(self, parent=None, ruta_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.ruta_data = ruta_data
        self.es_edicion = ruta_data is not None

        title_text = "Modificar Ruta" if self.es_edicion else "Nueva Ruta Operativa"
        self.titleLabel = SubtitleLabel(title_text, self)
        self.viewLayout.addWidget(self.titleLabel)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.txt_codigo = LineEdit(self)
        self.txt_codigo.setPlaceholderText("Ej: RUT-1-SB, RUT-A-EXP")
        form_layout.addRow("Código de Ruta:", self.txt_codigo)

        self.combo_linea = ComboBox(self)
        self.lineas = m2_routes_service.get_lineas_combo()
        for l in self.lineas:
            self.combo_linea.addItem(f"Linea {l['CODIGO']} - {l['NOMBRE']}", userData=_safe_int(l.get("ID_LINEA", 0)))
        form_layout.addRow("Linea Asociada:", self.combo_linea)

        self.combo_origen = ComboBox(self)
        self.combo_destino = ComboBox(self)
        self.estaciones = m2_routes_service.get_estaciones_combo()
        for e in self.estaciones:
            self.combo_origen.addItem(f"{e['NOMBRE']} ({e['CODIGO']})", userData=_safe_int(e.get("ID_ESTACION", 0)))
            self.combo_destino.addItem(f"{e['NOMBRE']} ({e['CODIGO']})", userData=_safe_int(e.get("ID_ESTACION", 0)))
        form_layout.addRow("Estación Origen:", self.combo_origen)
        form_layout.addRow("Estación Destino:", self.combo_destino)

        self.combo_sentido = ComboBox(self)
        self.combo_sentido.addItems([
            "Norte-Sur", "Sur-Norte",
            "Uptown-Downtown", "Downtown-Uptown",
            "Este-Oeste", "Oeste-Este"
        ])
        form_layout.addRow("Sentido del Recorrido:", self.combo_sentido)

        self.combo_tipo = ComboBox(self)
        self.combo_tipo.addItems(["Local", "Expreso", "Nocturno", "Especial", "Temporal"])
        form_layout.addRow("Tipo de Servicio:", self.combo_tipo)

        self.spin_distancia = DoubleSpinBox(self)
        self.spin_distancia.setRange(0.1, 200.0)
        self.spin_distancia.setDecimals(2)
        self.spin_distancia.setSuffix(" km")
        self.spin_distancia.setValue(20.0)
        form_layout.addRow("Distancia Total:", self.spin_distancia)

        self.spin_duracion = SpinBox(self)
        self.spin_duracion.setRange(1, 300)
        self.spin_duracion.setSuffix(" min")
        self.spin_duracion.setValue(45)
        form_layout.addRow("Duración Estimada:", self.spin_duracion)

        self.combo_estado = ComboBox(self)
        self.combo_estado.addItems(["Activa", "Cerrada Temporalmente", "Cancelada"])
        form_layout.addRow("Estado Operativo:", self.combo_estado)

        self.viewLayout.addLayout(form_layout)

        # Cargar valores en modo edicion
        if self.es_edicion and self.ruta_data:
            self.txt_codigo.setText(str(self.ruta_data.get("CODIGO", "")))
            lid = self.ruta_data.get("LINEA_ID")
            if lid is not None:
                lid_int = _safe_int(lid)
                for i in range(self.combo_linea.count()):
                    if self.combo_linea.itemData(i) == lid_int:
                        self.combo_linea.setCurrentIndex(i)
                        break

            oid = self.ruta_data.get("ESTACION_ORIGEN_ID")
            did = self.ruta_data.get("ESTACION_DESTINO_ID")
            if oid is not None:
                oid_int = _safe_int(oid)
                for i in range(self.combo_origen.count()):
                    if self.combo_origen.itemData(i) == oid_int:
                        self.combo_origen.setCurrentIndex(i)
                        break
            if did is not None:
                did_int = _safe_int(did)
                for i in range(self.combo_destino.count()):
                    if self.combo_destino.itemData(i) == did_int:
                        self.combo_destino.setCurrentIndex(i)
                        break

            self.combo_sentido.setCurrentText(str(self.ruta_data.get("SENTIDO", "Norte-Sur")))
            self.combo_tipo.setCurrentText(str(self.ruta_data.get("TIPO_SERVICIO", "Local")))
            self.spin_distancia.setValue(_safe_float(self.ruta_data.get("DISTANCIA_TOTAL_KM", 20.0), 20.0))
            self.spin_duracion.setValue(_safe_int(self.ruta_data.get("DURACION_ESTIMADA_MIN", 45), 45))
            self.combo_estado.setCurrentText(str(self.ruta_data.get("ESTADO", "Activa")))

    def get_data(self) -> Dict[str, Any]:
        return {
            "codigo": self.txt_codigo.text().strip().upper(),
            "linea_id": self.combo_linea.currentData(),
            "estacion_origen_id": self.combo_origen.currentData(),
            "estacion_destino_id": self.combo_destino.currentData(),
            "sentido": self.combo_sentido.currentText(),
            "tipo_servicio": self.combo_tipo.currentText(),
            "distancia_total_km": self.spin_distancia.value(),
            "duracion_estimada_min": self.spin_duracion.value(),
            "estado": self.combo_estado.currentText(),
            "fecha_vigencia_desde": date.today().strftime("%Y-%m-%d"),
            "fecha_vigencia_hasta": None
        }


class ParadaRutaDialog(MessageBoxBase):
    """Dialogo modal para agregar o modificar una parada en una ruta."""
    def __init__(self, parent=None, ruta_id: int = 0, parada_data: Optional[Dict[str, Any]] = None, sugerir_orden: int = 1):
        super().__init__(parent)
        self.ruta_id = ruta_id
        self.parada_data = parada_data
        self.es_edicion = parada_data is not None

        title_text = "Modificar Parada de Ruta" if self.es_edicion else "Agregar Parada a Secuencia de Ruta"
        self.titleLabel = SubtitleLabel(title_text, self)
        self.viewLayout.addWidget(self.titleLabel)

        form = QFormLayout()
        form.setSpacing(10)

        self.combo_estacion = ComboBox(self)
        self.estaciones = m2_routes_service.get_estaciones_combo()
        for e in self.estaciones:
            self.combo_estacion.addItem(f"{e['NOMBRE']} ({e['DISTRITO']})", userData=_safe_int(e.get("ID_ESTACION", 0)))
        form.addRow("Estacion:", self.combo_estacion)

        self.spin_orden = SpinBox(self)
        self.spin_orden.setRange(1, 99)
        self.spin_orden.setValue(sugerir_orden)
        form.addRow("Orden de Llegada:", self.spin_orden)

        self.txt_hora_llegada = LineEdit(self)
        self.txt_hora_llegada.setPlaceholderText("HH:MM (ej: 07:15)")
        form.addRow("Hora Estimada Llegada:", self.txt_hora_llegada)

        self.txt_hora_salida = LineEdit(self)
        self.txt_hora_salida.setPlaceholderText("HH:MM (ej: 07:17)")
        form.addRow("Hora Estimada Salida:", self.txt_hora_salida)

        self.spin_distancia = DoubleSpinBox(self)
        self.spin_distancia.setRange(0.0, 50.0)
        self.spin_distancia.setDecimals(2)
        self.spin_distancia.setSuffix(" km")
        self.spin_distancia.setValue(2.5)
        form.addRow("Distancia Anterior:", self.spin_distancia)

        self.spin_tiempo = SpinBox(self)
        self.spin_tiempo.setRange(0, 120)
        self.spin_tiempo.setSuffix(" min")
        self.spin_tiempo.setValue(4)
        form.addRow("Tiempo Anterior:", self.spin_tiempo)

        self.chk_se_detiene = CheckBox("El tren se detiene en esta estacion (Parada Local)", self)
        self.chk_se_detiene.setChecked(True)
        form.addRow("Condicion de Parada:", self.chk_se_detiene)

        self.viewLayout.addLayout(form)

        if self.es_edicion and self.parada_data:
            eid = self.parada_data.get("ESTACION_ID")
            if eid is not None:
                eid_int = _safe_int(eid)
                for i in range(self.combo_estacion.count()):
                    if self.combo_estacion.itemData(i) == eid_int:
                        self.combo_estacion.setCurrentIndex(i)
                        break
            self.spin_orden.setValue(_safe_int(self.parada_data.get("ORDEN_LLEGADA", 1), 1))
            self.txt_hora_llegada.setText(str(self.parada_data.get("HORA_LLEGADA", "") or ""))
            self.txt_hora_salida.setText(str(self.parada_data.get("HORA_SALIDA", "") or ""))
            self.spin_distancia.setValue(_safe_float(self.parada_data.get("DISTANCIA_DESDE_ANTERIOR_KM", 0.0), 0.0))
            self.spin_tiempo.setValue(_safe_int(self.parada_data.get("TIEMPO_DESDE_ANTERIOR_MIN", 0), 0))
            self.chk_se_detiene.setChecked(self.parada_data.get("SE_DETIENE") == "S")

    def get_data(self) -> Dict[str, Any]:
        return {
            "ruta_id": self.ruta_id,
            "estacion_id": self.combo_estacion.currentData(),
            "orden_llegada": self.spin_orden.value(),
            "hora_estimada_llegada": self.txt_hora_llegada.text().strip() or None,
            "hora_estimada_salida": self.txt_hora_salida.text().strip() or None,
            "distancia_desde_anterior_km": self.spin_distancia.value(),
            "tiempo_desde_anterior_min": self.spin_tiempo.value(),
            "se_detiene": "S" if self.chk_se_detiene.isChecked() else "N"
        }


class HorarioDialog(MessageBoxBase):
    """Dialogo modal para configurar o modificar horarios y frecuencias de una ruta."""
    def __init__(self, parent=None, ruta_id: int = 0, horario_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.ruta_id = ruta_id
        self.horario_data = horario_data
        self.es_edicion = horario_data is not None

        title_text = "Modificar Horario de Operación" if self.es_edicion else "Configurar Horario y Frecuencia"
        self.titleLabel = SubtitleLabel(title_text, self)
        self.viewLayout.addWidget(self.titleLabel)

        form = QFormLayout()
        form.setSpacing(10)

        self.combo_dia = ComboBox(self)
        self.combo_dia.addItems([
            "Lunes a Viernes", "Fin de Semana", "Sabado", "Domingo", "Festivo"
        ])
        form.addRow("Dia de la Semana:", self.combo_dia)

        self.txt_inicio = LineEdit(self)
        self.txt_inicio.setPlaceholderText("HH:MM (ej: 06:00)")
        self.txt_inicio.setText("06:00")
        form.addRow("Hora de Inicio:", self.txt_inicio)

        self.txt_fin = LineEdit(self)
        self.txt_fin.setPlaceholderText("HH:MM (ej: 09:30)")
        self.txt_fin.setText("09:30")
        form.addRow("Hora de Finalizacion:", self.txt_fin)

        self.spin_frecuencia = SpinBox(self)
        self.spin_frecuencia.setRange(1, 120)
        self.spin_frecuencia.setSuffix(" min entre trenes")
        self.spin_frecuencia.setValue(5)
        form.addRow("Frecuencia Programada:", self.spin_frecuencia)

        self.combo_tipo = ComboBox(self)
        self.combo_tipo.addItems([
            "Hora Pico Matutina", "Valle / Regular", "Hora Pico Vespertina",
            "Servicio Nocturno", "Fin de Semana", "Especial"
        ])
        form.addRow("Tipo de Horario:", self.combo_tipo)

        self.viewLayout.addLayout(form)

        if self.es_edicion and self.horario_data:
            dia = str(self.horario_data.get("DIA_SEMANA", "Lunes a Viernes"))
            self.combo_dia.setCurrentText(dia)
            self.txt_inicio.setText(str(self.horario_data.get("HORA_INICIO", "06:00")))
            self.txt_fin.setText(str(self.horario_data.get("HORA_FIN", "09:30")))
            self.spin_frecuencia.setValue(_safe_int(self.horario_data.get("FRECUENCIA_MINUTOS", 5), 5))
            tipo = str(self.horario_data.get("TIPO_SERVICIO", "Valle / Regular"))
            self.combo_tipo.setCurrentText(tipo)

    def get_data(self) -> Dict[str, Any]:
        return {
            "ruta_id": self.ruta_id,
            "dia_semana": self.combo_dia.currentText(),
            "hora_inicio": self.txt_inicio.text().strip(),
            "hora_fin": self.txt_fin.text().strip(),
            "frecuencia_minutos": self.spin_frecuencia.value(),
            "tipo_servicio": self.combo_tipo.currentText(),
            "fecha_vigencia_desde": date.today().strftime("%Y-%m-%d"),
            "fecha_vigencia_hasta": None
        }


class ProgramarViajeDialog(MessageBoxBase):
    """
    Dialogo modal para programar un viaje (SP_PROGRAMAR_VIAJE).
    Valida en tiempo real que el tren este disponible y el conductor tenga licencia vigente.
    """
    def __init__(self, parent=None, ruta_preseleccionada_id: Optional[int] = None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("Programar Nuevo Viaje (Despacho)", self)
        self.viewLayout.addWidget(self.titleLabel)

        form = QFormLayout()
        form.setSpacing(10)

        self.combo_ruta = ComboBox(self)
        self.rutas = m2_routes_service.get_rutas()
        for r in self.rutas:
            self.combo_ruta.addItem(f"Ruta {r['CODIGO']} ({r['SENTIDO']} - {r['TIPO_SERVICIO']})", userData=_safe_int(r.get("ID_RUTA", 0)))
        if ruta_preseleccionada_id:
            pre_id = _safe_int(ruta_preseleccionada_id)
            for i in range(self.combo_ruta.count()):
                if self.combo_ruta.itemData(i) == pre_id:
                    self.combo_ruta.setCurrentIndex(i)
                    break
        form.addRow("Ruta Programada:", self.combo_ruta)

        self.txt_fecha = LineEdit(self)
        self.txt_fecha.setText(date.today().strftime("%Y-%m-%d"))
        form.addRow("Fecha del Viaje:", self.txt_fecha)

        self.txt_salida = LineEdit(self)
        self.txt_salida.setPlaceholderText("HH:MM (ej: 08:00)")
        self.txt_salida.setText("08:00")
        form.addRow("Hora Programada Salida:", self.txt_salida)

        self.txt_llegada = LineEdit(self)
        self.txt_llegada.setPlaceholderText("HH:MM (ej: 08:45)")
        self.txt_llegada.setText("08:45")
        form.addRow("Hora Programada Llegada:", self.txt_llegada)

        self.combo_tren = ComboBox(self)
        self.trenes = m2_routes_service.get_trenes_disponibles_combo()
        for t in self.trenes:
            self.combo_tren.addItem(f"{t['CODIGO_INTERNO']} (Modelo {t['NOMBRE_MODELO']} - Cap: {t['CAPACIDAD_TOTAL']})", userData=_safe_int(t.get("ID_TREN", 0)))
        form.addRow("Tren Asignado (Disponible):", self.combo_tren)

        self.combo_conductor = ComboBox(self)
        self.conductores = m2_routes_service.get_conductores_combo()
        for c in self.conductores:
            cert_txt = f" - {c.get('ESTADO_CERTIFICACION', '')}" if c.get('ESTADO_CERTIFICACION') else ""
            self.combo_conductor.addItem(f"{c['NOMBRE_COMPLETO']} ({c['NUMERO_EMPLEADO']}){cert_txt}", userData=_safe_int(c.get("ID_EMPLEADO", 0)))
        form.addRow("Maquinista / Conductor:", self.combo_conductor)

        self.combo_estado = ComboBox(self)
        self.combo_estado.addItems(["Programado", "En Abordaje", "En Curso", "Retrasado", "Completado", "Cancelado"])
        self.combo_estado.setCurrentText("Programado")
        form.addRow("Estado Operativo:", self.combo_estado)

        self.spin_pasajeros = SpinBox(self)
        self.spin_pasajeros.setRange(0, 10000)
        self.spin_pasajeros.setValue(850)
        form.addRow("Pasajeros Estimados:", self.spin_pasajeros)

        self.viewLayout.addLayout(form)

    def get_data(self) -> Dict[str, Any]:
        return {
            "ruta_id": self.combo_ruta.currentData(),
            "fecha": self.txt_fecha.text().strip(),
            "hora_salida": self.txt_salida.text().strip(),
            "hora_llegada": self.txt_llegada.text().strip(),
            "tren_id": self.combo_tren.currentData(),
            "conductor_id": self.combo_conductor.currentData(),
            "estado": self.combo_estado.currentText(),
            "cantidad_estimada_pasajeros": self.spin_pasajeros.value() if self.spin_pasajeros.value() > 0 else None
        }


class EditarViajeDialog(MessageBoxBase):
    """Dialogo modal para reprogramar o modificar integralmente un viaje programado."""
    def __init__(self, parent=None, viaje_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.viaje_data = viaje_data or {}

        self.titleLabel = SubtitleLabel("Reprogramar / Modificar Viaje", self)
        self.viewLayout.addWidget(self.titleLabel)

        form = QFormLayout()
        form.setSpacing(10)

        num_viaje = str(self.viaje_data.get("NUMERO_VIAJE", ""))
        cod_ruta = str(self.viaje_data.get("CODIGO_RUTA", ""))
        lbl_info = StrongBodyLabel(f"Viaje: {num_viaje} - Ruta: {cod_ruta}", self)
        form.addRow("Identificación:", lbl_info)

        self.txt_fecha = LineEdit(self)
        self.txt_fecha.setText(str(self.viaje_data.get("FECHA", date.today().strftime("%Y-%m-%d"))))
        form.addRow("Fecha del Viaje:", self.txt_fecha)

        self.txt_salida = LineEdit(self)
        self.txt_salida.setPlaceholderText("HH:MM (ej: 08:00)")
        self.txt_salida.setText(str(self.viaje_data.get("HORA_PROG_SALIDA", "08:00")))
        form.addRow("Hora Programada Salida:", self.txt_salida)

        self.txt_llegada = LineEdit(self)
        self.txt_llegada.setPlaceholderText("HH:MM (ej: 08:45)")
        self.txt_llegada.setText(str(self.viaje_data.get("HORA_PROG_LLEGADA", "08:45")))
        form.addRow("Hora Programada Llegada:", self.txt_llegada)

        self.combo_tren = ComboBox(self)
        self.trenes = m2_routes_service.get_todos_trenes_combo()
        current_tren_id = _safe_int(self.viaje_data.get("TREN_ID", 0))
        sel_t_idx = 0
        for idx, t in enumerate(self.trenes):
            tid = _safe_int(t.get("ID_TREN", 0))
            self.combo_tren.addItem(f"{t['CODIGO_INTERNO']} ({t['NOMBRE_MODELO']} - {t.get('ESTADO_OPERATIVO', '')})", userData=tid)
            if tid == current_tren_id:
                sel_t_idx = idx
        if self.combo_tren.count() > 0:
            self.combo_tren.setCurrentIndex(sel_t_idx)
        form.addRow("Tren Asignado:", self.combo_tren)

        self.combo_conductor = ComboBox(self)
        self.conductores = m2_routes_service.get_conductores_combo()
        current_cond_id = _safe_int(self.viaje_data.get("CONDUCTOR_ID", 0))
        sel_c_idx = 0
        for idx, c in enumerate(self.conductores):
            cid = _safe_int(c.get("ID_EMPLEADO", 0))
            cert_txt = f" - {c.get('ESTADO_CERTIFICACION', '')}" if c.get('ESTADO_CERTIFICACION') else ""
            self.combo_conductor.addItem(f"{c['NOMBRE_COMPLETO']} ({c['NUMERO_EMPLEADO']}){cert_txt}", userData=cid)
            if cid == current_cond_id:
                sel_c_idx = idx
        if self.combo_conductor.count() > 0:
            self.combo_conductor.setCurrentIndex(sel_c_idx)
        form.addRow("Maquinista / Conductor:", self.combo_conductor)

        self.combo_estado = ComboBox(self)
        self.combo_estado.addItems(["Programado", "En Abordaje", "En Curso", "Retrasado", "Completado", "Cancelado"])
        self.combo_estado.setCurrentText(str(self.viaje_data.get("ESTADO", "Programado")))
        form.addRow("Estado Operativo:", self.combo_estado)

        self.spin_pasajeros = SpinBox(self)
        self.spin_pasajeros.setRange(0, 10000)
        self.spin_pasajeros.setValue(_safe_int(self.viaje_data.get("CANTIDAD_ESTIMADA_PASAJEROS", 0), 0))
        form.addRow("Pasajeros Estimados:", self.spin_pasajeros)

        self.viewLayout.addLayout(form)

    def get_data(self) -> Dict[str, Any]:
        return {
            "fecha": self.txt_fecha.text().strip(),
            "hora_salida": self.txt_salida.text().strip(),
            "hora_llegada": self.txt_llegada.text().strip(),
            "tren_id": self.combo_tren.currentData(),
            "conductor_id": self.combo_conductor.currentData(),
            "estado": self.combo_estado.currentText(),
            "cantidad_estimada_pasajeros": self.spin_pasajeros.value() if self.spin_pasajeros.value() > 0 else None
        }


# ==============================================================================
# VISTA PRINCIPAL (MODULO 2: RUTAS Y HORARIOS)
# ==============================================================================

class M2RoutesInterface(QWidget):
    """
    Vista principal para el Módulo 2: Rutas y Horarios.
    Dispone el titulo en su propio contenedor y las pestañas en un contenedor independiente.
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("m2RoutesInterface")

        self.selected_route_id: Optional[int] = None
        self.selected_line_filter_id: Optional[int] = None
        self.rutas_cache: List[Dict[str, Any]] = []

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

        title = TitleLabel("Rutas, Horarios y Despacho Operativo", header_card)
        subtitle = SubtitleLabel("Modulo 2: Gestion de recorridos locales y expresos, frecuencias, viajes y monitoreo", header_card)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        main_layout.addWidget(header_card)

        # ----------------------------------------------------------------------
        # 2. CONTENEDOR INDEPENDIENTE DE PESTANAS (SEGMENTED WIDGET)
        # ----------------------------------------------------------------------
        tabs_layout = QHBoxLayout()
        self.segmented_tabs = SegmentedWidget(self)
        self.segmented_tabs.addItem("tab_rutas", "Rutas y Paradas Secuenciales")
        self.segmented_tabs.addItem("tab_horarios", "Horarios y Frecuencias")
        self.segmented_tabs.addItem("tab_viajes", "Programacion de Viajes y Despacho")
        self.segmented_tabs.addItem("tab_arribos", "Proximos Arribos e Incidentes")
        self.segmented_tabs.currentItemChanged.connect(self.on_tab_changed)
        tabs_layout.addWidget(self.segmented_tabs)

        main_layout.addLayout(tabs_layout)

        # ----------------------------------------------------------------------
        # 3. STACK PRINCIPAL DE PANELES
        # ----------------------------------------------------------------------
        self.stack_views = QStackedWidget(self)

        self.init_tab_rutas()
        self.init_tab_horarios()
        self.init_tab_viajes()
        self.init_tab_arribos()

        main_layout.addWidget(self.stack_views)

        # Seleccionar la primera pestaña por defecto para que aparezca activa visualmente
        self.segmented_tabs.setCurrentItem("tab_rutas")

    # --------------------------------------------------------------------------
    # PESTANA 1: RUTAS Y PARADAS SECUENCIALES
    # --------------------------------------------------------------------------
    def init_tab_rutas(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 8, 0, 0)
        v_layout.setSpacing(12)

        # Barra de Filtros y Acciones
        bar_actions = QHBoxLayout()
        bar_actions.setSpacing(10)

        self.search_rutas = SearchLineEdit(tab_widget)
        self.search_rutas.setPlaceholderText("Buscar por codigo, origen o destino...")
        self.search_rutas.setClearButtonEnabled(True)
        self.search_rutas.textChanged.connect(self.apply_rutas_filter)
        bar_actions.addWidget(self.search_rutas, stretch=4)

        bar_actions.addWidget(CaptionLabel("Filtrar Linea:", tab_widget))
        self.combo_filtro_linea = ComboBox(tab_widget)
        self.combo_filtro_linea.addItem("(Todas las Lineas)", userData=None)
        lineas = m2_routes_service.get_lineas_combo()
        for l in lineas:
            self.combo_filtro_linea.addItem(f"Linea {l['CODIGO']}", userData=_safe_int(l.get("ID_LINEA", 0)))
        self.combo_filtro_linea.currentIndexChanged.connect(self.refresh_rutas)
        bar_actions.addWidget(self.combo_filtro_linea, stretch=2)

        self.btn_nueva_ruta = PrimaryPushButton("Nueva Ruta", tab_widget, FIF.ADD)
        self.btn_nueva_ruta.clicked.connect(self.handle_nueva_ruta)
        bar_actions.addWidget(self.btn_nueva_ruta)

        self.btn_modificar_ruta = PushButton("Modificar Ruta", tab_widget, FIF.EDIT)
        self.btn_modificar_ruta.clicked.connect(self.handle_modificar_ruta)
        bar_actions.addWidget(self.btn_modificar_ruta)

        self.btn_estado_ruta = PushButton("Cambiar Estado", tab_widget, FIF.SYNC)
        self.btn_estado_ruta.clicked.connect(self.handle_cambiar_estado_ruta)
        bar_actions.addWidget(self.btn_estado_ruta)

        self.btn_eliminar_ruta = PushButton("Eliminar Ruta", tab_widget, FIF.DELETE)
        self.btn_eliminar_ruta.clicked.connect(self.handle_eliminar_ruta)
        bar_actions.addWidget(self.btn_eliminar_ruta)

        v_layout.addLayout(bar_actions)

        # Tabla Maestra de Rutas
        self.table_rutas = TableWidget(tab_widget)
        self.table_rutas.setBorderVisible(True)
        self.table_rutas.setColumnCount(9)
        self.table_rutas.setHorizontalHeaderLabels([
            "Codigo", "Linea", "Servicio", "Sentido", "Origen", "Destino", "Distancia", "Duracion", "Estado"
        ])
        hr = self.table_rutas.horizontalHeader()
        if hr is not None:
            hr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_rutas.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_rutas.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table_rutas.itemSelectionChanged.connect(self.on_ruta_selected)
        v_layout.addWidget(self.table_rutas, stretch=4)

        # Panel Inferior: Secuencia de Paradas de la Ruta Seleccionada (RUTA_DETALLE)
        card_paradas = CardWidget(tab_widget)
        paradas_layout = QVBoxLayout(card_paradas)
        paradas_layout.setContentsMargins(16, 12, 16, 12)
        paradas_layout.setSpacing(8)

        bar_paradas = QHBoxLayout()
        self.lbl_paradas_title = StrongBodyLabel("Secuencia de Paradas y Saltos Expresos de la Ruta", card_paradas)
        bar_paradas.addWidget(self.lbl_paradas_title)
        bar_paradas.addStretch(1)

        self.btn_agregar_parada = PrimaryPushButton("Agregar Parada", card_paradas, FIF.ADD)
        self.btn_agregar_parada.clicked.connect(self.handle_nueva_parada)
        bar_paradas.addWidget(self.btn_agregar_parada)

        self.btn_editar_parada = PushButton("Editar Parada", card_paradas, FIF.EDIT)
        self.btn_editar_parada.clicked.connect(self.handle_modificar_parada)
        bar_paradas.addWidget(self.btn_editar_parada)

        self.btn_eliminar_parada = PushButton("Remover Parada", card_paradas, FIF.DELETE)
        self.btn_eliminar_parada.clicked.connect(self.handle_eliminar_parada)
        bar_paradas.addWidget(self.btn_eliminar_parada)

        paradas_layout.addLayout(bar_paradas)

        self.table_paradas = TableWidget(card_paradas)
        self.table_paradas.setBorderVisible(True)
        self.table_paradas.setColumnCount(8)
        self.table_paradas.setHorizontalHeaderLabels([
            "Orden", "Codigo", "Nombre Estacion", "Distrito", "Hora Llegada", "Condicion de Parada", "Distancia Ant.", "Tiempo Ant."
        ])
        hp = self.table_paradas.horizontalHeader()
        if hp is not None:
            hp.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_paradas.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_paradas.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        paradas_layout.addWidget(self.table_paradas)

        v_layout.addWidget(card_paradas, stretch=5)
        self.stack_views.addWidget(tab_widget)

    # --------------------------------------------------------------------------
    # PESTANA 2: HORARIOS Y FRECUENCIAS
    # --------------------------------------------------------------------------
    def init_tab_horarios(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 8, 0, 0)
        v_layout.setSpacing(12)

        bar_h = QHBoxLayout()
        bar_h.addWidget(CaptionLabel("Seleccionar Ruta:", tab_widget))
        self.combo_horario_ruta = ComboBox(tab_widget)
        self.combo_horario_ruta.currentIndexChanged.connect(self.refresh_horarios)
        bar_h.addWidget(self.combo_horario_ruta, stretch=4)
        bar_h.addStretch(1)

        self.btn_nuevo_horario = PrimaryPushButton("Configurar Horario", tab_widget, FIF.ADD)
        self.btn_nuevo_horario.clicked.connect(self.handle_nuevo_horario)
        bar_h.addWidget(self.btn_nuevo_horario)

        self.btn_modificar_horario = PushButton("Modificar Horario", tab_widget, FIF.EDIT)
        self.btn_modificar_horario.clicked.connect(self.handle_modificar_horario)
        bar_h.addWidget(self.btn_modificar_horario)

        self.btn_eliminar_horario = PushButton("Eliminar Horario", tab_widget, FIF.DELETE)
        self.btn_eliminar_horario.clicked.connect(self.handle_eliminar_horario)
        bar_h.addWidget(self.btn_eliminar_horario)

        v_layout.addLayout(bar_h)

        self.table_horarios = TableWidget(tab_widget)
        self.table_horarios.setBorderVisible(True)
        self.table_horarios.setColumnCount(6)
        self.table_horarios.setHorizontalHeaderLabels([
            "Dia de la Semana", "Hora Inicio", "Hora Fin", "Frecuencia (Intervalo)", "Tipo de Horario", "Vigencia Desde"
        ])
        hh = self.table_horarios.horizontalHeader()
        if hh is not None:
            hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_horarios.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_horarios.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        v_layout.addWidget(self.table_horarios)

        self.stack_views.addWidget(tab_widget)

    # --------------------------------------------------------------------------
    # PESTANA 3: PROGRAMACION DE VIAJES Y DESPACHO
    # --------------------------------------------------------------------------
    def init_tab_viajes(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 8, 0, 0)
        v_layout.setSpacing(12)

        bar_v = QHBoxLayout()
        bar_v.setSpacing(10)

        bar_v.addWidget(CaptionLabel("Fecha:", tab_widget))
        self.txt_filtro_fecha = LineEdit(tab_widget)
        self.txt_filtro_fecha.setPlaceholderText("YYYY-MM-DD")
        self.txt_filtro_fecha.textChanged.connect(self.refresh_viajes)
        bar_v.addWidget(self.txt_filtro_fecha, stretch=2)

        bar_v.addWidget(CaptionLabel("Estado:", tab_widget))
        self.combo_filtro_estado_viaje = ComboBox(tab_widget)
        self.combo_filtro_estado_viaje.addItems(["(Todos)", "Programado", "En Curso", "Completado", "Retrasado", "Cancelado"])
        self.combo_filtro_estado_viaje.currentIndexChanged.connect(self.refresh_viajes)
        bar_v.addWidget(self.combo_filtro_estado_viaje, stretch=2)

        self.btn_programar_viaje = PrimaryPushButton("Programar Viaje", tab_widget, FIF.ADD)
        self.btn_programar_viaje.clicked.connect(self.handle_programar_viaje)
        bar_v.addWidget(self.btn_programar_viaje)

        self.btn_cancelar_viaje = PushButton("Cancelar Viaje", tab_widget, FIF.CLOSE)
        self.btn_cancelar_viaje.clicked.connect(self.handle_cancelar_viaje)
        bar_v.addWidget(self.btn_cancelar_viaje)

        self.btn_reprogramar_viaje = PushButton("Reprogramar / Modificar", tab_widget, FIF.SYNC)
        self.btn_reprogramar_viaje.clicked.connect(self.handle_reprogramar_viaje)
        bar_v.addWidget(self.btn_reprogramar_viaje)

        self.btn_eliminar_viaje = PushButton("Eliminar Viaje", tab_widget, FIF.DELETE)
        self.btn_eliminar_viaje.clicked.connect(self.handle_eliminar_viaje)
        bar_v.addWidget(self.btn_eliminar_viaje)

        v_layout.addLayout(bar_v)

        self.table_viajes = TableWidget(tab_widget)
        self.table_viajes.setBorderVisible(True)
        self.table_viajes.setColumnCount(10)
        self.table_viajes.setHorizontalHeaderLabels([
            "Numero Viaje", "Ruta", "Linea", "Fecha", "Prog. Salida", "Prog. Llegada", "Tren Asignado", "Maquinista", "Estado", "Pasajeros Estimados"
        ])
        hv = self.table_viajes.horizontalHeader()
        if hv is not None:
            hv.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_viajes.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_viajes.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        v_layout.addWidget(self.table_viajes)

        self.stack_views.addWidget(tab_widget)

    # --------------------------------------------------------------------------
    # PESTANA 4: PROXIMOS ARRIBOS E INCIDENTES
    # --------------------------------------------------------------------------
    def init_tab_arribos(self):
        tab_widget = QWidget()
        v_layout = QVBoxLayout(tab_widget)
        v_layout.setContentsMargins(0, 8, 0, 0)
        v_layout.setSpacing(12)

        # Seccion Superior: Proximos arribos por estacion
        card_arribos = CardWidget(tab_widget)
        arribos_layout = QVBoxLayout(card_arribos)
        arribos_layout.setContentsMargins(16, 12, 16, 12)
        arribos_layout.setSpacing(8)

        bar_arr = QHBoxLayout()
        bar_arr.addWidget(StrongBodyLabel("Proximos Viajes Programados por Estacion", card_arribos))
        bar_arr.addStretch(1)
        bar_arr.addWidget(CaptionLabel("Seleccionar Estacion:", card_arribos))
        self.combo_estacion_arribo = ComboBox(card_arribos)
        estaciones = m2_routes_service.get_estaciones_combo()
        for e in estaciones:
            self.combo_estacion_arribo.addItem(f"{e['NOMBRE']} ({e['CODIGO']})", userData=_safe_int(e.get("ID_ESTACION", 0)))
        self.combo_estacion_arribo.currentIndexChanged.connect(self.refresh_arribos_estacion)
        bar_arr.addWidget(self.combo_estacion_arribo, stretch=3)
        arribos_layout.addLayout(bar_arr)

        self.table_arribos = TableWidget(card_arribos)
        self.table_arribos.setBorderVisible(True)
        self.table_arribos.setColumnCount(7)
        self.table_arribos.setHorizontalHeaderLabels([
            "Numero Viaje", "Ruta", "Linea", "Destino Final", "Arribo Estimado", "Tren", "Estado"
        ])
        ha = self.table_arribos.horizontalHeader()
        if ha is not None:
            ha.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_arribos.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_arribos.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        arribos_layout.addWidget(self.table_arribos)
        v_layout.addWidget(card_arribos, stretch=5)

        # Seccion Inferior: Rutas Afectadas por Incidentes
        card_afectaciones = CardWidget(tab_widget)
        afec_layout = QVBoxLayout(card_afectaciones)
        afec_layout.setContentsMargins(16, 12, 16, 12)
        afec_layout.setSpacing(8)

        bar_afec = QHBoxLayout()
        bar_afec.addWidget(StrongBodyLabel("Rutas Afectadas por Incidentes Activos", card_afectaciones))
        bar_afec.addStretch(1)

        self.btn_cancelar_afectados = PushButton("Cancelar Viajes Afectados en Cascada", card_afectaciones, FIF.CLOSE)
        self.btn_cancelar_afectados.clicked.connect(self.handle_cancelar_viajes_afectados)
        bar_afec.addWidget(self.btn_cancelar_afectados)
        afec_layout.addLayout(bar_afec)

        self.table_afectaciones = TableWidget(card_afectaciones)
        self.table_afectaciones.setBorderVisible(True)
        self.table_afectaciones.setColumnCount(7)
        self.table_afectaciones.setHorizontalHeaderLabels([
            "Codigo Ruta", "Linea", "Incidente", "Severidad", "Elemento Afectado", "Tipo Afectacion", "Inicio Incidente"
        ])
        hf = self.table_afectaciones.horizontalHeader()
        if hf is not None:
            hf.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_afectaciones.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table_afectaciones.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        afec_layout.addWidget(self.table_afectaciones)

        v_layout.addWidget(card_afectaciones, stretch=4)
        self.stack_views.addWidget(tab_widget)

    # ==========================================================================
    # LOGICA DE CONTROL Y PESTANAS
    # ==========================================================================

    def on_tab_changed(self, key: str):
        if key == "tab_rutas":
            self.stack_views.setCurrentIndex(0)
            self.refresh_rutas()
        elif key == "tab_horarios":
            self.stack_views.setCurrentIndex(1)
            self.refresh_horarios()
        elif key == "tab_viajes":
            self.stack_views.setCurrentIndex(2)
            self.refresh_viajes()
        else:
            self.stack_views.setCurrentIndex(3)
            self.refresh_arribos_estacion()
            self.refresh_afectaciones()

    def load_all_data(self):
        self.refresh_rutas()
        self.populate_rutas_combos()

    def populate_rutas_combos(self):
        rutas = m2_routes_service.get_rutas()
        self.combo_horario_ruta.blockSignals(True)
        self.combo_horario_ruta.clear()
        for r in rutas:
            self.combo_horario_ruta.addItem(f"Ruta {r['CODIGO']} ({r['SENTIDO']})", userData=_safe_int(r.get("ID_RUTA", 0)))
        self.combo_horario_ruta.blockSignals(False)

    # --------------------------------------------------------------------------
    # ACCIONES PESTANA 1: RUTAS
    # --------------------------------------------------------------------------

    def refresh_rutas(self):
        linea_id = self.combo_filtro_linea.currentData()
        self.rutas_cache = m2_routes_service.get_rutas(linea_id)
        self.apply_rutas_filter()

    def apply_rutas_filter(self):
        query = self.search_rutas.text().strip().lower()
        self.table_rutas.setRowCount(0)

        for r in self.rutas_cache:
            cod = str(r.get("CODIGO", "")).lower()
            orig = str(r.get("ORIGEN", "")).lower()
            dest = str(r.get("DESTINO", "")).lower()

            if query and query not in cod and query not in orig and query not in dest:
                continue

            row = self.table_rutas.rowCount()
            self.table_rutas.insertRow(row)

            items = [
                str(r.get("CODIGO", "")),
                f"Linea {r.get('CODIGO_LINEA', '')}",
                str(r.get("TIPO_SERVICIO", "")),
                str(r.get("SENTIDO", "")),
                str(r.get("ORIGEN", "")),
                str(r.get("DESTINO", "")),
                f"{_safe_float(r.get('DISTANCIA_TOTAL_KM', 0.0)):.1f} km",
                f"{_safe_int(r.get('DURACION_ESTIMADA_MIN', 0))} min",
                str(r.get("ESTADO", ""))
            ]
            for col, txt in enumerate(items):
                self.table_rutas.setItem(row, col, QTableWidgetItem(txt))

            # Guardar objeto completo en la primera columna
            first_item = self.table_rutas.item(row, 0)
            if first_item is not None:
                first_item.setData(Qt.ItemDataRole.UserRole, r)

        if self.table_rutas.rowCount() > 0:
            self.table_rutas.selectRow(0)

    def on_ruta_selected(self):
        selected_rows = self.table_rutas.selectedItems()
        if not selected_rows:
            return
        first_item = selected_rows[0]
        if first_item is None:
            return
        r = first_item.data(Qt.ItemDataRole.UserRole)
        if not r:
            return
        self.selected_route_id = _safe_int(r.get("ID_RUTA", 0))
        self.lbl_paradas_title.setText(f"Secuencia de Paradas de la Ruta {r['CODIGO']} ({r['SENTIDO']} - {r['TIPO_SERVICIO']})")
        self.refresh_paradas()

    def refresh_paradas(self):
        if not self.selected_route_id:
            self.table_paradas.setRowCount(0)
            return
        paradas = m2_routes_service.get_paradas_ruta(self.selected_route_id)
        self.table_paradas.setRowCount(0)

        for p in paradas:
            row = self.table_paradas.rowCount()
            self.table_paradas.insertRow(row)

            cond_texto = "Parada Local" if p.get("SE_DETIENE") == "S" else "Paso Expreso Sin Parada"
            items = [
                str(p.get("ORDEN_LLEGADA", "")),
                str(p.get("CODIGO_ESTACION", "")),
                str(p.get("NOMBRE_ESTACION", "")),
                str(p.get("DISTRITO", "")),
                str(p.get("HORA_LLEGADA", "-") or "-"),
                cond_texto,
                f"{_safe_float(p.get('DISTANCIA_DESDE_ANTERIOR_KM', 0.0)):.1f} km",
                f"{_safe_int(p.get('TIEMPO_DESDE_ANTERIOR_MIN', 0))} min"
            ]
            for col, txt in enumerate(items):
                self.table_paradas.setItem(row, col, QTableWidgetItem(txt))

            first_item = self.table_paradas.item(row, 0)
            if first_item is not None:
                first_item.setData(Qt.ItemDataRole.UserRole, p)

    def handle_nueva_ruta(self):
        dlg = RutaDialog(self.window())
        if dlg.exec():
            datos = dlg.get_data()
            res = m2_routes_service.crear_ruta(datos)
            if res.get("success"):
                InfoBar.success("Ruta Creada", res.get("mensaje", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)
                self.refresh_rutas()
                self.populate_rutas_combos()
            else:
                InfoBar.error("Error al Crear Ruta", res.get("error", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)

    def handle_modificar_ruta(self):
        selected_rows = self.table_rutas.selectedItems()
        if not selected_rows:
            InfoBar.warning("Atencion", "Selecciona una ruta de la tabla para modificarla.", parent=self, position=InfoBarPosition.TOP_RIGHT)
            return
        item = selected_rows[0]
        if item is None:
            return
        r = item.data(Qt.ItemDataRole.UserRole)
        dlg = RutaDialog(self.window(), ruta_data=r)
        if dlg.exec():
            datos = dlg.get_data()
            res = m2_routes_service.modificar_ruta(_safe_int(r.get("ID_RUTA", 0)), datos)
            if res.get("success"):
                InfoBar.success("Ruta Modificada", res.get("mensaje", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)
                self.refresh_rutas()
            else:
                InfoBar.error("Error al Modificar", res.get("error", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)

    def handle_cambiar_estado_ruta(self):
        selected_rows = self.table_rutas.selectedItems()
        if not selected_rows:
            InfoBar.warning("Atencion", "Selecciona una ruta para conmutar su estado.", parent=self, position=InfoBarPosition.TOP_RIGHT)
            return
        item = selected_rows[0]
        if item is None:
            return
        r = item.data(Qt.ItemDataRole.UserRole)
        estado_actual = r.get("ESTADO", "Activa")
        nuevo = "Cerrada Temporalmente" if estado_actual == "Activa" else "Activa"
        res = m2_routes_service.cambiar_estado_ruta(_safe_int(r.get("ID_RUTA", 0)), nuevo)
        if res.get("success"):
            InfoBar.success("Estado de Ruta", res.get("mensaje", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)
            self.refresh_rutas()
        else:
            InfoBar.error("Error", res.get("error", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)

    def handle_eliminar_ruta(self):
        selected_rows = self.table_rutas.selectedItems()
        if not selected_rows:
            InfoBar.warning("Atencion", "Selecciona una ruta de la tabla para eliminarla.", parent=self, position=InfoBarPosition.TOP_RIGHT)
            return
        item = selected_rows[0]
        if item is None:
            return
        r = item.data(Qt.ItemDataRole.UserRole)
        if not r:
            return
        rid = _safe_int(r.get("ID_RUTA", 0))
        codigo = str(r.get("CODIGO", ""))

        deps = m2_routes_service.get_dependencias_ruta(rid)
        paradas = deps.get("paradas", 0)
        horarios = deps.get("horarios", 0)
        viajes = deps.get("viajes", 0)

        msg = (
            f"¿Deseas eliminar permanentemente la Ruta '{codigo}' (ID #{rid})?\n\n"
            f"Se eliminaran en cascada en una transaccion atomica:\n"
            f"- {paradas} parada(s) secuencial(es) (RUTA_DETALLE)\n"
            f"- {horarios} horario(s) configurado(s) (HORARIO)\n"
            f"- {viajes} viaje(s) programado(s) y sus validaciones (VIAJE_PROGRAMADO / VIAJE_PASAJERO)\n\n"
            "Esta accion no se puede deshacer."
        )

        parent_w = self.window() if self.window() is not None else self
        dlg = MessageBox("Confirmar Eliminacion de Ruta", msg, parent_w)
        if dlg.exec():
            res = m2_routes_service.eliminar_ruta(rid)
            if res.get("success"):
                InfoBar.success("Ruta Eliminada", res.get("mensaje", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)
                self.selected_route_id = None
                self.table_paradas.setRowCount(0)
                self.lbl_paradas_title.setText("Secuencia de Paradas y Saltos Expresos de la Ruta")
                self.refresh_rutas()
                self.populate_rutas_combos()
            else:
                InfoBar.error("Error al Eliminar Ruta", res.get("error", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)

    def handle_nueva_parada(self):
        if not self.selected_route_id:
            InfoBar.warning("Atencion", "Selecciona primero una ruta en la lista superior.", parent=self, position=InfoBarPosition.TOP_RIGHT)
            return
        dlg = ParadaRutaDialog(self.window(), ruta_id=self.selected_route_id)
        if dlg.exec():
            datos = dlg.get_data()
            res = m2_routes_service.agregar_parada_ruta(datos)
            if res.get("success"):
                InfoBar.success("Parada Registrada", res.get("mensaje", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)
                self.refresh_paradas()
            else:
                InfoBar.error("Error al Asociar Parada", res.get("error", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)

    def handle_modificar_parada(self):
        selected_rows = self.table_paradas.selectedItems()
        if not selected_rows:
            InfoBar.warning("Atencion", "Selecciona la parada que deseas modificar.", parent=self, position=InfoBarPosition.TOP_RIGHT)
            return
        item = selected_rows[0]
        if item is None:
            return
        p = item.data(Qt.ItemDataRole.UserRole)
        dlg = ParadaRutaDialog(self.window(), ruta_id=self.selected_route_id or 0, parada_data=p)
        if dlg.exec():
            datos = dlg.get_data()
            res = m2_routes_service.modificar_parada_ruta(_safe_int(p.get("ID_RUTA_DETALLE", 0)), datos)
            if res.get("success"):
                InfoBar.success("Parada Actualizada", res.get("mensaje", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)
                self.refresh_paradas()
            else:
                InfoBar.error("Error", res.get("error", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)

    def handle_eliminar_parada(self):
        selected_rows = self.table_paradas.selectedItems()
        if not selected_rows:
            InfoBar.warning("Atencion", "Selecciona la parada que deseas desvincular.", parent=self, position=InfoBarPosition.TOP_RIGHT)
            return
        item = selected_rows[0]
        if item is None:
            return
        p = item.data(Qt.ItemDataRole.UserRole)
        res = m2_routes_service.eliminar_parada_ruta(_safe_int(p.get("ID_RUTA_DETALLE", 0)))
        if res.get("success"):
            InfoBar.success("Parada Removida", res.get("mensaje", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)
            self.refresh_paradas()
        else:
            InfoBar.error("Error", res.get("error", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)

    # --------------------------------------------------------------------------
    # ACCIONES PESTANA 2: HORARIOS
    # --------------------------------------------------------------------------

    def refresh_horarios(self):
        ruta_id = self.combo_horario_ruta.currentData()
        if not ruta_id:
            self.table_horarios.setRowCount(0)
            return
        horarios = m2_routes_service.get_horarios_ruta(_safe_int(ruta_id))
        self.table_horarios.setRowCount(0)

        for h in horarios:
            row = self.table_horarios.rowCount()
            self.table_horarios.insertRow(row)

            items = [
                str(h.get("DIA_SEMANA", "")),
                str(h.get("HORA_INICIO", "")),
                str(h.get("HORA_FIN", "")),
                f"Cada {_safe_int(h.get('FRECUENCIA_MINUTOS', 0))} min",
                str(h.get("TIPO_SERVICIO", "")),
                str(h.get("VIGENCIA_DESDE", ""))
            ]
            for col, txt in enumerate(items):
                self.table_horarios.setItem(row, col, QTableWidgetItem(txt))

            first_item = self.table_horarios.item(row, 0)
            if first_item is not None:
                first_item.setData(Qt.ItemDataRole.UserRole, h)

    def handle_nuevo_horario(self):
        ruta_id = self.combo_horario_ruta.currentData()
        if not ruta_id:
            InfoBar.warning("Atencion", "Selecciona una ruta para configurar su horario.", parent=self, position=InfoBarPosition.TOP_RIGHT)
            return
        dlg = HorarioDialog(self.window(), ruta_id=_safe_int(ruta_id))
        if dlg.exec():
            datos = dlg.get_data()
            res = m2_routes_service.crear_horario(datos)
            if res.get("success"):
                InfoBar.success("Horario Configurado", res.get("mensaje", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)
                self.refresh_horarios()
            else:
                InfoBar.error("Error al Crear Horario", res.get("error", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)

    def handle_modificar_horario(self):
        selected_rows = self.table_horarios.selectedItems()
        if not selected_rows:
            InfoBar.warning("Atencion", "Selecciona el horario que deseas modificar.", parent=self, position=InfoBarPosition.TOP_RIGHT)
            return
        item = selected_rows[0]
        if item is None:
            return
        h = item.data(Qt.ItemDataRole.UserRole)
        if not h:
            return
        hid = _safe_int(h.get("ID_HORARIO", 0))
        rid = _safe_int(h.get("RUTA_ID", self.combo_horario_ruta.currentData() or 0))

        parent_w = self.window() if self.window() is not None else self
        dlg = HorarioDialog(parent_w, ruta_id=rid, horario_data=h)
        if dlg.exec():
            datos = dlg.get_data()
            res = m2_routes_service.modificar_horario(hid, datos)
            if res.get("success"):
                InfoBar.success("Horario Actualizado", res.get("mensaje", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)
                self.refresh_horarios()
            else:
                InfoBar.error("Error al Modificar Horario", res.get("error", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)

    def handle_eliminar_horario(self):
        selected_rows = self.table_horarios.selectedItems()
        if not selected_rows:
            InfoBar.warning("Atencion", "Selecciona el horario que deseas eliminar.", parent=self, position=InfoBarPosition.TOP_RIGHT)
            return
        item = selected_rows[0]
        if item is None:
            return
        h = item.data(Qt.ItemDataRole.UserRole)
        res = m2_routes_service.eliminar_horario(_safe_int(h.get("ID_HORARIO", 0)))
        if res.get("success"):
            InfoBar.success("Horario Eliminado", res.get("mensaje", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)
            self.refresh_horarios()
        else:
            InfoBar.error("Error", res.get("error", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)

    # --------------------------------------------------------------------------
    # ACCIONES PESTANA 3: VIAJES
    # --------------------------------------------------------------------------

    def refresh_viajes(self):
        fecha = self.txt_filtro_fecha.text().strip() or None
        estado = self.combo_filtro_estado_viaje.currentText()
        viajes = m2_routes_service.get_viajes_programados(fecha=fecha, estado=estado)
        self.table_viajes.setRowCount(0)

        for v in viajes:
            row = self.table_viajes.rowCount()
            self.table_viajes.insertRow(row)

            pasajeros_val = v.get("CANTIDAD_ESTIMADA_PASAJEROS")
            pasajeros_str = str(_safe_int(pasajeros_val)) if pasajeros_val is not None and str(pasajeros_val).strip() != "" and str(pasajeros_val) != "-" else "-"

            items = [
                str(v.get("NUMERO_VIAJE", "")),
                str(v.get("CODIGO_RUTA", "")),
                f"Linea {v.get('CODIGO_LINEA', '')}",
                str(v.get("FECHA", "")),
                str(v.get("HORA_PROG_SALIDA", "")),
                str(v.get("HORA_PROG_LLEGADA", "")),
                f"{v.get('CODIGO_TREN', '')} ({v.get('MODELO_TREN', '')})",
                str(v.get("CONDUCTOR", "")),
                str(v.get("ESTADO", "")),
                pasajeros_str
            ]
            for col, txt in enumerate(items):
                self.table_viajes.setItem(row, col, QTableWidgetItem(txt))

            first_item = self.table_viajes.item(row, 0)
            if first_item is not None:
                first_item.setData(Qt.ItemDataRole.UserRole, v)

    def handle_programar_viaje(self):
        dlg = ProgramarViajeDialog(self.window(), ruta_preseleccionada_id=self.selected_route_id)
        if dlg.exec():
            datos = dlg.get_data()
            res = m2_routes_service.programar_nuevo_viaje(
                ruta_id=_safe_int(datos.get("ruta_id", 0)),
                fecha_str=datos["fecha"],
                hora_salida_str=datos["hora_salida"],
                hora_llegada_str=datos["hora_llegada"],
                tren_id=_safe_int(datos.get("tren_id", 0)),
                conductor_id=_safe_int(datos.get("conductor_id", 0)),
                estado=datos.get("estado"),
                cantidad_estimada_pasajeros=datos.get("cantidad_estimada_pasajeros")
            )
            if res.get("success"):
                InfoBar.success("Despacho Exitoso", res.get("mensaje", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)
                self.refresh_viajes()
            else:
                InfoBar.error("Validacion Fallida", res.get("error", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)

    def handle_cancelar_viaje(self):
        selected_rows = self.table_viajes.selectedItems()
        if not selected_rows:
            InfoBar.warning("Atencion", "Selecciona un viaje para cancelarlo.", parent=self, position=InfoBarPosition.TOP_RIGHT)
            return
        item = selected_rows[0]
        if item is None:
            return
        v = item.data(Qt.ItemDataRole.UserRole)
        res = m2_routes_service.cancelar_viaje(_safe_int(v.get("ID_VIAJE", 0)))
        if res.get("success"):
            InfoBar.success("Viaje Cancelado", res.get("mensaje", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)
            self.refresh_viajes()
        else:
            InfoBar.error("Error", res.get("error", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)

    def handle_reprogramar_viaje(self):
        selected_rows = self.table_viajes.selectedItems()
        if not selected_rows:
            InfoBar.warning("Atencion", "Selecciona un viaje para reprogramarlo o modificarlo.", parent=self, position=InfoBarPosition.TOP_RIGHT)
            return
        item = selected_rows[0]
        if item is None:
            return
        v = item.data(Qt.ItemDataRole.UserRole)
        if not v:
            return
        vid = _safe_int(v.get("ID_VIAJE", 0))

        parent_w = self.window() if self.window() is not None else self
        dlg = EditarViajeDialog(parent_w, viaje_data=v)
        if dlg.exec():
            datos = dlg.get_data()
            res = m2_routes_service.modificar_viaje(vid, datos)
            if res.get("success"):
                InfoBar.success("Viaje Modificado", res.get("mensaje", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)
                self.refresh_viajes()
            else:
                InfoBar.error("Error al Modificar Viaje", res.get("error", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)

    def handle_eliminar_viaje(self):
        selected_rows = self.table_viajes.selectedItems()
        if not selected_rows:
            InfoBar.warning("Atencion", "Selecciona un viaje para eliminarlo.", parent=self, position=InfoBarPosition.TOP_RIGHT)
            return
        item = selected_rows[0]
        if item is None:
            return
        v = item.data(Qt.ItemDataRole.UserRole)
        if not v:
            return
        vid = _safe_int(v.get("ID_VIAJE", 0))
        num_viaje = str(v.get("NUMERO_VIAJE", ""))

        parent_w = self.window() if self.window() is not None else self
        dlg = MessageBox(
            "Confirmar Eliminacion de Viaje",
            f"¿Deseas eliminar permanentemente el viaje {num_viaje} (ID #{vid})?",
            parent_w
        )
        if dlg.exec():
            res = m2_routes_service.eliminar_viaje(vid)
            if res.get("success"):
                InfoBar.success("Viaje Eliminado", res.get("mensaje", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)
                self.refresh_viajes()
            else:
                InfoBar.error("Error al Eliminar Viaje", res.get("error", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)

    # --------------------------------------------------------------------------
    # ACCIONES PESTANA 4: PROXIMOS ARRIBOS E INCIDENTES
    # --------------------------------------------------------------------------

    def refresh_arribos_estacion(self):
        eid = self.combo_estacion_arribo.currentData()
        if not eid:
            self.table_arribos.setRowCount(0)
            return
        arribos = m2_routes_service.get_proximos_viajes_estacion(_safe_int(eid))
        self.table_arribos.setRowCount(0)

        for a in arribos:
            row = self.table_arribos.rowCount()
            self.table_arribos.insertRow(row)

            items = [
                str(a.get("NUMERO_VIAJE", "")),
                f"Ruta {a.get('CODIGO_RUTA', '')} ({a.get('TIPO_SERVICIO', '')})",
                f"Linea {a.get('CODIGO_LINEA', '')}",
                str(a.get("DESTINO_FINAL", "")),
                str(a.get("ARRIBO_ESTIMADO", "-") or "-"),
                str(a.get("TREN", "Sin Tren")),
                str(a.get("ESTADO", ""))
            ]
            for col, txt in enumerate(items):
                self.table_arribos.setItem(row, col, QTableWidgetItem(txt))

    def refresh_afectaciones(self):
        afectadas = m2_routes_service.get_rutas_afectadas_incidentes()
        self.table_afectaciones.setRowCount(0)

        for af in afectadas:
            row = self.table_afectaciones.rowCount()
            self.table_afectaciones.insertRow(row)

            items = [
                f"Ruta {af.get('CODIGO_RUTA', '')}",
                f"Linea {af.get('CODIGO_LINEA', '')}",
                f"{af.get('NUMERO_INCIDENTE', '')} - {af.get('TIPO_INCIDENTE', '')}",
                str(af.get("NIVEL_SEVERIDAD", "")),
                str(af.get("TIPO_ELEMENTO", "")),
                str(af.get("TIPO_AFECTACION", "")),
                str(af.get("INICIO_INCIDENTE", ""))
            ]
            for col, txt in enumerate(items):
                self.table_afectaciones.setItem(row, col, QTableWidgetItem(txt))

            first_item = self.table_afectaciones.item(row, 0)
            if first_item is not None:
                first_item.setData(Qt.ItemDataRole.UserRole, af)

    def handle_cancelar_viajes_afectados(self):
        selected_rows = self.table_afectaciones.selectedItems()
        if not selected_rows:
            InfoBar.warning("Atencion", "Selecciona un incidente de la tabla para cancelar sus viajes afectados.", parent=self, position=InfoBarPosition.TOP_RIGHT)
            return
        item = selected_rows[0]
        if item is None:
            return
        af = item.data(Qt.ItemDataRole.UserRole)
        inc_id = _safe_int(af.get("ID_INCIDENTE", 0))
        res = m2_routes_service.cancelar_viajes_por_incidente(inc_id)
        if res.get("success"):
            InfoBar.success("Despacho de Contingencia", res.get("mensaje", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)
            self.refresh_afectaciones()
            self.refresh_viajes()
        else:
            InfoBar.error("Error", res.get("error", ""), parent=self, position=InfoBarPosition.TOP_RIGHT)
