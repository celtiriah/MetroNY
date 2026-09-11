"""
Interfaz de Gestión de Pasajeros, Tarifas y Simulador de Torniquetes OMNY.
Módulo 5 del Sistema de Gestión del Metro de Nueva York (MTA NYCT).
Implementa catálogo de tarjetas, recargas de saldo y simulación de paso por torniquete.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QHeaderView,
    QTableWidgetItem, QFrame, QStackedWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from qfluentwidgets import (
    TitleLabel, SubtitleLabel, CaptionLabel, BodyLabel, StrongBodyLabel,
    CardWidget, ComboBox, LineEdit, DoubleSpinBox, PrimaryPushButton,
    PushButton, TableWidget, InfoBar, InfoBarPosition, SegmentedWidget,
    FluentIcon as FIF
)

from config import MTA_BLUE
from components.stat_card import StatCard
from services import actions_service


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
        elif estado == "Bloqueada":
            self.lbl_saldo.setStyleSheet("color: #FF5252; font-size: 20px; font-weight: bold;")
        else:
            self.lbl_saldo.setStyleSheet("color: #FFD600; font-size: 20px; font-weight: bold;")


class CardsInterface(QWidget):
    """
    Pantalla interactiva del Módulo 5 (Pasajeros, Tarifas y Torniquetes).
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("cardsInterface")
        self.tarjetas_cache = []
        self.selected_card_num = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # 1. Cabecera
        title = TitleLabel("Pasajeros, Tarifas y Torniquetes OMNY", self)
        subtitle = SubtitleLabel(
            "Módulo 5: Gestión de tarjetas contactless, recargas en tiempo real y simulador de paso por torniquete", self
        )
        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # 2. Tarjetas Métricas (KPIs)
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(12)

        self.kpi_total = StatCard("Total Tarjetas", "💳", "-", self)
        self.kpi_activas = StatCard("Tarjetas Activas", "✅", "-", self)
        self.kpi_saldo = StatCard("Saldo en Circulación", "💵", "-", self)
        self.kpi_tarifa = StatCard("Tarifa Base MTA", "🎟️", "$2.90", self)

        kpi_layout.addWidget(self.kpi_total)
        kpi_layout.addWidget(self.kpi_activas)
        kpi_layout.addWidget(self.kpi_saldo)
        kpi_layout.addWidget(self.kpi_tarifa)
        main_layout.addLayout(kpi_layout)

        # 3. Contenedor Principal en 2 Columnas
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        # ======================================================================
        # COLUMNA IZQUIERDA: Simulador de Torniquete y Recargas
        # ======================================================================
        left_col = QVBoxLayout()
        left_col.setSpacing(14)

        # Tarjeta Visual OMNY
        self.visual_card = VisualOmnyCard(self)
        left_col.addWidget(self.visual_card, alignment=Qt.AlignmentFlag.AlignCenter)

        # Card A: Simulador de Paso en Torniquete
        card_turnstile = CardWidget(self)
        turnstile_layout = QVBoxLayout(card_turnstile)
        turnstile_layout.setContentsMargins(18, 16, 18, 16)
        turnstile_layout.setSpacing(10)

        lbl_sim_title = StrongBodyLabel("🚇 Simulador de Paso en Torniquete", card_turnstile)
        turnstile_layout.addWidget(lbl_sim_title)

        # Selector de Estación
        turnstile_layout.addWidget(CaptionLabel("Estación donde se ubica el torniquete:", card_turnstile))
        self.combo_estaciones = ComboBox(card_turnstile)
        turnstile_layout.addWidget(self.combo_estaciones)

        # Selector de Tarjeta
        turnstile_layout.addWidget(CaptionLabel("Tarjeta a aproximar al lector OMNY:", card_turnstile))
        self.combo_tarjetas = ComboBox(card_turnstile)
        self.combo_tarjetas.currentIndexChanged.connect(self.on_card_selection_changed)
        turnstile_layout.addWidget(self.combo_tarjetas)

        # Botón de paso
        self.btn_tap = PrimaryPushButton("Validar Paso en Torniquete ($2.90)", card_turnstile, FIF.QRCODE)
        self.btn_tap.clicked.connect(self.handle_turnstile_tap)
        turnstile_layout.addWidget(self.btn_tap)

        left_col.addWidget(card_turnstile)

        # Card B: Recarga de Saldo Express
        card_recharge = CardWidget(self)
        recharge_layout = QVBoxLayout(card_recharge)
        recharge_layout.setContentsMargins(18, 16, 18, 16)
        recharge_layout.setSpacing(10)

        lbl_rec_title = StrongBodyLabel("💳 Recarga de Saldo OMNY / MetroCard", card_recharge)
        recharge_layout.addWidget(lbl_rec_title)

        rec_input_layout = QHBoxLayout()
        rec_input_layout.setSpacing(8)

        # Monto
        col_monto = QVBoxLayout()
        col_monto.addWidget(CaptionLabel("Monto a Recargar ($):", card_recharge))
        self.spin_monto = DoubleSpinBox(card_recharge)
        self.spin_monto.setRange(1.00, 500.00)
        self.spin_monto.setValue(10.00)
        self.spin_monto.setSingleStep(5.00)
        col_monto.addWidget(self.spin_monto)
        rec_input_layout.addLayout(col_monto)

        # Medio de Pago
        col_pago = QVBoxLayout()
        col_pago.addWidget(CaptionLabel("Medio de Pago:", card_recharge))
        self.combo_medio_pago = ComboBox(card_recharge)
        self.combo_medio_pago.addItems(["Efectivo", "Tarjeta Débito", "Tarjeta Crédito", "App Móvil", "Transferencia"])
        col_pago.addWidget(self.combo_medio_pago)
        rec_input_layout.addLayout(col_pago)

        recharge_layout.addLayout(rec_input_layout)

        # Botones de Montos Rápidos
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(6)
        for amount in [5, 10, 20, 50]:
            btn_q = PushButton(f"+${amount}", card_recharge)
            btn_q.clicked.connect(lambda checked, a=amount: self.spin_monto.setValue(float(a)))
            quick_layout.addWidget(btn_q)
        recharge_layout.addLayout(quick_layout)

        # Botón Ejecutar Recarga
        self.btn_recharge = PrimaryPushButton("Abonar Saldo a la Tarjeta", card_recharge, FIF.ADD)
        self.btn_recharge.clicked.connect(self.handle_recharge)
        recharge_layout.addWidget(self.btn_recharge)

        left_col.addWidget(card_recharge)
        left_col.addStretch(1)

        content_layout.addLayout(left_col, stretch=4)

        # ======================================================================
        # COLUMNA DERECHA: Directorio de Tarjetas e Historiales
        # ======================================================================
        right_col = QVBoxLayout()
        right_col.setSpacing(14)

        # Card C: Catálogo de Tarjetas
        card_dir = CardWidget(self)
        dir_layout = QVBoxLayout(card_dir)
        dir_layout.setContentsMargins(18, 16, 18, 16)
        dir_layout.setSpacing(10)

        top_dir_row = QHBoxLayout()
        top_dir_row.addWidget(StrongBodyLabel("Directorio Institucional de Tarjetas", card_dir))
        top_dir_row.addStretch(1)
        top_dir_row.addWidget(CaptionLabel("Estado:", card_dir))

        self.combo_filtro_estado = ComboBox(card_dir)
        self.combo_filtro_estado.addItems(["(Todos)", "Activa", "Bloqueada", "Vencida", "Cancelada"])
        self.combo_filtro_estado.currentTextChanged.connect(self.filter_cards_table)
        top_dir_row.addWidget(self.combo_filtro_estado)

        dir_layout.addLayout(top_dir_row)

        # Tabla de Tarjetas
        self.table_cards = TableWidget(card_dir)
        self.table_cards.setBorderVisible(True)
        self.table_cards.setColumnCount(7)
        self.table_cards.setHorizontalHeaderLabels([
            "Número Tarjeta", "Titular", "Tipo Pasajero", "Tarifa", "Saldo", "Vigencia", "Estado"
        ])
        header_cards = self.table_cards.horizontalHeader()
        if header_cards is not None:
            header_cards.setSectionResizeMode(QHeaderView.Stretch)
        self.table_cards.setEditTriggers(TableWidget.NoEditTriggers)
        self.table_cards.setSelectionBehavior(TableWidget.SelectRows)
        self.table_cards.itemSelectionChanged.connect(self.on_table_row_selected)
        dir_layout.addWidget(self.table_cards)

        right_col.addWidget(card_dir, stretch=5)

        # Card D: Historial de la Tarjeta Seleccionada (Pestañas)
        card_hist = CardWidget(self)
        hist_layout = QVBoxLayout(card_hist)
        hist_layout.setContentsMargins(18, 14, 18, 14)
        hist_layout.setSpacing(8)

        self.segmented_hist = SegmentedWidget(card_hist)
        self.segmented_hist.addItem("viajes", "Historial de Pasos por Torniquete")
        self.segmented_hist.addItem("recargas", "Historial de Recargas")
        self.segmented_hist.currentItemChanged.connect(self.on_history_tab_changed)
        hist_layout.addWidget(self.segmented_hist)

        self.stack_hist = QStackedWidget(card_hist)

        # 1. Tabla de Viajes
        self.table_viajes = TableWidget(self.stack_hist)
        self.table_viajes.setBorderVisible(True)
        self.table_viajes.setColumnCount(5)
        self.table_viajes.setHorizontalHeaderLabels([
            "N° Transacción", "Estación de Ingreso", "Fecha y Hora", "Cobro", "Estado"
        ])
        header_viajes = self.table_viajes.horizontalHeader()
        if header_viajes is not None:
            header_viajes.setSectionResizeMode(QHeaderView.Stretch)
        self.table_viajes.setEditTriggers(TableWidget.NoEditTriggers)
        self.stack_hist.addWidget(self.table_viajes)

        # 2. Tabla de Recargas
        self.table_recargas = TableWidget(self.stack_hist)
        self.table_recargas.setBorderVisible(True)
        self.table_recargas.setColumnCount(6)
        self.table_recargas.setHorizontalHeaderLabels([
            "N° Transacción", "Monto", "Medio Pago", "Canal / Estación", "Saldo Post.", "Fecha y Hora"
        ])
        header_recargas = self.table_recargas.horizontalHeader()
        if header_recargas is not None:
            header_recargas.setSectionResizeMode(QHeaderView.Stretch)
        self.table_recargas.setEditTriggers(TableWidget.NoEditTriggers)
        self.stack_hist.addWidget(self.table_recargas)

        hist_layout.addWidget(self.stack_hist)
        right_col.addWidget(card_hist, stretch=4)

        content_layout.addLayout(right_col, stretch=6)
        main_layout.addLayout(content_layout)

    # ======================================================================
    # LÓGICA DE CARGA DE DATOS Y EVENTOS
    # ======================================================================

    def load_cards_data(self):
        """Carga y actualiza todos los datos del módulo de tarjetas y torniquetes."""
        try:
            # 1. Cargar combo de estaciones
            estaciones = actions_service.get_estaciones_combo()
            self.combo_estaciones.clear()
            for est_id, label in estaciones:
                self.combo_estaciones.addItem(label, userData=est_id)

            # 2. Cargar tarjetas
            self.refresh_cards_list()
        except Exception as e:
            print(f"Error al cargar módulo de tarjetas: {e}")

    def refresh_cards_list(self):
        """Actualiza tarjetas, métricas y combos conservando la selección."""
        prev_card = self.selected_card_num

        self.tarjetas_cache = actions_service.get_tarjetas_resumen()

        # Actualizar KPIs
        total_tarjetas = len(self.tarjetas_cache)
        activas = sum(1 for t in self.tarjetas_cache if t.get("ESTADO") == "Activa")
        total_saldo = sum(
            float(t.get("SALDO_DISPONIBLE", 0)) for t in self.tarjetas_cache if t.get("SALDO_DISPONIBLE") != "-"
        )

        self.kpi_total.set_value(str(total_tarjetas))
        self.kpi_activas.set_value(str(activas))
        self.kpi_saldo.set_value(f"${total_saldo:.2f}")

        # Actualizar ComboBox de tarjetas
        self.combo_tarjetas.blockSignals(True)
        self.combo_tarjetas.clear()
        target_idx = 0
        for i, t in enumerate(self.tarjetas_cache):
            num = t.get("NUMERO_TARJETA")
            titular = t.get("PASAJERO", "Anónima")
            saldo = float(t.get("SALDO_DISPONIBLE", 0)) if t.get("SALDO_DISPONIBLE") != "-" else 0.0
            label = f"{num} - {titular} (${saldo:.2f}) [{t.get('ESTADO')}]"
            self.combo_tarjetas.addItem(label, userData=num)
            if num == prev_card:
                target_idx = i

        self.combo_tarjetas.setCurrentIndex(target_idx)
        self.combo_tarjetas.blockSignals(False)

        # Actualizar tabla de tarjetas
        self.filter_cards_table()

        # Actualizar tarjeta visual
        if self.tarjetas_cache:
            raw_num = self.combo_tarjetas.currentData() or self.tarjetas_cache[0].get("NUMERO_TARJETA")
            if raw_num:
                self.set_active_card(str(raw_num))

    def filter_cards_table(self):
        """Aplica filtro de estado a la tabla de tarjetas."""
        filtro = self.combo_filtro_estado.currentText()
        filtered = self.tarjetas_cache if filtro == "(Todos)" else [
            t for t in self.tarjetas_cache if t.get("ESTADO") == filtro
        ]

        self.table_cards.blockSignals(True)
        self.table_cards.setRowCount(len(filtered))
        for r, row in enumerate(filtered):
            num = str(row.get("NUMERO_TARJETA", "-"))
            saldo = float(row.get("SALDO_DISPONIBLE", 0)) if row.get("SALDO_DISPONIBLE") != "-" else 0.0

            self.table_cards.setItem(r, 0, QTableWidgetItem(num))
            self.table_cards.setItem(r, 1, QTableWidgetItem(str(row.get("PASAJERO", "-"))))
            self.table_cards.setItem(r, 2, QTableWidgetItem(str(row.get("TIPO_PASAJERO", "-"))))
            self.table_cards.setItem(r, 3, QTableWidgetItem(str(row.get("TARIFA_NOMBRE", "-"))))
            self.table_cards.setItem(r, 4, QTableWidgetItem(f"${saldo:.2f}"))
            self.table_cards.setItem(r, 5, QTableWidgetItem(str(row.get("FECHA_VENCIMIENTO", "-"))))
            self.table_cards.setItem(r, 6, QTableWidgetItem(str(row.get("ESTADO", "-"))))

        self.table_cards.blockSignals(False)

    def set_active_card(self, numero_tarjeta: str):
        """Establece la tarjeta activa para visualización, torniquete y recarga."""
        self.selected_card_num = numero_tarjeta

        card_data = next((t for t in self.tarjetas_cache if t.get("NUMERO_TARJETA") == numero_tarjeta), None)
        if not card_data:
            return

        saldo = float(card_data.get("SALDO_DISPONIBLE", 0)) if card_data.get("SALDO_DISPONIBLE") != "-" else 0.0
        self.visual_card.set_card_data(
            numero=card_data.get("NUMERO_TARJETA", "-"),
            titular=card_data.get("PASAJERO", "Anónima"),
            tarifa=card_data.get("TARIFA_NOMBRE", "Tarifa Estándar"),
            saldo=saldo,
            estado=card_data.get("ESTADO", "Activa")
        )

        # Cargar historiales de viajes y recargas
        self.load_card_histories(numero_tarjeta)

    def load_card_histories(self, numero_tarjeta: str):
        """Carga las tablas de viajes y recargas de la tarjeta seleccionada."""
        # 1. Viajes
        viajes = actions_service.get_historial_viajes_tarjeta(numero_tarjeta, limit=12)
        self.table_viajes.setRowCount(len(viajes))
        for r, v in enumerate(viajes):
            cobro = float(v.get("MONTO_COBRADO", 0)) if v.get("MONTO_COBRADO") != "-" else 0.0
            self.table_viajes.setItem(r, 0, QTableWidgetItem(str(v.get("NUMERO_TRANSACCION", "-"))))
            self.table_viajes.setItem(r, 1, QTableWidgetItem(str(v.get("ESTACION_INGRESO", "-"))))
            self.table_viajes.setItem(r, 2, QTableWidgetItem(str(v.get("FECHA_HORA", "-"))))
            self.table_viajes.setItem(r, 3, QTableWidgetItem(f"${cobro:.2f}"))
            self.table_viajes.setItem(r, 4, QTableWidgetItem(str(v.get("ESTADO_TRANSACCION", "-"))))

        # 2. Recargas
        recargas = actions_service.get_historial_recargas_tarjeta(numero_tarjeta, limit=12)
        self.table_recargas.setRowCount(len(recargas))
        for r, rec in enumerate(recargas):
            monto = float(rec.get("MONTO", 0)) if rec.get("MONTO") != "-" else 0.0
            saldo_post = float(rec.get("SALDO_POSTERIOR", 0)) if rec.get("SALDO_POSTERIOR") != "-" else 0.0
            self.table_recargas.setItem(r, 0, QTableWidgetItem(str(rec.get("NUMERO_TRANSACCION", "-"))))
            self.table_recargas.setItem(r, 1, QTableWidgetItem(f"${monto:.2f}"))
            self.table_recargas.setItem(r, 2, QTableWidgetItem(str(rec.get("MEDIO_PAGO", "-"))))
            self.table_recargas.setItem(r, 3, QTableWidgetItem(str(rec.get("ESTACION_CANAL", "-"))))
            self.table_recargas.setItem(r, 4, QTableWidgetItem(f"${saldo_post:.2f}"))
            self.table_recargas.setItem(r, 5, QTableWidgetItem(str(rec.get("FECHA_HORA", "-"))))

    def on_card_selection_changed(self, index: int):
        """Manejador de cambio en el ComboBox de tarjetas."""
        num = self.combo_tarjetas.currentData()
        if num:
            self.set_active_card(num)

    def on_table_row_selected(self):
        """Manejador al hacer clic en una fila de la tabla de tarjetas."""
        selected_items = self.table_cards.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            item = self.table_cards.item(row, 0)
            if item is not None:
                card_num = item.text()
                # Sincronizar ComboBox
                idx = self.combo_tarjetas.findData(card_num)
                if idx >= 0:
                    self.combo_tarjetas.setCurrentIndex(idx)
                else:
                    self.set_active_card(card_num)

    def on_history_tab_changed(self, key: str):
        """Alterna entre la tabla de viajes y recargas."""
        if key == "viajes":
            self.stack_hist.setCurrentWidget(self.table_viajes)
        else:
            self.stack_hist.setCurrentWidget(self.table_recargas)

    # ======================================================================
    # ACCIONES TRANSACCIONALES
    # ======================================================================

    def handle_turnstile_tap(self):
        """Ejecuta la validación de ingreso en torniquete usando SP_REGISTRAR_INGRESO."""
        card_num = self.combo_tarjetas.currentData()
        estacion_id = self.combo_estaciones.currentData()

        if not card_num:
            InfoBar.warning("Sin Selección", "Selecciona una tarjeta para validar.", parent=self)
            return

        if not estacion_id:
            InfoBar.warning("Sin Selección", "Selecciona una estación operativa.", parent=self)
            return

        # Invocar SP_REGISTRAR_INGRESO
        res = actions_service.registrar_ingreso(numero_tarjeta=card_num, estacion_id=estacion_id)

        if res.get("success"):
            InfoBar.success(
                title="¡Paso Autorizado!",
                content=f"{res.get('mensaje')}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3500
            )
        elif res.get("resultado") == "SALDO_INSUFICIENTE":
            InfoBar.warning(
                title="Saldo Insuficiente",
                content=f"{res.get('mensaje')}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000
            )
        else:
            InfoBar.error(
                title="Acceso Denegado",
                content=f"{res.get('mensaje')}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000
            )

        # Actualizar datos en caliente
        self.refresh_cards_list()

    def handle_recharge(self):
        """Ejecuta la recarga de saldo usando SP_RECARGAR_TARJETA."""
        card_num = self.combo_tarjetas.currentData()
        monto = self.spin_monto.value()
        medio_pago = self.combo_medio_pago.currentText()

        if not card_num:
            InfoBar.warning("Sin Selección", "Selecciona una tarjeta para recargar.", parent=self)
            return

        if monto <= 0:
            InfoBar.warning("Monto Inválido", "El monto a recargar debe ser mayor a $0.", parent=self)
            return

        # Invocar SP_RECARGAR_TARJETA
        res = actions_service.recargar_tarjeta(
            numero_tarjeta=card_num,
            monto=monto,
            medio_pago=medio_pago,
            estacion_canal="Torniquete Estación"
        )

        if res.get("success"):
            InfoBar.success(
                title="Recarga Exitosa",
                content=f"{res.get('mensaje')}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3500
            )
            # Actualizar datos en caliente
            self.refresh_cards_list()
        else:
            InfoBar.error(
                title="Error en Recarga",
                content=f"{res.get('error', 'No se pudo procesar la recarga.')}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000
            )

