"""AskData agent: turns a business question into SQL and runs it read-only on DuckDB.
Usage:
  uv run python src/agent.py "your question"                (schema guide ON)
  uv run python src/agent.py "your question" --semantic     (guide + semantic layer)
  uv run python src/agent.py "your question" --no-guide     (schema only)
"""
import json
import os
import sys
import time

import duckdb
from dotenv import load_dotenv
from google import genai
from google.genai import types

from guardrails import check_sql, safe_connection

load_dotenv()

DB_PATH = "data/olist.duckdb"
GUIDE_PATH = "docs/schema_guide.md"
SEMANTIC_PATH = "semantic/metrics.yaml"
MODEL = "gemini-3.5-flash-lite"

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def get_schema(con):
    """List every table and its columns, so the AI knows what exists."""
    rows = con.execute(
        "SELECT table_name, column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'main' ORDER BY table_name, ordinal_position"
    ).fetchall()
    lines, current = [], None
    for table, column, dtype in rows:
        if table != current:
            lines.append(f"\nTable {table}:")
            current = table
        lines.append(f"  - {column} ({dtype})")
    return "\n".join(lines)


def build_prompt(question, schema, guide, semantic):
    """Put together everything the AI needs to see."""
    parts = [
        "You are a data analyst. Write ONE DuckDB SQL query that answers the question.",
        "Reply with JSON only, using these keys:",
        '  "needs_clarification": true if the question is too vague to answer correctly, otherwise false',
        '  "clarifying_question": what you would ask the user (only when needs_clarification is true)',
        '  "sql": the SQL query (empty string when needs_clarification is true)',
        '  "assumptions": a short note on any choices you made',
        "Only write SELECT queries. Use only the tables and columns listed below.",
        f"\nDATABASE SCHEMA:{schema}",
    ]
    if guide:
        parts.append(f"\nSCHEMA GUIDE (business rules you must follow):\n{guide}")
    if semantic:
        parts.append(
            "\nSEMANTIC LAYER (official metric definitions). When a question matches a metric or one of its "
            "synonyms, use that metric's sql formula and filters; adapt the joins and query structure to the question. 'valid_orders' in a where field means "
            f"the rule of that name below.\n{semantic}"
        )
    parts.append(f"\nQUESTION: {question}")
    return "\n".join(parts)


def ask(question, use_guide=True, use_semantic=False):
    """Ask one question. Returns the AI's reply plus the query result, time and tokens."""
    con = safe_connection(DB_PATH)  # guardrail: read-only, no access to other files
    guide = open(GUIDE_PATH).read() if use_guide else None
    semantic = open(SEMANTIC_PATH).read() if use_semantic else None
    prompt = build_prompt(question, get_schema(con), guide, semantic)

    start = time.time()
    resp = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    result = json.loads(resp.text)
    result["latency_s"] = round(time.time() - start, 2)
    result["tokens"] = resp.usage_metadata.total_token_count

    if not result.get("needs_clarification") and result.get("sql"):
        ok, reason = check_sql(result["sql"])  # guardrail: only a single SELECT may run
        if not ok:
            result["error"] = f"BLOCKED by guardrail: {reason}"
        else:
            try:
                result["df"] = con.execute(result["sql"]).df()
            except Exception as e:
                result["error"] = str(e)
    con.close()
    return result


if __name__ == "__main__":
    args = sys.argv[1:]
    use_guide = "--no-guide" not in args
    use_semantic = "--semantic" in args
    question = " ".join(a for a in args if a not in ("--no-guide", "--semantic"))

    r = ask(question, use_guide, use_semantic)
    print(f"\nQuestion: {question}")
    print(f"Schema guide: {'ON' if use_guide else 'OFF'} | Semantic layer: {'ON' if use_semantic else 'OFF'}")
    if r.get("needs_clarification"):
        print(f"\nThe AI asks: {r.get('clarifying_question')}")
    else:
        print(f"\nSQL:\n{r.get('sql')}")
        print(f"\nAssumptions: {r.get('assumptions')}")
        if "error" in r:
            print(f"\nERROR running SQL: {r['error']}")
        else:
            print(f"\nAnswer:\n{r['df'].head(20).to_string(index=False)}")
    print(f"\nTime: {r['latency_s']}s | Tokens: {r['tokens']}")
