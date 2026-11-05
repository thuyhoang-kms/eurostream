# Evidence sufficiency — eurostream  (run-01, 2026-11-05)

Axis C: the delivery lead decides **scope, waves and L/M/H per workload** before the client demo.

| Conclusion needed | Evidence required | In hand | State | If missing |
|---|---|---|---|---|
| Inventory of every data object, workload and consumer | Code + config + workspace listing | 65 inventory records from code and DEV jobs/pipelines (`inventory.jsonl`) | ⚠️ | DEV catalog `eurostream` tables not visible (OQ-10) — DEV half incomplete |
| Which objects are unused (retire) | Usage ≥ 90 days incl. month-end/quarter-end | none | ❌ | No object may be called orphan; `bronze.clicks`, `fraud_alerts` topic stay `defer` (OQ-08) |
| L/M/H complexity per workload | Analyzer or manual triage + trial conversion | manual triage on 13 local workloads (`complexity_source: manual`); DEV workloads unscored | ⚠️ range only | Lakebridge Analyzer does not cover Python/DuckDB; triage is labelled manual |
| Business rules with status | Code locators + doc diff | 24 rules: 10 VERIFIED, 3 CONFLICT, 10 CODE-ONLY, 1 DOC-ONLY | ✅ | Owners still to confirm intent (OQ-02, OQ-07) |
| Dependency graph topics → tables → consumers | Code + workspace job graph | 97 edges (`dependency_edges.jsonl`) | ✅ | External consumers of HF dataset unknowable |
| GDPR erasure coverage per store | Erasure code path + store inventory | every store carries `holds_pii`/`erasure_reaches`; 10 verified claims | ✅ | Adequacy is a DPO decision (OQ-04) |
| Security posture score | SAT or workspace read | score 2/5, 75% weighted coverage, basis workspace + SAT run 1 (2026-10-05) | ⚠️ | 11 account-level + 2 compute checks not assessed; SAT run is a month old |
| Behaviour reproduced (not only read) | Test suite / demo run on fixtures | none — `uv 0.8.23` is older than 0.9 and cannot run in the sandbox | ❌ | All behaviour findings are `stated`; upgrade uv (`curl -LsSf https://astral.sh/uv/install.sh \| sh`) to reproduce |
| Volume / sizing for estimate | Row counts, message rates | none | ❌ | Estimate is drivers + range only |
| Target region | Production workspace region | DEV only (us-east-2) | ❌ | Production workspace must be decided (OQ-05) |
| **Usage window** | log source · start · end · last restart | none — no query log, no API access log, no Kafka metrics | ❌ | Ask for Render logs and Aiven metrics ≥ 90 days |
