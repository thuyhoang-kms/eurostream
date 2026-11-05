# docs — stated intent

Status: ok

Result: The documents are mostly consistent, but they disagree on several points: the velocity rule's window, the DQ check count, the erasure sequence, the project name, and whether Bronze PII is anonymized or "retained". Paper, the production playbook and the configuration reference were only grepped. My tool budget ran out before I could read them in full.

Findings:

**1. Requirements**
- Functional, stated: fraud rules VELOCITY, AMOUNT_ZSCORE and GEO_MISMATCH, with severities HIGH, MEDIUM and LOW — `docs/rfc/0001-platform-design.md` §Fraud scoring:199-203.
- Functional, stated: medallion Bronze → Silver → Gold plus a governance schema — `docs/architecture.md`:59-103; `README.md`:117-121.
- Functional, stated: Art. 17 erasure cascade, with the Bronze/Silver/Gold/lake steps listed under item 2 — `docs/gdpr_erasure_flow.md`:53-60.
- Functional, stated: consent-aware Gold, "no non-consenting customer flows into marketing-facing aggregates" — `docs/rfc/0001-platform-design.md`:36-37.
- Non-functional, stated: erasure SLA 60s (`EUROSTREAM_ERASURE_SLA_SECONDS`). Breaches increment `erasure_sla_breach` — `docs/architecture.md`:195; `docs/gdpr_erasure_flow.md`:112-114.
- Non-functional, stated: fraud alert latency is "within one `fraud_window_seconds` window (300s)" — `docs/architecture.md`:194.
- Non-functional, stated: the RFC goal is "sub-minute (here: near-instant)" — `docs/rfc/0001-platform-design.md`:33.
- Non-functional, stated: the SQLite bus and DuckDB are single-node; there is no sharding or replication — `docs/adr/0002-event-bus.md`:52.
- Residency, stated: all storage and processing is pinned to EU regions, "region set at provider level" — `docs/adr/0001-eu-region-choice.md`:22-34.
- Residency, stated: no replicate-to-US DR; any future DR adds an EU-only second region — `docs/adr/0001-eu-region-choice.md`:43-45.
- Security, stated: the PII salt must come from a secret manager and be rotated per environment — `SECURITY.md`:19-20.
- Security, stated: the governance API needs SSO or a gateway in front of it — `SECURITY.md`:21-22.
- Security, stated: audit JSONL should ship to WORM storage (S3 Object Lock) in production — `SECURITY.md`:26-27.
- Security, stated: contracts are checked in CI; breaking schema drift blocks merge — `docs/rfc/0001-platform-design.md`:140-142.
- Data, stated: the PII manifest `governance/pii_manifest.json` is seeded on first run, and unregistered PII-like columns fail the DAG — `docs/adr/0003-pii-classification.md`:45-52.
- Scope, stated non-goals: multi-tenant BI, full Kubernetes, and real ML fraud — `docs/rfc/0001-platform-design.md`:40-49.
- Scope, stated: it is a portfolio and reference artifact, not hardened production — `SECURITY.md`:17; `README.md`:23.
- Integration, stated: Kafka adapter via `EUROSTREAM_EVENT_BUS_BACKEND=kafka`; Turso via `TURSO_DATABASE_URL`; Hugging Face via `EUROSTREAM_HF_REPO`; scheduled four-hour DAG in GitHub Actions — `README.md`:316-323.
- Retention: no retention period is stated anywhere I read.

**2. Stated business rules (verbatim where possible)**
- Velocity: "Velocity(c, W) = Σ I(t_now − t_e ≤ 300s) > 5" — `README.md`:218. The default threshold of `5` is in `site/src/content/docs/reference/configuration.mdx`:23 (grep hit).
- Velocity implementation: "uses fixed event-time buckets rather than the sliding-window formula" — `README.md`:157.
- Z-score: "Score(x) = |x − x̄| / s > 3.0" — `README.md`:228.
- Z-score baseline: "current payment is excluded from the baseline" and sample SD uses N−1 — `README.md`:221.
- Z-score history: "Each customer history is bounded to 200 values" — `README.md`:231.
- Geo: "billing country ≠ merchant country" — `README.md`:236; `docs/rfc/0001-platform-design.md`:203.
- Rolling window: "default 300s", windows expire after inactivity — `docs/architecture.md`:111; `docs/rfc/0001-platform-design.md`:205.
- Dedup: "Deduplicated with `row_number()`" — `README.md`:120.
- Bronze: "`INSERT OR IGNORE` and deterministic `event_id` keys" — `README.md`:119.
- Watermark: "Incremental merge using `occurred_at > watermark`" — `README.md`:120.
- Pseudonymization: "`sha256(salt:value)`" — `docs/rfc/0001-platform-design.md`:160. README says "salt, a colon, and the source value without adding a space" — `README.md`:145.
- Pseudonymization: "so these records are pseudonymized rather than anonymous" — `README.md`:120.
- Consent: "`bool_and(marketing_consent)`" in Gold — `README.md`:121.
- Consent: "no downstream marketing-serving filter" exists in the repo — `README.md`:121.
- Erasure order per `docs/gdpr_erasure_flow.md`:55-60:
  1. Suppression registry (in-memory plus `governance.suppression_registry`).
  2. Bronze `email`/`iban`/`ip_address` → `<anonymized>`.
  3. DELETE Silver customers/orders/payments.
  4. DELETE Gold customer_360/order_facts/fraud_summary.
  5. DELETE `bronze.fraud_alerts` rows.
  6. Lake re-export via the `on_complete` hook.
