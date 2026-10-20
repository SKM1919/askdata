# AskData

**Ask business questions in plain English; get answers from an e-commerce database.**
A text-to-SQL agent with a systematic evaluation, built as an AI Product Manager portfolio project.

## Headline result

A schema guide documenting 6 business-data traps raised execution accuracy from **74% to 98%** on a 50-question golden set.

| | Guide OFF | Guide ON |
|---|---|---|
| **Execution accuracy** | **74%** | **98%** |
| Joins (20 questions) | 13 | 20 |
| Hard (10 questions) | 5 | 10 |
| Avg tokens per question | 880 | 2,502 |
| Avg latency | 1.27s | 1.96s |

The entire gain came from questions that touch a documented trap (24/37 -> 36/37); questions with no trap scored 13/13 either way. Details in [docs/error_analysis.md](docs/error_analysis.md).

## How it works

cat > README.md << 'EOF'
# AskData

**Ask business questions in plain English; get answers from an e-commerce database.**
A text-to-SQL agent with a systematic evaluation, built as an AI Product Manager portfolio project.

## Headline result

A schema guide documenting 6 business-data traps raised execution accuracy from **74% to 98%** on a 50-question golden set.

| | Guide OFF | Guide ON |
|---|---|---|
| **Execution accuracy** | **74%** | **98%** |
| Joins (20 questions) | 13 | 20 |
| Hard (10 questions) | 5 | 10 |
| Avg tokens per question | 880 | 2,502 |
| Avg latency | 1.27s | 1.96s |

The entire gain came from questions that touch a documented trap (24/37 -> 36/37); questions with no trap scored 13/13 either way. Details in [docs/error_analysis.md](docs/error_analysis.md).

## How it works

    Question -> Gemini (schema + schema guide) -> SQL -> DuckDB (read-only) -> Answer + assumptions

1. The agent reads the database schema automatically and, optionally, the schema guide.
2. Gemini returns JSON: the SQL, the assumptions it made, or a clarifying question if the request is too vague.
3. The SQL runs on a **read-only** connection, so the agent can never change data.

## What I did as the PM

- **Found the data traps** that make AI answers wrong, and documented them with evidence and a rule for each: [schema guide](docs/schema_guide.md)
- **Built a 50-question golden set** with verified answers: 15 simple, 20 join, 10 hard, 5 ambiguous ([evals/golden.jsonl](evals/golden.jsonl))
- **Measured the agent with and without the guide**, then read every failure by hand
- **Found and fixed 3 bugs in my own evaluation**; the improvement stayed at 22-24 points across all versions
- **Made and logged the business decisions** behind the metrics: [decision log](docs/decision_log.md)

## Business insights found along the way

- A late delivery drops the average review from **4.29 to 2.57 stars**. Delivery speed drives satisfaction more than anything else in this data.
- The highest-revenue day was **Black Friday, 24 Nov 2017**, about 5x a normal day.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/), then run `uv sync`.
2. Download the [Olist dataset from Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and unzip the CSVs into `data/`. (The dataset has a non-commercial licence, so it is linked here rather than included.)
3. Copy `.env.example` to `.env` and add your Gemini API key.
4. Load the data: `uv run python src/load_data.py`
5. Ask a question: `uv run python src/agent.py "Which state has the most customers?"`
6. Run the evaluation: `uv run python evals/run_eval.py` (add `--no-guide` for the baseline)

## Project structure

| Path | What it is |
|---|---|
| `src/agent.py` | The text-to-SQL agent |
| `src/load_data.py` | Loads the Olist CSVs into DuckDB |
| `src/q.py` | Runs one SQL query (read-only) |
| `evals/golden.jsonl` | 50 questions with gold SQL |
| `evals/run_eval.py` | Scores the agent against the golden set |
| `evals/compare_runs.py` | Compares two runs by trap |
| `evals/results/` | Saved evaluation runs |
| `docs/` | Schema guide, error analysis, decision log |

## Roadmap

- [x] **Easy:** text-to-SQL agent, schema guide, 50-question eval, error analysis
- [ ] **Medium:** semantic layer, few-shot example retrieval, held-out test set, Postgres
- [ ] **Hard:** MCP server with read-only access, blocked destructive SQL, tracing, cost and latency report
- [ ] **Hardest:** multi-agent weekly business review, compared with human analyst time
