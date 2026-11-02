# Review — eurostream run-01 (2026-10-06)

**Read:** Python stack (fraud, erasure, API, quality, config); Databricks build (bundle, jobs, Bronze/Silver pipelines, notebooks 01–04, grants SQL); ADR-0001; workspace UC metadata, `system.lakeflow`, `system.billing`, SAT run 1.
**Produced:** 12 findings · 9 inventory records · 9 open questions. No business-rule or requirements register yet.

## Needs a human now
1. **FND-01 / OQ-07:** PII masks are not applied in the deployed catalog. Confirm whether that's true or a visibility gap.
2. **FND-02 / OQ-06:** The workspace is in US East (Ohio), but ADR-0001 requires EU. Decide whether this workspace is a rehearsal environment only.
3. **FND-03 / FND-04:** The target ran on one day only, and the fraud stream, quality gate and orchestrator are not deployed.
4. **OQ-02:** Where does the Python stack (Render, Turso, GitHub Actions) still run?
5. **OQ-08:** Decide which GEO_MISMATCH behaviour is intended.

## Unsure (confidence < 0.8)
FND-09 (API auth: read from the route declarations, not from a running server) and FND-04 (job-name matching).

## What was run, and what stayed unreproduced
Nothing was executed against the project; findings are `stated` from code or system tables. Erasure parity was not rehearsed.

## Deliberately not concluded
Go/no-go, the migrate/keep/retire matrix and cost (8 days of billing data only, ~41 DBU-equivalent units across products). These belong to synthesis, after review.

## Positive evidence (no finding)
Fraud thresholds match across both stacks. The Databricks erasure cascade reaches more than the Python one: quarantine, the lake Volume rewrite and a physical purge. The Databricks App replaces the unauthenticated erasure API with on-behalf-of reads plus a signed preview token.

## How to merge
Use the Review tab: accept, reject or defer each record. Accepted records go to `registers/`.
