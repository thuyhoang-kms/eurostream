## decision

**No-go today; go after three conditions, re-assessed at the end of wave 1.** Owner: delivery lead.

The Databricks build is the better design. Its erasure reaches more places than the Python stack (quarantine, the lake Volume, a physical purge of the fraud sink). Its App replaces an unauthenticated erasure API with per-user reads and a signed confirmation. Its fraud and quality logic matches the Python rules except for one alert rule. What is not ready is the workspace it runs in:

1. **Move production to an EU-region workspace.** The current one bills in US East (Ohio), and ADR-0001 promises EU-only processing. Treat this workspace as the rehearsal environment. Decide by answering OQ-06.
2. **Apply the governance script and prove it.** `50_grants_and_tags.sql` masks email, IBAN and IP address, but none of its masks, tags or filters exist in the deployed catalog. Re-read `information_schema` after applying it; zero masks means no go.
3. **Run unattended for 14 days.** Deploy the jobs from the bundle (fraud stream, medallion refresh, quality gate, export, erasure, orchestrator) and unpause them. Exit: no failed run in the last 7 days, and an erasure rehearsal that verifies every layer.

Retire the Python stack (GitHub Actions schedule, FastAPI app, Render) only after condition 3 holds, and only after OQ-02 confirms nobody outside the demo uses it. Turso stays deferred until its owner says whether it is still used. Agree the GEO_MISMATCH rule (OQ-08) before wave 1 starts, because it changes fraud alert counts.

## architecture

Keep the target the repo already designs, with these choices:

- **Workspace and region:** one production workspace in an EU region (`<eu-region>`), with Unity Catalog metastore admin delegated to a group (SAT GOV-21). The current US workspace stays dev/rehearsal with synthetic data only.
- **Catalog:** `eurostream` with `bronze`, `silver`, `gold`, `governance` and `lake`, as `databricks/sql/00_catalogs.sql` defines. Masks, governed tags and row filters come from `50_grants_and_tags.sql`, applied by the deploy pipeline rather than by hand, so a redeploy cannot drop them.
- **Ingestion:** Kafka → Lakeflow Bronze streaming tables, with a quarantine table for malformed events. The Bronze pipeline relies on a Beta feature (REPLACE USING, DBR 18.2+) on the CURRENT channel, which cannot be pinned. Verify it in the EU workspace before promotion.
- **Transform:** serverless Lakeflow pipelines for Silver (pseudonymised, salt from a secret scope) and Gold (consent-gated). Fraud scoring runs as a continuous job on job compute.
- **Orchestration:** one bundle (`databricks/dab`) as the deployment source of truth. Jobs run as service principals (SAT GOV-42); the 4-hourly orchestrator replaces GitHub Actions.
- **Serving:** the Databricks App for operators and the DPO. Add a SQL alert for the erasure SLA (60 s), which the App configures but nothing measures yet.
- **Export:** the Volume `lake.exports`, with the Hugging Face push switched on only if OQ-05 says it must continue.

Architect's decisions: the EU region, the Kafka provider, and whether Turso survives.

## roadmap

- **Wave 0 — foundations (before any cut-over).** EU workspace, metastore admin group, IP access list enforced, audit-log monitoring (SAT High checks). Bundle variables documented and the runbook moved out of `.gitignore` (OQ-03). Exit: SAT re-run with no High failures; the bundle deploys to an empty workspace.
- **Wave 1 — core pipeline.** Bronze ingestion, fraud stream, Silver/Gold, quality gate and erasure jobs from the bundle; governance script applied; GEO_MISMATCH aligned. Exit: 14 days unattended, the last 7 with no failed run; masks visible in `information_schema`; erasure rehearsal verified on every layer.
- **Wave 2 — schedule, serving and export.** Unpause the orchestrator, switch off the GitHub Actions cron, point users at the Databricks App, decide on the Hugging Face push. Exit: one week with both stacks producing comparable Gold counts, then the Python schedule is off.
- **Wave 3 — decommission.** Retire the FastAPI app, Render and Turso once OQ-02 has an answer from their owner.

## drivers

This is an estimate, not a price. Effort is driven by:

- **No code conversion.** The target code exists. Effort is deployment, hardening and proof, not transpiling.
- **Environment build:** a new EU workspace and its account-level settings. This is client-owned and the longest lead item.
- **Deployment rework:** 4 UI-created jobs replaced by the 8 bundle jobs (2 already exist by name: export and erasure). Workspace hosts, deployer id and Kafka bootstrap are supplied at deploy time.
- **Governance:** one 490-line SQL script to apply and verify.
- **One logic change** (GEO_MISMATCH).
- **One SLA alert to build.**
- **Calendar time:** 14 days of unattended running, plus a week of parallel run.

Range: a few weeks of one engineer plus the client's platform admin, dominated by calendar time rather than effort. Rehearsal compute so far was about 41 DBU-equivalent units over 8 days; there is no steady-state cost baseline yet.

## risks

- **EU residency:** cutting over in this workspace moves EU personal data to the US. Mitigation: wave 0 EU workspace. Owner: repo owner / DPO.
- **Clear-text PII:** without the masks, anyone with SELECT on Bronze reads email, IBAN and IP address. Mitigation: apply the governance script through the pipeline, plus a quality check that fails when no mask exists.
- **Unproven operations:** one rehearsal day with failures in every job. Mitigation: the 14-day exit criterion.
- **Hidden consumers:** Turso, the FastAPI endpoints and the Hugging Face dataset may have users nobody has named. Mitigation: OQ-02 and OQ-05 before wave 3.
- **Beta runtime feature:** Bronze relies on Beta REPLACE USING on a channel that cannot be pinned (`databricks/dab/resources/pipelines.yml:6-10`). Mitigation: verify it in the EU workspace in wave 0 and watch Databricks release notes.
