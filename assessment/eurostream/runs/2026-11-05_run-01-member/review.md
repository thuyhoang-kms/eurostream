# Review — eurostream run-01 (2026-11-05, member)

**Read, in order:**
1. Code first, with documents kept out of context: `src/`, config, CI, `infra/`. This was a parallel scan of 5 code areas.
2. Documents second, in a separate pass: postmortem, architecture, ADRs, RFC, README, paper, SECURITY.md.
3. The DEV workspace, read-only as service principal `workspace-assessor`.

Code-derived rules were then diffed against the documents. Worker line numbers were re-checked against the files before any record was written.

**Produced:** 11 source systems · 88 inventory objects (44 data, 20 workloads, 24 consumers) · 24 business rules · 52 dependency edges · 32 findings (27 from code and the workspace, 5 from the posture script) · 18 requirements · 20 open questions · `posture.json` + `RDY-security` (not scored).

## Needs a human now (≤5)
1. **OQ-01, the DPO:** erased customers come back after a full rebuild (FND-01, reproduced). Should the target filter suppressed ids or delete Bronze rows?
2. **OQ-02, the data lead:** the only producer is a synthetic Faker generator. Which real systems feed orders, clicks and payments?
3. **OQ-14, the bundle author:** a Databricks port (3 Lakeflow pipelines, 4 jobs) already runs in DEV, but its source was removed in c78138d. Recover it?
4. **OQ-15, the platform owner:** the DEV metastore is in us-east-2, while ADR-0001 says EU only. Which EU region will production use?
5. **OQ-18, you:** the posture card timed out, so the posture is not scored at 20% coverage. Re-run it with your admin login, import SAT from catalog `sat`, or leave it unscored?

## rule_status distribution
VERIFIED 10 · CODE-ONLY 8 · CONFLICT 4 · CONFIG-ONLY 1 · UNRESOLVED 1 · DOC-ONLY 0 · DEAD 0. Calibration with a client expert has not happened yet, so the correction rate is unknown.

## Unsure (confidence low / medium)
- SYS-9: the AWS Terraform may never have been applied.
- SYS-3: the Kafka host is only in CI secrets.
- BR-13: the trade-off between suppression and fraud monitoring.
- BR-15: currency.
- FND-21: the commit-past-unprocessed sequence was read across sqlite.py:158–187 but not reproduced.

## What was run
- `posture.py` as the SP: `logs/exec-01`, `logs/exec-02`.
- Identity of the user profile, read only: `logs/exec-03`. The user's login was NOT used for any read.
- UC and workload metadata, list/get only: `logs/exec-04`, `logs/exec-05`.
- `uv sync` failed. uv 0.8.23 is older than 0.9 and cannot run in this sandbox; upgrade uv with `curl -LsSf https://astral.sh/uv/install.sh | sh`. See `logs/exec-06`.
- Fallback install with pip into a temp venv: `logs/exec-07`.
- `pytest`: 18 failed, 59 passed. All 18 failures are `tests/databricks/*`, which need the removed `databricks/` folder. See `logs/exec-08`.
- Erasure-resurrection repro on synthetic data in a temp DuckDB, with no Turso and no network: `logs/exec-09` (FND-01, BR-17).

**Not reproduced, and why:** FND-09, FND-10 and FND-21 need a live Kafka or a crash injection, which was out of scope for this run. FND-02 and FND-15 are about the public deployment and were not probed (no client endpoint is ever called). The Turso and HF reach of erasure was read from code only.

## Deliberately not concluded
- No orphan or retire on usage grounds: there is no usage log at all, so every `orphan` is null.
- No volumes or estimate.
- No security score.
- No disposition per object; that is assessment-synthesis.
- Lakebridge Analyzer was not run, because the estate is Python, not SQL/ETL.
- 9 further Turso mirror tables are covered by locator `src/eurostream/warehouse.py:191-206` and not inventoried one by one.
- SAT's own jobs and the `sat` catalog are assessment tooling, not client estate, so they were not inventoried.

## How to merge
Review each card in the **Assess** step, or the Workspace panel's **Review** tab. Decisions land in `assessment/eurostream/registers/`. Nothing in this run is written there.
