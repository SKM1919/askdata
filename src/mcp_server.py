"""AskData MCP server: lets AI assistants (Claude, Cursor) use AskData as a tool.
Normally started by the assistant itself, not by hand.
"""
import json

import yaml
from mcp.server.mcpserver import MCPServer

from agent import DB_PATH, SEMANTIC_PATH
from agent import ask as agent_ask
from guardrails import check_sql, safe_connection

MAX_ROWS = 100  # never send huge results back to the assistant
mcp = MCPServer("askdata")


def _rows(df):
    """Convert a result table to plain JSON rows (dates as text)."""
    return json.loads(df.head(MAX_ROWS).to_json(orient="records", date_format="iso"))


def _semantic():
    return yaml.safe_load(open(SEMANTIC_PATH))


@mcp.tool()
def ask(question: str) -> dict:
    """Answer a business question about the Olist e-commerce data in plain English.
    Returns the SQL used, the assumptions made and the result rows,
    or a clarifying question if the request is too vague."""
    r = agent_ask(question, use_guide=True, use_semantic=True)
    if r.get("needs_clarification"):
        return {"clarifying_question": r.get("clarifying_question")}
    out = {"sql": r.get("sql"), "assumptions": r.get("assumptions")}
    if "error" in r:
        out["error"] = r["error"]
    if "df" in r:
        out["row_count"] = len(r["df"])
        out["rows"] = _rows(r["df"])
    return out


@mcp.tool()
def run_query(sql: str) -> dict:
    """Run ONE read-only SELECT query on the Olist DuckDB database.
    Anything other than a single SELECT is blocked by the guardrail."""
    ok, reason = check_sql(sql)
    if not ok:
        return {"error": f"BLOCKED by guardrail: {reason}"}
    con = safe_connection(DB_PATH)
    try:
        df = con.execute(sql).df()
        return {"row_count": len(df), "rows": _rows(df)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        con.close()


@mcp.tool()
def list_metrics() -> list:
    """List the official business metrics: name, definition and synonyms."""
    return [
        {"name": m["name"], "definition": m["definition"], "synonyms": m.get("synonyms", [])}
        for m in _semantic()["metrics"]
    ]


@mcp.tool()
def describe_metric(name: str) -> dict:
    """Get the official definition and SQL formula of one business metric,
    by name or synonym (for example 'revenue', 'average order value', 'delivery time')."""
    key = name.strip().lower()
    for m in _semantic()["metrics"]:
        if key == m["name"].lower() or key in [s.lower() for s in m.get("synonyms", [])]:
            return m
    return {"error": f"No metric called '{name}'. Use list_metrics to see all metrics."}


if __name__ == "__main__":
    mcp.run()
    