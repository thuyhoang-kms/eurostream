# governance: PII, erasure, contracts, quality

Status: ok

Result: Partial. The budget ran out before I could grep the repo for bronze/silver/gold table names, `refresh_lake`, the quality-gate wiring, the CI workflows, `benchmarks/benchmark_erasure.py`, or the body of the `erase` and `contracts` CLI commands. The read tool returned no line numbers, so a locator is exact only where a grep returned it. Other items are cited by file and function. The `submit_findings` entries carry a line only where one is known. Items 1 to 6 and 8 are condensed to what I read. Gaps are marked "not covered".

Findings:
- src/eurostream/config.py:22 — The PII salt is hard-coded as a literal default. The comment at line 21 says to override it via `EUROSTREAM_PII_SALT`, and line 83 uses the literal as the setting's default. Nothing in the code I read forces an override, so a deployment that doesn't set it hashes with the public default. Severity: high. Category: security. Layer: transform.
- src/eurostream/governance/pii.py (`hash_pii`) — Unkeyed `sha256(salt:value)` is deterministic, so emails and IBANs can be re-identified by dictionary attack once the salt is known. It is also a pseudonym, not anonymization, under GDPR. Severity: high. Category: security. Layer: transform.
- src/eurostream/governance/erasure.py:247 — The audit log keeps `customer_id` in clear text in `governance.erasure_audit_log`. Line 261 repeats the insert on Turso, and the JSONL audit file (`to_dict`) also holds it. The `confirmation_hash` is `sha256(request_id:customer_id)[:16]`, truncated and unsalted. The audit data outlives the erasure it records. Severity: medium. Category: governance. Layer: ops.
- src/eurostream/governance/erasure.py:117 — `governance.suppression_registry` permanently stores the erased `customer_id`. This is a defensible suppression list, but its retention is undefined. Severity: low. Category: governance. Layer: store.
- src/eurostream/governance/erasure.py:122 — The `lake` layer is recorded as touched whenever an `on_complete` hook is wired, not when a re-snapshot is verified. The hook is `refresh_lake` (cli.py:88, api.py:639). A hook failure is only logged (erasure.py:153-157), yet the audit says "completed". This audit claim is unverified. Severity: high. Category: governance. Layer: ops.
- src/eurostream/governance/erasure.py (`_anonymize_warehouse`) — Bronze is not erased, only partly masked. `bronze.orders` gets `email` and `iban` set to `<anonymized>`, `bronze.payments` gets `iban`, and `bronze.clicks` gets `ip_address`. `customer_id`, `session_id`, `country`, `amount` and the other fields remain and still link to the person. Severity: high. Category: governance. Layer: store.
- src/eurostream/governance/erasure.py (`_anonymize_warehouse`, Turso block) — Turso cascade errors are caught and only logged as a warning. The audit record is still written as "completed" even if the remote deletes failed. Severity: high. Category: governance. Layer: store.
- src/eurostream/governance/erasure.py (`_anonymize_warehouse`) — The DuckDB `fraud_alerts` delete is guarded by `table_exists`, but the Turso delete is not. Behaviour differs between the two stores. Severity: low. Category: logic. Layer: store.
- governance/pii_manifest.json — The manifest covers only `bronze.orders.email` and `bronze.orders.iban`. `bronze.payments.iban`, `bronze.clicks.ip_address`, and `silver.customers` (`email_hash`, `iban_hash`) are not registered. Both `payment_processed.iban` and `page_click.ip_address` carry PII per `governance/contracts.json`. Severity: medium. Category: governance. Layer: ingest.
- src/eurostream/governance/pii.py (`classify_value`) — The IBAN recogniser covers 11 countries only. The NAME rule only matches title-cased two-word values, and the phone rule requires a "+". Severity: low. Category: data_quality. Layer: ingest.
- src/eurostream/api.py:141 — The API reads parquet from the public HF dataset `swadhinbiswas/eustream` (`hf_base`). The same repo is the default for the `--hf-repo` option (cli.py:445), and `warehouse.seed_from_lake` uses it (cli.py:458). Pseudonymised hashes and other customer data may be published there, and erasure only reaches it via `refresh_lake`. I did not read what `refresh_lake` does. Severity: critical (unconfirmed). Category: governance. Layer: serving.
- src/eurostream/api.py:251 — A SQL string is built by f-string interpolation of `customer_id` against `governance.erasure_audit_log`, which is an injection risk. Severity: medium. Category: security. Layer: serving.
- src/eurostream/api.py:483 and 524 — These endpoints expose `SELECT *` from the audit log and `customer_id` from the suppression registry. Authentication was not checked. Severity: medium. Category: security. Layer: serving.
- src/eurostream/governance/erasure.py (`request_erasure`) — The default `requested_by` is a hard-coded address, `dsar@eurocart.eu`. The requester is not verified. Severity: low. Category: governance. Layer: ingest.
- src/eurostream/quality.py (`DataQualityEngine._check_pii_not_clear`) — The check samples only 50 rows (`LIMIT 50`) and covers only `silver.customers` `email_hash` and `iban_hash`. It silently skips a missing table. Severity: medium. Category: data_quality. Layer: transform.
- src/eurostream/quality.py (`DataQualityEngine.run_all`) — `run_all` only records results and returns a `DQReport`. The docstring says failure fails the DAG, but the enforcement is in the caller, which I did not read. Severity: medium. Category: governance. Layer: ops.
- src/eurostream/contracts.py (`check_against`) — Contract drift is checked only through the CLI `contracts` command (cli.py:93, :112). The docstring says CI runs it, but I did not read the CI workflows, so the claim is unverified. Severity: medium. Category: governance. Layer: ops.

