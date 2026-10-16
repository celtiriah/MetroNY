#!/bin/bash
export NLS_LANG=AMERICAN_AMERICA.AL32UTF8
cd "$(dirname "$0")"

PDB_NAME=""
if [ -f "../get_pdb.sql" ]; then
    PDB_NAME=$(sqlplus -S / as sysdba @../get_pdb.sql 2>/dev/null | tr -d '\r\n ')
fi
if [ -z "$PDB_NAME" ] && [ -f "get_pdb.sql" ]; then
    PDB_NAME=$(sqlplus -S / as sysdba @get_pdb.sql 2>/dev/null | tr -d '\r\n ')
fi
if [ -z "$PDB_NAME" ]; then
    PDB_NAME="FREEPDB1"
fi

echo "Servicio Oracle PDB: $PDB_NAME"
echo "Ejecutando Fase 1: Catalogo MTA..."

sqlplus -S METRO_NY/MetroPass123@localhost:1521/$PDB_NAME <<EOF
@fase1_catalogo_mta/01_mta_catalogo_enriquecido.sql
exit
EOF

