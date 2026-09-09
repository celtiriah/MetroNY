"""
Reusable Oracle Database Connection Status Card.
"""
from PyQt5.QtWidgets import QHBoxLayout
from qfluentwidgets import CardWidget, StrongBodyLabel, CaptionLabel


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

        self.status_title = StrongBodyLabel("🟡 Conectando a Oracle Database...", self)
        self.status_desc = CaptionLabel("Detectando servicio Pluggable Database...", self)

        layout.addWidget(self.status_title)
        layout.addStretch(1)
        layout.addWidget(self.status_desc)

    def set_online(self, pdb_name: str, user: str, host: str):
        self.status_title.setText(f"🟢 Oracle Database Activo ({pdb_name})")
        self.status_desc.setText(f"Esquema: {user} | Host: {host}")

    def set_error(self, error_msg: str):
        self.status_title.setText("🔴 Error de Conexión a Oracle")
        self.status_desc.setText(str(error_msg))

