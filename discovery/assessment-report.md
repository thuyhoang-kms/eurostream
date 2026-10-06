# eurostream — Discovery & Assessment

> Built with: databricks-discovery skills (Velox) · Databricks agent skills 0.2.25 · Databricks CLI 1.18.0

## Contents

- [Part A — Discovery](#part-a--discovery)
  - [1. Executive summary](#1-executive-summary)
  - [2. Business context & target-state requirements](#2-business-context--target-state-requirements)
  - [3. Data landscape & current-state architecture](#3-data-landscape--current-state-architecture)
  - [4. Workload catalogue](#4-workload-catalogue)
  - [5. Data dependencies & lineage, including external services](#5-data-dependencies--lineage-including-external-services)
- [Part B — Assessment](#part-b--assessment)
  - [6. Governance, PII & GDPR gaps](#6-governance-pii--gdpr-gaps)
  - [7. Databricks security posture](#7-databricks-security-posture)
  - [8. Technical debt register](#8-technical-debt-register)
  - [9. Migration complexity & scope](#9-migration-complexity--scope)
  - [10. Target architecture & component mapping](#10-target-architecture--component-mapping)
  - [11. Recommendations, phased roadmap & cost estimate](#11-recommendations-phased-roadmap--cost-estimate)
  - [12. Risk register, assumptions & open decisions](#12-risk-register-assumptions--open-decisions)
- [Appendix](#appendix)
  - [A. Evidence](#a-evidence)
- [Evidence sufficiency — eurostream  (run-01, 2026-10-06)](#evidence-sufficiency--eurostream--run-01-2026-10-06)
  - [B. Best-practice references](#b-best-practice-references)
  - [C. Stakeholder questionnaire](#c-stakeholder-questionnaire)

# Part A — Discovery

## 1. Executive summary

> This report is for **the delivery lead / repo owner** to decide **whether the Databricks build is ready to become the primary EuroStream runtime, and which Python / DuckDB / Turso components to migrate, keep or retire**, before **no fixed date**.  `stated` (decision) · `assumed` (audience, date) — OQ-04

**Readiness: 1 / 5** — the lowest dimension; an estate is as ready as its weakest part.

| Dimension | Score | Basis | Evidence |
|---|---|---|---|
| Data | 3 / 5 | Target Bronze/Silver/Gold/governance objects exist (37) and match the design, but nothing has been written to them since 2026-09-28 and Silver hash continuity is open. | eurostream.information_schema.tables grouped by schema/type |
| Logic / code | 4 / 5 | Fraud thresholds and the four quality gates match across stacks; one alert rule differs (GEO_MISMATCH); Databricks erasure reaches more stores than Python. | databricks/notebooks/03_fraud_streaming.py:378-388 |
| Governance & PII | 1 / 5 | PII masks, tags and row filters from 50_grants_and_tags.sql are absent in the deployed catalog, and the workspace runs in US East (Ohio) against the EU-only ADR. | eurostream.information_schema.column_masks → 0 rows; system.billing.usage 90d → sku_name LIKE '%US_EAST_OHIO' |
| Security | 2 / 5 | Read from the client's own SAT run 1 (2026-10-05) by thuyhoang@kms-technology.com via read-only SQL: 23 of 52 checks failed; severity-weighted pass share 59% (61/103); 3 failed High checks cap the score at 2 (security-posture scoring rule, applied by hand — posture.py could not run here). | sat.security_analysis.security_checks run_id=1 ⨝ security_best_practices, score=1 |
| Operations | 1 / 5 | All Databricks runs fall on one day (2026-09-28) with failures in every job; fraud stream, quality gate and orchestrator are not deployed; the bundle ships schedules paused and the UI is the declared source of truth. | system.lakeflow.jobs ⨝ job_run_timeline, 90d, name LIKE '%eurostream%' |

### Top 5 risks

| # | Severity | Risk | When migrated | Evidence |
|---|---|---|---|---|
| FND-01 | critical | PII masks, tags and row filters defined in code are not applied in the workspace | carried | stated: SELECT * FROM eurostream.information_schema.column_masks → 0 rows; routines/column_tags/row_filters → 0 rows; databricks/sql/50_grants_and_tags.sql:425-447 |
| FND-03 | high | Databricks build ran on one day only (2026-09-28); half the jobs failed at least once | carried | stated: system.lakeflow.jobs ⨝ job_run_timeline, 90d, name LIKE '%eurostream%' |
| FND-11 | high | SAT run 1 (2026-10-05): 23 of 52 checks failed, 3 of them High | carried | stated: sat.security_analysis.security_checks run_id=1 ⨝ security_best_practices, score=1 |
| FND-04 | high | Deployed jobs do not match the bundle; fraud stream, quality gate and orchestrator are absent | redesign | stated: databricks/dab/resources/jobs.yml:15-44; system.lakeflow.jobs name LIKE '%eurostream%' → 4 jobs |
| FND-02 | high | Workspace runs in US East (Ohio); ADR-0001 requires EU-only processing | redesign | stated: system.billing.usage 90d → sku_name LIKE '%US_EAST_OHIO'; docs/adr/0001-eu-region-choice.md:22 |

### Recommendation

**No-go today; go after three conditions, re-assessed at the end of wave 1.** Owner: delivery lead.

The Databricks build is the better design. Its erasure reaches more places than the Python stack (quarantine, the lake Volume, a physical purge of the fraud sink). Its App replaces an unauthenticated erasure API with per-user reads and a signed confirmation. Its fraud and quality logic matches the Python rules except for one alert rule. What is not ready is the workspace it runs in:

1. **Move production to an EU-region workspace.** The current one bills in US East (Ohio), and ADR-0001 promises EU-only processing. Treat this workspace as the rehearsal environment. Decide by answering OQ-06.
2. **Apply the governance script and prove it.** `50_grants_and_tags.sql` masks email, IBAN and IP address, but none of its masks, tags or filters exist in the deployed catalog. Re-read `information_schema` after applying it; zero masks means no go.
3. **Run unattended for 14 days.** Deploy the jobs from the bundle (fraud stream, medallion refresh, quality gate, export, erasure, orchestrator) and unpause them. Exit: no failed run in the last 7 days, and an erasure rehearsal that verifies every layer.

Retire the Python stack (GitHub Actions schedule, FastAPI app, Render) only after condition 3 holds, and only after OQ-02 confirms nobody outside the demo uses it. Turso stays deferred until its owner says whether it is still used. Agree the GEO_MISMATCH rule (OQ-08) before wave 1 starts, because it changes fraud alert counts.

4 open decision(s) block this — §12.

### What the evidence does not yet support

| Conclusion needed | Evidence required | In hand | State | If missing |
|---|---|---|---|---|
| Go / no-go on cut-over | Feature parity (code), deployed objects (UC), working runs (job history), security score | code ✅ · UC ✅ · runs ✅ (one day only, FND-03) · SAT ✅ | ⚠️ | Go/no-go can only be "not yet, conditions X" |
| Per-component disposition (migrate / keep / retire) | Python inventory + Databricks counterpart + consumers | code ✅ · consumers ❌ (OQ-02, OQ-05) | ⚠️ | "Retire" stays `defer` for Turso, Render API, HF publish |
| Erasure (Art. 17) parity | Both erasure paths read; a rehearsal run on Databricks | code ✅ · 8 erasure runs on 2026-09-28 (7 ok) | ⚠️ | Rehearsal outputs not inspected |
| Cost baseline | `system.billing.usage` ≥ 30 days of steady running | 2026-09-25 → 2026-10-06, rehearsal only | ❌ | No run-rate cost statement; only "rehearsal cost" |
| **Usage window** | `system.lakeflow.job_run_timeline` 90d | 2026-09-28 04:50 → 09:59 UTC (all runs) | ❌ | Nothing on Databricks has steady-state usage |

## 2. Business context & target-state requirements

Axis A — type

_Insufficient evidence — needs documents, transcripts or tickets read by requirements-extraction; risk if skipped: the target is designed against assumed use cases, SLAs and residency._

## 3. Data landscape & current-state architecture

| Kind | Objects | Holds PII | PII not classified |
|---|---|---|---|
| api_endpoint | 1 | 1 | 0 |
| export | 1 | 0 | 0 |
| external_consumer | 1 | 1 | 0 |
| job | 4 | 0 | 0 |
| queue | 1 | 1 | 0 |
| table | 1 | 1 | 0 |

Complexity: not assessed — no Lakebridge Analyzer output; `complexity` left null.

| Store | Kind | Layer | Volume | Holds PII | Evidence |
|---|---|---|---|---|---|
| Python event bus (SQLite / Kafka adapter): orders, clicks, payments, erasure_requests | queue | ingest | — | yes | stated: src/eurostream/producers.py |
| DuckDB warehouse bronze/silver/gold/governance | table | store | — | yes | stated: src/eurostream/warehouse.py |
| Parquet lake → Hugging Face swadhinbiswas/eustream | export | serving | — | no | stated: .github/workflows/orchestrate.yml |

## 4. Workload catalogue

6 workloads · 6 with no owner recorded — a wave cannot take a workload nobody owns.

| Workload | Kind | Frequency | Volume | Owner | Evidence |
|---|---|---|---|---|---|
| Deployed jobs: eurostream_bootstrap, eurostream_pipeline, eurostream_export_lake, eurostream_art17_erasure | job | — | — | NOT SET | stated: system.lakeflow.jobs name LIKE '%eurostream%' |
| FastAPI app (/erase, /erasure-requests, /produce, /stream, /transform, /quality-gate, /metrics, /sync-turso, gold/governance reads) | api_endpoint | — | — | NOT SET | stated: src/eurostream/api.py:206 |
| Python FraudStreamProcessor | job | — | — | NOT SET | stated: src/eurostream/streaming.py:56 |
| Python quality gates (uniqueness, PII not clear, consent gating, RI) | job | — | — | NOT SET | stated: src/eurostream/quality.py:48-55 |
| GitHub Actions orchestrate.yml (every 4h) | job | — | — | NOT SET | stated: .github/workflows/orchestrate.yml |
| Turso libSQL mirror | external_consumer | — | — | NOT SET | stated: src/eurostream/governance/erasure.py:215 |

## 5. Data dependencies & lineage, including external services

_Insufficient evidence — needs code or scanner output that shows reads and writes; risk if skipped: a wave ships without something it depends on._

# Part B — Assessment

## 6. Governance, PII & GDPR gaps

4 surfaces hold personal data; erasure is not proven to reach 2 of them; 0 stores are not yet classified.

| Surface | Kind | Erasure reaches | Evidence |
|---|---|---|---|
| FastAPI app (/erase, /erasure-requests, /produce, /stream, /transform, /quality-gate, /metrics, /sync-turso, gold/governance reads) | api_endpoint | unknown | stated: src/eurostream/api.py:206 |
| Python event bus (SQLite / Kafka adapter): orders, clicks, payments, erasure_requests | queue | no | stated: src/eurostream/producers.py |

| # | Severity | Finding | When migrated | Evidence |
|---|---|---|---|---|
| FND-08 | medium | pii_manifest.json omits payments.iban and clicks.ip_address | carried | stated: governance/pii_manifest.json:1-10 |
| FND-12 | low | Databricks erasure is broader than Python but does not verify the remote Hugging Face copy | carried | stated: databricks/notebooks/02_article17_erasure.py:911 |
| FND-02 | high | Workspace runs in US East (Ohio); ADR-0001 requires EU-only processing | redesign | stated: system.billing.usage 90d → sku_name LIKE '%US_EAST_OHIO'; docs/adr/0001-eu-region-choice.md:22 |

## 7. Databricks security posture

**Score: 2 / 5** — Read from the client's own SAT run 1 (2026-10-05) by thuyhoang@kms-technology.com via read-only SQL: 23 of 52 checks failed; severity-weighted pass share 59% (61/103); 3 failed High checks cap the score at 2 (security-posture scoring rule, applied by hand — posture.py could not run here). [sat: sat.security_analysis.security_checks run_id=1 ⨝ security_best_practices, score=1]

Not assessed: live workspace read (posture.py run --workspace) to cross-check SAT; GOV-21 and GOV-34 are known SAT false-fail candidates — if both are rejected on review the cap lifts to 3.

| # | Severity | Gap | When migrated | Evidence |
|---|---|---|---|---|
| FND-01 | critical | PII masks, tags and row filters defined in code are not applied in the workspace | carried | stated: SELECT * FROM eurostream.information_schema.column_masks → 0 rows; routines/column_tags/row_filters → 0 rows; databricks/sql/50_grants_and_tags.sql:425-447 |
| FND-11 | high | SAT run 1 (2026-10-05): 23 of 52 checks failed, 3 of them High | carried | stated: sat.security_analysis.security_checks run_id=1 ⨝ security_best_practices, score=1 |
| FND-09 | medium | Python API exposes erasure and data endpoints without authentication, CORS * | resolved-by-target | stated: src/eurostream/api.py:206 |
| FND-10 | medium | Hard-coded default PII salt in Python; Databricks reads it from Spark conf | resolved-by-target | stated: src/eurostream/config.py:22; databricks/dlt/silver_pseudonymize.py:31 |

## 8. Technical debt register

All findings — when migrated: carried 6 · redesign 4 · resolved-by-target 2  
Evidence: stated 12

| # | Severity | Category | Layer | Debt | When migrated | Evidence |
|---|---|---|---|---|---|---|
| FND-03 | high | ops | ops | Databricks build ran on one day only (2026-09-28); half the jobs failed at least once | carried | stated: system.lakeflow.jobs ⨝ job_run_timeline, 90d, name LIKE '%eurostream%' |
| FND-06 | medium | logic | transform | GEO_MISMATCH fires once per window in Python, on every event in Databricks | carried | stated: src/eurostream/streaming.py:134-146; databricks/notebooks/03_fraud_streaming.py:378-388 |
| FND-04 | high | ops | ops | Deployed jobs do not match the bundle; fraud stream, quality gate and orchestrator are absent | redesign | stated: databricks/dab/resources/jobs.yml:15-44; system.lakeflow.jobs name LIKE '%eurostream%' → 4 jobs |
| FND-07 | medium | dependency | store | Turso sync and its erasure cascade have no Databricks counterpart | redesign | stated: src/eurostream/governance/erasure.py:215 |
| FND-05 | medium | ops | ops | Bundle ships continuous ingest and the 4-hourly orchestrator PAUSED; UI is declared source of truth | redesign | stated: databricks/dab/resources/jobs.yml:376; databricks/dab/databricks.yml:3 |

## 9. Migration complexity & scope

**8 of 9 objects decided (88%). 1 undecided or deferred; 7 blocked on an open question.** In scope: migrate + modernize; out: retire; deferred: not yet in or out.

| Kind | migrate | modernize | retire | defer | undecided |
|---|---|---|---|---|---|
| job | 2 | 2 | 0 | 0 | 0 |
| api_endpoint | 0 | 1 | 0 | 0 | 0 |
| queue | 1 | 0 | 0 | 0 | 0 |
| table | 1 | 0 | 0 | 0 | 0 |
| export | 1 | 0 | 0 | 0 | 0 |
| external_consumer | 0 | 0 | 0 | 1 | 0 |

| Object | Kind | Disposition | Complexity (source) | Wave | Blocked by |
|---|---|---|---|---|---|
| Deployed jobs: eurostream_bootstrap, eurostream_pipeline, eurostream_export_lake, eurostream_art17_erasure | job | modernize | — | 1 | OQ-03 |
| Python event bus (SQLite / Kafka adapter): orders, clicks, payments, erasure_requests | queue | migrate | — | 1 | — |
| DuckDB warehouse bronze/silver/gold/governance | table | migrate | — | 1 | OQ-09 |
| Python FraudStreamProcessor | job | migrate | — | 1 | OQ-08 |
| Python quality gates (uniqueness, PII not clear, consent gating, RI) | job | migrate | — | 1 | — |
| FastAPI app (/erase, /erasure-requests, /produce, /stream, /transform, /quality-gate, /metrics, /sync-turso, gold/governance reads) | api_endpoint | modernize | — | 2 | OQ-02 |
| Parquet lake → Hugging Face swadhinbiswas/eustream | export | migrate | — | 2 | OQ-05 |
| GitHub Actions orchestrate.yml (every 4h) | job | modernize | — | 2 | OQ-02 |
| Turso libSQL mirror | external_consumer | defer | — | — | OQ-02 |

Retire recommendations: 0 (owner agreed: 0).

### Business rules at risk

No business rule extracted yet.

No rule is CONFLICT, CODE-ONLY or CONFIG-ONLY.

## 10. Target architecture & component mapping

Keep the target the repo already designs, with these choices:

- **Workspace and region:** one production workspace in an EU region (`<eu-region>`), with Unity Catalog metastore admin delegated to a group (SAT GOV-21). The current US workspace stays dev/rehearsal with synthetic data only.
- **Catalog:** `eurostream` with `bronze`, `silver`, `gold`, `governance` and `lake`, as `databricks/sql/00_catalogs.sql` defines. Masks, governed tags and row filters come from `50_grants_and_tags.sql`, applied by the deploy pipeline rather than by hand, so a redeploy cannot drop them.
- **Ingestion:** Kafka → Lakeflow Bronze streaming tables, with a quarantine table for malformed events. The Bronze pipeline relies on a Beta feature (REPLACE USING, DBR 18.2+) on the CURRENT channel, which cannot be pinned. Verify it in the EU workspace before promotion.
- **Transform:** serverless Lakeflow pipelines for Silver (pseudonymised, salt from a secret scope) and Gold (consent-gated). Fraud scoring runs as a continuous job on job compute.
- **Orchestration:** one bundle (`databricks/dab`) as the deployment source of truth. Jobs run as service principals (SAT GOV-42); the 4-hourly orchestrator replaces GitHub Actions.
- **Serving:** the Databricks App for operators and the DPO. Add a SQL alert for the erasure SLA (60 s), which the App configures but nothing measures yet.
- **Export:** the Volume `lake.exports`, with the Hugging Face push switched on only if OQ-05 says it must continue.

Architect's decisions: the EU region, the Kafka provider, and whether Turso survives.

| Object | Disposition | Target component |
|---|---|---|
| Deployed jobs: eurostream_bootstrap, eurostream_pipeline, eurostream_export_lake, eurostream_art17_erasure | modernize | Bundle-deployed jobs from databricks/dab/resources/jobs.yml (replace the UI-created ones) |
| FastAPI app (/erase, /erasure-requests, /produce, /stream, /transform, /quality-gate, /metrics, /sync-turso, gold/governance reads) | modernize | Databricks App (OBO reads + preview-token erasure); ingest/transform endpoints become Lakeflow Jobs; erasure SLA metric → SQL alert (to build) |
| Python event bus (SQLite / Kafka adapter): orders, clicks, payments, erasure_requests | migrate | Kafka → Lakeflow Bronze streaming tables eurostream.bronze.{orders,clicks,payments,erasure_requests} + ingest_quarantine (already built) |
| DuckDB warehouse bronze/silver/gold/governance | migrate | Unity Catalog eurostream.{bronze,silver,gold,governance} (37 objects deployed) |
| Python FraudStreamProcessor | migrate | Lakeflow Job eurostream_fraud_continuous running databricks/notebooks/03_fraud_streaming.py (defined in bundle, not deployed) |
| Parquet lake → Hugging Face swadhinbiswas/eustream | migrate | Job eurostream_export_lake → /Volumes/eurostream/lake/exports, sync_huggingface=true |
| Python quality gates (uniqueness, PII not clear, consent gating, RI) | migrate | Lakeflow Job eurostream_quality_gate running databricks/notebooks/01_quality_gates.py (defined in bundle, not deployed) |
| GitHub Actions orchestrate.yml (every 4h) | modernize | Lakeflow Job eurostream_orchestrator, cron 0 0 */4 * * ? (bundle; unpause after wave 1 exit) |

## 11. Recommendations, phased roadmap & cost estimate

- **Wave 0 — foundations (before any cut-over).** EU workspace, metastore admin group, IP access list enforced, audit-log monitoring (SAT High checks). Bundle variables documented and the runbook moved out of `.gitignore` (OQ-03). Exit: SAT re-run with no High failures; the bundle deploys to an empty workspace.
- **Wave 1 — core pipeline.** Bronze ingestion, fraud stream, Silver/Gold, quality gate and erasure jobs from the bundle; governance script applied; GEO_MISMATCH aligned. Exit: 14 days unattended, the last 7 with no failed run; masks visible in `information_schema`; erasure rehearsal verified on every layer.
- **Wave 2 — schedule, serving and export.** Unpause the orchestrator, switch off the GitHub Actions cron, point users at the Databricks App, decide on the Hugging Face push. Exit: one week with both stacks producing comparable Gold counts, then the Python schedule is off.
- **Wave 3 — decommission.** Retire the FastAPI app, Render and Turso once OQ-02 has an answer from their owner.

- Wave 1: 5 objects
- Wave 2: 3 objects

### Cost estimate

> An estimate: drivers and a range with the assumptions it rests on — not a price. The price is the delivery lead's.

This is an estimate, not a price. Effort is driven by:

- **No code conversion.** The target code exists. Effort is deployment, hardening and proof, not transpiling.
- **Environment build:** a new EU workspace and its account-level settings. This is client-owned and the longest lead item.
- **Deployment rework:** 4 UI-created jobs replaced by the 8 bundle jobs (2 already exist by name: export and erasure). Workspace hosts, deployer id and Kafka bootstrap are supplied at deploy time.
- **Governance:** one 490-line SQL script to apply and verify.
- **One logic change** (GEO_MISMATCH).
- **One SLA alert to build.**
- **Calendar time:** 14 days of unattended running, plus a week of parallel run.

Range: a few weeks of one engineer plus the client's platform admin, dominated by calendar time rather than effort. Rehearsal compute so far was about 41 DBU-equivalent units over 8 days; there is no steady-state cost baseline yet.

## 12. Risk register, assumptions & open decisions

### Risks

- **EU residency:** cutting over in this workspace moves EU personal data to the US. Mitigation: wave 0 EU workspace. Owner: repo owner / DPO.
- **Clear-text PII:** without the masks, anyone with SELECT on Bronze reads email, IBAN and IP address. Mitigation: apply the governance script through the pipeline, plus a quality check that fails when no mask exists.
- **Unproven operations:** one rehearsal day with failures in every job. Mitigation: the 14-day exit criterion.
- **Hidden consumers:** Turso, the FastAPI endpoints and the Hugging Face dataset may have users nobody has named. Mitigation: OQ-02 and OQ-05 before wave 3.
- **Beta runtime feature:** Bronze relies on Beta REPLACE USING on a channel that cannot be pinned (`databricks/dab/resources/pipelines.yml:6-10`). Mitigation: verify it in the EU workspace in wave 0 and watch Databricks release notes.

| # | Severity | Risk | When migrated | Requirements | Questions |
|---|---|---|---|---|---|
| FND-01 | critical | PII masks, tags and row filters defined in code are not applied in the workspace | carried | — | OQ-07 |
| FND-03 | high | Databricks build ran on one day only (2026-09-28); half the jobs failed at least once | carried | — | — |
| FND-11 | high | SAT run 1 (2026-10-05): 23 of 52 checks failed, 3 of them High | carried | — | — |
| FND-04 | high | Deployed jobs do not match the bundle; fraud stream, quality gate and orchestrator are absent | redesign | — | OQ-03 |
| FND-02 | high | Workspace runs in US East (Ohio); ADR-0001 requires EU-only processing | redesign | — | OQ-06 |

### Assumptions

Every record resting on inference, not on a source — each is an open question until confirmed.

No inferred record.

### Open decisions

| # | Decision | Owner | Blocking | Default if unanswered |
|---|---|---|---|---|
| OQ-01 | Why cut over now? If both runtimes keep running side by side for 12 more months, what breaks? | Repo owner (name: ?) | — | Driver = run one supported platform; retire what Databricks covers |
| OQ-02 | Where does the Python stack run today (Render, Docker, GitHub Actions orchestrate.yml, Turso), and who uses its API/dashboard? | Repo owner (name: ?) | FND-07, FND-09 | Treat Render, GitHub Actions and Turso as live; their disposition stays 'defer' until confirmed |
| OQ-06 | Is a US-region (us-east-2) workspace acceptable, or must production move to an EU-region workspace per ADR-0001? | Repo owner / DPO (name: ?) | FND-02 | Production needs an EU workspace; this one is a rehearsal environment |
| OQ-07 | Was 50_grants_and_tags.sql (masks, tags, row filters) never run, or run and later dropped? Who applies it? | Workspace admin (name: ?) | FND-01 | Treat as not applied; blocking until applied and re-read |

# Appendix

## A. Evidence

# Evidence sufficiency — eurostream  (run-01, 2026-10-06)

| Conclusion needed | Evidence required | In hand | State | If missing |
|---|---|---|---|---|
| Go / no-go on cut-over | Feature parity (code), deployed objects (UC), working runs (job history), security score | code ✅ · UC ✅ · runs ✅ (one day only, FND-03) · SAT ✅ | ⚠️ | Go/no-go can only be "not yet, conditions X" |
| Per-component disposition (migrate / keep / retire) | Python inventory + Databricks counterpart + consumers | code ✅ · consumers ❌ (OQ-02, OQ-05) | ⚠️ | "Retire" stays `defer` for Turso, Render API, HF publish |
| Erasure (Art. 17) parity | Both erasure paths read; a rehearsal run on Databricks | code ✅ · 8 erasure runs on 2026-09-28 (7 ok) | ⚠️ | Rehearsal outputs not inspected |
| Deployed = code (no drift) | UC objects vs `databricks/sql`, `dlt/`, `dab/` | ✅ | ✅ | Drift found: FND-01, FND-04 |
| Security readiness | SAT run on the target workspace | SAT run 1, 2026-10-05: 23/52 failed | ✅ | — |
| EU residency | Workspace region | `system.billing.usage` SKUs US_EAST_OHIO | ✅ | Conflict: FND-02 |
| Cost baseline | `system.billing.usage` ≥ 30 days of steady running | 2026-09-25 → 2026-10-06, rehearsal only | ❌ | No run-rate cost statement; only "rehearsal cost" |
| **Usage window** | `system.lakeflow.job_run_timeline` 90d | 2026-09-28 04:50 → 09:59 UTC (all runs) | ❌ | Nothing on Databricks has steady-state usage |

Every row in this report names its locator. Sources read: workbook tab *Sources*. Records still `extracted` (excluded unless --include-unreviewed): 0.

## B. Best-practice references

_No external reference cited._

## C. Stakeholder questionnaire

One list per person. High-impact ones are in §12; email drafts in workbook tab *Open Questions*.

**Fraud rule owner (name: ?)** — 1
- OQ-08: Which GEO_MISMATCH behaviour is intended: once per customer per 5-minute window (Python) or every event (Databricks)? [src/eurostream/streaming.py:134-146]

**Repo owner (name: ?)** — 5
- OQ-01: Why cut over now? — §12
- OQ-02: Where does the Python stack run today (Render, Docker, GitHub Actions orchestrate.yml,… — §12
- OQ-03: Can you share the private runbook docs/databricks/ (gitignored), and should the bundle become the deployment source of truth? [databricks/dab/databricks.yml:3]
- OQ-05: Does anyone consume the public Parquet lake on Hugging Face, and must Databricks keep publishing it (sync_huggingface is off by default)? [databricks/notebooks/04_export_lake.py:20]
- OQ-09: Is the production salt the same secret in both stacks, and must Silver hashes stay comparable across the cut-over? [src/eurostream/config.py:22]

**Repo owner / DPO (name: ?)** — 1
- OQ-06: Is a US-region (us-east-2) workspace acceptable, or must production move to an EU-region… — §12

**User** — 1
- OQ-04: Who reads the report and by when must the cut-over decision be made? [session 2026-10-06]

**Workspace admin (name: ?)** — 1
- OQ-07: Was 50_grants_and_tags.sql (masks, tags, row filters) never run, or run and later dropped? — §12
