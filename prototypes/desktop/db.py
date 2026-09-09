"""
Backwards-compatibility bridge for db.py.
Re-exports database connection helpers, settings, and query catalogues from services/.
"""
from services.db import (
    get_connection, execute_query, ACTIVE_PDB,
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, CANDIDATE_PDBS
)
from services.queries_catalog import CONSULTAS_CATALOGO

__all__ = [
    "get_connection", "execute_query", "ACTIVE_PDB",
    "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT",
    "CANDIDATE_PDBS", "CONSULTAS_CATALOGO"
]
