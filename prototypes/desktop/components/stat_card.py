"""
Reusable Fluent Stat / KPI Metric Card Component.
Displays operational metrics with vector FluentIcon, label, and bold value.
Automatically adapts to Light and Dark themes in real time.
"""
from typing import Union
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QIcon
from qfluentwidgets import (
    CardWidget, CaptionLabel, TitleLabel, IconWidget,
    FluentIconBase, FluentIcon as FIF, isDarkTheme, qconfig
)
from config import MTA_BLUE


class StatCard(CardWidget):
    """
    Elevated card displaying a single operational metric with vector Fluent icon, title, and bold value.
    Supports real-time dynamic switching between Light and Dark themes.
    """
    def __init__(self, title: str, icon: Union[FluentIconBase, QIcon, str, None] = FIF.INFO, initial_value: str = "-", parent=None):
        super().__init__(parent=parent)
        self.init_ui(title, icon, initial_value)

    def init_ui(self, title: str, icon: Union[FluentIconBase, QIcon, str, None], initial_value: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)

        if isinstance(icon, (FluentIconBase, QIcon)):
            self.icon_widget = IconWidget(icon, self)
            self.icon_widget.setFixedSize(16, 16)
            top_layout.addWidget(self.icon_widget)

        self.lbl_top = CaptionLabel(title.upper(), self)
        top_layout.addWidget(self.lbl_top)
        top_layout.addStretch(1)

        self.lbl_val = TitleLabel(initial_value, self)

        layout.addLayout(top_layout)
        layout.addWidget(self.lbl_val)

        self.update_style()
        qconfig.themeChanged.connect(self.update_style)

    def update_style(self):
        dark = isDarkTheme()
        val_color = "#4da6ff" if dark else MTA_BLUE
        top_color = "rgba(255, 255, 255, 0.70)" if dark else "rgba(0, 0, 0, 0.60)"
        self.lbl_val.setStyleSheet(f"color: {val_color}; padding-top: 4px; font-weight: bold;")
        self.lbl_top.setStyleSheet(f"font-weight: 700; color: {top_color};")

    def set_value(self, value: str):
        self.lbl_val.setText(str(value))
