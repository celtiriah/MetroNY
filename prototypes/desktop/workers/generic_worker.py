"""
generic_worker.py - Hilo de fondo genérico para consultas asíncronas en Oracle.
Ejecuta funciones de servicios en segundo plano para evitar bloqueos de la interfaz Fluent.
"""
from typing import Callable, Any, Optional
from PyQt5.QtCore import QThread, pyqtSignal, QObject


class GenericDataLoaderWorker(QThread):
    """
    Worker genérico basado en QThread para ejecutar funciones de extracción de datos
    de manera asíncrona, emitiendo señales al finalizar o si se produce una excepción.
    """
    data_loaded = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        fetch_fn: Callable[..., Any],
        *args: Any,
        parent: Optional[QObject] = None,
        **kwargs: Any
    ):
        super().__init__(parent)
        self.fetch_fn = fetch_fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.fetch_fn(*self.args, **self.kwargs)
            self.data_loaded.emit(result)
        except Exception as exc:
            self.error_occurred.emit(str(exc))

