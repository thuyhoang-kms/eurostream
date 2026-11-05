# Review — eurostream run-01 (2026-11-05, member)

**Read (in order):** code first (`src/`, docs out of context) → infra/CI (`infra/`, `.github/`, `render.yaml`, compose, `.env.example` names only) → documents (README, `docs/`, SECURITY.md, `.velox/*.md`) → DEV workspace metadata (jobs, pipelines, catalogs, secret scope names) → security posture (live + SAT results) → public HF dataset metadata. Six parallel readers scanned the code areas; every locator in the registers was re-checked by grep, and the 10 highest-impact claims were confirmed by independent verifiers (10/10 confirmed).

**Produced:** 11 source systems · 65 inventory · 24 business rules · 97 dependency edges · 47 findings (23 code/workspace + 24 security checks) · 10 open questions · RDY-security.

## Needs a human now (≤5)
1. **FND-01** public HF dataset with silver/gold customer data — accept, and ask the sponsor to stop the upload (OQ-01).
2. **FND-02 / FND-03** unauthenticated API incl. erasure and an SQL injection — accept.
3. **FND-11** DEV runs a bundle whose source was removed — accept; restore the source (OQ-09).
4. **BR-01** velocity rule CONFLICT — defer to the fraud owner (OQ-02).
5. **FND-13** DEV metastore in us-east-2 vs EU-only ADR — accept; production region (OQ-05).

## rule_status distribution
VERIFIED 10 · CONFLICT 3 (BR-01, BR-11, BR-12) · CODE-ONLY 10 · DOC-ONLY 1 (BR-24) · CONFIG-ONLY 0 · DEAD 0 · UNRESOLVED 0.

## Unsure (confidence medium/low)
SYS-3/4/7 (which Kafka and whether Terraform was applied) · obj-016 lineage_events writer not traced · obj-022 fraud_alerts topic consumer unknown · FND-07 masking adequacy · FND-14 concurrency (not reproduced).

## What was run
- `posture.py run` as `workspace-assessor` (exec-01: 20% coverage, not scored) → SAT rows read through the Serverless Starter Warehouse with the person's approval → re-run with `--sat-results` (exec-05: **score 2/5**, 31 pass / 24 fail / 13 not assessed, 75% coverage). SAT disagrees on GOV-20; the live read stands.
- DEV metadata reads (exec-02..04), GET only; no table rows read.
- `uv run pytest` (exec-06) **did not run**: uv 0.8.23 is older than 0.9 and cannot run in the sandbox — upgrade uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`). Therefore **every behaviour finding is `stated`, none `reproduced`** (races FND-14, duplicate alerts FND-09, Turso fallback FND-15).
- Lakebridge Analyzer **not run**: it has no Python/DuckDB source technology; complexity on local workloads is **manual triage**.

## Worker claims refuted by re-reading
- "Quality gate only warns" — refuted: `cli.py:252` raises and stops the DAG (BR-18).
- "Contracts are not checked in CI" — refuted: `ci.yml:58` runs `eurostream contracts`.
- Several API line numbers from readers were off by 10–30 lines; registers carry re-grepped lines.

## Deliberately not concluded
No object marked orphan/retire (no usage window). No effort number (no volumes, no trial conversion). No rationalisation matrix yet — next step `assessment-synthesis`. DEV catalog `eurostream` tables not inventoried (OQ-10). Whether events are real customer data (OQ-01).

## How to merge
Review in Velox's Assess step (or the Workspace panel's Review tab); decisions land in `assessment/eurostream/registers/`. Then say "regenerate" for the final report.
