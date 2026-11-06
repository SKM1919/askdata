"""Re-score a saved eval run against the CURRENT answer keys, without calling the AI again.
Usage: uv run python evals/rescore.py evals/results/<file>.jsonl
"""
import json
import sys

import duckdb

sys.path.insert(0, "evals")
from run_eval import score  # same checker as the live exam  # noqa: E402

questions = {}
for qfile in ("evals/golden.jsonl", "evals/heldout.jsonl"):
    questions.update({q["id"]: q for q in (json.loads(line) for line in open(qfile) if line.strip())})

con = duckdb.connect("data/olist.duckdb", read_only=True)
records = [json.loads(line) for line in open(sys.argv[1]) if line.strip()]

changed = []
for rec in records:
    q = questions[rec["id"]]
    if rec["status"] == "api_error":
        r = {"api_error": rec.get("error")}
    elif rec.get("clarifying_question") and not rec.get("sql"):
        r = {"needs_clarification": True}
    else:
        r = {}
        try:
            r["df"] = con.execute(rec["sql"]).df()
        except Exception as e:
            r["error"] = str(e)
    new_status = score(q, r, con)
    if new_status != rec["status"]:
        changed.append((rec["id"], rec["status"], new_status))
    rec["status"] = new_status

scored = [r for r in records if r["status"] != "api_error"]
correct = sum(r["status"] == "correct" for r in scored)
print(f"{sys.argv[1]}")
print(f"  Re-scored accuracy: {correct}/{len(scored)} = {100 * correct / max(len(scored), 1):.1f}%")
for qid, old, new in changed:
    print(f"  {qid}: {old} -> {new}")
