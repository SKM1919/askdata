"""Tests for the MCP server tools (no AI calls). Run with: uv run pytest -q"""
import sys

sys.path.insert(0, "src")
from mcp_server import describe_metric, list_metrics, run_query  # noqa: E402


def test_list_metrics_returns_all_13():
    assert len(list_metrics()) == 13


def test_describe_metric_by_synonym():
    assert describe_metric("average order value")["name"] == "aov"


def test_describe_unknown_metric():
    assert "error" in describe_metric("happiness index")


def test_run_query_works():
    assert run_query("SELECT COUNT(*) AS n FROM orders")["rows"][0]["n"] == 99441


def test_run_query_blocks_delete():
    assert "BLOCKED" in run_query("DELETE FROM orders")["error"]


def test_run_query_limits_rows():
    r = run_query("SELECT * FROM orders")
    assert r["row_count"] == 99441 and len(r["rows"]) == 100
    