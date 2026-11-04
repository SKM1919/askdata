# AskData: Product Requirements Document

| | |
|---|---|
| **Owner** | Saikumar M |
| **Status** | v1, Easy level shipped |
| **Last updated** | 2026-10-20 |
| **Related** | [Schema guide](schema_guide.md), [Error analysis](error_analysis.md), [Decision log](decision_log.md) |

---

## 1. Problem

Business teams make daily decisions from data they cannot query themselves.

- **Slow answers.** A marketing or category manager who needs a number, for example "revenue by state last month", raises a request with an analyst and waits. Decisions are delayed, or made on gut feel.
- **Inconsistent answers.** The same question returns different numbers depending on who answers it. In the Olist data, "total revenue" can honestly be R$ 13.59M (product price), R$ 15.84M (with freight) or R$ 16.01M (amount paid), an 18% spread. Teams argue about numbers instead of acting on them.
- **Generic AI tools make this worse.** A text-to-SQL model writes fluent SQL but does not know business definitions. In our test, a model given only table and column names answered **26% of questions wrong**, and wrong answers looked exactly as confident as right ones.

**Why it matters:** a wrong revenue or ROAS figure leads to wrong budget decisions, and analysts spend time on repetitive questions instead of deeper work.

## 2. Users

| User | Need | Today |
|---|---|---|
| **Marketing / growth manager** (primary) | Fast answers on revenue, customers, retention and campaign performance; no SQL | Waits for an analyst or uses a dashboard that does not answer the exact question |
| **Category and operations managers** | Answers on products, sellers and delivery performance | Same as above |
| **Data analysts** (owners of definitions) | Fewer repetitive requests; confidence that self-serve answers use the agreed definitions | Answer the same questions repeatedly; reconcile conflicting numbers |

**Core job to be done:** *"When I need a business number, I want a correct answer in seconds, with the definition it used, so I can decide without waiting or second-guessing."*

## 3. Goals and success metrics

**Goals**
1. **Correct:** answer everyday business questions correctly.
2. **Consistent:** always apply the agreed business definitions.
3. **Safe:** never change or damage data.
4. **Transparent:** show the SQL and the assumptions behind every answer.
5. **Honest about vagueness:** ask a clarifying question when a request cannot be answered correctly as stated.

**Metrics**

| Metric | Target | Easy-level result |
|---|---|---|
| **Execution accuracy** on the golden set (north star) | at least 95% | **98%** (49/50) |
| Accuracy on trap questions | at least 95% | **97%** (36/37) |
| Clarifies ambiguous questions | 5/5 | 4/5 |
| Unsafe data changes | 0 | 0 (read-only connection) |
| Average latency | under 3s | 1.96s |
| Tokens per question | track | about 2,500 |
| Accuracy on unseen (held-out) questions | at least 90% | not yet measured |

**In a real deployment, add:** share of questions answered without an analyst, time to answer, and how often users correct or reject an answer.

## 4. Non-goals (v1)

- Writing, updating or deleting data
- Charts, dashboards or written reports (planned for the Hardest level)
- Real-time or streaming data
- Multi-turn conversations with memory
- Replacing analysts for deep, open-ended analysis
- Questions the data cannot answer (e.g. marketing channel or ad spend; this dataset has none)

## 5. Solution

    Question -> Gemini (schema + schema guide) -> SQL -> DuckDB (read-only) -> Answer + assumptions

- The agent reads the database schema automatically.
- A **schema guide** gives the model the business rules: six documented data traps, each with evidence, a rule and its business impact.
- The model returns JSON: the SQL and its assumptions, or a clarifying question.
- The SQL runs on a **read-only** connection.

**Key design decisions** (details in the [decision log](decision_log.md)):
- **D1:** revenue = product price, excluding freight.
- **D2:** sales exclude cancelled and unavailable orders; order counts include all orders placed.
- **D3:** customer-behaviour metrics (repeat customers, "customers who bought") exclude cancelled and unavailable orders.
- **D4:** evaluation questions are not changed after seeing results.

