## decision

Do not start converting code yet. First contain two live exposures, then build on the Databricks port that already runs in DEV.

1. **Contain now (wave 0, days):** stop the four-hourly upload of silver and gold customer data to the public Hugging Face dataset, and take the unauthenticated API offline or put it behind SSO. Both are live today and outside any erasure or residency control.
2. **Recover the DEV port:** DEV already runs a bundle-deployed EuroStream (four jobs, three serverless declarative pipelines in catalog `eurostream`) whose source was deleted from the repository on 2026-10-08. Restore it before anything is designed, because it may turn most rewrites into review-and-harden work.
3. **Settle four owner decisions before wave 1:** fraud velocity semantics, consent gating of the customer profile, DPO acceptance of masking versus deleting raw rows, and which Kafka and region production uses.

Scope today: the DuckDB warehouse (16 tables), the event bus (5 topics), 13 workloads and the serving layer. Nothing can be retired yet because there is no usage evidence. The security posture of DEV scores 2 of 5, and DEV sits in a US region, so it may hold synthetic data only.

## architecture

Target, at domain level (names stay placeholders until agreed): one EU-region production workspace with Unity Catalog. Catalog `<catalog>` holds schemas bronze, silver, gold and governance, mirroring today's layout.

- **Ingestion:** events from the production Kafka (to be confirmed) land in bronze through streaming tables in Lakeflow Declarative Pipelines. Bronze is deduplicated on event_id, and malformed events go to a quarantine table instead of being dropped.
- **Silver:** the pseudonymisation logic moves here with the salt read from a secret scope, which DEV already does. Late data is kept by the pipeline's own checkpoints, not by an event-time watermark.
- **Gold:** customer 360, order facts and fraud summary as materialised views. A consent-gated view or a Unity Catalog row filter serves marketing, and spend and fraud measures can become Unity Catalog metric views.
- **Fraud scoring:** Structured Streaming with stateful operators and checkpoints replaces the in-memory scorer.
- **Erasure:** a Lakeflow job (the DEV `eurostream_art17_erasure` is the starting point) that deletes, applies VACUUM within an agreed retention, and records a verified result per store.
- **Sharing:** Delta Sharing replaces the public Parquet push.
- **Serving:** the FastAPI dashboard is replaced by a Databricks App or AI/BI dashboard using Unity Catalog permissions.
- **Security inputs:** PII tags and column masks, a service principal per job, and residency in the EU.

Architect's decisions: tumbling or sliding fraud windows, retention periods, and whether Turso, the S3 bucket and MSK are retired.

## roadmap

- **Wave 0, contain:** stop the HF upload, secure or stop the public API, purge GitHub Actions caches, rotate the salt. Exit: the HF dataset is private or deleted, and the API requires auth.
- **Wave 1, foundation:** restore the DEV bundle source, fix CI, grant the assessment identity catalog read, and stand up the EU production workspace. Exit: the bundle deploys from git, CI is green, and the region is agreed.
- **Wave 2, medallion:** move bronze, silver and gold onto declarative pipelines, with a parallel run against DuckDB. Exit: reconciliation within agreed tolerance, with late-data differences explained.
- **Wave 3, streaming fraud and erasure:** stateful fraud scoring and an erasure job with verified per-store results, signed off by the DPO. Exit: the erasure SLA is met on the target and the fraud owner signs off alert parity.
- **Wave 4, serving and retire:** re-point or replace the dashboard, replace HF with Delta Sharing, and retire Turso, the SQLite bus and the Render/HF Space after purging PII. Exit: the legacy stores are empty.

## drivers

Estimate drivers, not a price. Confidence is low until volumes and the DEV source are in hand.

- 16 warehouse tables, 5 topics, 13 local workloads (manual triage: 2 high, 5 medium, 6 low) and about 15 API endpoints plus 1 dashboard to replace.
- 3 CONFLICT and 10 CODE-ONLY rules. These need calendar time with owners, not engineering effort.
- The DEV port's reuse rate is unknown. It is the largest swing factor, from roughly half the medallion and erasure work already done down to none.
- No trial conversion is possible: Lakebridge does not cover Python or DuckDB, so this is a rewrite estimate given as a range.
- Volumes and backfill depth are unknown.

## risks

- **Public exposure continues:** customer data stays on the public dataset while the migration is planned. Owner: sponsor. Mitigation: wave 0.
- **Erasure gaps carried over:** bus, Turso, HF history and Delta time travel keep erased data. Owner: DPO and data lead. Mitigation: retention and VACUUM requirements before wave 2.
- **Residency:** DEV is in us-east-2. Real data must never land there. Owner: platform owner.
- **Duplicate effort:** rebuilding what DEV already runs. Mitigation: restore the bundle source first.
- **Parallel-run disputes:** the target will be more complete than legacy, which loses late and malformed events. Agree the tolerance up front.
- **Unscored security areas:** 11 account-level checks were not assessed and the SAT run is a month old.
