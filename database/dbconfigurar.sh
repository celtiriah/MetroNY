#!/usr/bin/env bash
# ======================================================================
#   SISTEMA DE GESTION DEL METRO DE NUEVA YORK (MTA NYCT)
#   Paso 1: Configuracion Inicial y Creacion de Tablas (Linux / macOS)
# ======================================================================

set -e

cd "$(dirname "$0")"
export NLS_LANG=AMERICAN_AMERICA.AL32UTF8

echo "======================================================================"
echo "   SISTEMA DE GESTION DEL METRO DE NUEVA YORK (MTA NYCT)"
echo "   Paso 1: Configuracion Inicial y Creacion de Tablas"
echo "======================================================================"
echo ""

echo "Detectando servicio Pluggable Database (PDB) activo..."
PDB_NAME=$(sqlplus -S / as sysdba @get_pdb.sql 2>/dev/null | tr -d '[:space:]' || true)

if [ -z "$PDB_NAME" ]; then
    PDB_NAME="FREEPDB1"
fi

echo "Servicio detectado: $PDB_NAME"
echo ""

echo "[1/4] Configurando tablespaces y usuario METRO_NY..."
sqlplus -S / as sysdba @01_setup/01_configuracion_usuario.ddl

echo ""
echo "[2/4] Creando 33 tablas normalizadas (3NF), claves foraneas y secuencias..."
sqlplus -S METRO_NY/MetroPass123@localhost:1521/$PDB_NAME @01_setup/02_ddl_tablas.ddl

echo ""
echo "[3/4] Insertando 208 registros de datos de prueba..."
sqlplus -S METRO_NY/MetroPass123@localhost:1521/$PDB_NAME @01_setup/03_datos_prueba.ddl

echo ""
echo "[4/4] Construyendo 63 indices B-Tree en TS_METRO_IDX..."
sqlplus -S METRO_NY/MetroPass123@localhost:1521/$PDB_NAME @01_setup/04_indices.ddl

echo ""
echo "======================================================================"
echo "   ¡CONFIGURACION INICIAL COMPLETADA EN $PDB_NAME!"
echo "   - 33 Tablas creadas en TS_METRO_DATA"
echo "   - 208 Registros iniciales cargados"
echo "   - 63 Indices B-Tree creados en TS_METRO_IDX"
echo ""
echo "   SIGUIENTE PASO:"
echo "   Ejecuta './dbprogramar.sh' para compilar la logica PL/SQL"
echo "   (Vistas, Funciones, Procedimientos y Triggers)."
echo "======================================================================"

