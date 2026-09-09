"""
Reusable Fluent Stat / KPI Metric Card Component.
"""
from PyQt5.QtWidgets import QVBoxLayout
from qfluentwidgets import CardWidget, CaptionLabel, TitleLabel
from config import MTA_BLUE


class StatCard(CardWidget):
    """
    Elevated card displaying a single operational metric with icon, title, and bold value.
    """
    def __init__(self, title: str, icon: str = "📊", initial_value: str = "-", parent=None):
        super().__init__(parent=parent)
        self.init_ui(title, icon, initial_value)

    def init_ui(self, title: str, icon: str, initial_value: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self.lbl_top = CaptionLabel(f"{icon} {title.upper()}", self)
        self.lbl_top.setStyleSheet("font-weight: 700; letter-spacing: 0.5px;")

        self.lbl_val = TitleLabel(initial_value, self)
        self.lbl_val.setStyleSheet(f"color: {MTA_BLUE}; padding-top: 4px;")

        layout.addWidget(self.lbl_top)
        layout.addWidget(self.lbl_val)

    def set_value(self, value: str):
        self.lbl_val.setText(str(value))

