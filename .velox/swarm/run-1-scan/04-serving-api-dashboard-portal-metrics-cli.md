# Serving: API, dashboard, portal, metrics, CLI

Status: ok

Result: Partial. api.py and dashboard.py were read in full. portal.py, metrics.py, cli.py and config.py were not read because the read budget ran out. The file reads returned no line numbers, so I locate each item by route or function name with a verbatim excerpt and give no `path:line` values.

Findings:
- **api.py, route `POST /erasure-requests` — erasure queued with no worker in this process.** When `sync` is false it returns `"status": "queued"`. `bootstrap()` only creates `bus.consumer("erasure_requests", "api-worker", ...)` and starts no loop. I saw no code in these two files that consumes the queue, so a queued erasure may never run. Severity: High. Category: erasure queued without a worker.
- **api.py, routes `POST /erase/{customer_id}`, `POST /erasure-requests` and `/produce`, `/stream`, `/transform`, `/quality-gate`, `/sync-turso` — no auth.** No auth dependency appears anywhere in the file. Anyone can trigger erasure, which is irreversible, and anyone can run pipeline workloads and a Turso sync. `requested_by="dsar@eurocart.eu"` is hard-coded, so the audit trail does not record who made the request. Severity: Critical. Category: unauthenticated destructive endpoint.
- **api.py, `CORSMiddleware` — CORS wide open.** The excerpt is `allow_origins=["*"], allow_credentials=True, allow_methods=["*"]`. Combined with the missing auth, any web page can call the erasure endpoints. Severity: High. Category: CORS.
- **api.py, routes `GET /verify-erasure/{customer_id}`, `GET /gold/customer-360?search=`, `GET /governance/erasure-audit`, `GET /governance/suppression-registry`, `GET /health` — unauthenticated PII and SQL injection.**
  - `/verify-erasure` interpolates the path parameter straight into SQL: `f"SELECT count(*) FROM gold.customer_360 WHERE customer_id='{customer_id}'"`. That is SQL injection, marked `# noqa: S608`.
  - `/gold/customer-360` runs `SELECT * FROM gold.customer_360` and only escapes `'` in `search`.
  - `/health` returns the full `"suppressed": erasure.suppressed_customers()` list. That exposes the IDs of erased customers without auth.
  - Severity: High. Category: SQL injection and PII exposure.
- **api.py, `GET /stats` — silent fallback to the Hugging Face dataset.** Condition: `if stats["total_rows"] == 0`. It reads `hf://datasets/swadhinbiswas/eustream/{silver/orders,gold/customer_360,gold/order_facts,gold/fraud_summary}.parquet` through `duckdb.query` and sets `stats["source"]="hf_lake"`. Per-table errors are swallowed with `except Exception: pass`. Two further problems:
  - The key mapping is wrong: `("silver/orders","silver_customers")` counts the orders file and labels it as the customer count.
  - The `try` around the warehouse counts catches errors at debug level only, so the dashboard shows zeros or foreign data with no error.
  - Severity: Medium. Category: silent fallback and untraceable numbers.
- **api.py, `GET /fraud_alerts` — silent fallback between tables.** If `bronze.fraud_alerts` fails, it returns `gold.fraud_summary ... ORDER BY last_alert DESC`. Those rows have a different shape from the `alert_ts` rows the UI expects. Severity: Low. Category: silent fallback.
- **api.py, `app = bootstrap()` — import-time side effects.** The excerpt is `app = bootstrap()`, with `logging.basicConfig` also running at import. `bootstrap()` creates `data_dir`, opens the SQLite or Kafka bus, opens `Warehouse(...)` with Turso url and token, and opens `Metrics`. Importing the module therefore opens the stores and possibly the network. Severity: Medium. Category: import-time side effect.
- **api.py, `create_app` — one shared `warehouse`, `bus`, `erasure` and `metrics` across all requests.** Sync handlers run in a threadpool, and no lock is visible. Severity: Medium. Category: shared connection across threads.
- **api.py, routes `POST /produce`, `/stream`, `/transform` — failures returned as HTTP 200.** They return `{"status": "error", "message": "Bus not initialized"}` with a 200 status. `/produce` and `/transform` also write synthetic data into the production bus and warehouse, and `/transform` ends with `warehouse.export_lake(settings.lake_root)`. Severity: Medium. Category: demo endpoints mixed with production.
- **api.py, `GET /gold/customer-360` — backend suppression not applied.** The query is `SELECT * FROM gold.customer_360` with no join to `governance.suppression_registry` and no consent filter. It relies only on the erasure cascade having deleted rows. `/fraud_alerts` and `/gold/fraud_summary` also have no suppression filter. Severity: Medium. Category: filter applied in backend but not in API.
- **dashboard.py, `fetchTabData` — tab names do not match.** It handles `'medallion'`, `'quality'` and `'metrics'`, but the tabs are named `warehouse` and `ops`. As a result `customers`, `dq` and `rawMetrics` are never loaded. The Customer 360 table, the data-quality list and the metric counters stay empty. The consent chart's literal fallback values then show up as real numbers. Severity: Medium. Category: broken or placeholder UI.
- **dashboard.py, `renderCharts` and the Customer 360 table — numbers that trace to no query.**
  - Ingest chart: `this.stats.bronze_orders || 65`, `|| 50`, `|| 75`. The "T-4…Now" series are fixed multiples of one count, such as `bo*0.6` and `bo*0.75`. The line is synthetic, not a time series.
  - Fraud chart: `counts.VELOCITY || 4, counts.GEO_MISMATCH || 2, counts.AMOUNT_ZSCORE || 1`.
  - Consent chart: `|| 18` and `|| 6`, and `Math.max(1, ...)` for the opt-out count.
  - Customer table: `c.total_spend_eur ? ... : '124.50'`, `'62.25'` and `c.total_orders||1`.
  - Erasure result panel: `latency_seconds || '0.04'`.
  - Severity: Medium. Category: numbers not traceable to data.
