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
from views.m1_stations_interface import StationsInterface
from views.m2_routes_interface import M2RoutesInterface
from views.m3_fleet_interface import FleetInterface
from views.m4_staff_interface import StaffInterface
from views.m5_cards_interface import CardsInterface
from views.m6_maintenance_interface import MaintenanceInterface
from views.m7_incidents_interface import IncidentsInterface
from views.queries_interface import QueriesInterface


class MetroFluentApp(FluentWindow):
    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self._loaded_interfaces = set()
        self.init_window()
        self.init_sub_interfaces()
        self.init_navigation()
        self.init_title_bar_actions()
        self.stackedWidget.currentChanged.connect(self.on_current_interface_changed)
        self.load_dashboard_data()

    def init_window(self):
        self.setWindowTitle(APP_TITLE)
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)

        setThemeColor(MTA_BLUE)
        setTheme(Theme.LIGHT)

    def init_sub_interfaces(self):
        self.dashboard_interface = DashboardInterface(self)
        self.stations_interface = StationsInterface(self)
        self.routes_interface = M2RoutesInterface(self)
        self.fleet_interface = FleetInterface(self)
        self.staff_interface = StaffInterface(self)
        self.cards_interface = CardsInterface(self)
        self.maintenance_interface = MaintenanceInterface(self)
        self.incidents_interface = IncidentsInterface(self)
        self.queries_interface = QueriesInterface(self)

    def init_navigation(self):
        # 1. Panel General
        self.addSubInterface(self.dashboard_interface, FIF.HOME, "Panel General")
        # 2. Módulo 1: Red y Estaciones
        self.addSubInterface(self.stations_interface, FIF.PIN, "M1: Red y Estaciones")
        # 3. Módulo 2: Rutas y Horarios
        self.addSubInterface(self.routes_interface, FIF.BUS, "M2: Rutas y Horarios")
        # 4. Módulo 3: Flota y Trenes
        self.addSubInterface(self.fleet_interface, FIF.TRAIN, "M3: Flota y Trenes")
        # 5. Módulo 4: Personal y Turnos
        self.addSubInterface(self.staff_interface, FIF.PEOPLE, "M4: Personal y Turnos")
        # 6. Módulo 5: Pasajeros y Torniquetes
        self.addSubInterface(self.cards_interface, FIF.QRCODE, "M5: Pasajeros y OMNY")
        # 7. Módulo 6: Mantenimiento
        self.addSubInterface(self.maintenance_interface, FIF.DEVELOPER_TOOLS, "M6: Mantenimiento")
        # 8. Módulo 7: Incidentes Operativos
        self.addSubInterface(self.incidents_interface, FIF.INFO, "M7: Incidentes")
        # 9. Consultas Mínimas Obligatorias
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

    def on_current_interface_changed(self, index: int):
        widget = self.stackedWidget.widget(index)
        if widget is not None and widget not in self._loaded_interfaces:
            self.load_interface_data(widget)

    def load_dashboard_data(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            health = metro_service.check_db_health()
            self.dashboard_interface.status_card.set_online(
                pdb_name=health["pdb"],
                user=health["user"],
                host=health["host"]
            )

            kpis = metro_service.get_dashboard_kpis()
            self.dashboard_interface.update_kpis(kpis)

            lines = metro_service.get_lines_summary()
            self.dashboard_interface.update_lines(lines)
            self._loaded_interfaces.add(self.dashboard_interface)
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
            if QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()

    def load_interface_data(self, widget):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            if widget is self.dashboard_interface:
                self.load_dashboard_data()
            elif widget is self.stations_interface:
                stations = metro_service.get_stations_summary()
                self.stations_interface.update_stations(stations)
            elif widget is self.routes_interface:
                self.routes_interface.load_all_data()
            elif widget is self.fleet_interface:
                fleet = metro_service.get_fleet_summary()
                self.fleet_interface.update_fleet(fleet)
            elif widget is self.staff_interface:
                staff = metro_service.get_staff_summary()
                self.staff_interface.update_staff(staff)
            elif widget is self.cards_interface:
                self.cards_interface.load_cards_data()
            elif widget is self.maintenance_interface:
                self.maintenance_interface.load_maintenance_data()
            elif widget is self.incidents_interface:
                self.incidents_interface.load_incidents_data()
            self._loaded_interfaces.add(widget)
        except Exception as e:
            InfoBar.error(
                title="Error al Cargar Módulo",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3500
            )
        finally:
            if QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()

    def load_all_data(self):
        """Sincroniza el dashboard y el módulo actualmente visible bajo demanda."""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.load_dashboard_data()
            current = self.stackedWidget.currentWidget()
            if current is not None and current is not self.dashboard_interface:
                self.load_interface_data(current)

            InfoBar.success(
                title="Datos Sincronizados",
                content="Módulos actualizados correctamente desde Oracle Database.",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2500
            )
        except Exception as e:
            InfoBar.error(
                title="Fallo de Sincronización",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000
            )
        finally:
            if QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()

