# Source request — eurostream  (run-01, 2026-10-06)

| # | Source | Why | How to obtain | Owner | Status |
|---|---|---|---|---|---|
| 1 | **Databricks workspace, read-only** | Deployed objects, job history, usage, cost, security | Velox workspace card | user | ✅ bound as thuyhoang@kms-technology.com (`dbc-9e28c516-33ae`) |

## Required
| # | Source | Why | How to obtain | Owner | Status |
|---|---|---|---|---|---|
| 2 | Python stack code + tests | Rules, inventory, behaviour to carry over | repo `src/eurostream/`, `tests/` | — | ✅ src-py |
| 3 | Databricks build code | Target design; compare with what is deployed | repo `databricks/` | — | ✅ src-dbx |
| 4 | Unity Catalog metadata for `eurostream` | Deployed inventory, drift against the code | `information_schema`, `system.information_schema` | — | ✅ src-uc |
| 5 | Job / pipeline run history ≥ 30 days | Proves the target actually runs (fraud stream, erasure, quality) | `system.lakeflow.*` | — | ⏳ workspace step |
| 6 | SAT results | Security readiness score | `sat.security_analysis.*` (1 run present) | — | ✅ src-sat |

## Recommended
| # | Source | Why | How to obtain | Owner | Status |
|---|---|---|---|---|---|
| 7 | Private runbook `docs/databricks/` | The README calls it the source of truth for the manual setup; it is gitignored | Repo owner shares it | repo owner (name: ?) | ❌ OQ-03 |
| 8 | Billing / usage | Cost baseline of the target | `system.billing.usage` | — | ⏳ workspace step |
| 9 | Where the Python stack runs today (Render, Docker, GitHub Actions) | Decides what "retire" really switches off | `render.yaml`, `.github/workflows/`, repo owner | repo owner | ⏳ OQ-02 |

## Optional
| # | Source | Why | How to obtain | Owner | Status |
|---|---|---|---|---|---|
| 10 | Terraform state for `infra/main.tf` | Whether the AWS resources exist | repo owner | repo owner | ❌ |
| 11 | Public Parquet lake consumers (Hugging Face) | External consumer of an export the target pushes only when `sync_huggingface=true` | dataset page / owner | repo owner | ❌ OQ-05 |