- **dashboard.py, static card labels — hard-coded and inconsistent.**
  - The "Fraud Caught" card has the badge `300s Win` and the text `SLA: <b>60s</b>`. The API returns `settings.erasure_sla_seconds`, so the card does not follow that setting.
  - The Gold card shows `Lake: 6 Parquet`.
  - The fraud filter labels hard-code `VELOCITY (> 5 payments / 300s)` and `AMOUNT_ZSCORE (> 3.0 std dev)`, although the API uses `settings.fraud_velocity_threshold`.
  - After a transform the banner says `Quality Gate: OK` without reading the response. The `/transform` response is never checked.
  - Severity: Low. Category: untraceable numbers.
- **dashboard.py, the `<head>` — third-party CDN dependencies.** It loads cdn.tailwindcss.com, jsdelivr (alpinejs, chart.js) and cdnjs font-awesome with no integrity hashes. Severity: Low. Category: external dependency.

Inventory and rules (all from api.py unless stated):

1. Sources read:
   - The DuckDB warehouse through `warehouse.scalar` and `warehouse.query`: `bronze.{orders,clicks,payments,fraud_alerts}`, `silver.{customers,orders,payments}`, `gold.{customer_360,order_facts,fraud_summary}`, `governance.{erasure_audit_log,data_quality_runs,suppression_registry,watermarks}`.
   - Turso, through `warehouse.turso.scalar` and `http_endpoint`. The URL and token come from `settings.turso_database_url` and `settings.turso_auth_token`.
   - The Hugging Face dataset `swadhinbiswas/eustream`.
   - The local file `settings.data_dir/lineage.jsonl` (last line, `[:400]`).
   - The event bus (SQLite `events.db`, or Kafka).
   - `metrics.snapshot()` and `metrics.render_prometheus()`.
2. Routes:

| Route | Reads / does | Returns |
|---|---|---|
| `GET /` and `GET /dashboard` | HTML from `get_dashboard_html()` | The dashboard page |
| `GET /api` | Static index | Route listing |
| `GET /stats` | Counts per table, `get_watermark("silver"/"gold")`, the lineage tail, the suppressed count | A stats dict. `total_rows` sums `bronze_orders`, `bronze_clicks`, `bronze_payments`, `silver_customers` and `gold_customers` |
| `POST /erasure-requests` | `erasure.request_erasure`; runs `execute` if `sync` is true | `status` is `queued` or `completed`, plus the confirmation hash |
| `POST /erase/{customer_id}` | Runs the synchronous ca

## Findings

- `src/eurostream/api.py` — POST /erasure-requests returns status 'queued' when sync is false, but bootstrap() only creates an erasure_requests consumer and I saw no worker loop in api.py or dashboard.py that drains it.
- `src/eurostream/api.py` — POST /erase/{customer_id}, POST /erasure-requests, /produce, /stream, /transform, /quality-gate and /sync-turso have no authentication, and requested_by is hard-coded to 'dsar@eurocart.eu'.
- `src/eurostream/api.py` — CORSMiddleware is configured with allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'].
- `src/eurostream/api.py` — GET /verify-erasure/{customer_id} interpolates customer_id into SQL via f-strings (SQL injection, noqa S608), and GET /gold/customer-360 only escapes single quotes in search.
- `src/eurostream/api.py` — GET /health returns the full list of suppressed (erased) customer IDs without authentication.
- `src/eurostream/api.py` — GET /stats silently falls back to hf://datasets/swadhinbiswas/eustream parquet counts when total_rows==0, swallows per-table errors with except/pass, and maps silver/orders to the silver_customers key.
- `src/eurostream/api.py` — GET /fraud_alerts silently falls back to gold.fraud_summary (different row shape) when the bronze.fraud_alerts query raises.
- `src/eurostream/api.py` — Module-level `app = bootstrap()` opens the bus, DuckDB warehouse (with Turso url/token) and metrics store at import time.
- `src/eurostream/api.py` — A single shared warehouse, bus, erasure service and metrics instance is used by all (threadpool) request handlers with no visible locking.
- `src/eurostream/api.py` — /produce, /stream and /transform return {'status':'error',...} with HTTP 200 when bus or warehouse is None, and /produce and /transform write synthetic data to the same stores.
- `src/eurostream/api.py` — GET /gold/customer-360, /fraud_alerts and /gold/fraud_summary apply no suppression-registry or consent filter in the query; they rely on the erasure cascade having deleted rows.
- `src/eurostream/dashboard.py` — fetchTabData handles tabs 'medallion','quality','metrics' but the tabs are named 'warehouse' and 'ops', so customers, dq and rawMetrics are never loaded.
- `src/eurostream/dashboard.py` — Charts and tables use literal fallback numbers (ingest 65/50/75, fraud 4/2/1, consent 18/6, spend 124.50/62.25, latency 0.04) and the ingest series are fixed multiples of one count, not a time series.
- `src/eurostream/dashboard.py` — Static labels hard-code SLA 60s, '300s Win', 'Lake: 6 Parquet', 'VELOCITY (> 5 payments / 300s)' and a transform banner 'Quality Gate: OK' that ignores the response, instead of reading settings or results.
