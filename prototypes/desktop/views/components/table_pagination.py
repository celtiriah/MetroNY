"""
table_pagination.py - Componente visual reutilizable de paginación variable para PyQt-Fluent-Widgets.
Estandariza la paginación, navegación, contador de registros y barra de progreso indeterminada
en todas las tablas del sistema Metro NY.
"""
from typing import Optional, List, Any, Callable, Sequence
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    CaptionLabel, ComboBox, ToolButton, IndeterminateProgressBar,
    FluentIcon as FIF
)


class TablePaginationBar(QWidget):
    """
    Barra inferior estandarizada de paginación variable.
    Proporciona:
    - Indicador visual de rango y total de registros.
    - Selector dinámico de tamaño de página (25, 50, 100, 250 filas).
    - Botones de navegación (Anterior / Siguiente).
    - Barra de progreso indeterminada integrada para cargas asíncronas.
    - Manejo centralizado del particionado de datos en memoria y cálculo de páginas.
    """
    page_changed = pyqtSignal(list, int, int)  # (page_items, current_page, total_pages)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        default_page_size: int = 50,
        item_label: str = "registros",
        show_progress: bool = True
    ):
        super().__init__(parent)
        self.item_label: str = item_label
        self.page_size: int = default_page_size
        self.current_page: int = 0
        self.all_items: List[Any] = []
        self._show_progress: bool = show_progress

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 4, 0, 0)
        main_layout.setSpacing(6)

        # Barra de progreso indeterminada
        self.progress_bar = IndeterminateProgressBar(self)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # Fila de controles de paginación
        controls_row = QHBoxLayout()
        controls_row.setContentsMargins(0, 0, 0, 0)
        controls_row.setSpacing(10)

        self.lbl_info = CaptionLabel(f"0 {self.item_label} registrados.", self)
        controls_row.addWidget(self.lbl_info)
        controls_row.addStretch(1)

        controls_row.addWidget(CaptionLabel("Mostrar:", self))
        self.combo_page_size = ComboBox(self)
        self.combo_page_size.addItem("25 filas / pág", userData=25)
        self.combo_page_size.addItem("50 filas / pág", userData=50)
        self.combo_page_size.addItem("100 filas / pág", userData=100)
        self.combo_page_size.addItem("250 filas / pág", userData=250)

        # Seleccionar el índice correspondiente al tamaño predeterminado
        default_idx = 1
        for i in range(self.combo_page_size.count()):
            if self.combo_page_size.itemData(i) == self.page_size:
                default_idx = i
                break
        self.combo_page_size.setCurrentIndex(default_idx)
        self.combo_page_size.currentIndexChanged.connect(self._on_combo_page_size_changed)
        controls_row.addWidget(self.combo_page_size)

        self.btn_prev = ToolButton(FIF.PAGE_LEFT, self)
        self.btn_prev.setToolTip("Página Anterior")
        self.btn_prev.setEnabled(False)
        self.btn_prev.clicked.connect(self.prev_page)
        controls_row.addWidget(self.btn_prev)

        self.btn_next = ToolButton(FIF.PAGE_RIGHT, self)
        self.btn_next.setToolTip("Página Siguiente")
        self.btn_next.setEnabled(False)
        self.btn_next.clicked.connect(self.next_page)
        controls_row.addWidget(self.btn_next)

        main_layout.addLayout(controls_row)

    def set_loading(self, is_loading: bool, message: str = ""):
        """Activa o desactiva el estado visual de carga."""
        if is_loading:
            if self._show_progress:
                self.progress_bar.show()
            self.btn_prev.setEnabled(False)
            self.btn_next.setEnabled(False)
            if message:
                self.lbl_info.setText(message)
        else:
            self.progress_bar.hide()
            self._update_controls_state()

    def set_data(
        self,
        items: Sequence[Any],
        reset_page: bool = True,
        highlight_predicate: Optional[Callable[[Any], bool]] = None
    ) -> List[Any]:
        """
        Almacena el conjunto completo de datos, ajusta la página actual y retorna
        la porción de elementos correspondiente a la página seleccionada.
        """
        self.progress_bar.hide()
        self.all_items = list(items)
        total_records = len(self.all_items)
        total_pages = max(1, (total_records + self.page_size - 1) // self.page_size)

        if highlight_predicate is not None:
            found_idx: Optional[int] = None
            for idx, item in enumerate(self.all_items):
                try:
                    if highlight_predicate(item):
                        found_idx = idx
                        break
                except Exception:
                    continue
            if found_idx is not None:
                self.current_page = found_idx // self.page_size
            elif reset_page:
                self.current_page = 0
        elif reset_page:
            self.current_page = 0

        self.current_page = max(0, min(self.current_page, total_pages - 1))
        self._update_controls_state()
        return self.get_current_page_items()

    def get_current_page_items(self) -> List[Any]:
        """Retorna la lista de elementos para la página actual."""
        total_records = len(self.all_items)
        if total_records == 0:
            return []
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, total_records)
        return self.all_items[start_idx:end_idx]

    def _update_controls_state(self):
        """Actualiza el texto descriptivo y el estado de habilitación de los botones."""
        total_records = len(self.all_items)
        if total_records == 0:
            self.lbl_info.setText(f"0 {self.item_label} encontrados.")
            self.btn_prev.setEnabled(False)
            self.btn_next.setEnabled(False)
            return

        total_pages = max(1, (total_records + self.page_size - 1) // self.page_size)
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, total_records)

        self.lbl_info.setText(
            f"Mostrando {self.item_label} {start_idx + 1} a {end_idx} de {total_records} "
            f"(Página {self.current_page + 1} de {total_pages})"
        )
        self.btn_prev.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled(self.current_page < total_pages - 1)

    def _on_combo_page_size_changed(self, index: int):
        val = self.combo_page_size.currentData()
        if val is not None:
            self.page_size = int(val)
            self.current_page = 0
            self._notify_page_change()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._notify_page_change()

    def next_page(self):
        total_records = len(self.all_items)
        total_pages = max(1, (total_records + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._notify_page_change()

    def _notify_page_change(self):
        self._update_controls_state()
        page_items = self.get_current_page_items()
        total_pages = max(1, (len(self.all_items) + self.page_size - 1) // self.page_size)
        self.page_changed.emit(page_items, self.current_page, total_pages)

