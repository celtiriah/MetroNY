"""
Reusable Status Badge and Line Color Chip components for the MetroNY UI.
Matches Windows 11 Fluent Design System aesthetics in both Light and Dark modes.
"""
from typing import Dict, Tuple
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt
from qfluentwidgets import isDarkTheme, qconfig


class StatusBadge(QWidget):
    """
    Renders a soft pill-shaped badge with semantic colors.
    Can be placed inside QTableWidget cells via setCellWidget().
    Automatically adapts to Light and Dark themes in real time.
    """
    SEMANTIC_COLORS_LIGHT: Dict[str, Tuple[str, str, str]] = {
        # Positivo / Operativo
        "activa": ("#E8F5E9", "#1B5E20", "#A5D6A7"),
        "operativa": ("#E8F5E9", "#1B5E20", "#A5D6A7"),
        "vigente": ("#E8F5E9", "#1B5E20", "#A5D6A7"),
        "disponible": ("#E8F5E9", "#1B5E20", "#A5D6A7"),
        "completada": ("#E8F5E9", "#1B5E20", "#A5D6A7"),
        "concluida": ("#E8F5E9", "#1B5E20", "#A5D6A7"),
        "cerrado": ("#E8F5E9", "#1B5E20", "#A5D6A7"),
        "sí": ("#E8F5E9", "#1B5E20", "#A5D6A7"),
        "si": ("#E8F5E9", "#1B5E20", "#A5D6A7"),

        # Advertencia / Transitorio
        "en mantenimiento": ("#FFF3E0", "#E65100", "#FFE0B2"),
        "en atencion": ("#FFF3E0", "#E65100", "#FFE0B2"),
        "en atención": ("#FFF3E0", "#E65100", "#FFE0B2"),
        "suspendida": ("#FFF3E0", "#E65100", "#FFE0B2"),
        "en taller": ("#FFF3E0", "#E65100", "#FFE0B2"),
        "retrasado": ("#FFF3E0", "#E65100", "#FFE0B2"),
        "reprogramado": ("#FFF8E1", "#F57F17", "#FFE082"),
        "medio": ("#FFF3E0", "#E65100", "#FFE0B2"),
        "bajo": ("#F1F8E9", "#33691E", "#DCEDC8"),

        # Peligro / Critico
        "fuera de servicio": ("#FFEBEE", "#C62828", "#FFCDD2"),
        "cerrada": ("#FFEBEE", "#C62828", "#FFCDD2"),
        "cancelado": ("#FFEBEE", "#C62828", "#FFCDD2"),
        "critico": ("#FFEBEE", "#C62828", "#FFCDD2"),
        "crítico": ("#FFEBEE", "#C62828", "#FFCDD2"),
        "alto": ("#FFEBEE", "#C62828", "#FFCDD2"),
        "vencida": ("#FFEBEE", "#C62828", "#FFCDD2"),
        "usado": ("#FFEBEE", "#C62828", "#FFCDD2"),
        "no": ("#F5F5F5", "#616161", "#E0E0E0"),

        # Informativo
        "programado": ("#E3F2FD", "#0D47A1", "#BBDEFB"),
        "en abordaje": ("#E1F5FE", "#01579B", "#B3E5FC"),
        "en curso": ("#E8EAF6", "#1A237E", "#C5CAE9"),
        "local": ("#EDE7F6", "#4A148C", "#D1C4E9"),
        "expreso": ("#F3E5F5", "#6A1B9A", "#E1BEE7"),
        "peatonal subterránea": ("#E0F2F1", "#004D40", "#B2DFDB"),
        "peatonal subterranea": ("#E0F2F1", "#004D40", "#B2DFDB"),
    }

    SEMANTIC_COLORS_DARK: Dict[str, Tuple[str, str, str]] = {
        # Positivo / Operativo
        "activa": ("rgba(46, 125, 50, 0.28)", "#81C784", "rgba(129, 199, 132, 0.45)"),
        "operativa": ("rgba(46, 125, 50, 0.28)", "#81C784", "rgba(129, 199, 132, 0.45)"),
        "vigente": ("rgba(46, 125, 50, 0.28)", "#81C784", "rgba(129, 199, 132, 0.45)"),
        "disponible": ("rgba(46, 125, 50, 0.28)", "#81C784", "rgba(129, 199, 132, 0.45)"),
        "completada": ("rgba(46, 125, 50, 0.28)", "#81C784", "rgba(129, 199, 132, 0.45)"),
        "concluida": ("rgba(46, 125, 50, 0.28)", "#81C784", "rgba(129, 199, 132, 0.45)"),
        "cerrado": ("rgba(46, 125, 50, 0.28)", "#81C784", "rgba(129, 199, 132, 0.45)"),
        "sí": ("rgba(46, 125, 50, 0.28)", "#81C784", "rgba(129, 199, 132, 0.45)"),
        "si": ("rgba(46, 125, 50, 0.28)", "#81C784", "rgba(129, 199, 132, 0.45)"),

        # Advertencia / Transitorio
        "en mantenimiento": ("rgba(230, 81, 0, 0.28)", "#FFB74D", "rgba(255, 183, 77, 0.45)"),
        "en atencion": ("rgba(230, 81, 0, 0.28)", "#FFB74D", "rgba(255, 183, 77, 0.45)"),
        "en atención": ("rgba(230, 81, 0, 0.28)", "#FFB74D", "rgba(255, 183, 77, 0.45)"),
        "suspendida": ("rgba(230, 81, 0, 0.28)", "#FFB74D", "rgba(255, 183, 77, 0.45)"),
        "en taller": ("rgba(230, 81, 0, 0.28)", "#FFB74D", "rgba(255, 183, 77, 0.45)"),
        "retrasado": ("rgba(230, 81, 0, 0.28)", "#FFB74D", "rgba(255, 183, 77, 0.45)"),
        "reprogramado": ("rgba(245, 127, 23, 0.28)", "#FFD54F", "rgba(255, 213, 79, 0.45)"),
        "medio": ("rgba(230, 81, 0, 0.28)", "#FFB74D", "rgba(255, 183, 77, 0.45)"),
        "bajo": ("rgba(85, 139, 47, 0.28)", "#AED581", "rgba(174, 213, 129, 0.45)"),

        # Peligro / Critico
        "fuera de servicio": ("rgba(198, 40, 40, 0.28)", "#E57373", "rgba(229, 115, 115, 0.45)"),
        "cerrada": ("rgba(198, 40, 40, 0.28)", "#E57373", "rgba(229, 115, 115, 0.45)"),
        "cancelado": ("rgba(198, 40, 40, 0.28)", "#E57373", "rgba(229, 115, 115, 0.45)"),
        "critico": ("rgba(198, 40, 40, 0.28)", "#E57373", "rgba(229, 115, 115, 0.45)"),
        "crítico": ("rgba(198, 40, 40, 0.28)", "#E57373", "rgba(229, 115, 115, 0.45)"),
        "alto": ("rgba(198, 40, 40, 0.28)", "#E57373", "rgba(229, 115, 115, 0.45)"),
        "vencida": ("rgba(198, 40, 40, 0.28)", "#E57373", "rgba(229, 115, 115, 0.45)"),
        "usado": ("rgba(198, 40, 40, 0.28)", "#E57373", "rgba(229, 115, 115, 0.45)"),
        "no": ("rgba(255, 255, 255, 0.08)", "#B0BEC5", "rgba(255, 255, 255, 0.15)"),

        # Informativo
        "programado": ("rgba(21, 101, 192, 0.28)", "#64B5F6", "rgba(100, 181, 246, 0.45)"),
        "en abordaje": ("rgba(2, 119, 189, 0.28)", "#4FC3F7", "rgba(79, 195, 247, 0.45)"),
        "en curso": ("rgba(40, 53, 147, 0.28)", "#7986CB", "rgba(121, 134, 203, 0.45)"),
        "local": ("rgba(106, 27, 154, 0.28)", "#BA68C8", "rgba(186, 104, 200, 0.45)"),
        "expreso": ("rgba(123, 31, 162, 0.28)", "#CE93D8", "rgba(206, 147, 216, 0.45)"),
        "peatonal subterránea": ("rgba(0, 105, 92, 0.28)", "#4DB6AC", "rgba(77, 182, 172, 0.45)"),
        "peatonal subterranea": ("rgba(0, 105, 92, 0.28)", "#4DB6AC", "rgba(77, 182, 172, 0.45)"),
    }

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.text_content = text
        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label = QLabel(text, self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.update_style()
        qconfig.themeChanged.connect(self.update_style)

    def update_style(self):
        dark = isDarkTheme()
        palette = self.SEMANTIC_COLORS_DARK if dark else self.SEMANTIC_COLORS_LIGHT
        default_fallback = (
            ("rgba(255, 255, 255, 0.08)", "#CFD8DC", "rgba(255, 255, 255, 0.15)")
            if dark else ("#F5F5F5", "#424242", "#E0E0E0")
        )
        key = self.text_content.strip().lower()
        if key in palette:
            bg, fg, border = palette[key]
        else:
            if any(k in key for k in ("activ", "operat", "vigente", "complet", "exito", "disponib", "sí", "si", "regular", "abierta", "al día", "estándar", "estandar", "base")):
                bg, fg, border = palette["activa"]
            elif any(k in key for k in ("manten", "atenc", "suspend", "taller", "pendient", "medio", "media", "parcial", "reparac", "estudiante", "adulto mayor", "reducid", "escolar")):
                bg, fg, border = palette["en mantenimiento"]
            elif any(k in key for k in ("fuera", "cerrad", "cancel", "critic", "crític", "alto", "alta", "vencid", "bloque", "ausent", "rechaz", "total", "no")):
                bg, fg, border = palette["fuera de servicio"]
            elif any(k in key for k in ("program", "abordaj", "curso", "local", "expres", "preventiv", "correctiv", "inspecc", "discapacidad")):
                bg, fg, border = palette["programado"]
            else:
                bg, fg, border = default_fallback

        self.label.setStyleSheet(
            f"background-color: {bg}; "
            f"color: {fg}; "
            f"border: 1px solid {border}; "
            f"border-radius: 10px; "
            f"padding: 2px 10px; "
            f"font-size: 11px; "
            f"font-weight: 600;"
        )


def resolve_mta_color(color_str: str, default_hex: str = "#0039A6") -> str:
    """
    Normalizes any color representation (hex code, Spanish/English color name, or line code)
    to a guaranteed-valid CSS hex color string (#RRGGBB).
    Prevents Qt CSS stylesheet parser errors when encountering non-ASCII or non-W3C color names.
    """
    if not color_str:
        return default_hex

    c = str(color_str).strip()

    # If already a valid hex color (#RGB or #RRGGBB or #RRGGBBAA)
    if c.startswith("#") and len(c) in (4, 7, 9) and all(ch in "0123456789abcdefABCDEF#" for ch in c):
        return c

    # Canonical color map (Spanish and English) to official MTA subway palette
    mta_color_map: Dict[str, str] = {
        "rojo": "#EE352E",
        "red": "#EE352E",
        "azul": "#0039A6",
        "blue": "#0039A6",
        "verde": "#00933C",
        "green": "#00933C",
        "purpura": "#B933AD",
        "púrpura": "#B933AD",
        "morado": "#B933AD",
        "purple": "#B933AD",
        "violeta": "#B933AD",
        "naranja": "#FF6319",
        "orange": "#FF6319",
        "amarillo": "#FCCC0A",
        "yellow": "#FCCC0A",
        "gris": "#A7A9AC",
        "gray": "#A7A9AC",
        "grey": "#A7A9AC",
        "marron": "#996633",
        "marrón": "#996633",
        "cafe": "#996633",
        "café": "#996633",
        "brown": "#996633",
        "lima": "#6CBE45",
        "lime": "#6CBE45",
        "turquesa": "#00A3E0",
        "cian": "#00A3E0",
        "cyan": "#00A3E0",
        "negro": "#121212",
        "black": "#121212",
        "blanco": "#FFFFFF",
        "white": "#FFFFFF",
    }

    clean = c.lower()
    if clean in mta_color_map:
        return mta_color_map[clean]

    clean_no_accents = (
        clean.replace("ú", "u")
             .replace("ó", "o")
             .replace("í", "i")
             .replace("é", "e")
             .replace("á", "a")
    )
    if clean_no_accents in mta_color_map:
        return mta_color_map[clean_no_accents]

    # Map by line code if the string is a line identifier
    mta_line_code_map: Dict[str, str] = {
        "1": "#EE352E", "2": "#EE352E", "3": "#EE352E",
        "4": "#00933C", "5": "#00933C", "6": "#00933C",
        "7": "#B933AD",
        "A": "#0039A6", "C": "#0039A6", "E": "#0039A6",
        "B": "#FF6319", "D": "#FF6319", "F": "#FF6319", "M": "#FF6319",
        "G": "#6CBE45",
        "J": "#996633", "Z": "#996633",
        "L": "#A7A9AC",
        "N": "#FCCC0A", "Q": "#FCCC0A", "R": "#FCCC0A", "W": "#FCCC0A",
        "S": "#808183", "SIR": "#0039A6",
    }
    if c.upper() in mta_line_code_map:
        return mta_line_code_map[c.upper()]

    return default_hex


class LineColorChip(QWidget):
    """
    Renders an MTA line color badge with an official circular dot and code label.
    Supports real-time dynamic switching between Light and Dark themes.
    """
    def __init__(self, codigo: str, hex_color: str = "#0039A6", nombre: str = "", parent=None):
        super().__init__(parent)
        self.codigo = str(codigo)
        self.raw_color = hex_color or "#0039A6"
        self.hex_color = resolve_mta_color(self.raw_color, default_hex="#0039A6")
        self.nombre = str(nombre)
        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Dot
        self.dot = QLabel(self)
        self.dot.setFixedSize(14, 14)
        layout.addWidget(self.dot)

        # Text
        display_text = (
            f"{self.codigo} - {self.nombre}"
            if (self.nombre and self.nombre not in (self.raw_color, self.hex_color))
            else self.codigo
        )
        self.text_label = QLabel(display_text, self)
        layout.addWidget(self.text_label)

        self.update_style()
        qconfig.themeChanged.connect(self.update_style)

    def update_style(self):
        dark = isDarkTheme()
        text_color = "#f8fafc" if dark else "#0f172a"
        border_col = "rgba(255, 255, 255, 0.35)" if dark else "rgba(0, 0, 0, 0.20)"

        self.dot.setStyleSheet(
            f"background-color: {self.hex_color}; "
            f"border-radius: 7px; "
            f"border: 1px solid {border_col};"
        )
        self.text_label.setStyleSheet(
            f"font-weight: 600; font-size: 12px; color: {text_color}; background: transparent;"
        )
