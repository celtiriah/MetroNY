"""
Background Worker Threads for Asynchronous Database Operations.
Prevents GUI freezing during heavy database queries and network calls.
"""
from PyQt5.QtCore import QThread, pyqtSignal
from services.db import execute_query


class QueryWorker(QThread):
    """
    Executes a SQL query in a separate thread and emits signals upon completion.
    """
    data_loaded = pyqtSignal(list, list, str)   # columns, rows, pdb
    error_occurred = pyqtSignal(str)

    def __init__(self, sql: str, params: dict = None, parent=None):
        super().__init__(parent)
        self.sql = sql
        self.params = params or {}

    def run(self):
        try:
            res = execute_query(self.sql, self.params)
            self.data_loaded.emit(res["columns"], res["rows"], res.get("pdb", "FREEPDB1"))
        except Exception as e:
            self.error_occurred.emit(str(e))

