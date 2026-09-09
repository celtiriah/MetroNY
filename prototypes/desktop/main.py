"""
Main Entry Point for the MetroNY Desktop Application.
Configures High-DPI scaling policies and launches the Fluent GUI event loop.
"""
import sys
import os

# Suppress deprecation warnings from legacy connectors
os.environ["PYTHONWARNINGS"] = "ignore"

# Ensure prototypes/desktop is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from views.main_window import MetroFluentApp


def main():
    # 1. Configure High-DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # 2. Launch Application Event Loop
    app = QApplication(sys.argv)
    window = MetroFluentApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

