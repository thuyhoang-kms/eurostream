# Source request — eurostream (Retailer X)  (run-01, 2026-11-05)

| # | Source | Why | How to obtain | Client owner | Status |
|---|---|---|---|---|---|
| 1 | **Databricks DEV workspace, read-only** (`dbc-9e28c516-33ae.cloud.databricks.com`) | Pipelines, jobs, Unity Catalog and security posture | Already granted: service principal `workspace-assessor`, non-admin | DEV workspace admin | ✅ connected (src-ws-dev). ⚠️ It cannot see catalog `eurostream` (OQ-17), and the posture is unscored at 20% coverage (OQ-18) |

## Required — the core conclusions are impossible without these
| # | Source | Why | How to obtain | Client owner | Status |
|---|---|---|---|---|---|
| 2 | `BROWSE` + `USE CATALOG` on catalog `eurostream` for `workspace-assessor` | DEV table inventory, grants and lineage of the existing port | `GRANT BROWSE, USE CATALOG ON CATALOG eurostream TO <sp>` (metadata only, no rows) | DEV workspace admin | ❌ OQ-17 |
| 3 | **Source of bundle `eurostream-free`** (`databricks/` before commit c78138d, or the deployed `.bundle` files) | The DEV port must be reviewed before scope and estimate | `git show c78138d^:databricks/`, or the author exports the bundle | Bundle author (name: ?) | ❌ OQ-14 |
| 4 | **The real upstream systems** for orders, clicks and payments (names, interfaces, volumes) | The only producer in the code is synthetic Faker | Interview the platform owner, plus the Kafka topic list | Client data lead | ❌ OQ-02 |
| 5 | Aiven Kafka: host/region, topic list, retention, consumer groups | Ingestion design, PII retention, residency | Aiven console export, read-only | Platform owner | ❌ OQ-06 |
| 6 | Row counts and sizes of the live warehouse (`eurocart.duckdb` from the CI cache, or the Turso mirror) | Volume drives the backfill and the estimate | `SELECT count(*)` per table by the client; metadata only | Platform owner | ❌ OQ-16 |
| 7 | Usage of the API and dashboard over ≥ 90 days (Render and HF Space access logs) | Without it, no consumer may be called unused | Render log export; HF Space analytics | Platform owner | ❌ OQ-20 |

## Recommended
| # | Source | Why | How to obtain | Client owner | Status |
|---|---|---|---|---|---|
| 8 | Region and account owner for Turso, Render, Hugging Face, Aiven; whether `infra/main.tf` was applied | ADR-0001 residency proof (SEC-02) | Console screenshots or exports | Platform owner | ❌ OQ-07 |
| 9 | Visibility and version history of HF dataset `swadhinbiswas/eustream` | Erased data in public history | HF repo settings page | Client data lead | ❌ OQ-04 |
| 10 | SAT results (catalog `sat` exists in DEV), or a one-time admin read | Scores the security posture | Read-only SQL on `sat.security_analysis.security_checks` on a SQL warehouse | You / DEV admin | ❌ OQ-18 |
| 11 | Business owners for fraud, finance/payments, marketing and the DPO | Every CONFLICT or CODE-ONLY rule needs an owner | Engagement lead | Engagement lead | ❌ OQ-19 |
| 12 | Expected outputs or UAT cases (e.g. the erasure demo output, fraud examples) | The most reliable statement of behaviour | QA / project folders | Client tech lead | ❌ |

## Optional
| # | Source | Why | How to obtain | Client owner | Status |
|---|---|---|---|---|---|
| 13 | Current hosting cost (Render, Aiven, Turso, HF) | Business-case baseline | Invoices | Finance | ❌ |
| 14 | Interview notes with the data lead and the DPO | Intent behind the code-only rules | Interview | Engagement lead | ❌ |

Received and registered: src-code (`src/`), src-cfg (`render.yaml`, `Dockerfile`, `docker-compose.yml`, `governance/`), src-ci (`.github/workflows/`), src-iac (`infra/main.tf`), the documents (`README.md`, `docs/`, `paper/`, `SECURITY.md`), src-ws-dev (DEV workspace metadata) and src-repro (local runs on synthetic data). Hashes are in `runs/2026-11-05_run-01-member/manifest.json`.
