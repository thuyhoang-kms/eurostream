# Transform: warehouse, orchestration, quality, contracts, lineage

Status: ok

Result: Partial. Warehouse, quality, orchestration and contracts.py were read in full. lineage.py, governance/contracts.json and config.py were not read, because the read budget ran out. I did not see the concrete DAG task list or the config defaults. Line numbers are counted by hand from windows that had no line prefixes, so treat them as ±2. Lines marked `~` are estimates.

Findings:

**1. Source systems**
- `src/eurostream/warehouse.py:123` — `self.conn = duckdb.connect(str(self._path))`. The primary store is a DuckDB file at `db_path`. The path value comes from a caller or config that I did not read.
- `warehouse.py:130,134` — `os.getenv("TURSO_DATABASE_URL")` and `os.getenv("TURSO_AUTH_TOKEN")`, with `EUROSTREAM_`-prefixed fallbacks. A secondary Turso/libSQL store is dual-written. The URL and token come from environment variables or constructor arguments, and I copied neither.
- `warehouse.py:~790-815` (`export_lake`) — `COPY {table} TO '{safe}' (FORMAT PARQUET)`. The lake is written to `<lake_root>/<schema>/<name>.parquet`. `lake_root` is a caller argument.
- `warehouse.py:~215` (`seed_from_lake`) — `hf_base = f"hf://datasets/{hf_repo}"`, default repo `swadhinbiswas/eustream`. The remote lake is Hugging Face Parquet, read only when a local table is empty.

**2. Data objects**

The write and read functions for each table are in section 5. Hash columns hold salted SHA-256 values, not clear text.

| Table | Line | Layer | PII | Key |
|---|---|---|---|---|
| `bronze.orders` | 32 | bronze | `email`, `iban` in clear text, plus `customer_id` | `event_id` PK |
| `bronze.clicks` | 37 | bronze | `ip_address`, `customer_id`, `session_id` | `event_id` PK |
| `bronze.payments` | 41 | bronze | `iban`, `customer_id` | `event_id` PK |
| `bronze.fraud_alerts` | 46 | bronze | `customer_id` only | none; plain INSERT |
| `silver.customers` | 53 | silver | `email_hash`, `iban_hash`, `name_hash` (always NULL) | `customer_id` PK |
| `silver.orders` | 59 | silver | `customer_id` | `order_id` PK |
| `silver.payments` | 63 | silver | `customer_id` | `payment_id` PK |
| `gold.customer_360` | 70 | gold | `customer_id` | `customer_id` PK |
| `gold.order_facts` | 76 | gold | `customer_id` | `order_id` PK |
| `gold.fraud_summary` | 80 | gold | `customer_id` | (`customer_id`, `rule`) PK |
| `governance.erasure_audit_log` | 87 | governance | `customer_id` | none |
| `governance.pii_manifest` | 91 | governance | none | none |
| `governance.data_quality_runs` | 94 | governance | none | none |
| `governance.suppression_registry` | 97 | governance | `customer_id` | `customer_id` PK |
| `governance.watermarks` | 100 | governance | none | `pipeline` PK (values `silver`, `gold`) |
| `governance.lineage_events` | 103 | governance | none | none |

- Lake files are `silver/{customers,orders,payments}.parquet` and `gold/{customer_360,order_facts,fraud_summary}.parquet`. The list is `LAKE_EXPORT_TABLES` (~`warehouse.py:780`).
- Two silver columns are extra: `silver.customers.erased` (`warehouse.py:57`, default FALSE) and `dedup_count` on orders and payments. `dedup_count` is always written as 1.
- Gold has two columns that mirror each other: `marketing_consent` and `consents_marketing` (`warehouse.py:73-74`).

**3. Workloads**
- `load_bronze_from_records`: loads bus records into bronze (~`warehouse.py:370`).
- `append_order`, `append_click`, `append_payment`, `ingest_fraud_alerts`: write to bronze. Each also dual-writes to Turso.
- `build_silver` (full rebuild) and `build_silver_incremental`.
- `build_gold` (full rebuild) and `build_gold_incremental`.
- `export_lake`, `seed_from_lake`, `sync_all_to_turso`.
- `save_manifest`, `record_dq` and `add_suppressed` write governance tables.
- `DataQualityEngine.run_all` (`quality.py:47`) runs these checks in order:
  1. uniqueness of `gold.customer_360.customer_id`
  2. uniqueness of `gold.order_facts.order_id`
  3. PII-not-clear on `silver.customers` (`email_hash`, `iban_hash`)
  4. consent gating
  5. referential integrity of `order_facts.customer_id` against `customer_360`
- `DAG.run` (`orchestration.py`): topological order via `_order`, which raises `DAGRunError` on a cycle, an unknown dependency or a duplicate `task_id`. It runs sequentially, never in parallel.
- `orchestration.py:35` — `max_retries: int = 1`. That gives two attempts per task with a 0.2 s sleep between. After the retries are used up, the whole DAG raises `DAGRunError`.
- The concrete task list, task names and schedule were not in my files.
- Watermarks: a `silver` watermark is set from `max(occurred_at)` of `bronze.orders`. A `gold` watermark is set from `max(last_seen)` of `silver.customers`.

**4. Business rules**
- Silver orders dedup, ~`warehouse.py:508`: `row_number() OVER (PARTITION BY order_id ORDER BY occurred_at) rn ... WHERE rn = 1`.
  - Meaning: keep the earliest event per order. Ties are not broken. Not config-driven.
