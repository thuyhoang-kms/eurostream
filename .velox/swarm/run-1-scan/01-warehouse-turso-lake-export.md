# warehouse + turso + lake export

Status: ok

Result: Partial. I read `warehouse.py` and `turso.py` in full. The budget ran out before `config.py`, `lineage.py`, `orchestration.py`, `models.py`, `types.py` and `cli.py`. The read output had no line numbers, so locators below are file plus function or symbol name, and no line numbers are claimed.

Findings:
- `src/eurostream/warehouse.py` (`build_silver_incremental`, `build_gold_incremental`) — The incremental `silver.orders`/`silver.payments` insert filters `occurred_at > watermark` and uses `INSERT OR IGNORE`. The silver watermark is only `max(bronze.orders.occurred_at)`, so late-arriving orders and any payments older than it are skipped for good. Payments never move the watermark. [high, data_quality, transform]
- `warehouse.py` (`build_silver_incremental` return value) — It reports `{"orders": 0, "payments": 0}` regardless of what it inserted, so the counts are misleading. [low, logic, ops]
- `warehouse.py` (`build_silver`, `build_gold`) — These are full rebuilds: `DELETE FROM` then `INSERT ... SELECT` over all of bronze, and every table is re-synced to Turso each run. [medium, cost, transform]
- `warehouse.py` (`build_silver`) — Delete-then-insert runs as multi-statement strings with no explicit transaction, so a failure mid-run can leave an empty silver table. The incremental path does the same with its DELETE and INSERT. [medium, data_quality, transform]
- `warehouse.py` (`build_silver`) — Customer attributes are `min(country)` and `bool_and(marketing_consent)`. `bool_and` makes a customer non-consenting if any order has consent false. `min(country)` is an arbitrary alphabetical pick. `name_hash` is always NULL. [medium, logic, transform]
- `warehouse.py` (`build_gold`) — `silver.customers.erased` is never set by the build and is not copied into gold, so the build does not itself exclude erased customers. A rebuild from bronze re-creates customers unless bronze rows were deleted. Whether erasure reaches bronze is unverified. [high, governance, transform]
- `warehouse.py` (`build_gold_incremental`) — `INSERT OR IGNORE INTO gold.order_facts` never updates existing rows. Gold order facts only ever pick up new rows. [medium, logic, transform]
- `warehouse.py` (`build_gold`, `build_gold_incremental`) — The `fraud_flag` subquery is `COUNT(*) > 0` over all `bronze.fraud_alerts`, with no time window. A customer is flagged forever. `LEFT JOIN`s to orders and fraud alerts keep customers with no orders, with total_spend 0 via COALESCE. `consents_marketing` duplicates `marketing_consent`. [low, logic, transform]
- `warehouse.py` (`CREATE_BRONZE`, `append_order`, `append_payment`, `append_click`, `load_bronze_from_records`) — `bronze.orders` stores `email` and `iban` in clear text, `bronze.payments` stores `iban`, and `bronze.clicks` stores `ip_address`. The same values are copied in clear text to Turso, a shared cloud store. [high, security, store]
- `src/eurostream/turso.py` (`TURSO_DDL`) — The Turso copy has no `silver`/`gold` PII hashing difference, but bronze PII sits in a remote database. See the finding above. [high, security, store]
- `warehouse.py` (`load_bronze_from_records`) — Bare `except Exception: continue` silently drops records that fail JSON decode or model validation. The records are not counted, quarantined or logged. [high, data_quality, ingest]
- `warehouse.py` (`load_bronze_from_records`, `append_*`) — `INSERT OR IGNORE` on `event_id` silently drops duplicates, and clicks have no downstream consumer in silver or gold. `load_bronze_from_records` has no `fraud_alerts` mapping. [medium, data_quality, ingest]
- `warehouse.py` (`append_*`, `ingest_fraud_alerts`, `set_watermark`, `add_suppressed`, `record_dq`, `save_manifest`) — Every Turso write is wrapped in `except ... logger.debug`, so a failed dual-write is invisible. DuckDB and Turso drift apart with no reconciliation. `ingest_fraud_alerts` has no key, so retries insert duplicates and inflate `alert_count`. [high, data_quality, store]
- `warehouse.py` (`query`, `scalar`, `count_rows`, `bronze_rows`, `get_watermark`, `suppressed_ids`) — Reads fall back to Turso when the DuckDB result is empty or zero. After an erasure or a legitimate empty table, stale remote rows can be served. `get_watermark` returns 0.0 when the row is missing, which triggers a full reprocess. [medium, logic, serving]
- `warehouse.py` (`seed_from_lake`) — It reads Parquet from the public HuggingFace dataset `swadhinbiswas/eustream` and runs `INSERT OR IGNORE ... SELECT *`. Column order is positional, and a bare `except` swallows failures. The default repo name is hard-coded. [medium, dependency, ingest]
- `warehouse.py` (`export_lake`, `LAKE_EXPORT_TABLES`) — It exports silver and gold to `lake_root/<schema>/<table>.parquet` with `COPY ... TO`. Output is a full overwrite snapshot with no partitioning. `silver.customers` carries `email_hash`/`iban_hash` (salted SHA-256), which are pseudonymous, not anonymous. The destination is the HuggingFace lake that `seed_from_lake` reads, probably public (inferred). The upload step is in `cli.py`, which I did not read. [high, governance, serving]
- `warehouse.py` (`build_silver`, `build_silver_incremental`) — `PII_SALT` from `eurostream.config` is interpolated into SQL by string formatting, with only quote-escaping. I could not check the salt's default or where it comes from. [medium, security, transform]
- `warehouse.py` (`Warehouse.__init__`, `turso_url`/`turso_token`) — `__init__` calls `Turso init_schema()` and `Path.mkdir` and connects to DuckDB. Constructing the object has network side effects. [low, ops, store]
- `warehouse.py` (`Warehouse.conn`) — One shared DuckDB connection is used by all methods with no lock. `TursoClient` shares one `httpx.Client` and one native connection with no lock. [medium, concurrency, store]
- `turso.py` (`_rewrite_sql_for_turso`) — A regex quotes `schema.table` names for SQLite. It uses the managed-table list, and `bronze.fraud_alerts` etc. rely on it. The Turso DDL stores booleans as INT and timestamps as REAL, so types differ from DuckDB. [low, logic, store]
- `warehouse.py`, `turso.py` — Every timestamp column (`occurred_at`, `ingested_at`, `alert_ts`, ...) is a DOUBLE epoch from `time.time()`. This is timezone-naive epoch and loses TIMESTAMP typing. [low, data_quality, store]
- `warehouse.py`, `turso.py` — DuckDB-specific and SQLite-specific SQL that will not port to Spark/Delta as written: `INSERT OR IGNORE`, `INSERT OR REPLACE`, `arg_max`, `bool_and`, `sha256()`, `COPY ... TO PARQUET`, `read_parquet('hf://...')`, `information_schema` use, and string-formatted multi-statement `DELETE; INSERT;` scripts. Primary keys are declared but not enforced in Delta. [medium, scope, transform]

