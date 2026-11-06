"""Summarise several eval runs: accuracy per run, mean, range, and flaky questions.
Usage: uv run python evals/summarize.py evals/results/<pattern>*
"""
import json
import sys
from collections import defaultdict

accs = []
per_question = defaultdict(list)
for path in sys.argv[1:]:
    records = [json.loads(line) for line in open(path) if line.strip()]
    scored = [r for r in records if r["status"] != "api_error"]
    acc = 100 * sum(r["status"] == "correct" for r in scored) / max(len(scored), 1)
    accs.append(acc)
    for r in scored:
        per_question[r["id"]].append(r["status"] == "correct")
    print(f"{path.split('/')[-1]:58} {acc:5.1f}%  ({len(scored)} scored)")

if accs:
    print(f"\nRuns: {len(accs)} | Mean: {sum(accs) / len(accs):.1f}% | Range: {min(accs):.1f}% to {max(accs):.1f}%")
    flaky = {q: v for q, v in per_question.items() if 0 < sum(v) < len(v)}
    always_wrong = [q for q, v in per_question.items() if sum(v) == 0]
    print(f"Flaky (right in some runs, wrong in others): {', '.join(f'{q} {sum(v)}/{len(v)}' for q, v in sorted(flaky.items())) or 'none'}")
    print(f"Always wrong: {', '.join(sorted(always_wrong)) or 'none'}")
