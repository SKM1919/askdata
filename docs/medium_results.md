# AskData: Medium-level Results

## What was added
- **Held-out test set:** 10 new questions written after the schema guide, to test generalisation ([evals/heldout.jsonl](../evals/heldout.jsonl)).
- **Semantic layer:** 13 metrics and 4 dimensions, each with one agreed formula ([semantic/metrics.yaml](../semantic/metrics.yaml)).
- **Repeated runs:** every configuration run 3 times, reported as mean and range.
- **Fairer evaluation:** a re-score tool (re-checks saved runs against corrected answer keys without new model calls) and support for more than one acceptable answer shape.

## Results (3 runs per configuration)

| Configuration | Golden set (50) | Held-out (10) | Tokens per question |
|---|---|---|---|
| Schema only (1 run) | 74% | 60% | ~880 |
| + Schema guide | **92.7%** (90-94) | **93.3%** (80-100) | ~2,500 |
| + Schema guide + semantic layer v2 | **96.7%** (94-100) | **93.0%** (89-100) | ~4,330 |

## Findings

1. **The schema guide generalises.** On questions written after it, accuracy rose from 60% to about 93%, a gain similar to the golden set's. This addresses the "teaching to the test" limitation from the Easy level.
2. **The semantic layer's accuracy gain is small and not conclusive:** +4 points on the golden set (its worst run equals the guide's best), a tie on held-out. Its clearer value is consistency: q37 (seller sales, decision D5) was right 3/3 vs 0/3, and q25 (asking before answering) 2/3 vs 0/3.
3. **Single runs are unreliable.** The same configuration scored 80% and 100% on the held-out set in different runs. Every comparison is now reported as a mean and range.
4. **Semantic layer v1 regressed, and the regression check caught it.** v1 scored 80% on held-out and 88% on golden. Causes: a review definition that dropped columns (h08 became invalid SQL) and over-confidence on vague questions (q22). v2 fixed both.
5. **Evaluation fixes mattered as much as model changes.** Two answer-key corrections (decision D5 for q37, an unrequested column in q10) moved scores by about 4 points; q20 needed a second acceptable answer shape. Two of q20's three "failures" were correct answers.

## Cost
The semantic layer adds about 1,800 tokens per question (+73%). Latency was unchanged (about 1.1-1.4s), apart from one period of provider overload (503 errors, 20s+ responses) unrelated to the code.

## Deferred, and why
- **Few-shot example retrieval:** hard questions already score 9-10/10; the remaining errors look like run-to-run variation, so expected value is low.
- **Postgres on Supabase:** an infrastructure change with no expected accuracy effect. Revisit at the Hard level if the MCP server needs a hosted database.

## Next: Hard level
Expose the agent as an MCP server (`run_query`, `describe_metric` backed by the semantic layer), block destructive SQL before execution, add tracing, and report cost and latency. Also send only the relevant metrics to cut the semantic layer's token cost.
