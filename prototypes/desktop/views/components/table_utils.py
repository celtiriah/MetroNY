"""
table_utils.py - Utilidades de dimensionamiento, alineacion y comportamiento interactivo para tablas Fluent.
Proporciona redimensionamiento interactivo de columnas, sincronizacion en tiempo real de cellWidgets
y centrado estetico automatico para celdas de texto con QFluentWidgets TableItemDelegate.
"""
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtWidgets import QHeaderView, QStyleOptionViewItem
from qfluentwidgets import TableWidget, TableItemDelegate


class CenteredTableItemDelegate(TableItemDelegate):
    """
    Delegado que hereda de TableItemDelegate de QFluentWidgets, preservando
    animaciones hover, seleccion Fluent con esquinas redondeadas y temas Claro/Oscuro,
    pero asegurando que el texto de cada celda se renderice centrado por defecto
    para lograr consistencia visual perfecta con las insignias y chips del sistema.
    """

    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        super().initStyleOption(option, index)
        raw_align = index.data(Qt.ItemDataRole.TextAlignmentRole)
        if raw_align is None:
            option.displayAlignment = Qt.AlignmentFlag.AlignCenter
        else:
            option.displayAlignment = Qt.AlignmentFlag(raw_align)


def configure_interactive_table(
    table: TableWidget,
    min_col_width: int = 70,
    default_row_height: int = 38
) -> None:
    """
    Configura una tabla TableWidget para permitir redimensionamiento interactivo por parte del usuario.
    - El usuario puede arrastrar libremente los bordes de cualquier columna con el cursor del mouse.
    - Los widgets dentro de las celdas (StatusBadge, LineColorChip) se sincronizan en tiempo real
      durante el arrastre del mouse mediante updateEditorGeometries.
    - Todas las celdas de texto quedan centradas por defecto a traves de CenteredTableItemDelegate.
    - Doble clic en la separacion auto-ajusta la columna al contenido.
    - Se habilita desplazamiento horizontal fluido cuando las columnas exceden el ancho visible.
    """
    header = table.horizontalHeader()
    if header is not None:
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setMinimumSectionSize(min_col_width)
        header.setStretchLastSection(False)
        try:
            header.sectionResized.disconnect(table.updateEditorGeometries)
        except (TypeError, RuntimeError):
            pass
        header.sectionResized.connect(table.updateEditorGeometries)

    table.setWordWrap(True)
    v_header = table.verticalHeader()
    if v_header is not None:
        v_header.setDefaultSectionSize(default_row_height)
        try:
            v_header.sectionResized.disconnect(table.updateEditorGeometries)
        except (TypeError, RuntimeError):
            pass
        v_header.sectionResized.connect(table.updateEditorGeometries)

    table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    # Configurar delegado centrado preservando el estilo Fluent
    if not isinstance(table.itemDelegate(), CenteredTableItemDelegate):
        table.setItemDelegate(CenteredTableItemDelegate(table))


def auto_fit_table_columns(
    table: TableWidget,
    padding: int = 20,
    min_width: int = 75,
    max_width: int = 450
) -> None:
    """
    Ajusta dinamicamente el ancho de todas las columnas al contenido actual,
    anadiendo un margen de respiracion visual para etiquetas y chips Fluent.
    """
    table.resizeColumnsToContents()
    for col in range(table.columnCount()):
        current_w = table.columnWidth(col)
        target_w = min(max(current_w + padding, min_width), max_width)
        table.setColumnWidth(col, target_w)
    table.updateEditorGeometries()
