from datetime import datetime
from typing import Optional, List, Dict, Any

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from qfluentwidgets import (
    FluentWindow, FluentIcon as FIF, setTheme, Theme,
    setThemeColor, TransparentToolButton, InfoBar, InfoBarPosition, InfoBarIcon
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
from views.components import NotificationTrayDialog


class MetroFluentApp(FluentWindow):
    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self._loaded_interfaces = set()
        self.notifications_history: List[Dict[str, Any]] = []
        self._setup_notification_interceptor()
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
        self.addSubInterface(self.routes_interface, FIF.DATE_TIME, "M2: Rutas y Horarios")
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
        # 9. Centro de Reporteria Analitica (BI)
        self.addSubInterface(self.queries_interface, FIF.PIE_SINGLE, "Centro de Reportería")

    def init_title_bar_actions(self):
        # Quick action buttons decoupled from navigation selection slider
        self.btn_sync = TransparentToolButton(FIF.SYNC, self)
        self.btn_sync.setToolTip("Actualizar Datos desde Oracle")
        self.btn_sync.clicked.connect(self.load_all_data)

        self.btn_notifications = TransparentToolButton(FIF.RINGER, self)
        self.btn_notifications.setToolTip("Bandeja de Notificaciones y Eventos")
        self.btn_notifications.clicked.connect(self.show_notification_tray)

        self.btn_theme = TransparentToolButton(FIF.BRUSH, self)
        self.btn_theme.setToolTip("Alternar Tema Claro / Oscuro")
        self.btn_theme.clicked.connect(self.toggle_theme)

        # Insert prior to system window controls (min/max/close)
        self.titleBar.hBoxLayout.insertWidget(3, self.btn_sync)
        self.titleBar.hBoxLayout.insertWidget(4, self.btn_notifications)
        self.titleBar.hBoxLayout.insertWidget(5, self.btn_theme)

    def _setup_notification_interceptor(self):
        """
        Intercepta globalmente todas las llamadas a InfoBar (success, error, warning, info)
        para que cualquier módulo (M1-M7, Consultas, Dashboard) automáticamente:
        1. Extienda su duración (6 a 10s).
        2. Se registre en el historial de la bandeja de notificaciones.
        """
        original_new = InfoBar.new
        app_ref = self

        @classmethod
        def hooked_infobar_new(
            cls, icon, title, content, orient=Qt.Orientation.Horizontal,
            isClosable=True, duration=1000, position=InfoBarPosition.TOP_RIGHT, parent=None
        ):
            icon_type_map = {
                InfoBarIcon.SUCCESS: "success",
                InfoBarIcon.WARNING: "warning",
                InfoBarIcon.ERROR: "error",
                InfoBarIcon.INFORMATION: "info",
            }
            msg_type = icon_type_map.get(icon, "info")

            min_durations = {
                "info": 6000,
                "success": 6000,
                "warning": 8000,
                "error": 10000,
            }
            effective_duration = max(duration, min_durations.get(msg_type, 6000))

            now_str = datetime.now().strftime("%H:%M:%S")
            app_ref.notifications_history.append({
                "time": now_str,
                "type": msg_type,
                "title": str(title),
                "content": str(content),
                "duration": effective_duration,
            })

            target_parent = parent if parent is not None else app_ref

            return original_new(
                icon, title, content, orient=orient,
                isClosable=isClosable, duration=effective_duration,
                position=position, parent=target_parent
            )

        setattr(InfoBar, "new", hooked_infobar_new)

    def notify(self, title: str, content: str, msg_type: str = "info", duration: Optional[int] = None):
        """
        Emite una notificación emergente con duración extendida y registro centralizado
        en el historial de la bandeja mediante el interceptor global.
        """
        if duration is None:
            if msg_type in ("error",):
                duration = 10000
            elif msg_type in ("warning",):
                duration = 8000
            else:
                duration = 6000

        if msg_type == "success":
            InfoBar.success(title=title, content=content, parent=self, position=InfoBarPosition.TOP_RIGHT, duration=duration)
        elif msg_type == "warning":
            InfoBar.warning(title=title, content=content, parent=self, position=InfoBarPosition.TOP_RIGHT, duration=duration)
        elif msg_type == "error":
            InfoBar.error(title=title, content=content, parent=self, position=InfoBarPosition.TOP_RIGHT, duration=duration)
        else:
            InfoBar.info(title=title, content=content, parent=self, position=InfoBarPosition.TOP_RIGHT, duration=duration)

    def show_notification_tray(self):
        """Abre la bandeja modal de historial de notificaciones y alertas."""
        dlg = NotificationTrayDialog(self.notifications_history, on_clear_callback=self.clear_notifications, parent=self)
        dlg.exec()

    def clear_notifications(self):
        """Limpia el historial de la bandeja de notificaciones."""
        self.notifications_history.clear()

    def toggle_theme(self):
        if self.current_theme == "light":
            self.current_theme = "dark"
            setTheme(Theme.DARK)
            self.notify(
                title="Modo Oscuro activado",
                content="La interfaz se ha cambiado a Tema Oscuro.",
                msg_type="info",
                duration=4000
            )
        else:
            self.current_theme = "light"
            setTheme(Theme.LIGHT)
            self.notify(
                title="Modo Claro activado",
                content="La interfaz se ha cambiado a Tema Claro.",
                msg_type="info",
                duration=4000
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

            incidents = metro_service.get_dashboard_active_incidents(5)
            self.dashboard_interface.update_active_incidents(incidents)

            top_stations = metro_service.get_dashboard_top_stations(5)
            self.dashboard_interface.update_top_stations(top_stations)

            lines = metro_service.get_lines_summary()
            self.dashboard_interface.update_lines(lines)
            self._loaded_interfaces.add(self.dashboard_interface)
        except Exception as e:
            self.dashboard_interface.status_card.set_error(str(e))
            self.notify(
                title="Fallo de Conexión a Oracle",
                content=str(e),
                msg_type="error",
                duration=10000
            )
        finally:
            if QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()

    def load_interface_data(self, widget):
        try:
            if widget is self.dashboard_interface:
                self.load_dashboard_data()
            elif widget is self.stations_interface:
                self.stations_interface.load_all_data()
            elif widget is self.routes_interface:
                self.routes_interface.load_all_data()
            elif widget is self.fleet_interface:
                self.fleet_interface.load_all_data()
            elif widget is self.staff_interface:
                self.staff_interface.load_all_data()
            elif widget is self.cards_interface:
                self.cards_interface.load_cards_data()
            elif widget is self.maintenance_interface:
                self.maintenance_interface.load_maintenance_data()
            elif widget is self.incidents_interface:
                self.incidents_interface.load_incidents_data()
            self._loaded_interfaces.add(widget)
        except Exception as e:
            self.notify(
                title="Error al Cargar Módulo",
                content=str(e),
                msg_type="error",
                duration=8000
            )

    def load_all_data(self):
        """Sincroniza el dashboard y el módulo actualmente visible bajo demanda."""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.load_dashboard_data()
            current = self.stackedWidget.currentWidget()
            if current is not None and current is not self.dashboard_interface:
                self.load_interface_data(current)

            self.notify(
                title="Datos Sincronizados",
                content="Módulos actualizados correctamente desde Oracle Database.",
                msg_type="success",
                duration=6000
            )
        except Exception as e:
            self.notify(
                title="Fallo de Sincronización",
                content=str(e),
                msg_type="error",
                duration=10000
            )
        finally:
            if QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()

