"""
Global Configuration for the MetroNY Desktop Application.
Manages database environment parameters, UI dimensions, and styling constants.
"""
import os

# --- Oracle Database Configuration ---
DB_USER = os.getenv("ORACLE_USER", "METRO_NY")
DB_PASSWORD = os.getenv("ORACLE_PASSWORD", "MetroPass123")
DB_HOST = os.getenv("ORACLE_HOST", "localhost")
DB_PORT = int(os.getenv("ORACLE_PORT", "1521"))
ORACLE_PDB = os.getenv("ORACLE_PDB")

CANDIDATE_PDBS = ["FREEPDB1", "XEPDB1", "ORCLPDB"]

# --- Application UI Configuration ---
APP_TITLE = "MTA New York City Subway - Sistema de Gestión"
APP_SUBTITLE = "Panel Operativo de Control y Consulta (Oracle Database)"
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 780
MIN_WIDTH = 980
MIN_HEIGHT = 650

# --- Brand & Theme Colors ---
MTA_BLUE = "#0039A6"
MTA_YELLOW = "#FCCC0A"
MTA_ORANGE = "#FF6319"
MTA_GREEN = "#00933C"
MTA_RED = "#EE352E"

