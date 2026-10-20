"""Run the 50-question golden set through the agent and score it.
Usage:
  uv run python evals/run_eval.py              (schema guide ON)
  uv run python evals/run_eval.py --no-guide   (schema guide OFF)

Checker rules (v2):
  - "Which ..." questions are graded on the item named (first gold column), not the supporting number.
  - Whole numbers must match exactly. Decimals match within 1%. A fraction matches its percentage (0.0343 = 3.43).
  - Text ignores case, spaces and symbols (On-Time = on_time). A month matches its first day (2017-11 = 2017-11-01).
  - Row order and extra AI columns are ignored; the number of rows must match.
"""
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime

import duckdb

sys.path.insert(0, "src")
from agent import ask  # noqa: E402

PAUSE_S = 4      # wait between questions to stay under Gemini's free-tier rate limit
NUM_TOL = 0.01   # 1% tolerance for decimals


def norm(v):
    """Turn a value into a float or a tidy lowercase string."""
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        s = str(v).strip().lower()
        return s[:-9] if s.endswith(" 00:00:00") else s


def values_match(g, a):
    if g is None or a is None:
        return g is None and a is None
    if isinstance(g, float) and isinstance(a, float):
        if g.is_integer() and a.is_integer():
            return g == a
        allowed = max(NUM_TOL * abs(g), 0.01)  # 1%, or 0.01 for small values rounded to 2 decimals
        return any(abs(c - g) <= allowed for c in (a, a * 100))
    if isinstance(g, str) and isinstance(a, str):
        if re.sub(r"[^a-z0-9]", "", g) == re.sub(r"[^a-z0-9]", "", a):
            return True
        return bool(re.fullmatch(r"\d{4}-\d{2}", g)) and a.startswith(g + "-01")
    return False


def row_match(gold_row, ai_row):
    """Every gold value must match a different value in the AI row."""
    available = list(ai_row)
    for gv in gold_row:
        for i, av in enumerate(available):
            if values_match(gv, av):
                available.pop(i)
                break
        else:
            return False
    return True


def results_match(gold_rows, ai_rows):
    if len(gold_rows) != len(ai_rows):
        return False
    remaining = list(ai_rows)
    for g in gold_rows:
        for i, r in enumerate(remaining):
            if row_match(g, r):
                remaining.pop(i)
                break
        else:
            return False
    return True


def rows_of(df):
    return [tuple(norm(v) for v in row) for row in df.itertuples(index=False)]


def score(q, r, con):
    if "api_error" in r:
        return "api_error"
    if q["gold_sql"] is None:
        return "correct" if r.get("needs_clarification") else "missed_ambiguity"
    if r.get("needs_clarification"):
        return "asked_unnecessarily"
    if "error" in r or "df" not in r:
        return "sql_error"
    gold_df = con.execute(q["gold_sql"]).df()
    if q["question"].lower().startswith("which"):
        gold_df = gold_df.iloc[:, :1]  # grade the item named, not the supporting number
    return "correct" if results_match(rows_of(gold_df), rows_of(r["df"])) else "wrong_result"


def main():
    use_guide = "--no-guide" not in sys.argv
    label = "guide_on" if use_guide else "guide_off"
    con = duckdb.connect("data/olist.duckdb", read_only=True)
    questions = [json.loads(line) for line in open("evals/golden.jsonl") if line.strip()]

    print(f"Running {len(questions)} questions with schema guide {'ON' if use_guide else 'OFF'}...\n")
    records = []
    for i, q in enumerate(questions, 1):
        try:
            r = ask(q["question"], use_guide)
        except Exception:
            time.sleep(30)  # probably a rate limit: wait, then retry once
            try:
                r = ask(q["question"], use_guide)
            except Exception as e:
                r = {"api_error": str(e)}

        status = score(q, r, con)
        records.append({
            "id": q["id"], "question": q["question"], "difficulty": q["difficulty"],
            "trap": q["trap"], "status": status,
            "sql": r.get("sql"), "assumptions": r.get("assumptions"),
            "clarifying_question": r.get("clarifying_question"),
            "error": r.get("error") or r.get("api_error"),
            "latency_s": r.get("latency_s"), "tokens": r.get("tokens"),
        })
        print(f"[{i:2}/{len(questions)}] {q['id']}  {status:20}  {q['question'][:55]}")
        time.sleep(PAUSE_S)

    os.makedirs("evals/results", exist_ok=True)
    out_path = f"evals/results/{label}_{datetime.now():%Y%m%d_%H%M}.jsonl"
    with open(out_path, "w") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

    scored = [r for r in records if r["status"] != "api_error"]
    correct = sum(r["status"] == "correct" for r in scored)
    print(f"\n===== RESULTS: schema guide {'ON' if use_guide else 'OFF'} =====")
    print(f"Execution accuracy: {correct}/{len(scored)} = {100 * correct / max(len(scored), 1):.1f}%")
    print("\nBy difficulty:")
    for d in ["simple", "join", "hard", "ambiguous"]:
        group = [r for r in scored if r["difficulty"] == d]
        ok = sum(r["status"] == "correct" for r in group)
        print(f"  {d:10} {ok}/{len(group)}")
    print("\nOutcomes:")
    for status, n in Counter(r["status"] for r in records).most_common():
        print(f"  {status:20} {n}")
    lat = [r["latency_s"] for r in scored if r["latency_s"]]
    tok = [r["tokens"] for r in scored if r["tokens"]]
    print(f"\nAvg latency: {sum(lat) / max(len(lat), 1):.2f}s | Avg tokens per question: {sum(tok) / max(len(tok), 1):.0f}")
    print(f"Saved details to {out_path}")


if __name__ == "__main__":
    main()
