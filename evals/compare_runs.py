"""Compare two eval runs question by question, grouped by trap.
Usage: uv run python evals/compare_runs.py <guide_off_file> <guide_on_file>
"""
import json
import sys
from collections import defaultdict


def load(path):
    return {r["id"]: r for r in (json.loads(line) for line in open(path) if line.strip())}


off, on = load(sys.argv[1]), load(sys.argv[2])

by_trap = defaultdict(lambda: [0, 0, 0])  # questions, correct OFF, correct ON
for qid, r in off.items():
    t = by_trap[r["trap"]]
    t[0] += 1
    t[1] += r["status"] == "correct"
    t[2] += on[qid]["status"] == "correct"

print(f"{'trap':28} {'questions':>9} {'OFF':>5} {'ON':>5}")
for trap, (n, a, b) in sorted(by_trap.items(), key=lambda x: -x[1][0]):
    print(f"{trap:28} {n:9} {a:5} {b:5}")

print("\nFixed by the guide (wrong OFF -> right ON):")
for qid, r in off.items():
    if r["status"] != "correct" and on[qid]["status"] == "correct":
        print(f"  {qid}  [{r['status']}]  {r['question']}")

print("\nBroken by the guide (right OFF -> wrong ON):")
for qid, r in off.items():
    if r["status"] == "correct" and on[qid]["status"] != "correct":
        print(f"  {qid}  [{on[qid]['status']}]  {r['question']}")
