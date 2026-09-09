"""
Main Window Shell for the MetroNY Desktop Application.
Manages the Fluent navigation sidebar, sub-interfaces, and title bar action buttons.
"""
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from qfluentwidgets import (
    FluentWindow, FluentIcon as FIF, setTheme, Theme,
    setThemeColor, TransparentToolButton, InfoBar, InfoBarPosition
)

from config import (
    APP_TITLE, DEFAULT_WIDTH, DEFAULT_HEIGHT, MIN_WIDTH,
    MIN_HEIGHT, MTA_BLUE
)
from services import metro_service
from views.dashboard_interface import DashboardInterface
from views.stations_interface import StationsInterface
from views.fleet_interface import FleetInterface
from views.staff_interface import StaffInterface
from views.incidents_interface import IncidentsInterface
from views.queries_interface import QueriesInterface


class MetroFluentApp(FluentWindow):
    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self.init_window()
        self.init_sub_interfaces()
        self.init_navigation()
        self.init_title_bar_actions()
        self.load_all_data()

    def init_window(self):
        self.setWindowTitle(APP_TITLE)
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)

        setThemeColor(MTA_BLUE)
        setTheme(Theme.LIGHT)

    def init_sub_interfaces(self):
        self.dashboard_interface = DashboardInterface(self)
        self.stations_interface = StationsInterface(self)
        self.fleet_interface = FleetInterface(self)
        self.staff_interface = StaffInterface(self)
        self.incidents_interface = IncidentsInterface(self)
        self.queries_interface = QueriesInterface(self)

    def init_navigation(self):
        # 1. Panel General
        self.addSubInterface(self.dashboard_interface, FIF.HOME, "Panel General")
        # 2. Estaciones y Red (Módulo 1 & 2)
        self.addSubInterface(self.stations_interface, FIF.PIN, "Estaciones y Red")
        # 3. Flota y Mantenimiento (Módulo 3 & 6)
        self.addSubInterface(self.fleet_interface, FIF.TRAIN, "Flota y Trenes")
        # 4. Personal y Turnos (Módulo 4)
        self.addSubInterface(self.staff_interface, FIF.PEOPLE, "Personal y Turnos")
        # 5. Operaciones e Incidentes (Módulo 7)
        self.addSubInterface(self.incidents_interface, FIF.INFO, "Incidentes Operativos")
        # 6. Consultas Mínimas Obligatorias
        self.addSubInterface(self.queries_interface, FIF.SEARCH, "15 Consultas Mínimas")

    def init_title_bar_actions(self):
        # Quick action buttons decoupled from navigation selection slider
        self.btn_sync = TransparentToolButton(FIF.SYNC, self)
        self.btn_sync.setToolTip("Actualizar Datos desde Oracle")
        self.btn_sync.clicked.connect(self.load_all_data)

        self.btn_theme = TransparentToolButton(FIF.BRUSH, self)
        self.btn_theme.setToolTip("Alternar Tema Claro / Oscuro")
        self.btn_theme.clicked.connect(self.toggle_theme)

        # Insert prior to system window controls (min/max/close)
        self.titleBar.hBoxLayout.insertWidget(3, self.btn_sync)
        self.titleBar.hBoxLayout.insertWidget(4, self.btn_theme)

    def toggle_theme(self):
        if self.current_theme == "light":
            self.current_theme = "dark"
            setTheme(Theme.DARK)
            InfoBar.info(
                title="Modo Oscuro activado",
                content="La interfaz se ha cambiado a Tema Oscuro.",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000
            )
        else:
            self.current_theme = "light"
            setTheme(Theme.LIGHT)
            InfoBar.info(
                title="Modo Claro activado",
                content="La interfaz se ha cambiado a Tema Claro.",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000
            )

    def load_all_data(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            # 1. Health check & Banner
            health = metro_service.check_db_health()
            self.dashboard_interface.status_card.set_online(
                pdb_name=health["pdb"],
                user=health["user"],
                host=health["host"]
            )

            # 2. KPIs & Lines (Dashboard)
            kpis = metro_service.get_dashboard_kpis()
            self.dashboard_interface.update_kpis(kpis)

            lines = metro_service.get_lines_summary()
            self.dashboard_interface.update_lines(lines)

            # 3. Stations
            stations = metro_service.get_stations_summary()
            self.stations_interface.update_stations(stations)

            # 4. Fleet
            fleet = metro_service.get_fleet_summary()
            self.fleet_interface.update_fleet(fleet)

            # 5. Staff
            staff = metro_service.get_staff_summary()
            self.staff_interface.update_staff(staff)

            # 6. Incidents
            incidents = metro_service.get_incidents_summary()
            self.incidents_interface.update_incidents(incidents)

            InfoBar.success(
                title="Datos Sincronizados",
                content=f"Conexión activa con Oracle Database ({health['pdb']}). Módulos actualizados.",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2500
            )
        except Exception as e:
            self.dashboard_interface.status_card.set_error(str(e))
            InfoBar.error(
                title="Fallo de Conexión a Oracle",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000
            )
        finally:
            QApplication.restoreOverrideCursor()