## 6. Requirements

**Functional**

| ID | Requirement | Priority | Status |
|---|---|---|---|
| FR1 | Answer a plain-English question with a single SQL query and its result | Must | Done |
| FR2 | Show the SQL and the assumptions with every answer | Must | Done |
| FR3 | Apply all business rules in the schema guide | Must | Done |
| FR4 | Ask a clarifying question when a request is too vague | Must | Partly (4/5) |
| FR5 | Report latency and token use for every question | Should | Done |
| FR6 | Say clearly when the data cannot answer a question | Should | Not yet |

**Guardrails**

| ID | Guardrail | Status |
|---|---|---|
| GR1 | Database opened read-only; writes are impossible | Done |
| GR2 | Only SELECT queries; destructive SQL blocked before execution | Instructed in the prompt; hard blocking planned for the Hard level |
| GR3 | No secrets in the repository (API key in `.env`, ignored by Git) | Done |
| GR4 | Source data not redistributed (non-commercial licence) | Done |

**Business rules:** see the [schema guide](schema_guide.md): real customers, revenue definition, order status, Portuguese categories, incomplete edge months, and duplicate reviews.

## 7. Evaluation

- **Golden set:** 50 questions with verified gold SQL: 15 simple, 20 join, 10 hard, 5 ambiguous. 37 questions test a specific data trap.
- **Metric:** execution accuracy. The agent's result is compared with the gold result (values, not SQL text). Ambiguous questions pass only if the agent asks a clarifying question.
- **Method:** each question is run with the schema guide OFF and ON, and every failure is read by hand and labelled.

| | Guide OFF | Guide ON |
|---|---|---|
| Execution accuracy | 74% | **98%** |
| Trap questions | 24/37 | 36/37 |
| Non-trap questions | 13/13 | 13/13 |
| Tokens per question | 880 | 2,502 |

The entire gain came from trap questions. Three bugs in the evaluation itself were found and fixed; the improvement stayed at 22-24 points across all versions. Full details: [error analysis](error_analysis.md).

## 8. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Confidently wrong answers | Wrong business decisions | Golden-set evaluation; SQL and assumptions shown with every answer |
| Teaching to the test: guide and exam written together | Accuracy overstated | Held-out question set written after the guide (Medium) |
| Business definitions change over time | Answers silently go out of date | Schema guide versioned and owned by the analytics team; evaluation re-run on every change |
| Prompt cost grows as the guide grows | Higher cost and latency (already 2.8x tokens) | Semantic layer and retrieval of only the relevant rules (Medium) |
| Agent assumes instead of asking (q25) | Answers a different question than intended | Explicit clarification policy, then re-test (Medium) |
| Model changes or is retired | Accuracy changes without warning | Re-run the full evaluation before switching models |
| Data privacy on a free API tier | Provider may use submitted data | Public data only; paid or enterprise tier for any real company data |

## 9. Roadmap

| Level | Scope | Success criteria |
|---|---|---|
| **Easy** (done) | Agent, schema guide, 50-question evaluation, error analysis | 98% execution accuracy; failures explained |
| **Medium** | Semantic layer (metric definitions), few-shot examples, held-out set, clarification policy, Postgres | At least 90% on held-out questions; 5/5 on ambiguous |
| **Hard** | MCP server (`run_query`, `describe_metric`), blocked destructive SQL, tracing, cost and latency report | Usable from Claude or Cursor; 0 unsafe queries; every call traced |
| **Hardest** | Planner, SQL, chart and narrative agents producing a weekly business review | Review quality accepted by a reviewer; analyst time saved measured |

## 10. Open questions

1. **Ask vs assume:** when should the agent ask, and when should it answer with a clearly stated assumption?
2. **Ownership:** in a real company, who owns and approves changes to the schema guide?
3. **Trust threshold:** what accuracy is good enough for self-serve use, and should it differ by question type?
4. **Unanswerable questions:** how should the agent respond when the data cannot answer a question at all?
