"""Guardrails: check AI-written SQL before it runs."""
import duckdb

ALLOWED_TYPES = {duckdb.StatementType.SELECT}


def check_sql(sql):
    """Return (ok, reason). Only a single SELECT statement is allowed."""
    if not sql or not sql.strip():
        return False, "empty query"
    try:
        statements = duckdb.extract_statements(sql)
    except Exception as e:
        return False, f"could not parse SQL: {e}"
    if len(statements) != 1:
        return False, f"expected exactly 1 statement, got {len(statements)}"
    if statements[0].type not in ALLOWED_TYPES:
        return False, f"only SELECT is allowed, got {statements[0].type.name}"
    return True, "ok"


def safe_connection(db_path):
    """Read-only connection that cannot read or write any other file."""
    return duckdb.connect(db_path, read_only=True, config={"enable_external_access": False})
