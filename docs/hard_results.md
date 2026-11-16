# AskData: Hard-level Results

## What was added
- **SQL guardrails** ([src/guardrails.py](../src/guardrails.py)): every AI-written query is checked before it runs. Only a single SELECT is allowed, and the database connection is read-only with no access to any other file.
- **MCP server** ([src/mcp_server.py](../src/mcp_server.py)): AskData is usable from AI assistants such as the Claude desktop app, through four tools: `ask`, `run_query`, `list_metrics` and `describe_metric`.
- **Tracing**: every question (from the terminal, from Claude via MCP, or from the evaluation) is logged locally with its source, SQL, status, latency and input/output tokens.
- **Cost and latency report** ([evals/cost_report.py](../evals/cost_report.py)), built from the traces.

## Safety: defence in depth

| Layer | What it does | How it is tested |
|---|---|---|
| 1. Model instructions | "Only write SELECT queries" | Red-team prompts: asked to delete data and to read a private file, the model refused both |
| 2. SQL check | Blocks anything other than one SELECT (DELETE, DROP, UPDATE, INSERT, COPY, ATTACH, SET, stacked statements) | 12 automated tests |
| 3. Safe connection | Read-only, no file access, even if a bad query got through | 2 automated tests |

The model is the first layer, not the one we rely on: code-enforced guardrails cannot be talked out of their rules. All MCP tools go through layers 2 and 3, including `run_query`, where the assistant writes the SQL itself. 20 automated tests in total (`uv run pytest -q`).

## MCP connection, verified from Claude

| Check through the live MCP connection | Result |
|---|---|
| `list_metrics` | 13 official metrics returned |
| `describe_metric("delivery time")` | Found `delivery_days` by synonym, with its exact formula |
| `run_query("DELETE FROM orders")` | Blocked by the guardrail |
| `ask("Which customer state has the highest percentage of late deliveries?")` | AL, 23.9%, matching the answer key, using the official `late_rate` metric |

## Cost and latency (122 traced questions)

| Configuration | Input tokens | Output tokens | Cost per question | Per 1,000 questions | p50 | p95 |
|---|---|---|---|---|---|---|
| Schema guide | 2,320 | 193 | $0.00118 | $1.18 | 0.94s | 1.57s |
| Guide + semantic layer | 4,174 | 168 | $0.00167 | $1.67 | 1.01s | 1.60s |

Prices: Gemini 3.5 Flash-Lite standard paid tier, $0.30 per 1M input tokens and $2.50 per 1M output tokens (checked 2026-11-15). The project itself runs on the free tier.

- **Cheap:** a team asking 22,000 questions a month (50 people x 20 a day x 22 days) would pay about $37 a month.
- **Fast:** about 1 second typically, under 2 seconds in slow cases.
- **Tokens are not cost:** the semantic layer adds about 80% more input tokens but only 41% more cost, because input tokens are much cheaper than output tokens. Input still makes up about two thirds of total cost.

## Lessons
- **A safety change broke the evaluation.** Once the agent used the safe connection, the evaluation script (which opened the same database with different settings) failed on every question, and labelled the failures `api_error`. The real message showed a DuckDB configuration clash. Error labels can mislead; read the underlying message.
- **Provider instability is real.** On one day the model returned 503 "high demand" errors and 20s+ responses. Tracing now records these failures, so they can be told apart from code problems.
- **Library versions move.** The MCP SDK released v2 during the build (`FastMCP` renamed to `MCPServer`); the migration guide made it a two-line change.

## Deliberately not built
- **Sending only the relevant metrics (H5):** it would save about $0.0005 per question (about $12 a month at team scale) and risks lower accuracy if a needed metric is left out. Decision D7: revisit if usage grows about 100x.