- Silver payments dedup, ~`warehouse.py:521`: same pattern, partitioned by `payment_id`.
  - Meaning: keep the earliest event per payment, so later status changes (for example a refund) are dropped. Not config-driven.
- Silver customers, `warehouse.py:492-496`:
  - `sha256('{salt}:' || arg_max(email, occurred_at))`: the hash uses the latest email and IBAN.
  - `min(country)`: the country is the alphabetically smallest value, not the latest or most common.
  - `bool_and(marketing_consent)`: a customer is consented only if every order carries consent.
  - `min(occurred_at), max(occurred_at)`: first and last seen.
  - Only orders feed customers.
  - `name_hash` is hard-coded NULL (~`warehouse.py:494`).
  - The salt comes from `PII_SALT` in `config.py`. The default was not read.
- Incremental Silver, ~`warehouse.py:635`: `SELECT DISTINCT customer_id FROM bronze.orders WHERE occurred_at > ?`.
  - Meaning: only customers with orders newer than the `silver` watermark are rebuilt.
- Incremental Silver orders and payments, ~`warehouse.py:665,676`: `INSERT OR IGNORE INTO silver.orders ... WHERE occurred_at > ?`.
  - Meaning: new rows are inserted, and existing keys are never updated.
- `build_silver_incremental` return, ~`warehouse.py:697`: `{"customers": len(affected), "orders": 0, "payments": 0}`.
  - Meaning: the reported order and payment counts are always 0.
- Gold `customer_360`, ~`warehouse.py:545-560`:
  - `COUNT(DISTINCT o.order_id)` gives total orders.
  - `COALESCE(SUM(o.amount_eur),0)` gives total spend.
  - `COALESCE(AVG(o.amount_eur),0)` gives average order value.
  - `COALESCE(f.fraud_flag, FALSE)` gives the fraud flag, which is true when any fraud alert exists, whatever the severity.
  - The joins are LEFT, so customers with no orders still appear. Nothing is rounded.
  - Amounts are `amount_eur` DOUBLE. There is no currency conversion in these files, although `bronze.orders` carries a `currency` column.
  - Silver does not carry `currency` forward.
- Gold `fraud_summary`, ~`warehouse.py:574`: `COUNT(*) as alert_count, MAX(alert_ts) as last_alert ... GROUP BY customer_id, rule`.
- Gold `order_facts`: a straight copy of `silver.orders`, with no filter on payment status.
- Incremental Gold, ~`warehouse.py:704-706`: `silver.customers WHERE last_seen > ? UNION ... bronze.fraud_alerts WHERE alert_ts > ?`.
  - Meaning: customers touched since the `gold` watermark are recomputed.
- Incremental `order_facts`, ~`warehouse.py:742-744`: `INSERT OR IGNORE INTO gold.order_facts ... WHERE occurred_at > ?`.
- Bronze, `warehouse.py:~250+`: `INSERT OR IGNORE INTO bronze.orders` on the `event_id` PK.
  - Meaning: a repeated `event_id` is dropped silently.
- `load_bronze_from_records`:
  - Records with an unparseable payload, the wrong `event_type`, or a model validation failure are skipped with a bare `except` and no log or dead-letter.
  - The `event_type` values are `order_placed`, `page_click` and `payment_processed`.
- Quality: all checks are recorded through `record_dq`. The thresholds are exact:
  - `quality.py:67` — uniqueness fails if any duplicate gro

## Findings

- `src/eurostream/warehouse.py:123` — Primary store is a DuckDB file via duckdb.connect(str(self._path)); single-writer engine with Turso dual-write to work around it.
- `src/eurostream/warehouse.py:32` — bronze.orders stores email and iban in clear text (no masking at rest), and bronze is synced to Turso.
- `src/eurostream/warehouse.py:508` — Silver orders dedup keeps earliest row per order_id: row_number() OVER (PARTITION BY order_id ORDER BY occurred_at) with no tie-breaker.
- `src/eurostream/warehouse.py:521` — Silver payments dedup keeps earliest row per payment_id, so later status changes are dropped.
- `src/eurostream/warehouse.py:496` — silver.customers marketing_consent is bool_and across all orders, and country is min(country), not the latest value.
- `src/eurostream/warehouse.py:635` — Incremental Silver selects customers with occurred_at > watermark, on event time; late or out-of-order events with older occurred_at are never processed.
- `src/eurostream/warehouse.py:665` — Incremental silver.orders uses INSERT OR IGNORE filtered by occurred_at > watermark, so corrected orders are never updated.
- `src/eurostream/warehouse.py:697` — build_silver_incremental always returns orders: 0 and payments: 0 regardless of rows inserted.
- `src/eurostream/warehouse.py:543` — build_gold does DELETE FROM gold.customer_360 then INSERT in one execute with no explicit transaction (full rebuild, non-atomic).
- `src/eurostream/warehouse.py:706` — Incremental Gold compares the gold watermark (derived from silver last_seen) against bronze.fraud_alerts.alert_ts, mixing two clocks.
- `src/eurostream/warehouse.py:486` — Salt is interpolated into SQL by f-string (only single quotes escaped) in the build_silver sha256 expression.
- `src/eurostream/quality.py:47` — run_all records results and returns a DQReport without raising, although the class docstring says checks fail the DAG; enforcement is not in this file.
- `src/eurostream/quality.py:107` — Consent gating check compares consents_marketing to marketing_consent, which are both written from c.marketing_consent in the gold build, so it cannot fail.
- `src/eurostream/orchestration.py:35` — DAG max_retries defaults to 1 (two attempts, 0.2s sleep); a task failing after retries raises DAGRunError and aborts the run.
