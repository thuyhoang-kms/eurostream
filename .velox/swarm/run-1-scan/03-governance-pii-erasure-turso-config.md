# Governance: PII, erasure, Turso, config

Status: ok

Result: Partial. The governance, PII, Turso and config files were read; the warehouse, lake and bus code and `benchmarks/benchmark_erasure.py` were not. The file reads returned no line numbers, so locators are file plus verbatim excerpt, and only `api.py` hits carry real line numbers.

**Findings:**
- `src/eurostream/config.py` (module constant `PII_SALT`) — hard-coded default salt: `PII_SALT = "eurostream-pii-salt"`. It is also the default of `Settings.pii_salt`. `config.py` says to override it via `EUROSTREAM_PII_SALT` in production, but nothing enforces that. Severity high, category security.
- `.env.example` — ships a placeholder salt, `EUROSTREAM_PII_SALT=change-me-in-production`. If that placeholder is copied unchanged into `.env`, it silently replaces the default. Severity medium, category security.
- `src/eurostream/governance/pii.py` (`hash_pii`) — `hashlib.sha256(f"{salt}:{value}".encode()).hexdigest()`. This is a plain salted SHA-256 with one global salt. The same input always gives the same hash, so it is linkable and brute-forceable for low-entropy inputs such as emails. It is pseudonymization, not anonymization. Severity medium, category governance.
- `src/eurostream/turso.py` (`TURSO_DDL`) — PII goes to the third-party cloud. `"bronze.orders"` has `email TEXT, iban TEXT`, `"bronze.payments"` has `iban TEXT`, and `"bronze.clicks"` has `ip_address TEXT`. All of these are raw columns in the Turso schema. Severity high, category governance. I did not read `sync_all_to_turso` in `warehouse.py`, so what it actually pushes is unconfirmed.
- `src/eurostream/governance/erasure.py` (`_anonymize_warehouse`) — erasure only anonymizes Bronze (`UPDATE bronze.orders SET email=?, iban=?`). It does not touch `customer_id`, `order_id`, `amount_eur` or `country`, and `bronze.clicks` keeps `session_id`. The customer ID stays linkable in Bronze. Severity medium, category governance.
- `src/eurostream/governance/erasure.py` — the Turso cascade swallows errors. It is wrapped in `except Exception as e: logger.warning("Turso erasure cascade error: %s", e)`, and the first failed statement aborts the remaining ones. `execute()` still records `status="completed"`, and `layers_touched` never lists Turso. Severity high, category governance.
- `src/eurostream/governance/erasure.py` — the Turso cascade is not in a transaction and has no verification. It is partial-failure prone: a cloud failure leaves PII in Turso while the audit says completed. Severity high, category governance.
- `src/eurostream/governance/erasure.py` — the `lake` layer is claimed without being done. `if self._on_complete is not None: layers.append("lake")` records the lake as touched only because a callback exists, and the callback runs after `_append_audit`. Failures in it are swallowed with `logger.exception("on_complete failed ...")`. The audit can therefore claim `lake` when it was not cleaned. Severity high, category governance. The re-snapshot hook is at `cli.py:76`, in the comment "Re-snapshot the lake after every erasure"; I did not read its code. The API-side `ErasureService` at `api.py:632` — I did not check whether it wires `on_complete`.
- `src/eurostream/governance/erasure.py` (`_anonymize_warehouse`) — the audit log stores the raw `customer_id` in `governance.erasure_audit_log`, in the JSONL file, in Turso, and in `suppression_registry`. The erased subject's identifier is retained indefinitely. This is arguably lawful (proof of erasure) but should be a documented decision. Severity low, category governance.
- `src/eurostream/governance/erasure.py` (`_confirmation_hash`) — `hashlib.sha256(f"{request_id}:{customer_id}".encode()).hexdigest()[:16]`. This is called "tamper-evident" in the docstring but is unkeyed and truncated to 16 hex characters, so anyone can recompute it. It is not tamper-evident. Severity low, category governance.
- `src/eurostream/governance/erasure.py` (`request_erasure`) — `requested_by: str = "dsar@eurocart.eu"`. The requester defaults to a hard-coded address, and `api.py:209` also passes `requested_by="dsar@eurocart.eu"`. The requester is therefore not authenticated or attributed. Severity low, category governance.
- `src/eurostream/api.py:251` — `f"SELECT count(*) FROM governance.erasure_audit_log WHERE customer_id='{customer_id}'"  # noqa: S608`. Raw path-parameter interpolation into SQL on the verify endpoint is a SQL injection risk. Severity high, category security.
- `src/eurostream/api.py:173-228` — the erasure endpoints have no authentication. `/erasure-requests`, `/verify-erasure/{customer_id}` and a direct-execute endpoint around line 208 are all exposed. The `/sync-turso` endpoint also has no visible auth at `api.py:531`. I did not read the middleware, so auth may be applied elsewhere. Severity medium, category security.
- `src/eurostream/governance/pii.py` (`_IPV4_RE`, `_PHONE_RE`, NAME rule) — false-positive risks:
  - NAME is `re.fullmatch(r"[A-Z][a-z]+ [A-Z][a-z]+", ...)` when no other hit. This flags any title-cased two-word value such as "Black Friday" or "New York" and misses accented or hyphenated names.
  - `_PHONE_RE` matches any `+` plus 8 or more digits.
  - IBAN validation is only for 11 countries (`_IBAN_LENGTHS`) and returns False for all others.
  - Severity low, category data_quality.
