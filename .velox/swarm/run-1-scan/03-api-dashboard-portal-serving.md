# API, dashboard, portal (serving)

Status: ok

Result: Partial. `api.py` and `portal.py` were read in full. `dashboard.py` was only grepped, so its JS fallback and chart logic is unread. The findings below are all in the serving layer.

Findings:
- src/eurostream/api.py:44-50 — CORS is wide open: `allow_origins=["*"]`, `allow_credentials=True`, all methods and headers. There is no authentication anywhere in the file.
- src/eurostream/api.py:162 — `POST /erasure-requests` has no auth. It enqueues an erasure for any `customer_id`, or runs the full cascade when `sync=true`. `requested_by` is the hard-coded literal `"dsar@eurocart.eu"` (also at :187), so the audit trail cannot identify the real caller.
- src/eurostream/api.py:186 — `POST /erase/{customer_id}` has no auth. It runs the destructive cascade synchronously, then `metrics.flush()`.
- src/eurostream/api.py:217-237 — `GET /verify-erasure/{customer_id}` builds SQL with an f-string around the raw path parameter, so it is SQL-injectable. It is also unauthenticated. The queries touch `gold.customer_360`, `silver.customers`, `bronze.orders` and `governance.erasure_audit_log`.
- src/eurostream/api.py:238-240 — The "verified" rule treats `bronze.orders` rows with `email <> '<anonymized>'` as clear text. Rows with `email = '<anonymized>'` are reported separately and do not block verification. Bronze is anonymised in place, not deleted.
- src/eurostream/api.py:433 — `GET /gold/customer-360` is unauthenticated and returns `SELECT *` from `gold.customer_360`. This is PII exposure unless the table is fully pseudonymised, and no masking is applied in the endpoint. The search is escaped with `replace("'", "''")` at :437. It is a `LIKE '%…%'` match on `customer_id` with `ORDER BY customer_id LIMIT int(limit)`, limit 1–1000, default 100.
- src/eurostream/api.py:427 — `GET /governance/erasure-audit` is unauthenticated and returns `SELECT *` of the last 50 rows of `governance.erasure_audit_log`. The log holds `customer_id` and may hold other PII.
- src/eurostream/api.py:156 — `GET /health` returns `erasure.suppressed_customers()`, the full list of erased customer IDs, with no auth. The dashboard reads this list.
- src/eurostream/api.py:419 — `GET /governance/suppression-registry` is unauthenticated and returns `customer_id` and `added_at`.
- src/eurostream/api.py:271 — `/produce`, `/stream`, `/transform`, `/quality-gate` and `/sync-turso` are all unauthenticated write or compute triggers. `/transform` mutates silver, gold and the lake. `/sync-turso` pushes local state to a cloud DB. These can be run by anyone and are a cost and abuse vector.
- src/eurostream/api.py:271-300 — `POST /produce` emits synthetic events into the same bus and warehouse path as real data. Demo data can mix with production data. Amounts are `random.uniform(900, 2000)` and `random.uniform(700, 1500)`. The countries `DE`/`NL`/`FR` and the `cust_burst_{random 100-999}` customer ID are hard-coded literals.
- src/eurostream/api.py:271 — `/produce` reports `events_produced=events` and increments the metric by `events*3`. The burst and anomaly events are not counted, so the numbers are inconsistent.
- src/eurostream/api.py:127-152 — `/stats` falls back silently to Hugging Face parquet (`hf://datasets/swadhinbiswas/eustream`, tables `silver/orders`, `gold/customer_360`, `gold/order_facts`, `gold/fraud_summary`) when `total_rows == 0`. The only signal is `source: "hf_lake"`. Failures are swallowed, and an `except` block at :120 uses `pass`.
- src/eurostream/api.py:152 — In the fallback, the `silver/orders` count is stored under `silver_customers`. That is a mislabelled mapping.
- src/eurostream/api.py:80-117 — `/stats` hides query failures behind `logger.debug`. A missing table gives partial or zero stats rather than an error. `total_rows` sums only `bronze_orders`, `bronze_clicks`, `bronze_payments`, `silver_customers` and `gold_customers`. It omits the other tables, so the label is misleading.
- src/eurostream/api.py:443-450 — `GET /fraud_alerts` catches any exception on `bronze.fraud_alerts` and returns `gold.fraud_summary` rows instead. The two sources have different schemas and the response does not say which one it is.
- src/eurostream/api.py:350,374 — Tool endpoints return HTTP 200 with `{"status":"error","message":"Bus not initialized"}` and similar instead of an error status. `/sync-turso` echoes the env var names `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` and returns `warehouse.turso.http_endpoint` (also at the `/turso/status` return).
- src/eurostream/api.py:454 — `/sync-turso` uses `settings.hf_repo if hasattr(settings, "hf_repo") else "swadhinbiswas/eustream"`. It falls back to a hard-coded third-party dataset, and `seed_from_lake` defaults to true. This can overwrite local state from an external dataset. Table counts fall back to 0 on any exception, which hides failures.
- src/eurostream/api.py:476 — `/turso/status` is unauthenticated and returns the endpoint URL and counts. On error it returns 0 counts.
- src/eurostream/api.py:520-570 — Import-time side effects. `app = bootstrap()` runs at module level and creates `data_dir`, opens the SQLite bus (or Kafka) and the `Warehouse`. It also connects to Turso and builds `Metrics` and `ErasureService`, which holds a consumer on `erasure_requests`. `logging.basicConfig` also runs at import.
- src/eurostream/api.py:548 — One `Warehouse` and one bus are shared across all requests. The endpoints are sync `def`, so FastAPI runs them in a threadpool and they use the same DuckDB or SQLite connection concurrently. This is a concurrency risk. The `/stream` and `/transform` consumers all use fixed group ids (`api-fraud-stream`, `api-bronze-ingest`), so concurrent calls conflict.
- src/eurostream/api.py:548 — Kafka failure falls back silently to the SQLite bus (`logger.warning` only). A production deployment could run on the wrong backend without noticing.
- src/eurostream/api.py:358-366 — `/transform` caps bronze ingest at 1000 records per topic per call (`len(records) >= 1000`), with `poll(0.05)`. Larger backlogs are left unprocessed with no warning. `pii_scan` samples only 200 `bronze.orders` rows (`bronze_rows("orders", 200)`). Unregistered PII in other tables or beyond the sample is not detected. On first run it auto-generates the PII manifest from the data, so there is no governed baseline.
- src/eurostream/api.py:337 — `pii_salt=settings.pii_salt` is passed to the silver build. Its source and default were not read. The API's pseudonymisation depends on that salt.
- src/eurostream/api.py:112 — The lineage file `settings.data_dir / "lineage.jsonl"` is read in full on every `/stats` call (`read_text().strip().splitlines()`). Only the last line, cut to 400 chars, is used. That is a performance risk as the file grows.
- src/eurostream/dashboard.py:213 — The dashboard shows `'124.50'` when `c.total_spend_eur` is falsy and `'62.25'` when `c.avg_order_value_eur` is falsy. `total_orders||1` at :212 does the same. These are demo literals that trace to no query, and a legitimate 0 shows as fake values.
- src/eurostream/dashboard.py:97 — `Lake: <b>6 Parquet</b>` is a hard-coded literal, not derived from the lake.
- src/eurostream/dashboard.py:250 — The default text `'suppression, warehouse, lake'` shows as "Layers touched" when the response has none. This differs from the API's own "6-layer" wording.
- src/eurostream/dashboard.py:383 — `apiUrl` falls back to `http://localhost:7860` when the origin has no port. The dashboard is also served at `/` and `/dashboard` without auth, and loads Tailwind, Alpine and FontAwesome from CDNs at runtime.
- src/eurostream/dashboard.py:84,96,179 — The dashboard KPIs fall back across sources: `stats.total_rows || (bronze sums)`, and `stats.gold_customers || customers.length || 0`. These produce silent zeros or sample-size counts, so `customers.length` is capped at 100 by the `?limit=100` fetch.
- src/eurostream/dashboard.py:442-466 — `fetchTelemetry` polls `/health`, `/stats` and `/fraud_alerts?limit=50` every 6000 ms

