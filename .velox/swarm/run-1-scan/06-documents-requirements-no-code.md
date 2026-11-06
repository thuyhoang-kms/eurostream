# Documents → requirements (no code)

Status: ok

Result: 38 requirements, 15 conflicts, 12 stated limitations and 12 open gaps extracted from all 11 documents. The documents disagree on several load-bearing points, mainly erasure completeness, the fraud window type and the target warehouse.

Findings:
- docs/postmortem/inc-2026-001-pii-false-positive.md:57 — the PII gate is fail-closed by design, so a false positive aborts the DAG after Bronze load and before Silver/Gold.
- README.md:127 — warehouse erasure is not atomic, which conflicts with paper/paper.md:56 ("atomic Six-Layer Deletion Cascade").
- README.md:171 — Layer 5 `FraudScorer.evacuate()` is a "design target rather than a wired call".
- SECURITY.md:21 — the governance API has no authentication, which conflicts with docs/rfc/0001-platform-design.md:262 ("logs the operator who issued it").
- docs/architecture.md:140 — the erasure cascade omits fraud-alert deletion and lake re-export, which docs/gdpr_erasure_flow.md:59-60 lists as steps 5 and 6.

## Requirements
Format: ID | type | statement | locator | excerpt | basis. Basis is stated (S) or inferred (I). Priority and owner are given only where a document states them.

**SLOs and performance**
- R1 | nonfunctional | The erasure cascade must complete within 60 s (`EUROSTREAM_ERASURE_SLA_SECONDS`); breaches increment `erasure_sla_breach`. | docs/architecture.md §SLOs | "Erasure SLA | 60s" | S
- R2 | nonfunctional | The erasure API response returns `request_id` and `sla_seconds`=60. | docs/gdpr_erasure_flow.md:37-45 | "sla_seconds": 60 | S
- R3 | nonfunctional | Fraud alert latency is within one `fraud_window_seconds` window (default 300 s). | docs/architecture.md §SLOs | "within one `fraud_window_seconds` window (300s)" | S
- R4 | nonfunctional | Fraud detection must be sub-minute ("near-instant") on the speed path. | docs/rfc/0001-platform-design.md:33 | "sub-minute (here: near-instant) latency" | S. RFC:14 says "within seconds", which conflicts with the 300 s SLO (C12).
- R5 | nonfunctional | The data-quality SLO is that all checks pass, and the DAG aborts if any gate fails. | docs/architecture.md §SLOs | "all checks pass" | S
- R6 | nonfunctional | The Databricks showcase and README describe Gold refresh as a four-hourly DAG schedule. | README.md:322 | "Scheduled four-hour DAG" | S. This is a schedule, not a freshness SLO.
- R7 | nonfunctional | The README benchmark reports erasure p95 of 109.20 ms over 50 iterations, local DuckDB only. | README.md:303 | "p95 Latency : 109.20 ms" | S

**EU residency**
- R8 | security | All storage and processing must be pinned to EU regions, set at provider level. | docs/adr/0001-eu-region-choice.md:22,32 | "All storage and processing is pinned to EU regions" | S
- R9 | security | There must be no cross-border transfer, no "replicate to US for DR", and no "temporary processing" outside the EU. | docs/adr/0001-eu-region-choice.md:44,52 | "No \"replicate to US for DR\"" | S
- R10 | integration | AWS resources go in `eu-central-1`: versioned AES-256 S3, MSK with 3 brokers and TLS, and an IAM role. | docs/architecture.md:179-183 | "AWS resources in `eu-central-1`" | S
- R11 | security | The platform must prove residency, not just assert it. | docs/adr/0001-eu-region-choice.md:14 | "The platform must prove residency" | S

**GDPR Art. 17 erasure**
- R12 | functional | Erasure is requested via POST `/erasure-requests` with `customer_id`; the API enqueues an `erasure_requested` tombstone on the `erasure_requests` topic. | docs/gdpr_erasure_flow.md:27-28 | "enqueues an `erasure_requested` tombstone" | S
- R13 | functional | Step 1 adds `customer_id` to the in-memory suppression set and the durable `governance.suppression_registry`. | docs/gdpr_erasure_flow.md:55 | "durable `governance.suppression_registry` table" | S
- R14 | functional | Bronze `email`, `iban` and `ip_address` are updated to `<anonymized>`; rows are kept, not deleted. | docs/gdpr_erasure_flow.md:56; docs/architecture.md:140 | "`<anonymized>`" | S
- R15 | functional | Silver `customers`, `orders` and `payments` rows for the customer are deleted. | docs/gdpr_erasure_flow.md:57 | "DELETE `customers`, `orders`, `payments`" | S
- R16 | functional | Gold `customer_360`, `order_facts` and `fraud_summary` rows for the customer are deleted. | docs/gdpr_erasure_flow.md:58 | "DELETE `customer_360`, `order_facts`, `fraud_summary`" | S
- R17 | functional | `bronze.fraud_alerts` rows for the customer are deleted. | docs/gdpr_erasure_flow.md:59 | "DELETE alerts for the customer from `bronze.fraud_alerts`" | S
- R18 | functional | Silver/Gold Parquet in the lake is re-snapshotted so a stale copy does not survive. | docs/gdpr_erasure_flow.md:60 | "must not survive in a stale lake copy" | S
- R19 | functional | Erasure must be idempotent, and the tombstone must be replayed from an uncommitted offset after a worker crash. | docs/gdpr_erasure_flow.md:125-141 | "running the same request twice produces the same end state" | S
- R20 | data | Each execution writes an audit record to `data/logs/erasure_audit.jsonl` and `governance.erasure_audit_log`, with a confirmation hash `sha256(request_id:customer_id)[:16]`. | docs/gdpr_erasure_flow.md:94-100 | "sha256(request_id:customer_id)[:16]" | S
- R21 | functional | `GET /governance/erasure-audit` returns erasure records, newest first. | docs/gdpr_erasure_flow.md:105-108 | "newest first" | S
- R22 | functional | `GET /verify-erasure/{customer_id}` spot-checks `gold.customer_360`, `silver.customers`, Bronze orders and the audit table. | README.md:190 | "spot check over `gold.customer_360`" | S
- R23 | security | An erroneous erasure cannot be rolled back; the guard is prevention through a bounded payload and operator logging. | docs/rfc/0001-platform-design.md:264-266 | "Rollback of an *erroneous* erasure is impossible by design" | S

