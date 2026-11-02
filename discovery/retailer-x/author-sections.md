## decision

**Recommendation: go, but conditional. Rebuild in an EU workspace; do not lift the current deployment.**

EuroStream maps cleanly onto Databricks. The medallion DAG becomes a Lakeflow Declarative Pipeline, the fraud scorer becomes a Structured Streaming job, the Art. 17 cascade becomes a Lakeflow Job, and the API becomes a Databricks App. Six of the 26 code findings are resolved by the target platform itself: watermark data loss, scorer state, silent drops, shared connections, hand-written lineage and the CI cache.

Three things block a "just migrate" plan:

1. **Residency.** The workspace that already holds a EuroStream deployment, with clear customer email and IBAN, runs in AWS us-east-2. ADR 0001 forbids processing outside the EU. Either the DPO confirms a transfer basis, or that deployment moves to an EU region (OQ-03).
2. **Erasure is not complete in today's design.**
   - A full Silver rebuild re-creates erased customers.
   - The event bus keeps clear PII.
   - A public Hugging Face dataset keeps pseudonymized rows that erasure never reaches.

   A faithful migration would carry all three. The current workspace build already filters suppressed customers out of Silver and Gold, and that design should be kept.
3. **Scope is undefined.** All sources are synthetic, the RFC calls the platform a portfolio artefact, and no production volume exists (OQ-01, OQ-04).

Decide now:

- (a) Accept the EU rebuild (owner: platform owner).
- (b) Stop the public Hugging Face upload and secure the API (owner: platform owner, this week).
- (c) Have the DPO answer OQ-03, OQ-05 and OQ-06 before wave 1 starts.

Security posture is 2/5 (SAT plus a live read, 75% coverage), with 4 high-severity checks failing.

## architecture

Domain-level outline. Names stay `<catalog>` placeholders until agreed. Built with `databricks-pipelines`, `databricks-jobs`, `databricks-unity-catalog` and `databricks-apps` guidance.

- **Workspace and metastore**: a new workspace in an EU region (eu-central-1 matches the IaC), configured to the SAT baseline: IP access lists, verbose audit logs, metastore admin delegated to a group, jobs run as service principals.
- **Catalogs**: one catalog per environment (`<env>_eurostream`) with schemas `bronze`, `silver`, `gold` and `governance`. The trade-off is simpler grants against one-catalog-per-layer isolation. Clear PII is allowed only in `bronze`, which gets UC governed tags (`pii=email|iban|ip`) and column masks. Quarantine tables hold no clear PII.
- **Ingestion**:
  - Kafka topics → Lakeflow streaming tables. PII is tokenized at the producer, or topic retention stays below the erasure deadline.
  - Real sources (OQ-04) → Lakeflow Connect where a connector exists.
- **Silver**:
  - AUTO CDC, plus an anti-join on `governance.suppression_registry`.
  - Keyed HMAC whose key lives in a secret scope (replaces the public salt).
  - Expectations replace the post-hoc quality gate.
- **Gold**: materialized views. Consent and fraud KPIs are defined once as UC metric views.
- **Fraud**: a Structured Streaming job (`transformWithState`, checkpointed), idempotent on `alert_id`, on serverless compute.
- **Erasure**: a Lakeflow Job that runs registry MERGE → Bronze mask → pipeline refresh → `REORG … APPLY (PURGE)` + VACUUM within the agreed retention → an audit row with per-surface status.
- **Serving**: a Databricks App with OAuth and on-behalf-of-user SQL replaces FastAPI on Render. Turso and the Hugging Face upload are retired. Any public sharing goes through Delta Sharing of anonymized aggregates.
- **Deployment**: a Declarative Automation Bundle in Git, CI with OIDC federation and a protected environment.

**Architect's decisions**: catalog topology, tokenization point, retention per layer, and whether the us-east-2 pipelines are reused as reference code (OQ-02).

## roadmap

- **Wave 0 – landing zone and containment (1–2 weeks).**
  - Stop the Hugging Face upload, take the API off the public internet, rotate the salt.
  - Create the EU workspace to the SAT baseline. Set up the suppression registry, audit log and erasure job skeleton. Get DPO answers on residency and retention.
  - *Exit:* SAT re-run on the new workspace shows no failed high-severity check; no public copy of customer data remains.
- **Wave 1 – pilot: orders → customer_360 (2–3 weeks).**
  - Bronze orders and clicks, Silver orders and customers, Gold customer_360, with the consent rule decided (OQ-07).
  - *Exit:* reconciliation against a DuckDB run on the same event set; an erasure test proves the customer is absent from every layer, Delta history and the bus.
- **Wave 2 – payments and fraud (2–3 weeks).** Payments, the streaming scorer, fraud_alerts, order_facts and fraud_summary.
  - *Exit:* the alert set equals the legacy scorer's on a replayed stream; latency meets OQ-12.
- **Wave 3 – serving and retirement (1–2 weeks).** Databricks App and dashboard; retire Turso, Render, GitHub Actions orchestration and the us-east-2 deployment.
  - *Exit:* no consumer reads a legacy store; the old workspace is decommissioned after the DPO signs off.

## drivers

This is an estimate, not a price. Drivers, each from code reading (manual tiers):

- **Workloads**: 9 jobs or endpoints, 3 of them High complexity (medallion DAG, fraud scorer, erasure), plus about 13 tables.
- **Rewrites**: 11+ DuckDB-specific statements (INSERT OR IGNORE/REPLACE, arg_max, COPY) become declarative pipelines or MERGE. No trial conversion was run. The prior attempt in the workspace suggests the conversion is feasible but unproven (1 of 5 pipeline runs succeeded).
- **Owner decisions**: 4 CONFLICT rules and 1 UNRESOLVED rule. This is calendar time with owners, not effort.
- **Volume**: unknown. All data is synthetic, so backfill and compute sizing cannot be estimated.
- **Current Databricks spend**: about 51 DBU over 2026-09-25→10-08 (serverless SQL 21.6, jobs 16.0, storage 7.4, DLT 5.5).

Range: **6–10 engineer-weeks** for waves 0–3. This assumes Kafka remains the source, volume stays under 1M events/day, and the DPO answers within wave 0. Confidence is low until OQ-04 is answered.

## risks

1. **Residency breach in place today** (FND-01). EU PII sits in us-east-2. *Mitigation:* DPO decision and EU rebuild in wave 0. *Owner:* DPO.
2. **Erasure gaps carried into Databricks** (FND-02, FND-03, FND-04, FND-20). *Mitigation:* the erasure job design plus the wave 1 exit test that covers Delta history and the bus. *Owner:* platform lead.
3. **Public exposure before migration** (FND-04, FND-05, FND-06): open API, SQL injection, public dataset. *Mitigation:* containment in wave 0. *Owner:* platform owner.
4. **Unknown scope** (FND-24). No real sources or volumes, so the estimate stays a range. *Mitigation:* answer OQ-04 before wave 1 is sized.
5. **Unowned prior attempt** (FND-18, FND-19). The live jobs run as a person and their source is not in VCS. *Mitigation:* decide OQ-02, pause the jobs, keep the code as reference only.

**Assumptions**: Kafka stays the bus; serverless compute is acceptable; the workspace owner is the delivery team, not the client.
