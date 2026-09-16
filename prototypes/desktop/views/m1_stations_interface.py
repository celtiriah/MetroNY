"""
Interfaz de Administración de la Red y Estaciones.
Módulo 1 del Sistema de Gestión del Metro de Nueva York (MTA NYCT).
Implementa:
1. Crear, modificar, consultar y desactivar líneas.
2. Crear y modificar estaciones.
3. Asociar estaciones con líneas.
4. Definir el orden secuencial de las estaciones.
5. Registrar distancias y tiempos entre estaciones.
6. Administrar plataformas de estación.
7. Definir estaciones de transferencia.
8. Consultar todas las líneas que pasan por una estación.
9. Consultar todas las estaciones de una línea en el orden correcto.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QHeaderView,
    QTableWidgetItem, QStackedWidget, QFrame
)
from PyQt5.QtCore import Qt

from qfluentwidgets import (
    TitleLabel, SubtitleLabel, CaptionLabel, BodyLabel, StrongBodyLabel,
    CardWidget, ComboBox, LineEdit, SearchLineEdit, DoubleSpinBox, SpinBox,
    PrimaryPushButton, PushButton, TableWidget, InfoBar, InfoBarPosition,
    SegmentedWidget, CheckBox, MessageBoxBase, FluentIcon as FIF
)

from services import m1_network_service as network_service


# ==============================================================================
# DIÁLOGOS MODALES FLUENT
# ==============================================================================

class EstacionDialog(MessageBoxBase):
    """Diálogo modal para crear o modificar una estación."""
    def __init__(self, estacion_data=None, parent=None):
        super().__init__(parent or None)
        data = estacion_data or {}
        self.estacion_data = estacion_data
        self.is_edit = estacion_data is not None

        title_text = "Modificar Estación" if self.is_edit else "Nueva Estación de Metro"
        self.titleLabel = SubtitleLabel(title_text, self)
        self.viewLayout.addWidget(self.titleLabel)

        form_layout = QGridLayout()
        form_layout.setSpacing(10)

        # Código
        form_layout.addWidget(CaptionLabel("Código Único:", self), 0, 0)
        self.txt_codigo = LineEdit(self)
        self.txt_codigo.setPlaceholderText("Ej: EST-01, TSQ-42")
        if self.is_edit:
            self.txt_codigo.setText(str(data.get("CODIGO", "")))
            self.txt_codigo.setEnabled(False)
        form_layout.addWidget(self.txt_codigo, 0, 1)

        # Nombre
        form_layout.addWidget(CaptionLabel("Nombre de la Estación:", self), 1, 0)
        self.txt_nombre = LineEdit(self)
        self.txt_nombre.setPlaceholderText("Ej: Times Square - 42nd St")
        if self.is_edit:
            self.txt_nombre.setText(str(data.get("NOMBRE", "")))
        form_layout.addWidget(self.txt_nombre, 1, 1)

        # Dirección
        form_layout.addWidget(CaptionLabel("Dirección / Calle:", self), 2, 0)
        self.txt_direccion = LineEdit(self)
        self.txt_direccion.setPlaceholderText("Ej: Broadway & 7th Ave")
        if self.is_edit:
            self.txt_direccion.setText(str(data.get("DIRECCION", "")))
        form_layout.addWidget(self.txt_direccion, 2, 1)

        # Distrito (Borough)
        form_layout.addWidget(CaptionLabel("Distrito (Borough):", self), 3, 0)
        self.combo_distrito = ComboBox(self)
        distritos = ["Manhattan", "Brooklyn", "Queens", "The Bronx", "Staten Island"]
        self.combo_distrito.addItems(distritos)
        if self.is_edit and data.get("DISTRITO") in distritos:
            self.combo_distrito.setCurrentText(str(data.get("DISTRITO")))
        form_layout.addWidget(self.combo_distrito, 3, 1)

        # Tipo de Estación
        form_layout.addWidget(CaptionLabel("Tipo de Estación:", self), 4, 0)
        self.combo_tipo = ComboBox(self)
        tipos = ["Local", "Expresa", "Terminal", "Transferencia", "Cerrada Temporalmente"]
        self.combo_tipo.addItems(tipos)
        if self.is_edit and data.get("TIPO_ESTACION") in tipos:
            self.combo_tipo.setCurrentText(str(data.get("TIPO_ESTACION")))
        form_layout.addWidget(self.combo_tipo, 4, 1)

        # Coordenadas (Latitud y Longitud)
        form_layout.addWidget(CaptionLabel("Latitud WGS84:", self), 5, 0)
        self.spin_lat = DoubleSpinBox(self)
        self.spin_lat.setRange(-90.0, 90.0)
        self.spin_lat.setDecimals(6)
        lat_val = float(data.get("LATITUD", 40.7580)) if self.is_edit and data.get("LATITUD") != "-" else 40.7580
        self.spin_lat.setValue(lat_val)
        form_layout.addWidget(self.spin_lat, 5, 1)

        form_layout.addWidget(CaptionLabel("Longitud WGS84:", self), 6, 0)
        self.spin_lon = DoubleSpinBox(self)
        self.spin_lon.setRange(-180.0, 180.0)
        self.spin_lon.setDecimals(6)
        lon_val = float(data.get("LONGITUD", -73.9855)) if self.is_edit and data.get("LONGITUD") != "-" else -73.9855
        self.spin_lon.setValue(lon_val)
        form_layout.addWidget(self.spin_lon, 6, 1)

        # Horario
        form_layout.addWidget(CaptionLabel("Horario de Servicio:", self), 7, 0)
        self.txt_horario = LineEdit(self)
        self.txt_horario.setText(str(data.get("HORARIO_FUNCIONAMIENTO", "24/7")) if self.is_edit else "24/7")
        form_layout.addWidget(self.txt_horario, 7, 1)

        # Estado Operativo
        form_layout.addWidget(CaptionLabel("Estado Operativo:", self), 8, 0)
        self.combo_estado = ComboBox(self)
        estados = ["Operativa", "Cerrada", "Cerrada Temporalmente"]
        self.combo_estado.addItems(estados)
        if self.is_edit and data.get("ESTADO_OPERATIVO") in estados:
            self.combo_estado.setCurrentText(str(data.get("ESTADO_OPERATIVO")))
        form_layout.addWidget(self.combo_estado, 8, 1)

        # Checkboxes de Accesibilidad
        chk_layout = QVBoxLayout()
        self.chk_ada = CheckBox("Accesibilidad para personas con discapacidad (ADA)", self)
        self.chk_elevadores = CheckBox("Dispone de Elevadores en servicio", self)
        self.chk_escaleras = CheckBox("Dispone de Escaleras Eléctricas", self)

        if self.is_edit:
            self.chk_ada.setChecked(data.get("ACCESIBLE_DISCAPACIDAD") == "S")
            self.chk_elevadores.setChecked(data.get("ELEVADORES_DISPONIBLES") == "S")
            self.chk_escaleras.setChecked(data.get("ESCALERAS_ELECTRICAS_DISPONIBLES") == "S")
        else:
            self.chk_ada.setChecked(True)
            self.chk_elevadores.setChecked(True)
            self.chk_escaleras.setChecked(True)

        chk_layout.addWidget(self.chk_ada)
        chk_layout.addWidget(self.chk_elevadores)
        chk_layout.addWidget(self.chk_escaleras)
        form_layout.addLayout(chk_layout, 9, 0, 1, 2)

        self.viewLayout.addLayout(form_layout)
        self.yesButton.setText("Guardar Estación")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(440)

    def get_data(self) -> dict:
        return {
            "codigo": self.txt_codigo.text().strip(),
            "nombre": self.txt_nombre.text().strip(),
            "direccion": self.txt_direccion.text().strip(),
            "distrito": self.combo_distrito.currentText(),
            "tipo_estacion": self.combo_tipo.currentText(),
            "latitud": self.spin_lat.value(),
            "longitud": self.spin_lon.value(),
            "horario_funcionamiento": self.txt_horario.text().strip(),
            "estado_operativo": self.combo_estado.currentText(),
            "ada": self.chk_ada.isChecked(),
            "elevadores": self.chk_elevadores.isChecked(),
            "escaleras": self.chk_escaleras.isChecked(),
            "cantidad_accesos": 2,
            "cantidad_plataformas": 2
        }


class LineaDialog(MessageBoxBase):
    """Diálogo modal para crear o modificar una línea de metro."""
    def __init__(self, linea_data=None, estaciones=None, parent=None):
        super().__init__(parent or None)
        data = linea_data or {}
        self.linea_data = linea_data
        self.is_edit = linea_data is not None

        title_text = "Modificar Línea" if self.is_edit else "Nueva Línea de Metro"
        self.titleLabel = SubtitleLabel(title_text, self)
        self.viewLayout.addWidget(self.titleLabel)

        form_layout = QGridLayout()
        form_layout.setSpacing(10)

        # Código
        form_layout.addWidget(CaptionLabel("Código Identificador:", self), 0, 0)
        self.txt_codigo = LineEdit(self)
        self.txt_codigo.setPlaceholderText("Ej: A, 1, 7, L, N")
        if self.is_edit:
            self.txt_codigo.setText(str(data.get("CODIGO", "")))
            self.txt_codigo.setEnabled(False)
        form_layout.addWidget(self.txt_codigo, 0, 1)

        # Nombre
        form_layout.addWidget(CaptionLabel("Nombre Descriptivo:", self), 1, 0)
        self.txt_nombre = LineEdit(self)
        self.txt_nombre.setPlaceholderText("Ej: 8th Avenue Express, Flushing Line")
        if self.is_edit:
            self.txt_nombre.setText(str(data.get("NOMBRE", "")))
        form_layout.addWidget(self.txt_nombre, 1, 1)

        # Color oficial MTA
        form_layout.addWidget(CaptionLabel("Color Oficial (Hex):", self), 2, 0)
        self.txt_color = LineEdit(self)
        self.txt_color.setPlaceholderText("Ej: #0039A6, #EE352E, #B933AD")
        self.txt_color.setText(str(data.get("COLOR", "#0039A6")) if self.is_edit else "#0039A6")
        form_layout.addWidget(self.txt_color, 2, 1)

        # Tipo de Servicio
        form_layout.addWidget(CaptionLabel("Tipo de Servicio Principal:", self), 3, 0)
        self.combo_servicio = ComboBox(self)
        servicios = ["Local", "Expreso", "Nocturno", "Especial", "Temporal"]
        self.combo_servicio.addItems(servicios)
        if self.is_edit and data.get("TIPO_SERVICIO_PRINCIPAL") in servicios:
            self.combo_servicio.setCurrentText(str(data.get("TIPO_SERVICIO_PRINCIPAL")))
        form_layout.addWidget(self.combo_servicio, 3, 1)

        # Terminal de Origen
        form_layout.addWidget(CaptionLabel("Terminal de Origen:", self), 4, 0)
        self.combo_origen = ComboBox(self)
        self.combo_origen.addItem("(Sin asignar)", userData=None)
        for est in (estaciones or []):
            self.combo_origen.addItem(f"{est['NOMBRE']} ({est['CODIGO']})", est['ID_ESTACION'])
        if self.is_edit and data.get("ESTACION_ORIGEN_ID") and data.get("ESTACION_ORIGEN_ID") != "-":
            idx = self.combo_origen.findData(int(data["ESTACION_ORIGEN_ID"]))
            if idx >= 0:
                self.combo_origen.setCurrentIndex(idx)
        form_layout.addWidget(self.combo_origen, 4, 1)

        # Terminal de Destino
        form_layout.addWidget(CaptionLabel("Terminal de Destino:", self), 5, 0)
        self.combo_destino = ComboBox(self)
        self.combo_destino.addItem("(Sin asignar)", userData=None)
        for est in (estaciones or []):
            self.combo_destino.addItem(f"{est['NOMBRE']} ({est['CODIGO']})", est['ID_ESTACION'])
        if self.is_edit and data.get("ESTACION_DESTINO_ID") and data.get("ESTACION_DESTINO_ID") != "-":
            idx = self.combo_destino.findData(int(data["ESTACION_DESTINO_ID"]))
            if idx >= 0:
                self.combo_destino.setCurrentIndex(idx)
        form_layout.addWidget(self.combo_destino, 5, 1)

        # Longitud Aproximada en Km
        form_layout.addWidget(CaptionLabel("Longitud Total (km):", self), 6, 0)
        self.spin_longitud = DoubleSpinBox(self)
        self.spin_longitud.setRange(1.0, 150.0)
        self.spin_longitud.setDecimals(2)
        lon_km = float(data.get("LONGITUD_KM", 25.0)) if self.is_edit and data.get("LONGITUD_KM") != "-" else 25.0
        self.spin_longitud.setValue(lon_km)
        form_layout.addWidget(self.spin_longitud, 6, 1)

        # Operador Responsable
        form_layout.addWidget(CaptionLabel("Operador Responsable:", self), 7, 0)
        self.txt_operador = LineEdit(self)
        self.txt_operador.setText(str(data.get("OPERADOR_RESPONSABLE", "NYCT")) if self.is_edit else "NYCT")
        form_layout.addWidget(self.txt_operador, 7, 1)

        # Estado Operativo
        form_layout.addWidget(CaptionLabel("Estado Operativo:", self), 8, 0)
        self.combo_estado = ComboBox(self)
        estados = ["Activa", "Suspendida", "Fuera de Servicio"]
        self.combo_estado.addItems(estados)
        if self.is_edit and data.get("ESTADO_OPERATIVO") in estados:
            self.combo_estado.setCurrentText(str(data.get("ESTADO_OPERATIVO")))
        form_layout.addWidget(self.combo_estado, 8, 1)

        self.viewLayout.addLayout(form_layout)
        self.yesButton.setText("Guardar Línea")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(440)

    def get_data(self) -> dict:
        return {
            "codigo": self.txt_codigo.text().strip(),
            "nombre": self.txt_nombre.text().strip(),
            "color": self.txt_color.text().strip(),
            "tipo_servicio": self.combo_servicio.currentText(),
            "origen_id": self.combo_origen.currentData(),
            "destino_id": self.combo_destino.currentData(),
            "longitud_km": self.spin_longitud.value(),
            "operador": self.txt_operador.text().strip(),
            "estado_operativo": self.combo_estado.currentText()
        }


class PlataformaDialog(MessageBoxBase):
    """Diálogo modal para agregar o editar una plataforma."""
    def __init__(self, plataforma_data=None, parent=None):
        super().__init__(parent or None)
        data = plataforma_data or {}
        self.is_edit = plataforma_data is not None

        title_text = "Modificar Plataforma" if self.is_edit else "Agregar Plataforma a Estación"
        self.titleLabel = SubtitleLabel(title_text, self)
        self.viewLayout.addWidget(self.titleLabel)

        form = QGridLayout()
        form.setSpacing(10)

        form.addWidget(CaptionLabel("Identificador de Andén:", self), 0, 0)
        self.txt_identificador = LineEdit(self)
        self.txt_identificador.setPlaceholderText("Ej: Plat-1, Track 2, Andén Norte")
        if self.is_edit:
            self.txt_identificador.setText(str(data.get("IDENTIFICADOR", "")))
        form.addWidget(self.txt_identificador, 0, 1)

        form.addWidget(CaptionLabel("Dirección de Viaje:", self), 1, 0)
        self.combo_direccion = ComboBox(self)
        dirs = ["Uptown & The Bronx", "Downtown & Brooklyn", "Manhattan-bound", "Queens-bound", "Norte", "Sur"]
        self.combo_direccion.addItems(dirs)
        if self.is_edit and data.get("DIRECCION_VIAJE") in dirs:
            self.combo_direccion.setCurrentText(str(data.get("DIRECCION_VIAJE")))
        form.addWidget(self.combo_direccion, 1, 1)

        form.addWidget(CaptionLabel("Capacidad Aprox. (Pasajeros):", self), 2, 0)
        self.spin_capacidad = SpinBox(self)
        self.spin_capacidad.setRange(100, 5000)
        self.spin_capacidad.setValue(int(data.get("CAPACIDAD_APROXIMADA", 1000)) if self.is_edit else 1000)
        form.addWidget(self.spin_capacidad, 2, 1)

        form.addWidget(CaptionLabel("Estado Operativo:", self), 3, 0)
        self.combo_estado = ComboBox(self)
        estados = ["Operativa", "Mantenimiento", "Fuera de Servicio"]
        self.combo_estado.addItems(estados)
        if self.is_edit and data.get("ESTADO_OPERATIVO") in estados:
            self.combo_estado.setCurrentText(str(data.get("ESTADO_OPERATIVO")))
        form.addWidget(self.combo_estado, 3, 1)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Guardar Plataforma")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(380)

    def get_data(self) -> dict:
        return {
            "identificador": self.txt_identificador.text().strip(),
            "direccion_viaje": self.combo_direccion.currentText(),
            "capacidad": self.spin_capacidad.value(),
            "estado": self.combo_estado.currentText()
        }


class TransferenciaDialog(MessageBoxBase):
    """Diálogo modal para definir una transferencia entre líneas en una estación."""
    def __init__(self, lineas=None, parent=None):
        super().__init__(parent or None)
        self.titleLabel = SubtitleLabel("Definir Transferencia Peatonal", self)
        self.viewLayout.addWidget(self.titleLabel)

        form = QGridLayout()
        form.setSpacing(10)

        form.addWidget(CaptionLabel("Línea de Origen:", self), 0, 0)
        self.combo_origen = ComboBox(self)
        for l in (lineas or []):
            self.combo_origen.addItem(f"Línea {l['CODIGO']} - {l['NOMBRE']}", l['ID_LINEA'])
        form.addWidget(self.combo_origen, 0, 1)

        form.addWidget(CaptionLabel("Línea de Destino (Correspondencia):", self), 1, 0)
        self.combo_destino = ComboBox(self)
        for l in (lineas or []):
            self.combo_destino.addItem(f"Línea {l['CODIGO']} - {l['NOMBRE']}", l['ID_LINEA'])
        if len(lineas or []) > 1:
            self.combo_destino.setCurrentIndex(1)
        form.addWidget(self.combo_destino, 1, 1)

        form.addWidget(CaptionLabel("Tiempo Estimado de Caminata (min):", self), 2, 0)
        self.spin_tiempo = SpinBox(self)
        self.spin_tiempo.setRange(1, 25)
        self.spin_tiempo.setValue(3)
        form.addWidget(self.spin_tiempo, 2, 1)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Habilitar Transferencia")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(400)

    def get_data(self) -> dict:
        return {
            "linea_origen_id": self.combo_origen.currentData(),
            "linea_destino_id": self.combo_destino.currentData(),
            "tiempo_min": self.spin_tiempo.value()
        }


class AsociarEstacionDialog(MessageBoxBase):
    """Diálogo modal para asociar una estación a una línea definiendo orden, distancia y tiempo."""
    def __init__(self, estaciones_disponibles=None, next_order=1, tramo_data=None, parent=None):
        super().__init__(parent or None)
        data = tramo_data or {}
        self.is_edit = tramo_data is not None

        title_text = "Modificar Tramo de Línea" if self.is_edit else "Asociar Estación a Línea"
        self.titleLabel = SubtitleLabel(title_text, self)
        self.viewLayout.addWidget(self.titleLabel)

        form = QGridLayout()
        form.setSpacing(10)

        # Selector de Estación
        form.addWidget(CaptionLabel("Estación:", self), 0, 0)
        if self.is_edit:
            self.lbl_est_nom = BodyLabel(f"{data.get('NOMBRE_ESTACION')} ({data.get('CODIGO_ESTACION')})", self)
            form.addWidget(self.lbl_est_nom, 0, 1)
        else:
            self.combo_estacion = ComboBox(self)
            for est in (estaciones_disponibles or []):
                self.combo_estacion.addItem(f"{est['NOMBRE']} ({est['CODIGO']}) - {est['DISTRITO']}", est['ID_ESTACION'])
            form.addWidget(self.combo_estacion, 0, 1)

        # Orden secuencial
        form.addWidget(CaptionLabel("Orden Secuencial de Parada:", self), 1, 0)
        self.spin_orden = SpinBox(self)
        self.spin_orden.setRange(1, 150)
        self.spin_orden.setValue(int(data.get("ORDEN", next_order)) if self.is_edit else next_order)
        form.addWidget(self.spin_orden, 1, 1)

        # Distancia en Km
        form.addWidget(CaptionLabel("Distancia desde Estación Anterior (km):", self), 2, 0)
        self.spin_distancia = DoubleSpinBox(self)
        self.spin_distancia.setRange(0.1, 30.0)
        self.spin_distancia.setDecimals(2)
        dist_val = float(data.get("DISTANCIA_KM", 1.5)) if self.is_edit and data.get("DISTANCIA_KM") != "-" else 1.5
        self.spin_distancia.setValue(dist_val)
        form.addWidget(self.spin_distancia, 2, 1)

        # Tiempo estimado en minutos
        form.addWidget(CaptionLabel("Tiempo Estimado de Viaje (minutos):", self), 3, 0)
        self.spin_tiempo = SpinBox(self)
        self.spin_tiempo.setRange(1, 60)
        t_val = int(data.get("TIEMPO_ESTIMADO_MIN", 2)) if self.is_edit and data.get("TIEMPO_ESTIMADO_MIN") != "-" else 2
        self.spin_tiempo.setValue(t_val)
        form.addWidget(self.spin_tiempo, 3, 1)

        self.viewLayout.addLayout(form)
        self.yesButton.setText("Guardar Tramo")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(420)

    def get_data(self) -> dict:
        return {
            "estacion_id": self.combo_estacion.currentData() if not self.is_edit else None,
            "orden": self.spin_orden.value(),
            "distancia_km": self.spin_distancia.value(),
            "tiempo_min": self.spin_tiempo.value()
        }


# ==============================================================================
# INTERFAZ PRINCIPAL DE ESTACIONES Y RED (MÓDULO 1)
# ==============================================================================

class StationsInterface(QWidget):
    """
    Vista completa para el Módulo 1: Administración de la Red.
    Integra gestión de Estaciones (con plataformas y transferencias) y Líneas (con topología secuencial).
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("stationsInterface")

        self.selected_station_id = None
        self.selected_line_id = None
        self.estaciones_cache = []
        self.lineas_cache = []

        self.init_ui()
        self.load_all_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # Cabecera
        header_row = QHBoxLayout()
        v_title = QVBoxLayout()
        v_title.setSpacing(4)
        title = TitleLabel("Administración de la Red y Estaciones", self)
        subtitle = SubtitleLabel("Módulo 1: Control integral de infraestructura, líneas, topología secuencial, andenes y transferencias", self)
        v_title.addWidget(title)
        v_title.addWidget(subtitle)
        header_row.addLayout(v_title)
        header_row.addStretch(1)
        main_layout.addLayout(header_row)

        # Segmented Widget Maestro para alternar entre Estaciones y Líneas
        tabs_row = QHBoxLayout()
        self.segmented_master = SegmentedWidget(self)
        self.segmented_master.addItem("tab_estaciones", "Directorio y Gestión de Estaciones")
        self.segmented_master.addItem("tab_lineas", "Líneas y Topología de Red")
        self.segmented_master.currentItemChanged.connect(self.on_master_tab_changed)
        tabs_row.addWidget(self.segmented_master)

        main_layout.addLayout(tabs_row)

        # Stack de Vistas Principales
        self.stack_master = QStackedWidget(self)

        # ----------------------------------------------------------------------
        # VISTA 1: GESTIÓN DE ESTACIONES
        # ----------------------------------------------------------------------
        view_estaciones = QWidget()
        v_est_layout = QVBoxLayout(view_estaciones)
        v_est_layout.setContentsMargins(0, 8, 0, 0)
        v_est_layout.setSpacing(12)

        # Barra de Filtros y Acciones de Estaciones
        bar_est = QHBoxLayout()
        bar_est.setSpacing(10)

        self.search_est = SearchLineEdit(view_estaciones)
        self.search_est.setPlaceholderText("Buscar estación por nombre, código o calle...")
        self.search_est.setClearButtonEnabled(True)
        self.search_est.textChanged.connect(self.apply_station_filters)
        bar_est.addWidget(self.search_est, stretch=4)

        bar_est.addWidget(CaptionLabel("Distrito:", view_estaciones))
        self.combo_filtro_distrito = ComboBox(view_estaciones)
        self.combo_filtro_distrito.addItems(["(Todos)", "Manhattan", "Brooklyn", "Queens", "The Bronx", "Staten Island"])
        self.combo_filtro_distrito.currentIndexChanged.connect(self.apply_station_filters)
        bar_est.addWidget(self.combo_filtro_distrito, stretch=2)

        bar_est.addWidget(CaptionLabel("Estado:", view_estaciones))
        self.combo_filtro_estado = ComboBox(view_estaciones)
        self.combo_filtro_estado.addItems(["(Todos)", "Operativa", "Cerrada", "Cerrada Temporalmente"])
        self.combo_filtro_estado.currentIndexChanged.connect(self.apply_station_filters)
        bar_est.addWidget(self.combo_filtro_estado, stretch=2)

        self.chk_filtro_ada = CheckBox("Solo ADA", view_estaciones)
        self.chk_filtro_ada.stateChanged.connect(self.apply_station_filters)
        bar_est.addWidget(self.chk_filtro_ada)

        # Botones de Acción de Estación
        self.btn_nueva_estacion = PrimaryPushButton("Nueva Estación", view_estaciones, FIF.ADD)
        self.btn_nueva_estacion.clicked.connect(self.handle_nueva_estacion)
        bar_est.addWidget(self.btn_nueva_estacion)

        self.btn_modificar_estacion = PushButton("Modificar", view_estaciones, FIF.EDIT)
        self.btn_modificar_estacion.clicked.connect(self.handle_modificar_estacion)
        bar_est.addWidget(self.btn_modificar_estacion)

        self.btn_estado_estacion = PushButton("Cambiar Estado", view_estaciones, FIF.SYNC)
        self.btn_estado_estacion.clicked.connect(self.handle_cambiar_estado_estacion)
        bar_est.addWidget(self.btn_estado_estacion)

        v_est_layout.addLayout(bar_est)

        # Tabla Principal de Estaciones
        self.table_stations = TableWidget(view_estaciones)
        self.table_stations.setBorderVisible(True)
        self.table_stations.setColumnCount(8)
        self.table_stations.setHorizontalHeaderLabels([
            "Código", "Nombre", "Distrito", "Tipo", "Plataformas", "Líneas Conectadas", "Accesibilidad ADA", "Estado"
        ])
        header_s = self.table_stations.horizontalHeader()
        if header_s is not None:
            header_s.setSectionResizeMode(QHeaderView.Stretch)
        self.table_stations.setEditTriggers(TableWidget.NoEditTriggers)
        self.table_stations.setSelectionBehavior(TableWidget.SelectRows)
        self.table_stations.itemSelectionChanged.connect(self.on_station_row_selected)
        v_est_layout.addWidget(self.table_stations, stretch=5)

        # Inspector Inferior de la Estación Seleccionada
        card_est_inspector = CardWidget(view_estaciones)
        card_insp_layout = QVBoxLayout(card_est_inspector)
        card_insp_layout.setContentsMargins(16, 12, 16, 12)
        card_insp_layout.setSpacing(8)

        # Encabezado del inspector
        insp_header = QHBoxLayout()
        self.lbl_insp_estacion = StrongBodyLabel("Selecciona una estación para inspeccionar sus plataformas, líneas y transferencias", card_est_inspector)
        insp_header.addWidget(self.lbl_insp_estacion)
        insp_header.addStretch(1)

        self.segmented_est_detail = SegmentedWidget(card_est_inspector)
        self.segmented_est_detail.addItem("sub_plataformas", "Andenes / Plataformas")
        self.segmented_est_detail.addItem("sub_lineas", "Líneas que la Conectan")
        self.segmented_est_detail.addItem("sub_transferencias", "Transferencias Peatonales")
        self.segmented_est_detail.currentItemChanged.connect(self.on_station_detail_tab_changed)
        insp_header.addWidget(self.segmented_est_detail)
        card_insp_layout.addLayout(insp_header)

        # Stack de Detalles de Estación
        self.stack_est_detail = QStackedWidget(card_est_inspector)

        # Sub-Tab 1: Plataformas
        tab_plat = QWidget()
        v_plat = QVBoxLayout(tab_plat)
        v_plat.setContentsMargins(0, 4, 0, 0)
        v_plat.setSpacing(6)
        bar_plat = QHBoxLayout()
        self.btn_add_plat = PrimaryPushButton("Agregar Plataforma", tab_plat, FIF.ADD)
        self.btn_add_plat.clicked.connect(self.handle_agregar_plataforma)
        bar_plat.addWidget(self.btn_add_plat)
        self.btn_del_plat = PushButton("Eliminar Plataforma", tab_plat, FIF.DELETE)
        self.btn_del_plat.clicked.connect(self.handle_eliminar_plataforma)
        bar_plat.addWidget(self.btn_del_plat)
        bar_plat.addStretch(1)
        v_plat.addLayout(bar_plat)

        self.table_plataformas = TableWidget(tab_plat)
        self.table_plataformas.setBorderVisible(True)
        self.table_plataformas.setColumnCount(4)
        self.table_plataformas.setHorizontalHeaderLabels(["Identificador", "Dirección de Viaje", "Capacidad Aprox.", "Estado Operativo"])
        h_plat = self.table_plataformas.horizontalHeader()
        if h_plat is not None:
            h_plat.setSectionResizeMode(QHeaderView.Stretch)
        self.table_plataformas.setEditTriggers(TableWidget.NoEditTriggers)
        self.table_plataformas.setSelectionBehavior(TableWidget.SelectRows)
        v_plat.addWidget(self.table_plataformas)
        self.stack_est_detail.addWidget(tab_plat)

        # Sub-Tab 2: Líneas que la Conectan (Requerimiento 8)
        tab_lin_est = QWidget()
        v_lin_est = QVBoxLayout(tab_lin_est)
        v_lin_est.setContentsMargins(0, 4, 0, 0)
        v_lin_est.setSpacing(6)
        self.table_lineas_est = TableWidget(tab_lin_est)
        self.table_lineas_est.setBorderVisible(True)
        self.table_lineas_est.setColumnCount(6)
        self.table_lineas_est.setHorizontalHeaderLabels(["Línea", "Nombre de Línea", "Color Oficial", "Orden en Recorrido", "Tipo de Servicio", "Estado Línea"])
        h_lin_est = self.table_lineas_est.horizontalHeader()
        if h_lin_est is not None:
            h_lin_est.setSectionResizeMode(QHeaderView.Stretch)
        self.table_lineas_est.setEditTriggers(TableWidget.NoEditTriggers)
        v_lin_est.addWidget(self.table_lineas_est)
        self.stack_est_detail.addWidget(tab_lin_est)

        # Sub-Tab 3: Transferencias Peatonales (Requerimiento 7)
        tab_trans = QWidget()
        v_trans = QVBoxLayout(tab_trans)
        v_trans.setContentsMargins(0, 4, 0, 0)
        v_trans.setSpacing(6)
        bar_trans = QHBoxLayout()
        self.btn_add_trans = PrimaryPushButton("Definir Transferencia", tab_trans, FIF.ADD)
        self.btn_add_trans.clicked.connect(self.handle_definir_transferencia)
        bar_trans.addWidget(self.btn_add_trans)
        self.btn_del_trans = PushButton("Eliminar Transferencia", tab_trans, FIF.DELETE)
        self.btn_del_trans.clicked.connect(self.handle_eliminar_transferencia)
        bar_trans.addWidget(self.btn_del_trans)
        bar_trans.addStretch(1)
        v_trans.addLayout(bar_trans)

        self.table_trans = TableWidget(tab_trans)
        self.table_trans.setBorderVisible(True)
        self.table_trans.setColumnCount(4)
        self.table_trans.setHorizontalHeaderLabels(["Línea Origen", "Línea Destino (Conexión)", "Tiempo Caminata", "Acción"])
        h_trans = self.table_trans.horizontalHeader()
        if h_trans is not None:
            h_trans.setSectionResizeMode(QHeaderView.Stretch)
        self.table_trans.setEditTriggers(TableWidget.NoEditTriggers)
        self.table_trans.setSelectionBehavior(TableWidget.SelectRows)
        v_trans.addWidget(self.table_trans)
        self.stack_est_detail.addWidget(tab_trans)

        card_insp_layout.addWidget(self.stack_est_detail)
        v_est_layout.addWidget(card_est_inspector, stretch=4)
        self.stack_master.addWidget(view_estaciones)

        # ----------------------------------------------------------------------
        # VISTA 2: GESTIÓN DE LÍNEAS Y TOPOLOGÍA
        # ----------------------------------------------------------------------
        view_lineas = QWidget()
        v_lin_layout = QVBoxLayout(view_lineas)
        v_lin_layout.setContentsMargins(0, 8, 0, 0)
        v_lin_layout.setSpacing(12)

        # Barra de Acciones de Líneas
        bar_lin = QHBoxLayout()
        bar_lin.setSpacing(10)

        lbl_lineas_info = BodyLabel("Líneas troncales comerciales del sistema de metro de Nueva York", view_lineas)
        bar_lin.addWidget(lbl_lineas_info)
        bar_lin.addStretch(1)

        self.btn_nueva_linea = PrimaryPushButton("Nueva Línea", view_lineas, FIF.ADD)
        self.btn_nueva_linea.clicked.connect(self.handle_nueva_linea)
        bar_lin.addWidget(self.btn_nueva_linea)

        self.btn_modificar_linea = PushButton("Modificar Línea", view_lineas, FIF.EDIT)
        self.btn_modificar_linea.clicked.connect(self.handle_modificar_linea)
        bar_lin.addWidget(self.btn_modificar_linea)

        self.btn_desactivar_linea = PushButton("Suspender / Reactivar", view_lineas, FIF.PAUSE)
        self.btn_desactivar_linea.clicked.connect(self.handle_desactivar_linea)
        bar_lin.addWidget(self.btn_desactivar_linea)

        v_lin_layout.addLayout(bar_lin)

        # Tabla Principal de Líneas
        self.table_lines = TableWidget(view_lineas)
        self.table_lines.setBorderVisible(True)
        self.table_lines.setColumnCount(8)
        self.table_lines.setHorizontalHeaderLabels([
            "Código", "Nombre de Línea", "Color Oficial", "Terminal Origen", "Terminal Destino", "Servicio Principal", "Longitud", "Estado Operativo"
        ])
        h_lines = self.table_lines.horizontalHeader()
        if h_lines is not None:
            h_lines.setSectionResizeMode(QHeaderView.Stretch)
        self.table_lines.setEditTriggers(TableWidget.NoEditTriggers)
        self.table_lines.setSelectionBehavior(TableWidget.SelectRows)
        self.table_lines.itemSelectionChanged.connect(self.on_line_row_selected)
        v_lin_layout.addWidget(self.table_lines, stretch=4)

        # Panel de Recorrido Secuencial de Paradas (Topología de Línea)
        card_topo = CardWidget(view_lineas)
        topo_layout = QVBoxLayout(card_topo)
        topo_layout.setContentsMargins(16, 12, 16, 12)
        topo_layout.setSpacing(8)

        bar_topo = QHBoxLayout()
        self.lbl_topo_title = StrongBodyLabel("Recorrido Secuencial de Estaciones (Topología)", card_topo)
        bar_topo.addWidget(self.lbl_topo_title)
        bar_topo.addStretch(1)

        self.btn_asociar_est = PrimaryPushButton("Asociar Estación a Línea", card_topo, FIF.ADD)
        self.btn_asociar_est.clicked.connect(self.handle_asociar_estacion)
        bar_topo.addWidget(self.btn_asociar_est)

        self.btn_modificar_tramo = PushButton("Modificar Tramo", card_topo, FIF.EDIT)
        self.btn_modificar_tramo.clicked.connect(self.handle_modificar_tramo)
        bar_topo.addWidget(self.btn_modificar_tramo)

        self.btn_desvincular_est = PushButton("Desvincular Estación", card_topo, FIF.DELETE)
        self.btn_desvincular_est.clicked.connect(self.handle_desvincular_estacion)
        bar_topo.addWidget(self.btn_desvincular_est)

        topo_layout.addLayout(bar_topo)

        # Tabla Secuencial de Estaciones en la Línea (Requerimiento 9)
        self.table_line_stations = TableWidget(card_topo)
        self.table_line_stations.setBorderVisible(True)
        self.table_line_stations.setColumnCount(7)
        self.table_line_stations.setHorizontalHeaderLabels([
            "Orden Parada", "Código Estación", "Nombre de Estación", "Distrito", "Distancia Anterior (km)", "Tiempo Estimado (min)", "Accesible ADA"
        ])
        h_ls = self.table_line_stations.horizontalHeader()
        if h_ls is not None:
            h_ls.setSectionResizeMode(QHeaderView.Stretch)
        self.table_line_stations.setEditTriggers(TableWidget.NoEditTriggers)
        self.table_line_stations.setSelectionBehavior(TableWidget.SelectRows)
        topo_layout.addWidget(self.table_line_stations)

        v_lin_layout.addWidget(card_topo, stretch=5)
        self.stack_master.addWidget(view_lineas)
        main_layout.addWidget(self.stack_master)

        # Seleccionar pestañas por defecto para que aparezcan activas visualmente
        self.segmented_master.setCurrentItem("tab_estaciones")
        self.segmented_est_detail.setCurrentItem("sub_plataformas")

    # ==========================================================================
    # CONTROL DE PESTAÑAS Y CARGA DE DATOS
    # ==========================================================================

    def on_master_tab_changed(self, key: str):
        if key == "tab_estaciones":
            self.stack_master.setCurrentIndex(0)
        else:
            self.stack_master.setCurrentIndex(1)

    def on_station_detail_tab_changed(self, key: str):
        if key == "sub_plataformas":
            self.stack_est_detail.setCurrentIndex(0)
        elif key == "sub_lineas":
            self.stack_est_detail.setCurrentIndex(1)
        else:
            self.stack_est_detail.setCurrentIndex(2)

    def load_all_data(self):
        """Carga todas las estaciones y líneas desde Oracle."""
        self.refresh_stations()
        self.refresh_lines()

    def refresh_stations(self):
        """Refresca la tabla de estaciones respetando filtros."""
        dist = self.combo_filtro_distrito.currentText()
        est = self.combo_filtro_estado.currentText()
        ada = self.chk_filtro_ada.isChecked()
        txt = self.search_est.text()

        self.estaciones_cache = network_service.get_estaciones_completas(
            filtro_texto=txt, distrito=dist, estado=est, solo_ada=ada
        )
        self.table_stations.setRowCount(len(self.estaciones_cache))
        for r, row in enumerate(self.estaciones_cache):
            self.table_stations.setItem(r, 0, QTableWidgetItem(str(row.get("CODIGO", "-"))))
            self.table_stations.setItem(r, 1, QTableWidgetItem(str(row.get("NOMBRE", "-"))))
            self.table_stations.setItem(r, 2, QTableWidgetItem(str(row.get("DISTRITO", "-"))))
            self.table_stations.setItem(r, 3, QTableWidgetItem(str(row.get("TIPO_ESTACION", "Local"))))
            self.table_stations.setItem(r, 4, QTableWidgetItem(str(row.get("CANTIDAD_PLATAFORMAS", "0"))))
            self.table_stations.setItem(r, 5, QTableWidgetItem(f"{row.get('TOTAL_LINEAS', 0)} líneas"))
            ada_str = "Sí (ADA)" if row.get("ACCESIBLE_DISCAPACIDAD") == "S" else "No"
            self.table_stations.setItem(r, 6, QTableWidgetItem(ada_str))
            self.table_stations.setItem(r, 7, QTableWidgetItem(str(row.get("ESTADO_OPERATIVO", "-"))))

        # Re-seleccionar primera fila si existe
        if self.estaciones_cache:
            self.table_stations.selectRow(0)

    def refresh_lines(self):
        """Refresca la tabla principal de líneas."""
        self.lineas_cache = network_service.get_lineas_completas()
        self.table_lines.setRowCount(len(self.lineas_cache))
        for r, row in enumerate(self.lineas_cache):
            self.table_lines.setItem(r, 0, QTableWidgetItem(str(row.get("CODIGO", "-"))))
            self.table_lines.setItem(r, 1, QTableWidgetItem(str(row.get("NOMBRE", "-"))))
            self.table_lines.setItem(r, 2, QTableWidgetItem(str(row.get("COLOR", "-"))))
            self.table_lines.setItem(r, 3, QTableWidgetItem(str(row.get("TERMINAL_ORIGEN", "(No asignada)"))))
            self.table_lines.setItem(r, 4, QTableWidgetItem(str(row.get("TERMINAL_DESTINO", "(No asignada)"))))
            self.table_lines.setItem(r, 5, QTableWidgetItem(str(row.get("TIPO_SERVICIO_PRINCIPAL", "-"))))
            self.table_lines.setItem(r, 6, QTableWidgetItem(f"{row.get('LONGITUD_KM', 0)} km"))
            self.table_lines.setItem(r, 7, QTableWidgetItem(str(row.get("ESTADO_OPERATIVO", "-"))))

        if self.lineas_cache:
            self.table_lines.selectRow(0)

    def apply_station_filters(self):
        self.refresh_stations()

    def update_stations(self, stations: list):
        """Compatibilidad con cargador global MainWindow."""
        self.refresh_stations()

    # ==========================================================================
    # MANEJADORES DE SELECCIÓN Y SUB-PANELES
    # ==========================================================================

    def on_station_row_selected(self):
        selected_items = self.table_stations.selectedItems()
        if not selected_items:
            return
        row = selected_items[0].row()
        if row < len(self.estaciones_cache):
            est = self.estaciones_cache[row]
            self.selected_station_id = int(est["ID_ESTACION"])
            self.lbl_insp_estacion.setText(f"Estación: {est.get('NOMBRE')} [{est.get('CODIGO')}] — Distrito: {est.get('DISTRITO')} | Estado: {est.get('ESTADO_OPERATIVO')}")
            self.load_station_details(self.selected_station_id)

    def load_station_details(self, id_estacion: int):
        # 1. Plataformas
        plats = network_service.get_plataformas_estacion(id_estacion)
        self.table_plataformas.setRowCount(len(plats))
        for r, p in enumerate(plats):
            self.table_plataformas.setItem(r, 0, QTableWidgetItem(str(p.get("IDENTIFICADOR", "-"))))
            self.table_plataformas.setItem(r, 1, QTableWidgetItem(str(p.get("DIRECCION_VIAJE", "-"))))
            self.table_plataformas.setItem(r, 2, QTableWidgetItem(f"{p.get('CAPACIDAD_APROXIMADA', 0)} pasajeros"))
            self.table_plataformas.setItem(r, 3, QTableWidgetItem(str(p.get("ESTADO_OPERATIVO", "-"))))

        # 2. Líneas que la conectan (Requerimiento 8)
        lins = network_service.get_lineas_por_estacion(id_estacion)
        self.table_lineas_est.setRowCount(len(lins))
        for r, l in enumerate(lins):
            self.table_lineas_est.setItem(r, 0, QTableWidgetItem(f"Línea {l.get('CODIGO_LINEA')}"))
            self.table_lineas_est.setItem(r, 1, QTableWidgetItem(str(l.get("NOMBRE_LINEA", "-"))))
            self.table_lineas_est.setItem(r, 2, QTableWidgetItem(str(l.get("COLOR", "-"))))
            self.table_lineas_est.setItem(r, 3, QTableWidgetItem(f"Parada #{l.get('ORDEN', '-') }"))
            self.table_lineas_est.setItem(r, 4, QTableWidgetItem(str(l.get("TIPO_SERVICIO_PRINCIPAL", "-"))))
            self.table_lineas_est.setItem(r, 5, QTableWidgetItem(str(l.get("ESTADO_LINEA", "-"))))

        # 3. Transferencias (Requerimiento 7)
        trans = network_service.get_transferencias_estacion(id_estacion)
        self.table_trans.setRowCount(len(trans))
        for r, t in enumerate(trans):
            self.table_trans.setItem(r, 0, QTableWidgetItem(f"Línea {t.get('CODIGO_ORIG')} ({t.get('NOMBRE_ORIG')})"))
            self.table_trans.setItem(r, 1, QTableWidgetItem(f"Línea {t.get('CODIGO_DEST')} ({t.get('NOMBRE_DEST')})"))
            self.table_trans.setItem(r, 2, QTableWidgetItem(f"{t.get('TIEMPO_ESTIMADO_MIN', 3)} minutos"))
            self.table_trans.setItem(r, 3, QTableWidgetItem("Peatonal Subterránea"))

    def on_line_row_selected(self):
        selected_items = self.table_lines.selectedItems()
        if not selected_items:
            return
        row = selected_items[0].row()
        if row < len(self.lineas_cache):
            lin = self.lineas_cache[row]
            self.selected_line_id = int(lin["ID_LINEA"])
            self.lbl_topo_title.setText(f"Recorrido Secuencial de Paradas — Línea {lin.get('CODIGO')} ({lin.get('NOMBRE')})")
            self.load_line_topology(self.selected_line_id)

    def load_line_topology(self, id_linea: int):
        """Requerimiento 9: Consultar todas las estaciones de una línea en el orden correcto."""
        tramos = network_service.get_estaciones_de_linea_ordenadas(id_linea)
        self.table_line_stations.setRowCount(len(tramos))
        for r, t in enumerate(tramos):
            self.table_line_stations.setItem(r, 0, QTableWidgetItem(f"#{t.get('ORDEN')}"))
            self.table_line_stations.setItem(r, 1, QTableWidgetItem(str(t.get("CODIGO_ESTACION", "-"))))
            self.table_line_stations.setItem(r, 2, QTableWidgetItem(str(t.get("NOMBRE_ESTACION", "-"))))
            self.table_line_stations.setItem(r, 3, QTableWidgetItem(str(t.get("DISTRITO", "-"))))
            self.table_line_stations.setItem(r, 4, QTableWidgetItem(f"{t.get('DISTANCIA_KM', 0)} km"))
            self.table_line_stations.setItem(r, 5, QTableWidgetItem(f"{t.get('TIEMPO_ESTIMADO_MIN', 0)} min"))
            ada = "Sí (ADA)" if t.get("ACCESIBLE_DISCAPACIDAD") == "S" else "No"
            self.table_line_stations.setItem(r, 6, QTableWidgetItem(ada))

    # ==========================================================================
    # ACCIONES CRUD DE ESTACIONES
    # ==========================================================================

    def handle_nueva_estacion(self):
        dlg = EstacionDialog(estacion_data=None, parent=self.window())
        if dlg.exec():
            datos = dlg.get_data()
            if not datos["codigo"] or not datos["nombre"]:
                InfoBar.warning("Campos Requeridos", "El código y el nombre de la estación son obligatorios.", parent=self.window())
                return
            res = network_service.crear_estacion(datos)
            if res.get("success"):
                InfoBar.success("Estación Creada", res.get("mensaje"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)
                self.refresh_stations()
            else:
                InfoBar.error("Error al Crear", res.get("error", "Fallo al insertar en Oracle."), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)

    def handle_modificar_estacion(self):
        selected_items = self.table_stations.selectedItems()
        if not selected_items:
            InfoBar.warning("Sin Selección", "Selecciona una estación de la tabla para modificar.", parent=self.window())
            return
        row = selected_items[0].row()
        est_data = self.estaciones_cache[row]
        dlg = EstacionDialog(estacion_data=est_data, parent=self.window())
        if dlg.exec():
            datos = dlg.get_data()
            res = network_service.modificar_estacion(int(est_data["ID_ESTACION"]), datos)
            if res.get("success"):
                InfoBar.success("Estación Actualizada", res.get("mensaje"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)
                self.refresh_stations()
            else:
                InfoBar.error("Error al Modificar", res.get("error", "Fallo al actualizar."), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)

    def handle_cambiar_estado_estacion(self):
        selected_items = self.table_stations.selectedItems()
        if not selected_items:
            InfoBar.warning("Sin Selección", "Selecciona una estación para alternar su estado.", parent=self.window())
            return
        row = selected_items[0].row()
        est_data = self.estaciones_cache[row]
        curr_estado = est_data.get("ESTADO_OPERATIVO")
        nuevo_estado = "Cerrada Temporalmente" if curr_estado == "Operativa" else "Operativa"
        res = network_service.cambiar_estado_estacion(int(est_data["ID_ESTACION"]), nuevo_estado)
        if res.get("success"):
            InfoBar.success("Estado Actualizado", res.get("mensaje"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)
            self.refresh_stations()
        else:
            InfoBar.error("Error", res.get("error"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)

    # ==========================================================================
    # ACCIONES DE PLATAFORMAS Y TRANSFERENCIAS (REQUERIMIENTOS 6 Y 7)
    # ==========================================================================

    def handle_agregar_plataforma(self):
        if not self.selected_station_id:
            InfoBar.warning("Sin Selección", "Selecciona una estación en la tabla superior.", parent=self.window())
            return
        dlg = PlataformaDialog(plataforma_data=None, parent=self.window())
        if dlg.exec():
            d = dlg.get_data()
            if not d["identificador"]:
                InfoBar.warning("Campo Requerido", "El identificador de plataforma es obligatorio.", parent=self.window())
                return
            res = network_service.agregar_plataforma(
                id_estacion=self.selected_station_id,
                identificador=d["identificador"],
                direccion_viaje=d["direccion_viaje"],
                capacidad=d["capacidad"],
                estado=d["estado"]
            )
            if res.get("success"):
                InfoBar.success("Plataforma Creada", res.get("mensaje"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)
                self.load_station_details(self.selected_station_id)
                self.refresh_stations()
            else:
                InfoBar.error("Error", res.get("error"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)

    def handle_eliminar_plataforma(self):
        selected_items = self.table_plataformas.selectedItems()
        if not selected_items or not self.selected_station_id:
            InfoBar.warning("Sin Selección", "Selecciona una plataforma en la tabla para eliminar.", parent=self.window())
            return
        row = selected_items[0].row()
        plats = network_service.get_plataformas_estacion(self.selected_station_id)
        if row < len(plats):
            plat_id = int(plats[row]["ID_PLATAFORMA"])
            res = network_service.eliminar_plataforma(plat_id, self.selected_station_id)
            if res.get("success"):
                InfoBar.success("Plataforma Eliminada", res.get("mensaje"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)
                self.load_station_details(self.selected_station_id)
                self.refresh_stations()
            else:
                InfoBar.error("Error", res.get("error"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)

    def handle_definir_transferencia(self):
        if not self.selected_station_id:
            InfoBar.warning("Sin Selección", "Selecciona una estación en la tabla superior.", parent=self.window())
            return
        dlg = TransferenciaDialog(lineas=self.lineas_cache, parent=self.window())
        if dlg.exec():
            d = dlg.get_data()
            res = network_service.definir_transferencia(
                id_estacion=self.selected_station_id,
                id_linea_origen=d["linea_origen_id"],
                id_linea_destino=d["linea_destino_id"],
                tiempo_min=d["tiempo_min"]
            )
            if res.get("success"):
                InfoBar.success("Transferencia Habilitada", res.get("mensaje"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)
                self.load_station_details(self.selected_station_id)
            else:
                InfoBar.error("Error", res.get("error"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)

    def handle_eliminar_transferencia(self):
        selected_items = self.table_trans.selectedItems()
        if not selected_items or not self.selected_station_id:
            InfoBar.warning("Sin Selección", "Selecciona una transferencia para eliminar.", parent=self.window())
            return
        row = selected_items[0].row()
        trans = network_service.get_transferencias_estacion(self.selected_station_id)
        if row < len(trans):
            trans_id = int(trans[row]["ID_TRANSFERENCIA"])
            res = network_service.eliminar_transferencia(trans_id)
            if res.get("success"):
                InfoBar.success("Transferencia Eliminada", res.get("mensaje"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)
                self.load_station_details(self.selected_station_id)
            else:
                InfoBar.error("Error", res.get("error"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)

    # ==========================================================================
    # ACCIONES CRUD DE LÍNEAS (REQUERIMIENTO 1)
    # ==========================================================================

    def handle_nueva_linea(self):
        dlg = LineaDialog(linea_data=None, estaciones=self.estaciones_cache, parent=self.window())
        if dlg.exec():
            datos = dlg.get_data()
            if not datos["codigo"] or not datos["nombre"]:
                InfoBar.warning("Campos Requeridos", "El código y el nombre de la línea son obligatorios.", parent=self.window())
                return
            res = network_service.crear_linea(datos)
            if res.get("success"):
                InfoBar.success("Línea Creada", res.get("mensaje"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)
                self.refresh_lines()
            else:
                InfoBar.error("Error", res.get("error"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)

    def handle_modificar_linea(self):
        selected_items = self.table_lines.selectedItems()
        if not selected_items:
            InfoBar.warning("Sin Selección", "Selecciona una línea para modificar.", parent=self.window())
            return
        row = selected_items[0].row()
        linea_data = self.lineas_cache[row]
        dlg = LineaDialog(linea_data=linea_data, estaciones=self.estaciones_cache, parent=self.window())
        if dlg.exec():
            datos = dlg.get_data()
            res = network_service.modificar_linea(int(linea_data["ID_LINEA"]), datos)
            if res.get("success"):
                InfoBar.success("Línea Actualizada", res.get("mensaje"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)
                self.refresh_lines()
            else:
                InfoBar.error("Error", res.get("error"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)

    def handle_desactivar_linea(self):
        selected_items = self.table_lines.selectedItems()
        if not selected_items:
            InfoBar.warning("Sin Selección", "Selecciona una línea para cambiar su estado.", parent=self.window())
            return
        row = selected_items[0].row()
        linea_data = self.lineas_cache[row]
        curr = linea_data.get("ESTADO_OPERATIVO")
        nuevo = "Suspendida" if curr == "Activa" else "Activa"
        res = network_service.cambiar_estado_linea(int(linea_data["ID_LINEA"]), nuevo)
        if res.get("success"):
            InfoBar.success("Estado de Línea Cambiado", res.get("mensaje"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)
            self.refresh_lines()
        else:
            InfoBar.error("Error", res.get("error"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)

    # ==========================================================================
    # GESTIÓN DE TOPOLOGÍA DE LÍNEA (REQUERIMIENTOS 3, 4, 5 Y 9)
    # ==========================================================================

    def handle_asociar_estacion(self):
        if not self.selected_line_id:
            InfoBar.warning("Sin Selección", "Selecciona una línea en la tabla superior.", parent=self.window())
            return
        disponibles = network_service.get_estaciones_disponibles_para_linea(self.selected_line_id)
        if not disponibles:
            InfoBar.warning("Sin Estaciones Disponibles", "Todas las estaciones ya están asociadas a esta línea.", parent=self.window())
            return
        next_ord = self.table_line_stations.rowCount() + 1
        dlg = AsociarEstacionDialog(estaciones_disponibles=disponibles, next_order=next_ord, parent=self.window())
        if dlg.exec():
            d = dlg.get_data()
            if not d["estacion_id"]:
                return
            res = network_service.asociar_estacion_linea(
                id_linea=self.selected_line_id,
                id_estacion=d["estacion_id"],
                orden=d["orden"],
                distancia_km=d["distancia_km"],
                tiempo_min=d["tiempo_min"]
            )
            if res.get("success"):
                InfoBar.success("Estación Asociada", res.get("mensaje"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)
                self.load_line_topology(self.selected_line_id)
                self.refresh_lines()
            else:
                InfoBar.error("Error al Asociar", res.get("error"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)

    def handle_modificar_tramo(self):
        selected_items = self.table_line_stations.selectedItems()
        if not selected_items or not self.selected_line_id:
            InfoBar.warning("Sin Selección", "Selecciona un tramo/estación de la tabla de recorrido.", parent=self.window())
            return
        row = selected_items[0].row()
        tramos = network_service.get_estaciones_de_linea_ordenadas(self.selected_line_id)
        if row < len(tramos):
            tramo = tramos[row]
            dlg = AsociarEstacionDialog(tramo_data=tramo, parent=self.window())
            if dlg.exec():
                d = dlg.get_data()
                res = network_service.modificar_tramo_linea_estacion(
                    id_linea_estacion=int(tramo["ID_LINEA_ESTACION"]),
                    orden=d["orden"],
                    distancia_km=d["distancia_km"],
                    tiempo_min=d["tiempo_min"]
                )
                if res.get("success"):
                    InfoBar.success("Tramo Actualizado", res.get("mensaje"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)
                    self.load_line_topology(self.selected_line_id)
                else:
                    InfoBar.error("Error", res.get("error"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)

    def handle_desvincular_estacion(self):
        selected_items = self.table_line_stations.selectedItems()
        if not selected_items or not self.selected_line_id:
            InfoBar.warning("Sin Selección", "Selecciona una estación del recorrido para desvincular.", parent=self.window())
            return
        row = selected_items[0].row()
        tramos = network_service.get_estaciones_de_linea_ordenadas(self.selected_line_id)
        if row < len(tramos):
            tramo_id = int(tramos[row]["ID_LINEA_ESTACION"])
            res = network_service.desvincular_estacion_linea(tramo_id)
            if res.get("success"):
                InfoBar.success("Estación Desvinculada", res.get("mensaje"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)
                self.load_line_topology(self.selected_line_id)
                self.refresh_lines()
            else:
                InfoBar.error("Error", res.get("error"), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)
