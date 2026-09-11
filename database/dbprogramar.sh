#!/usr/bin/env bash
# ======================================================================
#   SISTEMA DE GESTION DEL METRO DE NUEVA YORK (MTA NYCT)
#   Paso 2: Compilacion de Logica PL/SQL en Oracle (Linux / macOS)
# ======================================================================

set -e

cd "$(dirname "$0")"
export NLS_LANG=AMERICAN_AMERICA.AL32UTF8

echo "======================================================================"
echo "   SISTEMA DE GESTION DEL METRO DE NUEVA YORK (MTA NYCT)"
echo "   Paso 2: Compilacion de Logica PL/SQL en Oracle"
echo "======================================================================"
echo ""

echo "Detectando servicio Pluggable Database (PDB) activo..."
PDB_NAME=$(sqlplus -S / as sysdba @get_pdb.sql 2>/dev/null | tr -d '[:space:]' || true)

if [ -z "$PDB_NAME" ]; then
    PDB_NAME="FREEPDB1"
fi

echo "Servicio detectado: $PDB_NAME"
echo ""

echo "[1/4] Compilando 9 Vistas analiticas y operativas..."
sqlplus -S METRO_NY/MetroPass123@localhost:1521/$PDB_NAME @02_plsql/05_vistas.sql

echo ""
echo "[2/4] Compilando 9 Funciones de negocio..."
sqlplus -S METRO_NY/MetroPass123@localhost:1521/$PDB_NAME @02_plsql/06_funciones.sql

echo ""
echo "[3/4] Compilando 6 Procedimientos almacenados transaccionales (SPs)..."
sqlplus -S METRO_NY/MetroPass123@localhost:1521/$PDB_NAME @02_plsql/07_procedimientos.sql

echo ""
echo "[4/4] Compilando 8 Triggers de integridad y auditoria..."
sqlplus -S METRO_NY/MetroPass123@localhost:1521/$PDB_NAME @02_plsql/08_triggers.sql

echo ""
echo "Verificando estado de compilacion en Oracle..."
sqlplus -S METRO_NY/MetroPass123@localhost:1521/$PDB_NAME <<EOF
SET PAGESIZE 50 LINESIZE 120
SELECT name, type, line, text FROM user_errors ORDER BY name, line;
EXIT;
EOF

echo ""
echo "======================================================================"
echo "   ¡LOGICA PL/SQL COMPILADA EXITOSAMENTE EN $PDB_NAME!"
echo "   - 9 Vistas creadas / reemplazadas (VW_*)"
echo "   - 9 Funciones de calculo compiladas (FN_*)"
echo "   - 6 Procedimientos almacenados listos (SP_*)"
echo "   - 8 Triggers activos en la base de datos (TRG_*)"
echo "======================================================================"

