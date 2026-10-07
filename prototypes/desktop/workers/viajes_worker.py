"""
ViajesLoaderWorker - Hilo de fondo para carga asíncrona de viajes programados.
Previene el congelamiento de la GUI al consultar grandes volúmenes de viajes en Oracle.
"""
from typing import Optional, List, Dict, Any
from PyQt5.QtCore import QThread, pyqtSignal
from services import m2_routes_service


class ViajesLoaderWorker(QThread):
    """
    Ejecuta la extracción de viajes programados y catálogo de fechas disponibles
    en un hilo separado para mantener la fluidez total de la interfaz Fluent.
    """
    data_loaded = pyqtSignal(list, list)   # viajes (List[Dict]), fechas_disponibles (List[str])
    error_occurred = pyqtSignal(str)

    def __init__(self, fecha: Optional[str] = None, estado: str = "(Todos)", parent=None):
        super().__init__(parent)
        self.fecha = fecha
        self.estado = estado

    def run(self):
        try:
            fechas_disp = m2_routes_service.get_fechas_viajes_registrados()
            viajes = m2_routes_service.get_viajes_programados(fecha=self.fecha, estado=self.estado)
            self.data_loaded.emit(viajes, fechas_disp)
        except Exception as exc:
            self.error_occurred.emit(str(exc))

