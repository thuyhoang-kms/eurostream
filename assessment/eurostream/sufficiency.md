# Evidence sufficiency — eurostream  (run-01, 2026-11-05)

Decision served: the client data lead decides **what migrates, in which wave, and the pilot**.

| Conclusion needed | Evidence required | In hand | State | If missing |
|---|---|---|---|---|
| Inventory of every data store, workload and consumer | Code read per store, with locators | 88 inventory objects across 11 systems (src-code, src-ci, src-ws-dev) | ✅ | — |
| DEV Databricks tables and grants | UC metadata for catalog `eurostream` | Pipelines and jobs ✅; tables ❌ (no grant) | ⚠️ | The DEV port's tables stay unknown. Needs OQ-17 |
| Topics → tables → consumers lineage | Code edges | 52 edges (`dependency_edges.jsonl`) | ✅ | — |
| Business rules and their status | Code first, then a diff with the docs | 24 rules: 10 VERIFIED, 4 CONFLICT, 8 CODE-ONLY, 1 CONFIG-ONLY, 1 UNRESOLVED | ✅ | The owners must still confirm the CONFLICT and CODE-ONLY rules |
| Erasure reaches every PII store | Code read plus a reproduction | Reproduced: rebuild brings erased customers back (exec-09); HF, bus and audit not reached (code) | ✅ | — |
| Real source systems behind the bus | Interview and Kafka topic list | ❌ (producer is synthetic) | ❌ | Ingestion scope for wave 1 cannot be stated. Needs OQ-02 |
| Volumes / backfill size | Row counts per table | ❌ | ❌ | Backfill effort is unknown. Needs OQ-16 |
| **Usage window** | Access logs ≥ 90 days, including a month-end and a quarter-end. Source: none; start: —; end: —; restart: n/a | ❌ | ❌ | Nothing can be called orphan or retired on usage grounds (every `orphan` is null). Needs OQ-20 |
| Complexity per workload | Code read (manual tier) | Manual L/M/H on 13 code workloads | ⚠️ | Manual triage only. No Lakebridge Analyzer: the estate is Python, not SQL/ETL, so it does not apply |
| Effort / estimate | Complexity, plus reuse of the DEV port | Complexity ⚠️; reuse of the DEV port ❌ | ⚠️ | Range only, once OQ-14 is answered |
| Security posture score | Admin read or SAT results | 10 pass, 5 fail, 53 not assessed (20% weighted) | ❌ | §7 reads "not scored". Needs OQ-18 |
| Residency (EU only) | Region per store | DEV metastore us-east-2 (observed); Render frankfurt (config); others unknown | ⚠️ | Needs OQ-07 and OQ-15 |