**Consent**
- R24 | functional | No non-consenting customer may flow into marketing-facing aggregates. | docs/rfc/0001-platform-design.md:36 | "no non-consenting customer flows into" | S
- R25 | data | Gold combines consent with `bool_and(marketing_consent)`, and the quality gate checks `consents_marketing` matches upstream. | README.md:121,249 | "`bool_and(marketing_consent)`" | S

**Pseudonymization and PII**
- R26 | security | Silver hashes configured PII fields as salted SHA-256 over `salt:value`; this is pseudonymized, not anonymous. | docs/rfc/0001-platform-design.md:160; README.md:120 | "`sha256(salt:value)`" | S
- R27 | security | The salt `EUROSTREAM_PII_SALT` must come from a secret manager and be rotated per environment in production; the default is public. | SECURITY.md:19-20 | "defaults to a public value" | S
- R28 | functional | PII recognizers cover email, IBAN (mod-97), IPv4, phone and a conservative name heuristic. | docs/adr/0003-pii-classification.md:24-30 | "pure-Python recognizer set" | S
- R29 | functional | Column classification is a majority vote over sampled values, with a 60% threshold. | docs/adr/0003-pii-classification.md:45 | "threshold: 60%" | S
- R30 | functional | The DAG seeds `governance/pii_manifest.json` on the first run and fails on an unregistered PII-like column. | docs/adr/0003-pii-classification.md:50-52 | "*fails* if a new PII-like column appears" | S
- R31 | functional | The IBAN recognizer must apply the ISO 13616 mod-97 checksum. | docs/postmortem/inc-2026-001-pii-false-positive.md:31 | "mod-97 (ISO 13616) checksum validation added" | S
- R32 | security | The PII gate must not be disabled; false positives are preferred over missed PII. | docs/postmortem/inc-2026-001-pii-false-positive.md:73 | "We are not disabling the gate" | S

**Fraud rules**
- R33 | functional | VELOCITY fires above N payments per window, severity HIGH; the README gives N=5 in 300 s. | docs/rfc/0001-platform-design.md:201; README.md:218 | "> 5" | S
- R34 | functional | AMOUNT_ZSCORE fires when z > 3.0, severity MEDIUM. The history excludes the current payment, uses N−1 degrees of freedom and holds at most 200 values; the paper requi

## Findings

- `docs/rfc/0001-platform-design.md:222` — RFC says the DataQualityEngine runs 'five checks' but the list that follows (lines 224-229) enumerates six; README.md:243 says six.
- `docs/architecture.md:140` — The documented erasure cascade (Bronze anonymize, Silver/Gold delete, audit) omits deleting bronze.fraud_alerts and the lake re-export that docs/gdpr_erasure_flow.md lists as steps 5 and 6.
- `paper/paper.md:27` — Paper claims the cascade guarantees verifiable physical erasure across all storage tiers, while README.md:23 and README.md:137 say there is no guarantee of physical deletion externally and the event bus is not purged.
- `README.md:171` — README admits the Layer 5 scorer-evacuation (FraudScorer.evacuate()) is a design target rather than a wired call, although line 180 and the paper present it as part of the six-layer cascade.
- `README.md:157` — README says the velocity rule uses fixed event-time buckets, conflicting with docs/architecture.md:111 (rolling windows), paper/paper.md:54 (tumbling windows) and README.md:218 (sliding-window formula).
- `README.md:147` — README says suppression is not refreshed automatically in existing services, conflicting with docs/gdpr_erasure_flow.md:55 which says other processes pick it up from the table on startup.
- `SECURITY.md:21` — SECURITY.md says the governance API has no authentication, conflicting with docs/rfc/0001-platform-design.md:262 which says the API logs the operator who issued the erasure.
- `README.md:121` — README states no downstream marketing-serving filter exists, conflicting with docs/architecture.md:35 and RFC goal (rfc:36) of a consent-aware marketing view with no non-consenting customers.
- `README.md:318` — Hosted services (Aiven Kafka, Turso, Hugging Face public lake, Render, Cloudflare) are named with no EU region, conflicting with docs/adr/0001-eu-region-choice.md:22 requiring all storage and processing pinned to EU regions.
- `paper/paper.md:115` — Paper claims erasures complete in under 2 seconds and sub-minute guarantees, whereas README.md:303-310 shows a local-DuckDB-only benchmark that excludes bus, Turso, scorer and Hugging Face.
- `docs/architecture.md:118` — Architecture says the batch path re-reads the event log from earliest, whereas README.md:120 describes an incremental merge on occurred_at > watermark.
- `docs/adr/0001-eu-region-choice.md:24` — ADR names Snowflake/BigQuery as the managed warehouse and never mentions Databricks, while README.md:352 presents a Databricks/Unity Catalog implementation; RFC:275 defers column-level security that README.md:361 lists as implemented.
- `docs/gdpr_erasure_flow.md:80` — Audit record is called tamper-evident though its hash is sha256(request_id:customer_id)[:16] over non-secret inputs, and README.md:205 says it is not a proof of deletion.
