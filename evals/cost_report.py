"""Cost and latency report built from traces/*.jsonl.
Usage: uv run python evals/cost_report.py

Prices: Gemini 3.5 Flash-Lite, standard paid tier, USD per 1M tokens (checked 2026-11-15).
On the free tier the actual cost is zero; this shows what a paying company would pay.
"""
import glob
import json
import statistics
from collections import defaultdict

PRICE_IN = 0.30 / 1_000_000   # per input token
PRICE_OUT = 2.50 / 1_000_000  # per output token (includes thinking tokens)


def percentile(values, p):
    s = sorted(values)
    if not s:
        return 0.0
    return s[max(0, min(len(s) - 1, round(p / 100 * (len(s) - 1))))]


rows = [json.loads(line) for f in sorted(glob.glob("traces/*.jsonl")) for line in open(f) if line.strip()]
groups = defaultdict(list)
for r in rows:
    config = "guide+semantic" if r.get("semantic") else ("guide" if r.get("guide") else "schema only")
    groups[(r.get("source", "?"), config)].append(r)

print(f"Traced questions: {len(rows)}\n")
header = (f"{'source':7} {'config':15} {'n':>4} {'ran ok':>7} {'in tok':>7} {'out tok':>7} "
          f"{'$/question':>11} {'$/1k q':>7} {'p50 s':>6} {'p95 s':>6} {'max s':>6}")
print(header)
print("-" * len(header))

total_in_cost = total_out_cost = 0.0
for (source, config), rs in sorted(groups.items()):
    done = [r for r in rs if r.get("status") != "api_error"]
    if not done:
        continue
    tin = statistics.mean(r["input_tokens"] for r in done)
    tout = statistics.mean(r["output_tokens"] for r in done)
    cost = tin * PRICE_IN + tout * PRICE_OUT
    total_in_cost += sum(r["input_tokens"] for r in done) * PRICE_IN
    total_out_cost += sum(r["output_tokens"] for r in done) * PRICE_OUT
    lat = [r["total_s"] for r in done]
    ran_ok = 100 * sum(r["status"] in ("ok", "clarify") for r in done) / len(done)
    print(f"{source:7} {config:15} {len(rs):4} {ran_ok:6.0f}% {tin:7.0f} {tout:7.0f} "
          f"{cost:11.5f} {cost * 1000:7.2f} {percentile(lat, 50):6.2f} {percentile(lat, 95):6.2f} {max(lat):6.2f}")

statuses = defaultdict(int)
for r in rows:
    statuses[r.get("status", "?")] += 1
print("\nOutcomes:", ", ".join(f"{k} {v}" for k, v in sorted(statuses.items())))
if total_in_cost + total_out_cost:
    print(f"Input tokens' share of total cost: {100 * total_in_cost / (total_in_cost + total_out_cost):.0f}%")
print("\n'ran ok' = answered or asked a clarifying question without an error (not the same as correct).")
