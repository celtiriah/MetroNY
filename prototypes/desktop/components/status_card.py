"""
Reusable Oracle Database Connection Status Card.
Displays connection health and active PDB using native Fluent icons.
"""
from PyQt5.QtWidgets import QHBoxLayout
from qfluentwidgets import CardWidget, StrongBodyLabel, CaptionLabel, IconWidget, FluentIcon as FIF


class StatusCard(CardWidget):
    """
    Status bar displaying the health of the Oracle connection and active PDB.
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        self.icon_status = IconWidget(FIF.SYNC, self)
        self.icon_status.setFixedSize(16, 16)
        layout.addWidget(self.icon_status)

        self.status_title = StrongBodyLabel("Conectando a Oracle Database...", self)
        self.status_desc = CaptionLabel("Detectando servicio Pluggable Database...", self)

        layout.addWidget(self.status_title)
        layout.addStretch(1)
        layout.addWidget(self.status_desc)

    def set_online(self, pdb_name: str, user: str, host: str):
        self.icon_status.setIcon(FIF.COMPLETED)
        self.status_title.setText(f"Oracle Database Activo ({pdb_name})")
        self.status_desc.setText(f"Esquema: {user} | Host: {host}")

    def set_error(self, error_msg: str):
        self.icon_status.setIcon(FIF.CANCEL)
        self.status_title.setText("Error de Conexión a Oracle")
        self.status_desc.setText(str(error_msg))
