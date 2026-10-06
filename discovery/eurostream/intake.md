# Intake — eurostream  (run-01, 2026-10-06)

## Axis A — type
Primary **1 Migration / modernization** `stated` — the user chose "cut over to Databricks" (session, 2026-10-06). Source: the local Python stack (`src/eurostream/`, DuckDB / FastAPI / Turso / in-process bus). Target: the Databricks build in `databricks/`, which is already deployed in catalog `eurostream`.
Secondary **5 Real-time / streaming** `inferred` — continuous fraud scoring (`databricks/notebooks/03_fraud_streaming.py`, `src/eurostream/streaming.py`).
Real driver ("why now?") — not stated yet → OQ-01.

Note: `databricks/README.md` says the Databricks build "does not call, replace, pause, or migrate" the Python app. So no cut-over path exists in code today. That is the gap this assessment measures.

## Axis B — inputs per source system
| System | Level | In hand (source_id) | Missing to reach next level |
|---|---|---|---|
| Python stack (`src/eurostream`, `tests/`) | L2 | code, tests, `governance/*.json` | run logs / volumes of the live demo (L3); is it still deployed anywhere? (`render.yaml`, `Dockerfile`) → OQ-02 |
| Databricks build (`databricks/`) | L2 → L4 | notebooks, Lakeflow (`dlt/`), SQL DDL, AppKit app, bundle (`dab/`) | — |
| Databricks workspace `dbc-9e28c516-33ae` | L4 | catalog `eurostream` (37 objects: bronze 14, silver 11, gold 7, governance 5; `lake` holds only Volume `exports`), `system.*`, `sat.security_analysis` (1 SAT run, 52 check rows) | job/pipeline run history depth → read in workspace step |
| Infrastructure (`infra/main.tf`, AWS eu-central-1) | L2 | Terraform | whether it is applied (no state in repo) |
| Documents | L1 | README, `docs/rfc/0001`, `docs/adr/0001-0003`, `docs/postmortem/inc-2026-001`, `paper/paper.md` | private runbook `docs/databricks/` is gitignored and absent → OQ-03 |

## Axis C — decision
> This report is for **the delivery lead / repo owner** to decide **whether the Databricks build is ready to become the primary EuroStream runtime, and which Python / DuckDB / Turso components to migrate, keep or retire**, before **no fixed date**.  `stated` (decision) · `assumed` (audience, date) — OQ-04

## Blocking questions this turn (≤5)
See `open_questions` in the run. Taken as defaults for now: audience = delivery lead, no deadline, scope excludes `site/`, `paper/`, `benchmarks/`.
