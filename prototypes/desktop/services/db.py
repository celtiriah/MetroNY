"""
Core Database Access Layer for Oracle Database.
Handles automatic PDB fallback (FREEPDB1 / XEPDB1) and query execution.
"""
import os
import atexit
from typing import Optional
import oracledb
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, ORACLE_PDB, CANDIDATE_PDBS

ACTIVE_PDB = None
_DB_POOL: Optional[oracledb.ConnectionPool] = None


def get_pool() -> oracledb.ConnectionPool:
    """
    Returns an active oracledb ConnectionPool singleton, discovering the active PDB on first run.
    """
    global ACTIVE_PDB, _DB_POOL
    if _DB_POOL is not None:
        return _DB_POOL

    candidates = [ORACLE_PDB] if ORACLE_PDB else ([ACTIVE_PDB] if ACTIVE_PDB else CANDIDATE_PDBS)

    last_error = None
    for pdb in candidates:
        if not pdb:
            continue
        try:
            dsn = f"{DB_HOST}:{DB_PORT}/{pdb}"
            pool = oracledb.create_pool(
                user=DB_USER,
                password=DB_PASSWORD,
                dsn=dsn,
                min=1,
                max=10,
                increment=1
            )
            ACTIVE_PDB = pdb
            _DB_POOL = pool
            return _DB_POOL
        except Exception as e:
            last_error = e

    for pdb in CANDIDATE_PDBS:
        if pdb in candidates:
            continue
        try:
            dsn = f"{DB_HOST}:{DB_PORT}/{pdb}"
            pool = oracledb.create_pool(
                user=DB_USER,
                password=DB_PASSWORD,
                dsn=dsn,
                min=1,
                max=10,
                increment=1
            )
            ACTIVE_PDB = pdb
            _DB_POOL = pool
            return _DB_POOL
        except Exception as e:
            last_error = e

    raise RuntimeError(
        f"Could not connect to Oracle at {DB_HOST}:{DB_PORT}. "
        f"Attempted PDBs: {CANDIDATE_PDBS}. Error: {last_error}"
    )


def close_pool():
    """
    Gracefully closes all pooled connections.
    """
    global _DB_POOL
    if _DB_POOL is not None:
        try:
            _DB_POOL.close()
        except Exception:
            pass
        _DB_POOL = None


atexit.register(close_pool)


def get_connection():
    """
    Returns an active oracledb connection from the connection pool.
    Calling conn.close() on the returned connection safely releases it back to the pool.
    """
    pool = get_pool()
    return pool.acquire()


def execute_query(sql: str, params: Optional[dict] = None) -> dict:
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


def execute_dml(sql: str, params: Optional[dict] = None) -> dict:
    """
    Executes an INSERT, UPDATE, or DELETE statement and commits the transaction.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or {})
        conn.commit()
        return {"success": True, "rowcount": cursor.rowcount}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

