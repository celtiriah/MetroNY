"""
date_utils.py - Utilidades tipadas para componentes de seleccion de fechas y horas en MetroNY.
Proporciona interoperabilidad segura entre tipos nativos (str, date, datetime, time) y QDate/QTime con CalendarPicker y TimePicker de QFluentWidgets.
Incluye un traductor integrado (SpanishFluentTranslator) para asegurar que todos los widgets y dialogos de QFluentWidgets se muestren al 100% en español.
Proporciona RecordCalendarPicker para busqueda y filtrado de registros restringido exclusivamente a fechas existentes en base de datos.
"""
from datetime import date, datetime, time
from typing import Optional, Any, Set, Iterable
from PyQt5.QtCore import QDate, QTime, Qt, QTranslator, QModelIndex, QPoint
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QWidget, QApplication, QStyleOptionViewItem
from qfluentwidgets import CalendarPicker, TimePicker, themeColor, isDarkTheme
from qfluentwidgets.components.date_time.calendar_picker import CalendarView
from qfluentwidgets.components.date_time.calendar_view import DayScrollItemDelegate


class SpanishFluentTranslator(QTranslator):
    """
    Traductor dinamico en memoria para los componentes internos de QFluentWidgets.
    Garantiza que cadenas en ingles como 'Pick a date', 'hour', 'minute', 'second',
    meses y dias se presenten formalmente en español.
    """
    _TRANSLATIONS = {
        "Pick a date": "Seleccionar fecha",
        "hour": "Hora",
        "minute": "Minuto",
        "second": "Segundo",
        "Mo": "Lu",
        "Tu": "Ma",
        "We": "Mi",
        "Th": "Ju",
        "Fr": "Vi",
        "Sa": "Sa",
        "Su": "Do",
        "Jan": "Ene",
        "Feb": "Feb",
        "Mar": "Mar",
        "Apr": "Abr",
        "May": "May",
        "Jun": "Jun",
        "Jul": "Jul",
        "Aug": "Ago",
        "Sep": "Sep",
        "Oct": "Oct",
        "Nov": "Nov",
        "Dec": "Dic",
        "OK": "Aceptar",
        "Cancel": "Cancelar",
        "Reset": "Restablecer",
        "Today": "Hoy",
        "Clear": "Limpiar",
        "Select": "Seleccionar",
    }

    def translate(self, context: Optional[str], sourceText: Optional[str], disambiguation: Optional[str] = None, n: int = -1) -> str:
        if sourceText:
            return self._TRANSLATIONS.get(sourceText, "")
        return ""


_SPANISH_TRANSLATOR: Optional[SpanishFluentTranslator] = None


def ensure_spanish_translator() -> None:
    """
    Asegura la instalacion del traductor al español en la instancia activa de QApplication.
    """
    global _SPANISH_TRANSLATOR
    app = QApplication.instance()
    if app is not None and _SPANISH_TRANSLATOR is None:
        _SPANISH_TRANSLATOR = SpanishFluentTranslator(app)
        app.installTranslator(_SPANISH_TRANSLATOR)


def to_qdate(val: Any) -> Optional[QDate]:
    """
    Convierte cualquier representacion de fecha (date, datetime, str YYYY-MM-DD o QDate)
    a un objeto QDate valido. Retorna None si el valor es nulo o invalido.
    """
    if val is None or val == "" or val == "-":
        return None
    if isinstance(val, QDate):
        return val if val.isValid() else None
    if isinstance(val, (datetime, date)):
        return QDate(val.year, val.month, val.day)
    if isinstance(val, str):
        cleaned = val.strip()[:10]
        qd = QDate.fromString(cleaned, "yyyy-MM-dd")
        if qd.isValid():
            return qd
    return None


def qdate_to_iso(qd: Optional[QDate]) -> Optional[str]:
    """
    Convierte un QDate a una cadena en formato ISO (YYYY-MM-DD).
    Retorna None si el QDate es nulo o invalido.
    """
    if qd is not None and qd.isValid():
        return qd.toString(Qt.DateFormat.ISODate)
    return None