- Audit hash: "`sha256(request_id:customer_id)[:16]`" — `docs/gdpr_erasure_flow.md`:94.
- Audit sinks: `data/logs/erasure_audit.jsonl` and `governance.erasure_audit_log` — `docs/gdpr_erasure_flow.md`:99-100.
- Idempotency: replay of the tombstone from the uncommitted offset — `docs/gdpr_erasure_flow.md`:132-138.
- PII classification: "majority-vote over sampled values per column (threshold: 60%)" — `docs/adr/0003-pii-classification.md`:45-46.
- IBAN: structural match plus ISO 13616 mod-97 — `docs/adr/0003-pii-classification.md`:27.
- Name heuristic: "title-cased two-word, < 40 chars" — `docs/adr/0003-pii-classification.md`:30.
- DQ gate: any failure aborts the DAG, and results go to `governance.data_quality_runs` — `docs/rfc/0001-platform-design.md`:232-233.
- Streaming suppression is described as "immediately", but it only applies to processors given the `is_suppressed` callback — `README.md`:147; `docs/gdpr_erasure_flow.md`:55.

**3. Systems named**
- Kafka at Aiven, SASL_SSL + SCRAM-SHA-256, no host or region given — `README.md`:109, 318.
- AWS MSK (Terraform, `eu-central-1`, 3 brokers) — `docs/architecture.md`:179-183.
- SQLite WAL bus; DuckDB at `data/eurocart.duckdb` — `README.md`:318-319.
- Turso libSQL (`libsql://...`), optional sync — `README.md`:319.
- Hugging Face dataset `swadhinbiswas/eustream` — `README.md`:15, 320.
- Render or Docker at `0.0.0.0:PORT` — `README.md`:321.
- Cloudflare Pages: `eurostream-docs.pages.dev` — `README.md`:15, 323.
- GitHub Actions: `ci.yml`, `orchestrate.yml` — `README.md`:7-8, 322.
- Snowflake on AWS `eu-central-1`, or BigQuery location `EU` — `docs/adr/0001-eu-region-choice.md`:24-26.
- S3 versioned and AES-256, with an IAM role — `docs/architecture.md`:181-182.
- Databricks target: Azure trial workspace — `.velox/PoC.md`:25.
- Delta VACUUM and Iceberg are mentioned only as prior art in `paper/paper.md`:44 (grep hit).

**4. Limitations, gaps and the postmortem**
- No benchmark of the incremental-compute reduction — `README.md`:123.
- Warehouse erasure steps are independent statements. A Turso or lake failure does not roll back the warehouse — `README.md`:127.
- The event bus is not purged on erasure; the suppression set is not a global replay filter — `README.md`:137.
- `FraudScorer` has no explicit purge; the README says state expires during normal processing — `README.md`:157.
- Scorer evacuation (`FraudScorer.evacuate()`) is "a design target rather than a wired call" — `README.md`:171.
- The API queues erasure by default and needs a separately started worker — `README.md`:97, 186.
- Some dashboard panels are shells — `README.md`:97.
- Turso does not auto-rebuild after a restart — `README.md`:161.
- `/verify-erasure` is only a spot check and does not inspect Kafka, Turso, HF or scorer memory — `README.md`:190.
- The audit hash is not proof of downstream deletion — `README.md`:205.
- The contracts check does not classify every Bronze column — `README.md`:165.
- The IBAN table covers only some European countries — `README.md`:252.
- The benchmark does not exercise Turso, the bus or HF — `RE

## Findings

- `README.md:157` — README says the velocity rule uses fixed event-time buckets, while README:218 shows a sliding-window formula and architecture.md describes rolling windows.
- `docs/rfc/0001-platform-design.md:222` — RFC says DataQualityEngine runs 'five checks' but lists six (lines 224-229); README:243 says six.
- `README.md:171` — README states scorer evacuation (Layer 5 FraudScorer.evacuate()) is a design target not wired, yet the diagram at lines 176-181 and architecture.md present it as part of the cascade.
- `docs/postmortem/inc-2026-001-pii-false-positive.md:69` — Corrective action 'Review remaining recognizers for similar structural false positives' is still 'Next' (open) while the header status says Resolved.
- `docs/gdpr_erasure_flow.md:22` — Erasure API examples use port 8000 while README documents the API on port 7860.
- `docs/adr/0001-eu-region-choice.md:52` — ADR claims no code path transfers data outside the EU, but README:320 documents Hugging Face lake upload and Aiven/Turso/Render hosting with no stated EU region.
- `docs/architecture.md:195` — Metric named erasure_sla_breach here but README:271 uses erasure_sla_breaches_total.
