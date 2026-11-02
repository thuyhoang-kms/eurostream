# Review — Retailer X, run 2026-10-08_run-01

**Read, in order:**
1. Code (`src/`, `governance/`, `tests/databricks/`, `.github/workflows/`, `infra/`). Docs were kept out of the code pass.
2. Documents (README, RFC 0001, ADR 0001–0003, postmortem, architecture.md, gdpr_erasure_flow.md).
3. Workspace dbc-9e28c516-33ae (Unity Catalog, `system.lakeflow`, `system.billing`).
4. SAT run 1 (2026-10-05) plus a live read as service principal `workspace-assessor`.

**Produced:** 15 requirements · 18 rules · 38 inventory objects · 40 edges · 50 findings (26 code/workspace + 24 SAT/posture) · 15 open questions · 30 dispositions · 5 readiness records.

## Needs a human now (≤5)
1. **FND-01 / FND-SEC-VX-RES-1**: EU PII in us-east-2. Accept, and send OQ-03 to the DPO.
2. **FND-18**: the live deployment's source was removed in `c78138d`. Accept, and answer OQ-02 (keep, rebuild or discard).
3. **FND-04 / FND-05 / FND-06**: public Hugging Face dataset, unauthenticated API, SQL injection. Accept as wave 0 containment.
4. **BR-06 / OQ-07**: the consent rule (`bool_and` over all orders). Business owner to decide.
5. **FND-SEC-GOV-21**: SAT flags a metastore owned by the creating account. Reject it if the metastore is Databricks-managed (a known generic check).

## rule_status distribution
VERIFIED 7 · CONFLICT 4 (BR-10, BR-11, BR-12, BR-17) · CODE-ONLY 4 · CONFIG-ONLY 2 · UNRESOLVED 1 · DOC-ONLY 0 · DEAD 0

## Unsure (confidence < 0.6)
None below 0.6. Lowest: NFR-01 (0.7) and the inferred workspace edges silver→gold (dependency_edges, `kind: inferred`).

## What was run, and what stayed unreproduced
- **Run:** `posture.py` (GET only, 44 calls), the swarm scan (5 workers), and `verify_claims` on 12 high-impact claims (12 confirmed).
- **Workspace erasure check:** the suppressed customer has 0 rows in silver/gold and no clear email in bronze, so the target design works on current data.
- **Not run:** the repo test suite (`uv run pytest`) and the local demo. FND-02, FND-03, FND-10 and FND-12 rest on `stated` code evidence, not `reproduced`.
- **Workers:** three ran out of read budget. The docs worker covered 4 of 11 documents; I read the ADRs and the postmortem myself. `paper/paper.md`, CONTRIBUTING and SECURITY were not read.

## Deliberately not concluded
- Effort is a range only: there was no trial conversion and no real volume.
- Nothing is called orphan: there is no usage log (the Databricks job history covers 8 days).
- The removed `databricks/` source (commit 85b9686) was **not read**. It is the subject of OQ-02, and reading it would have mixed a prior design into the legacy assessment.
- The cost business case: current hosting spend is unknown.
- Account-level security checks (11): these need account admin or account-level SAT.

## How to merge
Velox → Workspace → **Review**: accept or reject each record. Decisions land in `discovery/retailer-x/registers/`. Then ask for **"regenerate"** to build the final report from the registers only.
