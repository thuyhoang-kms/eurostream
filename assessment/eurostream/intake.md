# Intake — eurostream (Retailer X)  (run-01, 2026-11-05)

**Assessment level:** code and workspace assessment. The DEV workspace `dbc-9e28c516-33ae.cloud.databricks.com` was read read-only as the service principal `workspace-assessor` through the Databricks CLI (profile `eurostream-assessor`). No table rows were read.

## Team knowledge
No team-knowledge tool was attached to this session, so Axis 0 was skipped.

## Axis A — type
- **Primary type:** **1 Migration / modernization**. Status: `stated`. The person chose this on the intake card on 2026-11-05.
- **Driver:** the Python platform cannot scale or govern GDPR. That platform is a DuckDB file warehouse, a SQLite/Kafka bus, a Turso mirror and a public Hugging Face lake. The evidence is the single-writer stores (FND-19) and the erasure gaps (FND-01, FND-03, FND-04, FND-05).
- **Secondary type:** 3 Consolidation, for the security posture of the DEV workspace only. A partial Databricks port already runs there (FND-07).
- **To confirm:** OQ-19, the decision owner and date.

## Axis B — inputs per source system
| System | Level | In hand (source_id) | Missing to reach next level |
|---|---|---|---|
| SYS-1 DuckDB warehouse | L2 | src-code (`src/eurostream/warehouse.py`), src-repro (local run on synthetic data) | the real `eurocart.duckdb` file: row counts and size (L3) |
| SYS-2 SQLite bus / SYS-3 Aiven Kafka | L2 | src-code, src-ci | Kafka host, region, topic list and retention (OQ-06) |
| SYS-4 Turso | L2 | src-code | account, region, row counts (OQ-07) |
| SYS-5 Hugging Face dataset | L2 | src-ci, src-code | visibility, version history, downloads (OQ-04) |
| SYS-6/7 local lake and logs | L2 | src-code | — |
| SYS-8 Databricks DEV | L4 (partial) | src-ws-dev (pipelines, jobs, metastore, posture as a non-admin) | BROWSE on catalog `eurostream` (OQ-17); admin read or SAT results for the posture (OQ-18) |
| SYS-9 AWS Terraform | L2 (design only) | src-iac | whether it was ever applied (OQ-07) |
| SYS-10/11 Render, HF Space | L2 | src-cfg, src-ci | access logs ≥ 90 days (OQ-20) |
| Documents | L1 | README, docs/, ADRs, RFC, postmortem, paper, SECURITY.md | business owners; UAT or expected outputs |

## Axis C — decision
> This report is for **the client data lead** (name: ?) to decide **what migrates, in which wave, and which pilot** before **build kick-off** (date: ?).

Status: `stated` (scope & waves chosen on the intake card). The owner and date are `assumed`; see OQ-19.

## Blocking questions this turn (≤5)
OQ-01 (erasure design), OQ-02 (the real upstream systems), OQ-14 (the source of the DEV bundle), OQ-15 (the EU region), OQ-18 (how to score the posture). See `runs/2026-11-05_run-01-member/review.md`.
