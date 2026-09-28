"""
Notification Tray Dialog for the MetroNY Desktop Application.
Provides a centralized drawer to review past operational notifications and events.
Adapts seamlessly to Windows 11 Fluent Design in both Light and Dark modes.
"""
from typing import List, Dict, Any
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QWidget, QFrame
)
from PyQt5.QtCore import Qt
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, CaptionLabel, BodyLabel,
    PrimaryPushButton, PushButton, SegmentedWidget, FluentIcon as FIF,
    CardWidget, IconWidget, InfoBarIcon, isDarkTheme, qconfig
)


class NotificationTrayDialog(MessageBoxBase):
    """
    Diálogo modal para visualizar el historial de notificaciones y alertas emitidas.
    Soporta visualización reactiva con temas Claro y Oscuro.
    """
    def __init__(self, notifications: List[Dict[str, Any]], on_clear_callback=None, parent=None):
        super().__init__(parent)
        self.notifications = list(notifications)
        self.on_clear_callback = on_clear_callback
        self.current_filter = "all"

        self.titleLabel = SubtitleLabel("Bandeja de Notificaciones y Eventos", self)
        self.viewLayout.addWidget(self.titleLabel)

        self.sub_desc = CaptionLabel("Historial de alertas, sincronizaciones y eventos operacionales de la sesión activa.", self)
        self.viewLayout.addWidget(self.sub_desc)

        # Barra de Filtros
        self.seg_filter = SegmentedWidget(self)
        self.seg_filter.addItem("all", "Todas")
        self.seg_filter.addItem("success", "Exitosas")
        self.seg_filter.addItem("warning", "Advertencias")
        self.seg_filter.addItem("error", "Errores")
        self.seg_filter.setCurrentItem("all")
        self.seg_filter.currentItemChanged.connect(self.on_filter_changed)
        self.viewLayout.addWidget(self.seg_filter)

        # Contenedor desplazable de notificaciones
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setFixedHeight(360)

        self.container_widget = QWidget(self.scroll_area)
        self.container_layout = QVBoxLayout(self.container_widget)
        self.container_layout.setContentsMargins(0, 4, 8, 4)
        self.container_layout.setSpacing(8)
        self.scroll_area.setWidget(self.container_widget)
        self.viewLayout.addWidget(self.scroll_area)

        # Botón para limpiar
        btn_bar = QHBoxLayout()
        self.btn_clear = PushButton("Limpiar Bandeja", self, FIF.DELETE)
        self.btn_clear.clicked.connect(self.handle_clear)
        btn_bar.addWidget(self.btn_clear)
        btn_bar.addStretch(1)
        self.viewLayout.addLayout(btn_bar)

        self.yesButton.setText("Cerrar")
        self.cancelButton.hide()
        self.widget.setMinimumWidth(540)

        self.apply_theme_styles()
        self.render_notifications()

        qconfig.themeChanged.connect(self._on_theme_changed)

    def _on_theme_changed(self):
        self.apply_theme_styles()
        self.render_notifications()

    def apply_theme_styles(self):
        dark = isDarkTheme()
        sub_color = "#94a3b8" if dark else "#64748b"
        self.sub_desc.setStyleSheet(f"color: {sub_color};")
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.container_widget.setStyleSheet("background: transparent;")

    def on_filter_changed(self, route_key: str):
        self.current_filter = route_key
        self.render_notifications()

    def render_notifications(self):
        # Limpiar contenedor de forma segura
        while self.container_layout.count() > 0:
            item = self.container_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        filtered = [
            n for n in reversed(self.notifications)
            if self.current_filter == "all" or n.get("type") == self.current_filter
        ]

        dark = isDarkTheme()
        card_bg = "#202020" if dark else "#ffffff"
        card_border = "rgba(255, 255, 255, 0.08)" if dark else "rgba(0, 0, 0, 0.06)"
        title_color = "#f8fafc" if dark else "#0f172a"
        time_color = "#94a3b8" if dark else "#64748b"
        content_color = "#cbd5e1" if dark else "#334155"
        empty_color = "#94a3b8" if dark else "#64748b"

        if not filtered:
            empty_card = CardWidget(self.container_widget)
            empty_card.setStyleSheet(
                f"CardWidget {{ background-color: {card_bg}; border: 1px solid {card_border}; border-radius: 8px; }}"
            )
            empty_layout = QVBoxLayout(empty_card)
            empty_layout.setContentsMargins(20, 24, 20, 24)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_empty = BodyLabel("No hay notificaciones registradas en esta categoría.", empty_card)
            lbl_empty.setStyleSheet(f"color: {empty_color}; font-style: italic; background: transparent;")
            empty_layout.addWidget(lbl_empty)
            self.container_layout.addWidget(empty_card)
            return

        for notif in filtered:
            card = CardWidget(self.container_widget)
            card.setStyleSheet(
                f"CardWidget {{ background-color: {card_bg}; border: 1px solid {card_border}; border-radius: 8px; }}"
            )
            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(14, 10, 14, 10)
            c_layout.setSpacing(12)

            # Icono según tipo
            ntype = notif.get("type", "info")
            if ntype == "success":
                icon = InfoBarIcon.SUCCESS
            elif ntype == "warning":
                icon = InfoBarIcon.WARNING
            elif ntype == "error":
                icon = InfoBarIcon.ERROR
            else:
                icon = InfoBarIcon.INFORMATION

            icon_widget = IconWidget(icon, card)
            icon_widget.setFixedSize(22, 22)
            c_layout.addWidget(icon_widget)

            # Textos
            v_text = QVBoxLayout()
            v_text.setSpacing(2)

            h_top = QHBoxLayout()
            t_title = BodyLabel(notif.get("title", "Notificación"), card)
            t_title.setStyleSheet(f"font-weight: 700; color: {title_color}; font-size: 13px; background: transparent;")
            h_top.addWidget(t_title)
            h_top.addStretch(1)

            t_time = CaptionLabel(notif.get("time", ""), card)
            t_time.setStyleSheet(f"color: {time_color}; font-size: 11px; background: transparent;")
            h_top.addWidget(t_time)
            v_text.addLayout(h_top)

            t_content = CaptionLabel(notif.get("content", ""), card)
            t_content.setWordWrap(True)
            t_content.setStyleSheet(f"color: {content_color}; font-size: 12px; background: transparent;")
            v_text.addWidget(t_content)

            c_layout.addLayout(v_text, stretch=1)
            self.container_layout.addWidget(card)

        self.container_layout.addStretch(1)

    def handle_clear(self):
        self.notifications.clear()
        if callable(self.on_clear_callback):
            self.on_clear_callback()
        self.render_notifications()
