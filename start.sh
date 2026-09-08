#!/usr/bin/env bash
# ======================================================================
#   SISTEMA DE GESTION DEL METRO DE NUEVA YORK (MTA NYCT)
#   Iniciador del Servidor Web y Mini-Backend Python (Linux / macOS)
# ======================================================================

set -e

echo "======================================================================"
echo "   SISTEMA DE GESTION DEL METRO DE NUEVA YORK (MTA NYCT)"
echo "   Iniciando Servidor Web y Mini-Backend Python..."
echo "======================================================================"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 no fue encontrado. Por favor instalalo."
    exit 1
fi

echo "[1/2] Verificando dependencias de Python..."
python3 -c "import flask, oracledb" 2>/dev/null || {
    echo "Instalando dependencias desde backend/requirements.txt..."
    python3 -m pip install -r backend/requirements.txt
}

echo "[2/2] Abriendo http://localhost:5000..."
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5000 &
elif command -v open &> /dev/null; then
    open http://localhost:5000 &
fi

echo ""
echo "======================================================================"
echo " Servidor activo. Presiona Ctrl + C para detenerlo."
echo "======================================================================"
echo ""
python3 backend/app.py
