"""Attack tests for the SQL guardrails. Run with: uv run pytest -q"""
import sys

import pytest

sys.path.insert(0, "src")
from guardrails import check_sql, safe_connection  # noqa: E402

ALLOWED = [
    "SELECT 1",
    "SELECT COUNT(*) FROM orders",
    "WITH x AS (SELECT 1 AS n) SELECT n FROM x",
]

BLOCKED = [
    "",
    "DELETE FROM orders",
    "DROP TABLE orders",
    "UPDATE orders SET order_status = 'x'",
    "INSERT INTO sellers VALUES ('a', 1, 'b', 'c')",
    "SELECT 1; DROP TABLE orders",
    "COPY orders TO 'stolen.csv'",
    "ATTACH 'other.db'",
    "SET enable_external_access = true",
]


@pytest.mark.parametrize("sql", ALLOWED)
def test_allows_select(sql):
    ok, _ = check_sql(sql)
    assert ok


@pytest.mark.parametrize("sql", BLOCKED)
def test_blocks_everything_else(sql):
    ok, _ = check_sql(sql)
    assert not ok


def test_cannot_read_files_even_with_select():
    con = safe_connection("data/olist.duckdb")
    with pytest.raises(Exception):
        con.execute("SELECT * FROM read_csv('data/olist_orders_dataset.csv')").fetchall()


def test_normal_queries_still_work():
    con = safe_connection("data/olist.duckdb")
    assert con.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 99441
