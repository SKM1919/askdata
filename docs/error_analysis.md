# AskData: Error Analysis (Easy level)

## 1. Headline result

| | Guide OFF | Guide ON | Change |
|---|---|---|---|
| **Execution accuracy** | **74%** (37/50) | **98%** (49/50) | **+24 pts** |
| Simple (15) | 14 | 15 | +1 |
| Join (20) | 13 | 20 | +7 |
| Hard (10) | 5 | 10 | +5 |
| Ambiguous (5) | 5 | 4 | -1 |
| Avg tokens per question | 880 | 2,502 | 2.8x |
| Avg latency | 1.27s | 1.96s | +0.7s |

Setup: Gemini 3.5 Flash-Lite, 50-question golden set, one run per configuration.
"Guide OFF" = the model sees only table and column names. "Guide ON" = it also sees `docs/schema_guide.md` (6 documented data traps).

## 2. Where the schema guide helps

| Trap tested | Questions | OFF | ON |
|---|---|---|---|
| none | 13 | 13 | 13 |
| customer_unique_id | 8 | 5 | 8 |
| revenue_definition | 8 | 5 | 8 |
| portuguese_categories | 7 | 3 | 7 |
| ambiguous | 5 | 5 | 4 |
| edge_months | 4 | 2 | 4 |
| duplicate_reviews | 3 | 2 | 3 |
| canceled_spelling | 1 | 1 | 1 |
| order_count_all_statuses | 1 | 1 | 1 |

- Questions with no trap scored 13/13 in both runs. **The entire gain comes from trap questions: 24/37 -> 36/37.**
- The guide fixed 13 questions and broke 1 (q25).
- Biggest gains: Portuguese category names, revenue definition, real customers. These are rules a model cannot infer from column names.

## 3. Error taxonomy

All 14 failures from the first run (guide ON, checker v1) were read by hand and labelled:

| Category | Questions | Count | Root cause |
|---|---|---|---|
| Checker too strict (AI answer was correct) | q05, q10, q14, q17 | 4 | Evaluation |
| Business rule missing from guide: do cancelled orders count as a purchase? | q15, q42, q45, q47, q50 | 5 | Guide / gold set |
| AI misread a guide rule ("last month", counting orders) | q19, q20 | 2 | AI |
| AI misunderstood a column (summed `order_item_id`, a sequence number) | q35 | 1 | AI + guide gap |
| Invalid SQL (column out of scope) | q46 | 1 | AI |
| Answered with an assumption instead of asking | q25 | 1 | Open product question |

**Key lesson: 10 of the 14 first-run failures were problems in the evaluation or the business rules, not in the AI.**

## 4. Fixes made to the evaluation

| Version | Change | Guide OFF | Guide ON | Gap |
|---|---|---|---|---|
| v1 | First run | 50% | 72% | +22 |
| v2 | Gold set: cancelled orders excluded from customer-behaviour questions (decision B). Checker: "which" questions graded on the item named, 1% decimal tolerance, fraction = percentage, label and date-format normalisation | 72% | 96% | +24 |
| v3 | Checker: absolute tolerance of 0.01 for small values rounded to 2 decimals (q43) | 74% | 98% | +24 |

The gap stayed between 22 and 24 points across all three versions, so the improvement is not an artefact of the checker.

## 5. Limitations and open questions

- **q25 (ask vs assume):** without the guide the AI asked a clarifying question; with it, it answered using a stated assumption. Hypothesis: rules like "always state which filter was used" push the model to answer rather than ask. The right product behaviour is an open decision.
- **Teaching to the test:** the guide and the golden set were written together from the same traps. A held-out set written after the guide is needed to measure generalisation.
- **Lenient grading:** "which" questions are graded on the item named only, so a wrong method that lands on the right answer still passes (e.g. q35).
- **One run per configuration:** model outputs vary between runs; differences of 1-2 questions may be noise.
- **Cost:** the guide adds about 1,600 tokens and 0.7s per question.

## 6. Next steps (Medium level)

1. Schema guide v2: add rules for "last month" wording, `order_item_id`, and percentages shown as 0-100.
2. Write a held-out set of new questions to test generalisation.
3. Define a clarification policy (when to ask vs answer with an assumption) and re-test q21-q25.
4. Run each configuration several times to measure variance.