## Findings

- `src/eurostream/api.py:44` — CORS is wide open (allow_origins=['*'] with allow_credentials=True) and no endpoint in the file has authentication.
- `src/eurostream/api.py:162` — POST /erasure-requests is unauthenticated and can enqueue or synchronously execute an erasure for any customer_id, with requested_by hard-coded as 'dsar@eurocart.eu'.
- `src/eurostream/api.py:186` — POST /erase/{customer_id} is unauthenticated and synchronously runs the destructive erasure cascade.
- `src/eurostream/api.py:217` — GET /verify-erasure/{customer_id} interpolates the raw path parameter into SQL f-strings (SQL injection) and is unauthenticated.
- `src/eurostream/api.py:433` — GET /gold/customer-360 is unauthenticated and returns SELECT * from gold.customer_360 with no masking in the endpoint.
- `src/eurostream/api.py:407` — GET /health returns the full list of suppressed (erased) customer IDs without authentication.
- `src/eurostream/api.py:127` — /stats silently falls back to a hard-coded hf://datasets/swadhinbiswas/eustream parquet lake when local total_rows is 0, and maps silver/orders counts onto silver_customers.
- `src/eurostream/api.py:443` — GET /fraud_alerts silently falls back to gold.fraud_summary (a different schema) on any exception reading bronze.fraud_alerts.
- `src/eurostream/api.py:570` — app = bootstrap() runs at import time, creating data_dir, opening the event bus, Warehouse, Turso connection and an erasure consumer, with one shared Warehouse/bus across all threadpooled requests.
- `src/eurostream/api.py:271` — POST /produce is an unauthenticated endpoint that injects random synthetic orders, clicks and payments into the live bus, and under-reports the metric (events*3 excludes burst and anomaly events).
- `src/eurostream/api.py:454` — /sync-turso defaults seed_lake=True and falls back to the hard-coded third-party dataset 'swadhinbiswas/eustream' to seed local state before pushing to Turso, unauthenticated.
- `src/eurostream/api.py:341` — POST /transform caps bronze ingest at 1000 records per topic and PII-scans only 200 bronze.orders rows, auto-generating the PII manifest on first run, so unregistered PII can go undetected.
- `src/eurostream/dashboard.py:213` — Customer 360 table shows hard-coded demo values '124.50' and '62.25' (and total_orders||1) when spend/AOV are falsy, tracing to no query.
- `src/eurostream/dashboard.py:97` — The Lake card shows a hard-coded literal '6 Parquet' not derived from the lake.
- `src/eurostream/portal.py:6` — build_portal_html is a static marketing shell with no data reads, and no route in api.py uses it.
