#!/usr/bin/env bash
# ======================================================================
#   SISTEMA DE GESTION DEL METRO DE NUEVA YORK (MTA NYCT)
#   Instalador Automatizado de Base de Datos Oracle (Linux / macOS / WSL)
# ======================================================================

set -e

export NLS_LANG=FRENCH_FRANCE.AL32UTF8

echo "======================================================================"
echo "   SISTEMA DE GESTION DEL METRO DE NUEVA YORK (MTA NYCT)"
echo "   Instalador Automatizado de Base de Datos Oracle (Linux / macOS)"
echo "======================================================================"
echo ""

# 1. Detectar PDB activo (FREEPDB1, XEPDB1, etc.)
echo "Detectando servicio Pluggable Database (PDB) activo..."
PDB_NAME=$(sqlplus -S / as sysdba @database/get_pdb.sql 2>/dev/null | tr -d '[:space:]' || true)

if [ -z "$PDB_NAME" ]; then
    PDB_NAME="FREEPDB1"
fi

echo "Servicio detectado: $PDB_NAME"
echo ""

echo "[1/4] Configurando tablespaces y usuario METRO_NY..."
sqlplus -S / as sysdba @database/01_configuracion_usuario.ddl

echo ""
echo "[2/4] Creando 33 tablas normalizadas (3FN), claves foraneas y secuencias..."
sqlplus -S METRO_NY/MetroPass123@localhost:1521/$PDB_NAME @database/02_ddl_tablas.ddl

echo ""
echo "[3/4] Insertando 208 registros de datos de prueba reales..."
sqlplus -S METRO_NY/MetroPass123@localhost:1521/$PDB_NAME @database/03_datos_prueba.ddl

echo ""
echo "[4/4] Construyendo 63 indices B-Tree en TS_METRO_IDX..."
sqlplus -S METRO_NY/MetroPass123@localhost:1521/$PDB_NAME @database/04_indices.ddl

echo ""
echo "======================================================================"
echo "   ¡INSTALACION COMPLETADA CON EXITO EN $PDB_NAME!"
echo "   - 33 Tablas creadas en TS_METRO_DATA"
echo "   - 208 Registros iniciales listos"
echo "   - 63 Indices B-Tree optimizados en TS_METRO_IDX"
echo ""
echo "   Para probar las 15 consultas del proyecto ejecuta:"
echo "   sqlplus METRO_NY/MetroPass123@localhost:1521/$PDB_NAME @database/consultas_minimas.ddl"
echo "======================================================================"