1. SOURCE SYSTEMS (from `warehouse.py` and `turso.py` only)
- DuckDB file: path is the `db_path` argument of `Warehouse.__init__`. The default and env var are in `config.py`/`cli.py`, not read. No host or port.
- Turso (libSQL): engine libSQL/SQLite, host taken from the URL given by `TURSO_DATABASE_URL` or `EUROSTREAM_TURSO_DATABASE_URL`. Token env vars are `TURSO_AUTH_TOKEN` and `EUROSTREAM_TURSO_AUTH_TOKEN`. The client converts `libsql://` to `https://` and calls `<url>/v2/pipeline` over HTTP, with the native `libsql`/`libsql_experimental` package tried first. Port is the URL default. The database name is not set in code.
- HuggingFace dataset `swadhinbiswas/eustream` (in `seed_from_lake`): read via `hf://datasets/...` paths for silver and gold Parquet.
- Local Parquet lake directory: the `lake_root` argument of `export_lake`.
- Message bus (`eurostream.bus`, `Record`): consumed by `load_bronze_from_records`. Not read.
- No hard-coded credential found in the two files read.

2. DATA SURFACES
All DDL is in `warehouse.py` (`CREATE_BRONZE`, `CREATE_SILVER`, `CREATE_GOLD`, `CREATE_GOVERNANCE`), with mirrors in `turso.py` `TURSO_DDL`. The writer is the `Warehouse` method named. Erasure reach is unknown for every row because I did not read `governance/erasure

## Findings

- `src/eurostream/warehouse.py` — build_silver_incremental/build_gold_incremental filter occurred_at > watermark with INSERT OR IGNORE, and the silver watermark is max(bronze.orders.occurred_at) only, so late-arriving or out-of-order orders/payments are permanently skipped.
- `src/eurostream/warehouse.py` — load_bronze_from_records swallows JSON-decode and model-validation errors with bare except/continue, silently dropping invalid records with no count or quarantine.
- `src/eurostream/warehouse.py` — bronze.orders stores email and iban, bronze.payments stores iban, and bronze.clicks stores ip_address in clear text, and the same values are dual-written to Turso.
- `src/eurostream/warehouse.py` — All Turso writes in append_*, ingest_fraud_alerts, set_watermark, add_suppressed and record_dq are wrapped in except with logger.debug, so dual-write failures are silent and DuckDB and Turso can drift.
- `src/eurostream/warehouse.py` — export_lake writes silver/gold Parquet including email_hash and iban_hash (salted SHA-256, pseudonymous), and seed_from_lake reads the public HuggingFace dataset swadhinbiswas/eustream, so pseudonymised data is probably published.
- `src/eurostream/warehouse.py` — build_silver and build_gold do DELETE then INSERT as multi-statement strings with no explicit transaction, so a mid-run failure can leave an empty table; this is a full rebuild with no incremental safety.
- `src/eurostream/warehouse.py` — ingest_fraud_alerts inserts into bronze.fraud_alerts, which has no primary key, so retries insert duplicates and inflate gold.fraud_summary alert_count.
- `src/eurostream/warehouse.py` — Reads in query, scalar, count_rows, bronze_rows and get_watermark fall back to Turso when the DuckDB result is empty or zero, which can serve stale rows after erasure or for a legitimately empty table.
- `src/eurostream/warehouse.py` — DuckDB-specific SQL (INSERT OR IGNORE, INSERT OR REPLACE, arg_max, bool_and, sha256, COPY TO PARQUET, read_parquet hf://) and unenforced primary keys will not port directly to Spark/Delta.
- `src/eurostream/turso.py` — TursoClient shares one httpx.Client and one native libsql connection across calls without locking, and its DDL stores booleans as INT and timestamps as REAL epoch, so types differ from DuckDB.