- `governance/pii_manifest.json` — the manifest only covers `bronze.orders` (`email`: EMAIL, `iban`: IBAN). It does not list `bronze.payments.iban`, `bronze.clicks.ip_address`, the Silver hash columns or `customer_id`. The governance gate (`PIIClassifier.detect_unregistered`) would flag those columns, but erasure hard-codes them regardless of the manifest. Severity medium, category governance.
- `src/eurostream/config.py` (`consent_default`) — the consent default is `False` (opt-out). `.env.example` has `EUROSTREAM_CONSENT_DEFAULT=false`. This is the safe default and is config-driven. The `consent_default` setting's consumer was not located.
- Credentials: `config.py` holds no secret values. `kafka_password` (default None) and `turso_auth_token` (default None) come from the env, and `.env.example` leaves the Kafka username and password blank. The only hard-coded secret default is the salt.
- `src/eurostream/turso.py` (`_init_native`) — `except Exception: self._native_conn = None` silently swallows native-driver failures. `execute` then falls back to HTTP, where failures raise. Severity low, category data_quality.
- `src/eurostream/turso.py` (`TursoClient.__init__`) — `httpx.Client(timeout=15.0, ...)` and `chunk_size = 250` are hard-coded. Severity low.

**1. Source systems and settings**
- **Settings (`config.py`, env prefix `EUROSTREAM_`, `.env`):**

| Setting | Default |
|---|---|
| `event_bus_backend` | `"sqlite"` (`sqlite` or `kafka`) |
| `data_dir` | `PROJECT_ROOT/data` |
| `kafka_bootstrap_servers` | `"localhost:9092"` |
| `kafka_schema_registry_url` | `"http://localhost:8081"` |
| `kafka_username` | `None` |
| `kafka_password` | `None` |
| `kafka_security_protocol` | `"SASL_SSL"` |
| `kafka_sasl_mechanism` | `"SCRAM-SHA-256"` |
| `warehouse_path` | `data/eurocart.duckdb` |
| `lake_root` | `data/lake` |
| `pii_manifest_path` | `governance/pii_manifest.json` |
| `consent_default` | `False` |
| `pii_salt` | `PII_SALT` constant |
| `fraud_velocity_threshold` | `5` |
| `fraud_window_seconds` | `300` |
| `fraud_amount_zscore` | `3.0` |
| `erasure_sla_seconds` | `60` |
| `audit_log_path` | `data/logs/erasure_audit.jsonl` |
| `metrics_path` | `data/logs/metrics.jsonl` |
| `pipeline_log_path` | `data/logs/pipeline.jsonl` |
| `turso_database_url` | `None` |
| `turso_auth_token` | `None` |

  - `kafka_bootstrap_servers` has a validator that strips a scheme and `user:pass@` from a pasted Aiven URI.
  - The Turso URL and token also accept the aliases `TURSO_DATABASE_URL` / `TURSO_AUTH_TOKEN`.
  - `PROJECT_ROOT` falls back to `Path.cwd()` when there is no `pyproject.toml`.
- **Turso/libSQL:** `turso.py` takes `database_url` and `auth_token` and converts `libs

## Findings

- `src/eurostream/config.py` — Hard-coded default PII salt: PII_SALT = "eurostream-pii-salt" is also the default of Settings.pii_salt, so hashes use a public salt unless EUROSTREAM_PII_SALT is overridden.
- `.env.example` — .env.example ships a placeholder salt EUROSTREAM_PII_SALT=change-me-in-production that would silently replace the default if copied unchanged.
- `src/eurostream/governance/pii.py` — hash_pii is plain SHA-256 of f"{salt}:{value}" with a single global salt; deterministic and brute-forceable for low-entropy values, so pseudonymization not anonymization.
- `src/eurostream/turso.py` — TURSO_DDL creates bronze.orders with raw email and iban, bronze.payments with raw iban, and bronze.clicks with raw ip_address columns in third-party cloud Turso.
- `src/eurostream/governance/erasure.py` — Turso erasure cascade is wrapped in a single try/except that only logs a warning; the first failure aborts the remaining statements, yet the audit still records status 'completed' and layers_touched never lists Turso.
- `src/eurostream/governance/erasure.py` — layers.append("lake") is conditioned only on self._on_complete being set, and the hook runs after the audit is written and its exceptions are swallowed, so the audit can claim the lake was cleaned when it was not.
- `src/eurostream/governance/erasure.py` — Bronze is only masked (email, iban, ip_address overwritten with '<anonymized>'); customer_id, order_id, session_id and amounts remain in Bronze rows, so the data subject stays linkable.
- `src/eurostream/governance/erasure.py` — _confirmation_hash is an unkeyed sha256 of request_id:customer_id truncated to 16 hex chars, described as tamper-evident but recomputable by anyone.
- `src/eurostream/governance/erasure.py` — request_erasure defaults requested_by to the hard-coded address dsar@eurocart.eu, so the requester is not attributed or authenticated.
- `src/eurostream/governance/erasure.py` — Erasure reaches no event-bus topic payloads, the audit JSONL file or the Parquet lake directly; erased customer_id is retained in audit log, suppression registry and JSONL.
- `src/eurostream/api.py:251` — verify-erasure interpolates the customer_id path parameter directly into SQL via f-string (WHERE customer_id='{customer_id}') with noqa S608, a SQL injection risk.
- `src/eurostream/governance/pii.py` — NAME classification flags any title-cased two-word string (regex [A-Z][a-z]+ [A-Z][a-z]+) such as place names, and the IBAN checker supports only 11 countries, causing false positives and negatives.
- `governance/pii_manifest.json` — PII manifest only registers bronze.orders email and iban; bronze.payments.iban and bronze.clicks.ip_address are absent although erasure masks them.
