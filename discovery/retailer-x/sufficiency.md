# Evidence sufficiency — Retailer X (run-01)

| Conclusion needed | Evidence required | In hand | State | If missing |
|---|---|---|---|---|
| Workloads in scope, with target component | Code inventory + workspace inventory | code ✅ · workspace UC ✅ | ✅ | — |
| Which workloads to retire | Usage ≥ 90 days incl. month/quarter end | none | ❌ | Insufficient evidence. Needs production usage logs. If skipped, everything is migrated "just in case". |
| Migration effort | Complexity per workload + trial conversion | manual L/M/H ✅ · no trial; prior attempt exists but is unreviewed | ⚠️ range only | — |
| Erasure completeness on Databricks | Every PII surface + reach proof | code ✅ · workspace current state ✅ (suppressed customer absent in silver/gold, bronze masked) · Delta history / bus / HF ❌ | ⚠️ | Time travel, Kafka and the HF copy may still hold erased data |
| EU residency | Region of every store and processor | AWS IaC eu-central-1 ✅ · workspace us-east-2 ✅ · Aiven/Turso/HF/GHA ❌ | ⚠️ (one breach proven) | — |
| Security posture score | SAT or workspace read | SAT run 1 + live SP read ✅, 75% weighted coverage | ✅ score 2/5 | 11 account-level checks not assessed |
| Data volume / sizing | Row counts and growth from production | workspace only, ~1.5k rows per table, synthetic | ❌ | Cluster and cost sizing cannot be stated |
| Cost baseline | Current spend + Databricks usage | `system.billing.usage` 2026-09-25→10-08 ≈ 51.3 DBU ✅ · current hosting spend ❌ | ⚠️ | No business case |
| **Usage window** | Source / start / end | none for the legacy runtime; Databricks `system.lakeflow.job_run_timeline` 2026-09-28→2026-10-05 (8 days, no month end) | ❌ | Nothing can be called orphan |
