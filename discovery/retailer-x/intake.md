# Intake — Retailer X (EuroStream)  (run-01, 2026-10-08)

## Axis A — type
Primary **Migration / modernization** `inferred`. A Python + DuckDB + SQLite/Kafka (Aiven) + Turso medallion platform with a FastAPI serving layer (`pyproject.toml:9-20`, `src/eurostream/warehouse.py`, `src/eurostream/bus/`) is to move to Databricks.
Secondary **Real-time / streaming**: a payment fraud scorer on the event bus (`src/eurostream/streaming.py:54-56`).
A previous migration attempt exists. The Databricks workspace already holds a deployed `eurostream` catalog (Lakeflow streaming tables and materialized views, 4 jobs, created 2026-09-28). Its source (`databricks/`, 94 files) was removed from the repo in commit `c78138d` on 2026-10-08.
The real driver is not stated in any source. It is to be confirmed in OQ-01.

## Axis B — inputs per source system
| System | Level | In hand (source_id) | Missing to reach next level |
|---|---|---|---|
| EuroStream application (Python) | L2 | src-code (src/, governance/, tests/), src-ci (.github/workflows), src-iac (infra/main.tf, render.yaml, Dockerfile) | usage or volume from a running production instance; production config values |
| EuroStream documentation | L1 | src-docs (README, RFC 0001, ADR 0001-0003, postmortem INC-2026-001, architecture.md, gdpr_erasure_flow.md) | stakeholder interviews, SLAs signed by an owner, a data volume statement |
| Hosted runtimes (Aiven Kafka, Turso, Render, Hugging Face, GitHub Actions) | L0 | named in code only | region and retention settings, access logs |
| Databricks workspace dbc-9e28c516-33ae (AWS us-east-2) | L4 | src-ws (Unity Catalog, `system.lakeflow`, `system.billing`), src-sat (SAT run 1, 2026-10-05), src-posture | account-level checks (11 not assessed); audit log access; the removed `databricks/` source as a reviewed artefact |

## Axis C — decision
> This report is for **the Retailer X platform owner (name: ?)** to decide **which workloads move to Databricks, in which waves, and what must be fixed first (GDPR erasure, EU residency, security posture), including whether the existing workspace deployment is kept, redone or discarded**, before **the migration is committed (date: ?)**.  `assumed` — OQ-01, OQ-02

## Blocking questions this turn (≤5)
OQ-01 driver and decision owner · OQ-02 fate of the existing workspace deployment · OQ-03 EU residency vs us-east-2 workspace · OQ-04 real sources vs synthetic producers · OQ-05 public Hugging Face dataset
