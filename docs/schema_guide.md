# AskData: Schema Guide

This guide explains the Olist database to the AI: what each table means and the traps that cause wrong answers.

## Data traps

### Trap 1: `customer_id` is not a real customer
- **What happens:** Olist creates a new `customer_id` for every order. One person who buys 3 times has 3 different `customer_id`s. The real person is `customer_unique_id`.
- **Evidence:** 99,441 `customer_id`s but only 96,096 real customers (`customer_unique_id`). 2,997 customers ordered more than once.
- **Rule for the AI:** To count customers or find repeat customers, always use `COUNT(DISTINCT customer_unique_id)`. Never count `customer_id`.
- **Business impact:** Using `customer_id` makes every customer look like a one-time buyer (repeat rate 0%). The true repeat rate is about 3.1% (2,997 ÷ 96,096). Customer count, repeat rate, CLV and retention reports would all be wrong.

### Trap 2: "revenue" has three possible definitions
- **What happens:** "Revenue" can come from 3 places: product prices (`order_items.price`), product prices + shipping (`price + freight_value`), or what customers paid (`order_payments.payment_value`). They give different totals.
- **Evidence:** Products only: R$ 13.59M. Products + shipping: R$ 15.84M. Total paid: R$ 16.01M. Gap of R$ 2.4M (about 18%). Shipping is about 14% of the total. Vouchers are R$ 0.38M of payments.
- **Rule for the AI:** By default, "revenue" or "sales" = `SUM(order_items.price)`, excluding shipping. Use `payment_value` only for questions about payments (amount paid, payment methods). Always state which definition was used.
- **Business impact:** If marketing uses total paid and finance uses product sales, dashboards differ by up to 18%. ROAS and campaign ROI change depending on who calculated them, and teams argue about numbers instead of acting.

### Trap 3: not every order is a real sale
- **What happens:** Orders have 8 statuses. Some never became real sales (`canceled`, `unavailable`). Others are still in progress (`shipped`, `invoiced`, `processing`, `created`, `approved`). Counting every order as a sale makes revenue too high.
- **Evidence:** 99,441 orders: 97.0% delivered, 1.7% in progress, 1.2% never completed (625 canceled + 609 unavailable). In-progress orders are mostly the most recent ones, so recent periods are affected more than the 3% total suggests.
- **Rule for the AI:** For revenue and sales questions, exclude cancelled and unavailable orders: `WHERE order_status NOT IN ('canceled', 'unavailable')`. For "how many orders were placed", count all orders. Always state which filter was used. Note: the database spells it `canceled` (one "l").
- **Business impact:** Counting cancelled orders makes campaign sales and ROAS look better than reality. Using only delivered orders makes the latest month look worse, because recent orders haven't arrived yet. Either mistake can lead to wrong budget decisions.
