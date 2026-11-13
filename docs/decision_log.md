# AskData: Decision Log

Each entry records a product decision, the options considered, and why.

---

## D1: Default definition of "revenue" (2026-10-16)
- **Context:** The data supports three revenue figures: product price (R$ 13.59M), price + freight (R$ 15.84M) and amount paid (R$ 16.01M), an 18% spread.
- **Options:** A) product price, B) price + freight, C) amount paid.
- **Decision:** A, product price (`SUM(order_items.price)`), excluding freight. Use `payment_value` only for payment questions.
- **Why:** Freight mostly passes through to carriers. Only `order_items` can be split by category and seller. One default stops different teams reporting different numbers.

## D2: Which orders count as sales (2026-10-16)
- **Context:** 1.2% of orders were cancelled or unavailable; 1.7% were still in progress.
- **Options:** A) all orders, B) delivered only, C) all except cancelled and unavailable.
- **Decision:** C for revenue and sales. All orders when the question is "how many orders were placed". Always state the filter used.
- **Why:** Cancelled money is never received. "Delivered only" would understate the latest month, because recent orders have not arrived yet.

## D3: Cancelled orders in customer-behaviour metrics (2026-10-20)
- **Context:** The first evaluation run exposed a gap: for "customers who bought more than once", the AI excluded cancelled orders while the answer key included them. Five questions were affected (q15, q42, q45, q47, q50).
- **Options:** A) count every order placed, B) count only orders that were not cancelled or unavailable.
- **Decision:** B.
- **Why:** A cancelled order is not a real purchase, and B matches the sales rule in D2. One consistent rule is easier for both people and the AI to follow. The answer key was updated to match.
- **Impact:** Repeat-customer figures change slightly from the 3.1% first measured on all orders.

## D4: Keep q25 as an "ask first" question (2026-10-20)
- **Context:** For "Is delivery getting better?", the AI answered with a stated assumption instead of asking what "better" means.
- **Options:** A) keep the question and report the failure, B) change the expected behaviour after seeing the result.
- **Decision:** A.
- **Why:** Changing the exam after seeing a failure would inflate the score. When the AI should ask versus assume is an open product question for the Medium level.

## D5: Cancelled orders do not count as seller sales (2026-11-04)
- **Context:** In the semantic-layer run, the AI counted only sellers with valid orders for "How many sellers sell health and beauty products?" (q37); the answer key counted all sellers.
- **Options:** A) count every seller with any order, B) count only sellers with valid (not cancelled or unavailable) orders.
- **Decision:** B.
- **Why:** Same logic as D3: a cancelled order is not a real purchase for the customer, so it is not a real sale for the seller. One rule everywhere keeps customer and seller numbers consistent. The answer key was updated.

## D6: Keep the semantic layer (2026-11-13)
- **Context:** Over 3 runs each, guide + semantic layer v2 scored 96.7% on the golden set (after the q20 answer-key fix) vs 92.7% for the guide alone, and 93.0% vs 93.3% on the held-out set: within run-to-run variation. It uses about 73% more tokens per question (4,330 vs 2,500).
- **Options:** A) keep it, B) drop it.
- **Decision:** A, keep it.
- **Why:** Its value is consistent metric definitions, not raw accuracy. It fixed questions the guide alone got wrong in every run (q37, decision D5) and made the agent ask on vague questions more often (q25). The Hard level's `describe_metric` tool will read from it. Cost will be reduced by sending only the relevant metrics.
