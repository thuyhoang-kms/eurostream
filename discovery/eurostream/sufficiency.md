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