def create_calendar_picker(
    parent: Optional[QWidget] = None,
    initial_date: Any = None,
    allow_reset: bool = False
) -> CalendarPicker:
    """
    Construye y configura una instancia de CalendarPicker:
    - Asegura la traduccion a español.
    - Formato estandar ISO (YYYY-MM-DD).
    - Habilitacion opcional de boton de reinicio (limpiar a nulo).
    - Carga inicial segura de fecha o texto inicial en español.
    """
    ensure_spanish_translator()
    picker = CalendarPicker(parent)
    picker.setDateFormat(Qt.DateFormat.ISODate)
    if allow_reset:
        picker.setResetEnabled(True)

    qd = to_qdate(initial_date)
    if qd is not None:
        picker.setDate(qd)
    else:
        picker.setText("Seleccionar fecha")

    return picker


def to_qtime(val: Any) -> Optional[QTime]:
    """
    Convierte cualquier representacion de hora (time, datetime, str HH:MM / HH:MM:SS o QTime)
    a un objeto QTime valido. Retorna None si el valor es nulo o invalido.
    """
    if val is None or val == "" or val == "-":
        return None
    if isinstance(val, QTime):
        return val if val.isValid() else None
    if isinstance(val, (datetime, time)):
        return QTime(val.hour, val.minute, getattr(val, "second", 0))
    if isinstance(val, str):
        cleaned = val.strip()
        for fmt in ("hh:mm:ss", "hh:mm", "h:mm:ss", "h:mm"):
            qt = QTime.fromString(cleaned, fmt)
            if qt.isValid():
                return qt
    return None


def qtime_to_str(qt: Optional[QTime], include_seconds: bool = False) -> Optional[str]:
    """
    Convierte un QTime a una cadena en formato HH:MM o HH:MM:SS.
    Retorna None si el QTime es nulo o invalido.
    """
    if qt is not None and qt.isValid():
        return qt.toString("hh:mm:ss" if include_seconds else "hh:mm")
    return None


def create_time_picker(
    parent: Optional[QWidget] = None,
    initial_time: Any = None,
    allow_reset: bool = False,
    show_seconds: bool = False
) -> TimePicker:
    """
    Construye y configura una instancia de TimePicker:
    - Asegura la traduccion a español en las columnas.
    - Habilitacion opcional de boton de reinicio.
    - Carga inicial segura de hora.
    """
    ensure_spanish_translator()
    picker = TimePicker(parent, showSeconds=show_seconds)
    if allow_reset:
        picker.setResetEnabled(True)

    qt = to_qtime(initial_time)
    if qt is not None:
        picker.setTime(qt)

    return picker


# ==============================================================================
# SELECTOR DE FECHAS CON RESTRICCION A DIAS CON REGISTROS EN BASE DE DATOS
# ==============================================================================

