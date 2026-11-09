# Source request — eurostream  (run-01, 2026-11-05)

Status legend: ✅ received (source id) · ⏳ requested <date> · ❌ not yet. A system is **named**, never signed in to — no credentials are requested in this document; access is granted by the client to an identity they control.

## Required
| # | Source | Why | How to obtain | Client owner | Status |
|---|---|---|---|---|---|
| 1 | **Databricks DEV workspace access** | Unity Catalog, jobs, pipelines, security posture | Already bound: `dbc-9e28c516-33ae` as SP `workspace-assessor` | DEV workspace admin | ✅ connected as the assessment service principal (`src-ws-dev`) |
| 2 | **USE CATALOG + BROWSE on catalog `eurostream`** for `workspace-assessor` | DEV table inventory, grants, lineage — currently invisible (FND-23) | `GRANT USE CATALOG, BROWSE ON CATALOG eurostream TO <sp>` | DEV workspace admin | ❌ (OQ-10) |
| 3 | **DEV bundle source** (`eurostream-free`, deployed 2026-09-28) | 4 jobs + 3 pipelines run with no source in repo (FND-11) | Restore `databricks/` from the commit before `c78138d`, or export `/Users/…/.bundle/eurostream-free` | Repository owner | ❌ (OQ-09) |
| 4 | **Production topology**: which Kafka (Aiven / MSK), broker region, topic list with retention and partitions; Turso region; whether `infra/main.tf` was applied | Ingestion design, residency, erasure scope (FND-13, FND-18) | Aiven console export, `terraform state list`, Turso dashboard | Platform owner | ❌ (OQ-05) |
| 5 | **Real upstream event producers** (shop, payment, web) or confirmation that data is synthetic | The repo only contains a Faker generator; volume and PII reality depend on it | Interview + system list | Product owner / sponsor | ❌ (OQ-01) |
| 6 | **Volumes and usage**: row counts per table, Kafka message rates, API/dashboard traffic ≥ 90 days | Orphan calls (bronze.clicks, fraud_alerts topic), sizing, backfill | DuckDB `SELECT count(*)` run by the client; Aiven metrics; Render logs | Data engineering lead | ❌ |
| 7 | **DPO position on erasure and retention** | Masking vs deleting bronze, suppression list, audit retention, Delta history (FND-05, FND-07) | DPO written answer | Data Protection Officer | ❌ (OQ-04) |

## Recommended
| # | Source | Why | How to obtain | Client owner | Status |
|---|---|---|---|---|---|
| 8 | Fraud rule owner sign-off (velocity semantics, fraud flag expiry) | CONFLICT BR-01 | 30-min review of BR-01/BR-13 | Fraud / risk owner | ❌ (OQ-02) |
| 9 | Marketing consumer list for `gold.customer_360` | Consent gating (BR-12) | Interview | Marketing analytics owner | ❌ (OQ-07) |
| 10 | Production PII salt provenance (not the value) | Re-keying decision (FND-04) | Platform owner statement | Platform owner | ❌ (OQ-03) |
| 11 | Account-level read or a fresh SAT run (last SAT run 2026-10-05) | 11 account-level security checks not assessed | Client account admin runs SAT; Velox reads results | Databricks account admin | ⏳ SAT rows read 2026-11-05 (`src-sat-01`, run_id 1) |
| 12 | Databricks system tables (`system.billing`, `system.access`, `system.lineage`) read grant | Cost baseline and lineage of the DEV port | `GRANT SELECT ON SCHEMA system.billing …` | Account admin | ❌ |

## Optional
| # | Source | Why | How to obtain | Client owner | Status |
|---|---|---|---|---|---|
| 13 | Hugging Face dataset download stats | Size of the public exposure (FND-01) | HF account owner | Repo owner | ✅ metadata (`src-hf-api`); stats ❌ |
| 14 | Stakeholder interview notes | `stated` requirements beyond repo docs | Interviews | Sponsor | ❌ |

Received this run: code `src-code-01`, infra/CI `src-iac-01`, documents `src-docs-01`, git history `src-git`, DEV workspace metadata `src-ws-dev`, posture `src-posture`, SAT results `src-sat-01`, HF public metadata `src-hf-api`.