**1. Erasure path** (all in `erasure.py` unless noted)
- `request_erasure` produces an `erasure_requested` event to the bus topic `erasure_requests`, keyed by `customer_id` (line 100). The API and CLI only enqueue, and the worker consumes (`run_worker`, around line 172).
- `execute` runs in this order:
  1. It adds the id to the in-memory set (line 114).
  2. It writes the durable `governance.suppression_registry` row via `warehouse.add_suppressed` (line 117) and records the `suppression_registry` layer (line 118).
  3. It calls `_anonymize_warehouse` and records the `warehouse` layer.
  4. It records the `lake` layer if `on_complete` is set (line 122).
  5. It writes the audit record, then calls the hook.
- `_anonymize_warehouse`, on DuckDB, then repeated on Turso if configured:

| Store | Action | Reached |
|---|---|---|
| `bronze.orders` | UPDATE `email`, `iban` to `<anonymized>` | true (partial) |
| `bronze.payments` | UPDATE `iban` | true (partial) |
| `bronze.clicks` | UPDATE `ip_address` | true (partial) |
| `silver.customers`, `silver.orders`, `silver.payments` | DELETE | true |
| `gold.customer_360`, `gold.order_facts`, `gold.fraud_summary` | DELETE | true |
| `bronze.fraud_alerts` | DELETE, guarded by `table_exists` on DuckDB | true |
| Turso replica of the same tables | same SQL, errors swallowed | true, unreliable |
| Streaming suppression | `suppression_check=erasure.is_suppressed` (cli.py:163, 364; api.py:326) | true (future events only) |

- Parquet lake / HF dataset: erasure_reaches null. The only link is the `on_complete=refresh_lake` hook (cli.py:88, api.py:639). I did not read it.
- Not touched by the erasure code:
  - The Kafka or sqlite bus. The `messages` table (bus/sqlite.py:12) retains past `order_placed`, `payment_processed` and `page_click` events with email, IBAN and IP. Erasure_reaches false. The `erasure_requests` event itself also holds `customer_id`.
  - The audit JSONL file and the audit table, which keep `customer_id`. Erasure_reaches false.
  - Application logs, which print `customer_id` (erasure.py:~131-157). Erasure_reaches false.
  - Any other bronze table beyond the three above (not covered).

**2. PII classification**
- The manifest `governance/pii_manifest

## Findings

- `src/eurostream/config.py:22` — PII_SALT is hard-coded as a literal default in code; comment at line 21 says to override via EUROSTREAM_PII_SALT and line 83 uses it as the setting default.
- `src/eurostream/governance/erasure.py:247` — The erasure audit log (DB table, Turso copy at line 261, and JSONL) keeps customer_id in clear text, so the audit record itself retains the erased identifier.
- `src/eurostream/governance/erasure.py:122` — The 'lake' layer is recorded as touched whenever on_complete is wired, not when a lake re-snapshot is verified; hook failures are only logged (lines 153-157) while status stays 'completed'.
- `src/eurostream/governance/erasure.py:117` — governance.suppression_registry permanently stores the erased customer_id via add_suppressed with no retention rule.
- `src/eurostream/governance/erasure.py` — _anonymize_warehouse only sets email/iban/ip_address to '<anonymized>' in bronze.orders/payments/clicks and leaves customer_id and other fields, so Bronze is pseudonymized not erased.
- `src/eurostream/governance/erasure.py` — Turso erasure cascade exceptions are caught and only logged as warnings, yet the audit is still written with status 'completed'.
- `src/eurostream/governance/pii.py` — hash_pii uses deterministic unkeyed SHA-256 of salt:value, enabling dictionary re-identification of emails/IBANs and is pseudonymization only.
- `governance/pii_manifest.json` — Manifest registers only bronze.orders.email and bronze.orders.iban; payments.iban and clicks.ip_address (PII per contracts.json) are unclassified.
- `src/eurostream/api.py:141` — API reads parquet from the public HuggingFace dataset swadhinbiswas/eustream; pseudonymized data may be published publicly and erasure reaches it only through refresh_lake (unverified).
- `src/eurostream/api.py:251` — customer_id is interpolated by f-string into SQL against governance.erasure_audit_log, an SQL injection risk.
- `src/eurostream/quality.py` — run_all only records DQ results and returns a report; enforcement of failure (docstring says fails the DAG) lives in an unread caller, and the PII-not-clear check samples only 50 rows of silver.customers.
- `src/eurostream/contracts.py` — Docstring claims CI runs check_against against contracts.json, but enforcement was only seen in the CLI contracts command (cli.py:93,112); CI wiring unverified.
