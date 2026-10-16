#!/bin/bash
export NLS_LANG=AMERICAN_AMERICA.AL32UTF8
cd "$(dirname "$0")"

echo "======================================================================"
echo "   SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]"
echo "   Insercion Masiva: Catalogo MTA + Simulacion Anual de Operaciones"
echo "======================================================================"
echo ""

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

echo "Servicio Oracle PDB detectado: $PDB_NAME"
echo "Esquema de Base de Datos: METRO_NY"
echo ""
echo "Ejecutando todas las inserciones del sistema en orden..."
echo "[Fase 1] Catalogo Masivo MTA (Lineas, Estaciones, Trenes, Empleados)"
echo "[Fase 2] Simulacion Operativa Anual (~5,300 registros operativos)"
echo ""

sqlplus -S METRO_NY/MetroPass123@localhost:1521/$PDB_NAME <<EOF
@realizar_todas_las_inserciones.sql
exit
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Ocurrio un fallo durante la ejecucion de las inserciones."
    exit 1
fi

echo ""
echo "======================================================================"
echo "[EXITO] Todas las inserciones fueron ejecutadas correctamente en $PDB_NAME!"
echo "======================================================================"

