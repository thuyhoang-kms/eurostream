✅ Databricks workspace bound read-only: SQL as thuyhoang@kms-technology.com (MCP); REST as service principal `workspace-assessor` (profile `eurostream-assessor`, not admin) — 2026-10-08

# Source request — Retailer X

## Required
| # | Source | Why | How to obtain | Client owner | Status |
|---|---|---|---|---|---|
| 1 | Read-only workspace access | Live estate, security posture | Already granted | Platform owner (name: ?) | ✅ src-ws, src-posture |
| 2 | Application code, DDL, CI, IaC | Rules, inventory, dependencies | Repo | Platform Engineering | ✅ src-code, src-ci, src-iac |
| 3 | The real source systems behind `orders`, `clicks`, `payments` (today: the synthetic `EventGenerator`) | Ingestion design, volume, CDC | Owner names each source, its format and rate | Platform owner (name: ?) | ❌ OQ-04 — without it, ingestion scope and volume cannot be concluded |
| 4 | Production volumes and usage ≥ 90 days (Kafka topic sizes, DuckDB/Turso row counts, API access logs) | Sizing, orphans, consumers | Aiven console, Turso dashboard, Render logs | Platform owner | ❌ — no retire decision is possible |
| 5 | Region and retention of Aiven, Turso, Hugging Face, Render, GitHub Actions cache | GDPR residency and erasure reach | Provider consoles | Platform owner | ❌ OQ-03, OQ-05 |
| 6 | The removed `databricks/` source (commit 85b9686) and who owns the workspace deployment | Prior attempt; it is live but not in VCS | `git show 85b9686`; owner interview | thuyhoang@kms-technology.com (deployer) | ⏳ OQ-02 — not read on purpose (see review.md) |

## Recommended
| # | Source | Why | How to obtain | Client owner | Status |
|---|---|---|---|---|---|
| 7 | DPO / legal statement of the erasure SLA and retention periods | `EUROSTREAM_ERASURE_SLA_SECONDS=60` is an application target, not a legal one | DPO | DPO (name: ?) | ❌ OQ-06 |
| 8 | Marketing consumer of `gold.customer_360` | The consent filter lives downstream and is not in the repo (README §Medallion) | Interview | Marketing lead (name: ?) | ❌ OQ-07 |
| 9 | Account-level SAT results / account admin read | 11 checks not assessed | Client account admin | Account admin (name: ?) | ❌ |
| 10 | Test suite run log (`uv run pytest`) | `reproduced` evidence | Run locally | — | ⏳ not run in this session |

## Optional
Masked samples ≤ 20 rows/table · paper/paper.md review · site/ docs portal.
