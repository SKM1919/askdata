"""Print every question the AI got wrong, with its SQL next to the gold SQL.
Usage: uv run python evals/show_failures.py evals/results/<file>.jsonl
"""
import json
import sys

gold = {q["id"]: q for q in (json.loads(line) for line in open("evals/golden.jsonl") if line.strip())}

for line in open(sys.argv[1]):
    r = json.loads(line)
    if r["status"] == "correct":
        continue
    g = gold[r["id"]]
    print("=" * 70)
    print(f"{r['id']}  [{r['status']}]  {r['question']}")
    print(f"  trap: {r['trap']}")
    print(f"\n  AI SQL:\n    {r['sql']}")
    print(f"\n  Gold SQL:\n    {g['gold_sql']}")
    if r.get("assumptions"):
        print(f"\n  AI assumptions: {r['assumptions']}")
    if r.get("error"):
        print(f"\n  Error: {r['error']}")
    print()
