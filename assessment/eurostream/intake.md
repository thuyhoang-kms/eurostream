# Intake — eurostream  (run-01, 2026-11-05)

Level: **code and workspace assessment** (brief from the Assess step) — DEV `dbc-9e28c516-33ae.cloud.databricks.com`, read as service principal `workspace-assessor` (profile `eurostream-assessor`, not admin) through the Databricks CLI, metadata only; SAT result rows imported with the person's explicit approval (2026-11-05).

## Team knowledge
No team-knowledge tool attached to this session — axis skipped.

## Axis A — type
Primary **Migration / modernization** `inferred` — Python estate (DuckDB warehouse, SQLite/Kafka bus, Turso, FastAPI, GitHub Actions scheduler) moving to Databricks; driver stated only as a PoC objective (`.velox/PoC.md:5`, "MIGRATION scope"). Secondary **governance / GDPR** (erasure, PII, consent — `README.md`, `docs/gdpr_erasure_flow.md`). Real business driver ("why now?") not stated by the client — OQ-01.

## Axis B — inputs per source system
| System | Level | In hand (source_id) | Missing to reach next level |
|---|---|---|---|
| SYS-1 DuckDB warehouse | L2 | code `src-code-01` (DDL, transforms) | row counts, sizes, query usage (L3) |
| SYS-2 SQLite bus · SYS-3 Aiven Kafka | L2 | code, `.env.example`, `render.yaml` | broker host/region, topic retention, consumer lag (L3) |
| SYS-4 AWS MSK · SYS-7 S3 | L2 (design only) | `infra/main.tf` | whether applied (Terraform state / AWS console) |
| SYS-5 Turso | L2 | code | region, table sizes |
| SYS-6 HF dataset | L3 | public API metadata `src-hf-api` | download/usage stats |
| SYS-8 local files | L2 | config paths | — |
| SYS-9 Databricks DEV | L4 (partial) | jobs, pipelines, posture, SAT `src-ws-dev`, `src-sat-01` | catalog `eurostream` tables/grants (SP lacks USE CATALOG — OQ-10); system tables (billing, lineage) |
| SYS-10/11 Render, HF Space | L2 | `render.yaml`, `deploy-space.yml` | traffic / users |
| Documents | L1 | README, docs/adr, docs/rfc, SECURITY.md, `.velox/*.md` `src-docs-01` | client stakeholder interviews |

## Axis C — decision
> This report is for **the delivery lead** to decide **what migrates to Databricks, in which waves, with an L/M/H complexity per workload** before **the client demo**.  `stated` (chosen on the intake card, 2026-11-05).

## Blocking questions this turn (≤5)
OQ-01 (production event source + stop the public HF upload) · OQ-04 (DPO: erasure adequacy and retention) · OQ-05 (which Kafka, which regions) · OQ-09 (restore the DEV bundle source) · OQ-03 (which PII salt production used).
