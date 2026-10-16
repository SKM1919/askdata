"""Run every gold SQL in evals/golden.jsonl and print the answer, so we can check each one by eye."""
import json
import duckdb

con = duckdb.connect("data/olist.duckdb", read_only=True)

with open("evals/golden.jsonl") as f:
    for line in f:
        if not line.strip():
            continue
        q = json.loads(line)
        print(f"\n[{q['id']}] {q['question']}  ({q['difficulty']}, trap: {q['trap']})")
        try:
            con.sql(q["gold_sql"]).show(max_rows=10)
        except Exception as e:
            print("  ERROR:", e)
