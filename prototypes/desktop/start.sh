#!/usr/bin/env bash
# ======================================================================
#   SISTEMA DE GESTION DEL METRO DE NUEVA YORK (MTA NYCT)
#   Iniciador de la Aplicacion de Escritorio PyQt5 (Linux / macOS)
# ======================================================================

set -e
cd "$(dirname "$0")"

echo "======================================================================"
echo "   SISTEMA DE GESTION DEL METRO DE NUEVA YORK (MTA NYCT)"
echo "   Iniciando Aplicacion de Escritorio Nativa (PyQt5)..."
echo "======================================================================"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 no fue encontrado. Por favor instalalo."
    exit 1
fi

echo "[1/2] Verificando dependencias..."
python3 -c "import PyQt5, oracledb" 2>/dev/null || {
    echo "Instalando dependencias desde requirements.txt..."
    python3 -m pip install -r requirements.txt
}

echo "[2/2] Abriendo aplicacion PyQt5..."
python3 app.py

