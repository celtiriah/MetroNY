"""
Core Database Access Layer for Oracle Database.
Handles automatic PDB fallback (FREEPDB1 / XEPDB1) and query execution.
"""
import os
import oracledb
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, ORACLE_PDB, CANDIDATE_PDBS

ACTIVE_PDB = None


def get_connection():
    """
    Returns an active oracledb connection, resolving Pluggable Database automatically.
    """
    global ACTIVE_PDB

    candidates = [ORACLE_PDB] if ORACLE_PDB else ([ACTIVE_PDB] if ACTIVE_PDB else CANDIDATE_PDBS)

    last_error = None
    for pdb in candidates:
        if not pdb:
            continue
        try:
            dsn = f"{DB_HOST}:{DB_PORT}/{pdb}"
            conn = oracledb.connect(
                user=DB_USER,
                password=DB_PASSWORD,
                dsn=dsn
            )
            ACTIVE_PDB = pdb
            return conn
        except Exception as e:
            last_error = e

    for pdb in CANDIDATE_PDBS:
        if pdb in candidates:
            continue
        try:
            dsn = f"{DB_HOST}:{DB_PORT}/{pdb}"
            conn = oracledb.connect(
                user=DB_USER,
                password=DB_PASSWORD,
                dsn=dsn
            )
            ACTIVE_PDB = pdb
            return conn
        except Exception as e:
            last_error = e

    raise RuntimeError(
        f"Could not connect to Oracle at {DB_HOST}:{DB_PORT}. "
        f"Attempted PDBs: {CANDIDATE_PDBS}. Error: {last_error}"
    )


def execute_query(sql: str, params: dict = None) -> dict:
    """
    Executes a SQL query against Oracle and returns column headers and rows.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or {})
        columns = [col[0] for col in cursor.description] if cursor.description else []
        rows = []
        if cursor.description:
            for row in cursor.fetchall():
                row_dict = {}
                for col_name, val in zip(columns, row):
                    if val is None:
                        row_dict[col_name] = "-"
                    elif hasattr(val, "strftime"):
                        if hasattr(val, "hour") and val.hour != 0:
                            row_dict[col_name] = val.strftime("%Y-%m-%d %H:%M")
                        else:
                            row_dict[col_name] = val.strftime("%Y-%m-%d")
                    elif isinstance(val, (int, float)):
                        row_dict[col_name] = str(val)
                    else:
                        row_dict[col_name] = str(val)
                rows.append(row_dict)
        return {"columns": columns, "rows": rows, "total": len(rows), "pdb": ACTIVE_PDB}
    finally:
        cursor.close()
        conn.close()

