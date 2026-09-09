"""
Qt Style Sheets (QSS) for the MetroNY PyQt5 Desktop Application.
Supports Light Theme (Default) and Dark Theme with instant switching.
"""

LIGHT_THEME_QSS = """
QMainWindow, QWidget {
    background-color: #f8fafc;
    color: #0f172a;
    font-family: 'Segoe UI', -apple-system, sans-serif;
    font-size: 13px;
}

/* Header & ToolBar */
QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 8px 16px;
    spacing: 12px;
}

QToolBar QLabel {
    color: #0f172a;
    font-size: 15px;
    font-weight: 700;
}

/* TabWidget */
QTabWidget::pane {
    border: 1px solid #e2e8f0;
    background-color: #ffffff;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #f1f5f9;
    color: #64748b;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #0039A6;
    border-bottom: 2px solid #0039A6;
}

QTabBar::tab:hover:!selected {
    background-color: #e2e8f0;
    color: #0f172a;
}

/* GroupBoxes & Cards */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 24px;
    padding: 16px;
    font-weight: 700;
    color: #0f172a;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
}

/* Tables */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    gridline-color: #f1f5f9;
    selection-background-color: #e0f2fe;
    selection-color: #0369a1;
    alternate-background-color: #f8fafc;
}

QHeaderView::section {
    background-color: #f1f5f9;
    color: #475569;
    padding: 8px 12px;
    border: none;
    border-right: 1px solid #e2e8f0;
    border-bottom: 2px solid #cbd5e1;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
}

/* Buttons */
QPushButton {
    background-color: #0039A6;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #002b80;
}

QPushButton:pressed {
    background-color: #001f5c;
}

QPushButton#themeToggleBtn {
    background-color: #f1f5f9;
    color: #0f172a;
    border: 1px solid #cbd5e1;
}

QPushButton#themeToggleBtn:hover {
    background-color: #e2e8f0;
}

/* Inputs & ComboBox */
QLineEdit, QComboBox, QPlainTextEdit {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 12px;
    color: #0f172a;
}

QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {
    border: 1px solid #0039A6;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

/* ScrollBar */
QScrollBar:vertical {
    border: none;
    background: #f1f5f9;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}
"""

DARK_THEME_QSS = """
QMainWindow, QWidget {
    background-color: #0b0f19;
    color: #f1f5f9;
    font-family: 'Segoe UI', -apple-system, sans-serif;
    font-size: 13px;
}

/* Header & ToolBar */
QToolBar {
    background-color: #131b2e;
    border-bottom: 1px solid #273553;
    padding: 8px 16px;
    spacing: 12px;
}

QToolBar QLabel {
    color: #ffffff;
    font-size: 15px;
    font-weight: 700;
}

/* TabWidget */
QTabWidget::pane {
    border: 1px solid #273553;
    background-color: #131b2e;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #0b0f19;
    color: #94a3b8;
    border: 1px solid #273553;
    border-bottom: none;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: #131b2e;
    color: #60a5fa;
    border-bottom: 2px solid #3b82f6;
}

QTabBar::tab:hover:!selected {
    background-color: #1e293b;
    color: #f1f5f9;
}

/* GroupBoxes & Cards */
QGroupBox {
    background-color: #131b2e;
    border: 1px solid #273553;
    border-radius: 8px;
    margin-top: 24px;
    padding: 16px;
    font-weight: 700;
    color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
}

/* Tables */
QTableWidget {
    background-color: #131b2e;
    border: 1px solid #273553;
    border-radius: 6px;
    gridline-color: #1e293b;
    selection-background-color: #1e3a8a;
    selection-color: #93c5fd;
    alternate-background-color: #17223b;
}

QHeaderView::section {
    background-color: #0b0f19;
    color: #cbd5e1;
    padding: 8px 12px;
    border: none;
    border-right: 1px solid #273553;
    border-bottom: 2px solid #334155;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
}

/* Buttons */
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #1d4ed8;
}

QPushButton:pressed {
    background-color: #1e40af;
}

QPushButton#themeToggleBtn {
    background-color: #1e293b;
    color: #f1f5f9;
    border: 1px solid #334155;
}

QPushButton#themeToggleBtn:hover {
    background-color: #334155;
}

/* Inputs & ComboBox */
QLineEdit, QComboBox, QPlainTextEdit {
    background-color: #0b0f19;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 12px;
    color: #f1f5f9;
}

QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {
    border: 1px solid #3b82f6;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

/* ScrollBar */
QScrollBar:vertical {
    border: none;
    background: #0b0f19;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}
"""