class AvailableDaysDelegate(DayScrollItemDelegate):
    """
    Delegado de renderizado para las celdas de dias en CalendarView.
    - Destaca los dias que tienen registros en la base de datos con un punto de color de acento Fluent.
    - Atenua fuertemente (25% opacidad) los dias sin registros y desactiva su respuesta visual a interaccion.
    """
    def __init__(self, parent_view: Optional[QWidget] = None, available_dates: Optional[Iterable[str]] = None):
        super().__init__(0, 0)
        self.parent_view = parent_view
        self.available_dates: Set[str] = {str(d).strip()[:10] for d in (available_dates or []) if d}

    def setAvailableDates(self, dates: Iterable[str]) -> None:
        self.available_dates = {str(d).strip()[:10] for d in dates if d}

    def _isDateAvailable(self, index: QModelIndex) -> bool:
        if not self.available_dates:
            return True
        qd = index.data(Qt.ItemDataRole.UserRole)
        if isinstance(qd, QDate) and qd.isValid():
            return qd.toString("yyyy-MM-dd") in self.available_dates
        return False

    def _drawBackground(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        avail = self._isDateAvailable(index)
        if not avail:
            # Los dias sin registros no reciben iluminacion de seleccion ni hover
            return
        super()._drawBackground(painter, option, index)

        qd = index.data(Qt.ItemDataRole.UserRole)
        if (
            isinstance(qd, QDate)
            and qd.isValid()
            and qd.toString("yyyy-MM-dd") in self.available_dates
            and index != self.currentIndex
        ):
            painter.save()
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(themeColor())
            r = option.rect
            painter.drawEllipse(int(r.center().x() - 2), int(r.bottom() - 6), 4, 4)
            painter.restore()

    def _drawText(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        avail = self._isDateAvailable(index)
        painter.save()
        painter.setFont(self.font)

        if not avail:
            painter.setOpacity(0.25)
            painter.setPen(Qt.GlobalColor.white if isDarkTheme() else Qt.GlobalColor.black)
            text = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
            painter.drawText(option.rect, int(Qt.AlignmentFlag.AlignCenter), text)
            painter.restore()
            return

        super()._drawText(painter, option, index)
        painter.restore()


class RecordCalendarView(CalendarView):
    """
    Vista de calendario emergente que restringe la seleccion unicamente a dias con registros.
    """
    def __init__(self, parent: Optional[QWidget] = None, available_dates: Optional[Iterable[str]] = None):
        super().__init__(parent)
        self.available_dates: Set[str] = {str(d).strip()[:10] for d in (available_dates or []) if d}
        self.custom_delegate = AvailableDaysDelegate(self.dayView.scrollView, self.available_dates)
        self.dayView.scrollView.delegate = self.custom_delegate
        self.dayView.scrollView.setItemDelegate(self.custom_delegate)

    def _onDayItemClicked(self, date: QDate) -> None:
        d_str = date.toString("yyyy-MM-dd")
        if self.available_dates and d_str not in self.available_dates:
            # Bloquea la seleccion de dias sin registros en BD
            return
        super()._onDayItemClicked(date)


class RecordCalendarPicker(CalendarPicker):
    """
    Selector de fecha interactivo para busqueda y filtrado de registros.
    - Muestra 'Todas las fechas' (o texto configurable) cuando no hay fecha activa.
    - En el popup, unicamente las fechas existentes en base de datos son interactivas y seleccionables.
    - Soporta reinicio limpio con boton cancelar a 'Todas las fechas', emitiendo dateChanged(QDate()).
    - Al abrirse sin fecha previa, enfoca automaticamente el mes con registros mas recientes.
    """
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        available_dates: Optional[Iterable[str]] = None,
        placeholder_text: str = "Todas las fechas"
    ):
        ensure_spanish_translator()
        super().__init__(parent)
        self.setDateFormat(Qt.DateFormat.ISODate)
        self.setResetEnabled(True)
        self.placeholder_text = placeholder_text
        self.available_dates: Set[str] = {str(d).strip()[:10] for d in (available_dates or []) if d}
        self.setText(self.placeholder_text)

    def set_available_dates(self, dates: Iterable[str]) -> None:
        """Actualiza el conjunto de fechas habilitadas en el calendario."""
        self.available_dates = {str(d).strip()[:10] for d in dates if d}
        if not self.getDate().isValid():
            self.setText(self.placeholder_text)

    def reset(self) -> None:
        """Restablece el filtro a 'Todas las fechas' y emite la señal dateChanged."""
        super().reset()
        self.setText(self.placeholder_text)
        self.dateChanged.emit(QDate())

    def _showCalendarView(self) -> None:
        view = RecordCalendarView(self.window(), available_dates=self.available_dates)
        view.setResetEnabled(self.isRestEnabled())

        view.resetted.connect(self.reset)
        view.dateChanged.connect(self._onDateChanged)

        if self.date.isValid():
            view.setDate(self.date)
        elif self.available_dates:
            sorted_dates = sorted(self.available_dates)
            most_recent_qd = QDate.fromString(sorted_dates[-1], "yyyy-MM-dd")
            if most_recent_qd.isValid():
                view.setDate(most_recent_qd)

        x = int(self.width() / 2 - view.sizeHint().width() / 2)
        y = self.height()
        view.exec(self.mapToGlobal(QPoint(x, y)))
