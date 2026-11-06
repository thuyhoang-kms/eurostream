# Platform: infra, CI, Render, Docker, Databricks tests

Status: ok

Still working: the databricks test output was too large, so I'm re-reading just the assert lines from the two remaining test files.

Result: the Databricks target (`databricks/`, a 94-file bundle) was deleted in commit c78138d. The CI `databricks-app` job and `tests/databricks/*` still depend on it, so they fail today.

Findings:
- `.github/workflows/ci.yml:36` — `working-directory: databricks/app`; the directory no longer exists, so the `databricks-app` job (lines 32-50) fails at `npm ci` (cache path `databricks/app/package-lock.json`, line 43).
- `tests/databricks/test_bundle_contracts.py:6` — `DAB = ROOT / "databricks" / "dab"` is missing. All 5 tests fail; `pyproject.toml:53` sets `testpaths = ["tests"]`, so the CI `test` job (`ci.yml:30`) fails too.
- `tests/databricks/test_critical_repairs.py:9` — `DATABRICKS_ROOT = REPO_ROOT / "databricks"` is missing, so every test in this file fails.
- `tests/databricks/test_notebook_contracts.py:11` — `NOTEBOOKS = REPO_ROOT / "databricks" / "notebooks"` is missing, so these tests fail as well.
- `.gitignore:37-46` — still ignores `docs/databricks/`, `.databricks/`, `databricks-target-*/` and `**/databricks/.dab-cache/`. A stale remnant.
- `.github/workflows/orchestrate.yml:82-90` — pushes `data/lake` to the Hugging Face dataset `swadhinbiswas/eustream` (`repo_type='dataset'`). The lake holds pseudonymized PII, and the repo has no visibility or private setting. *High, privacy.*
- `.github/workflows/orchestrate.yml:87` — `if not tok: print('HF_TOKEN missing'); exit(0)` makes the upload step silently succeed when the token is missing. *Medium, reliability.*
- `.github/workflows/orchestrate.yml:4-5` — runs on cron `0 */4 * * *`, on every push to master, and on dispatch. The concurrency group `orchestrate-medallion` (lines 12-14, `cancel-in-progress: false`) queues runs, so they don't overlap. *Medium, no env separation and no approval gate before it writes to production Turso/HF.*
- `.github/workflows/orchestrate.yml:18-26` — the warehouse cache holds `data/eurocart.duckdb`, `data/events.db` and `governance/pii_manifest.json`. The "cumulative lake" lives in the GitHub Actions cache, which can be evicted. The cache key also hashes the very manifest the pipeline rewrites. *Medium, durability and integrity.*
- `.github/workflows/orchestrate.yml:38-43` — the probe falls back to `backend=sqlite` on any Kafka error. The workflow then keeps going on a different backend and the data diverges. *Medium.*
- `.github/workflows/orchestrate.yml:5-6` — there is no `permissions:` block in `orchestrate.yml`, `ci.yml` or `deploy-space.yml`, so `GITHUB_TOKEN` gets its default scope. *Low.*
- `.github/workflows/deploy-space.yml:35` — the Space `swadhinbiswas/eustream` is a personal account. `upload_folder(folder_path='.')` at line 40 uploads the whole repo except the ignore list, and the 402 fallback publishes a static portal. It deploys automatically on every master push with no approval. *Medium.*
- `.github/workflows/deploy-space.yml:44` — the ignore list excludes `.git/**`, `data/**` and `notes/**` but not `governance/**`. `docs/**`, `tests/**` and `benchmarks/**` also go to the Space. *Low.*
- `infra/main.tf:109` — `client_subnets = var.subnet_ids`, and `subnet_ids` defaults to `[]` (line 166). `vpc_id` has no default. The MSK cluster can't be created as written. *Low.*
- `infra/main.tf:102-118` — no `at_rest` KMS key (MSK encrypts at rest with the AWS-managed key by default), and no logging or authentication block. *Low.*
- `infra/main.tf:139` — the MSK security group allows egress `0.0.0.0/0` on all ports. *Low.*
- `infra/main.tf:58-60` — S3 SSE uses `AES256` (SSE-S3), not a KMS CMK. *Low.*
- `infra/main.tf:5-13` — no `backend` block, so Terraform state is local. *Medium.*
- `infra/main.tf:25` — `environment` defaults to `"prod"`; there is no dev/stg separation. *Medium.*
- `infra/main.tf:1-166` — the Terraform is AWS-only (S3, IAM, MSK). Nothing in the repo provisions Render, HF, Turso, Aiven or Cloudflare, and the Terraform has no Databricks resources. The runtime actually uses Aiven Kafka, Turso, HF and Render, so the Terraform doesn't describe the real stack. *Medium.*
- `render.yaml:5` — plan `free`, `autoDeploy: true`. The `/health` path is not authenticated, and the service is publicly reachable. Production has no environment separation. *Medium.*
- `render.yaml:30-31` — `HF_TOKEN` is injected into the public API service. Whether the API needs it is unclear. *Low.*
- `Dockerfile:41` — exposes 7860 (the HF Space port), while `docker-compose.yml:6` maps `8000:8000` and its healthcheck (line 15) hits `localhost:8000`. The Dockerfile CMD serves on 7860, so compose's API healthcheck and port mapping point at a closed port. *Medium, bug.*
- `Dockerfile:21` — the image source label is `https://github.com/your-org/eurostream`, a placeholder. *Low.*
- `site/deploy.sh:19` — `grep -oP` is GNU-only and fails on macOS. *Low.*
- `.github/workflows/ci.yml:3-7` — CI runs on PRs and on push to master/main, and `deploy-space.yml` and `orchestrate.yml` also trigger on push to master. Deploys don't wait for CI.
- `.github/workflows/orchestrate.yml:59` — `eurostream stream --max-events 3000` does not match the "real-time" label. It is a bounded batch in a 15-minute runner.

Inventory (1, 2, 3, 5):
- **Hosted services:**
  - AWS provider `region = "eurostream"`-style pin: `infra/main.tf:16-17` `region = "eu-central-1"`.
  - Resources: `aws_s3_bucket "lake"` (private, versioned), `aws_iam_role "pipeline"` (assumed by `ec2.amazonaws.com`), `aws_msk_cluster "events"` (3× `kafka.t3.small`, kafka 3.6.0, TLS), `aws_security_group "msk"` (ingress 9094 from `10.0.0.0/16`).
  - Render: `render.yaml:2-6` `eurostream-api`, `type: web`, `env: docker`, `plan: free`, `region: frankfurt`. Start command `uvicorn eurostream.api:app --port $PORT`, health check `/health`.
  - Render env: Kafka `SASL_SSL` with `SCRAM-SHA-256`. The username, password, bootstrap, Turso URL and token, `EUROSTREAM_PII_SALT` and `HF_TOKEN` are all `sync: false`, i.e. set in the dashboard.
  - Hugging Face: Docker Space `swadhinbiswas/eurostream` (`deploy-space.yml:35`, secret `HF_TOKEN`); dataset `swadhinbiswas/eustream` (`orchestrate.yml:89`).
  - Kafka is Aiven-style SASL/SCRAM, with bootstrap taken from the secret `KAFKA_BOOTSTRAP_SERVERS` (`orchestrate.yml:34`). The Aiven provider isn't named in the files I read.
  - Turso uses the secrets `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` (`orchestrate.yml:56-57`).
  - Cloudflare Pages: `site/wrangler.toml:1` name `eurostream-docs`, `site/wrangler.toml:10` `SITE_URL = "https://eurostream-docs.pages.dev"`. Deploy is manual via `site/deploy.sh:28-31` (`wrangler pages deploy dist`) or `make site-deploy` (`Makefile:51-52`). No Actions workflow deploys it.
- **Workloads:**
  - `orchestrate` pipeline (`orchestrate.yml:1-14`): cron `0 */4 * * *`, push to master, dispatch; `timeout-minutes: 15`, job `medallion`. The steps are:
    1. Restore the cache.
    2. Probe Kafka.
    3. `eurostream produce --events 1000`.
    4. `eurostream stream --max-events 3000`.
    5. `eurostream transform --incremental`.
    6. `eurostream sync-turso`.
    7. Push `data/lake` to the HF dataset.
  - `CI` (`ci.yml:3-11`): PR, push to master/main, dispatch. Jobs are `lint-typecheck`, `test`, `databricks-app`, `contract` (`eurostream contracts --baseline governance/contracts.json`), `docker` (build, then `docker run eurostream demo`) and `docs`. There are no timeouts.
  - `deploy-space` (`deploy-space.yml:3-16`): push to master with path filters, `timeout-minutes: 5`.
- **Tests expect (all missing from the repo):**
  - Bundle (`databricks/dab/`):
    - `databricks.yml`.
    - `resources/pipelines.yml` (3 pipelines, `channel: CURRENT`, `serverless: true`).
    - `resources/jobs.yml` with jobs `eurostream_art17_erasure`, `eurostream_erasure_benchmark` and `eurostream_fraud_continuous`.
    - `resources/app.yml` with the groups `eurostream_dpo_operators` and `eu

## Findings

- `.github/workflows/ci.yml:36` — databricks-app job sets working-directory: databricks/app, which was deleted in commit c78138d, so the job fails at npm ci
- `tests/databricks/test_bundle_contracts.py:6` — DAB = ROOT/'databricks'/'dab' does not exist in the repo, so all tests in this file fail and break the CI pytest job
- `tests/databricks/test_critical_repairs.py:9` — DATABRICKS_ROOT = REPO_ROOT/'databricks' does not exist, so every test reading sql/dlt/notebooks files fails
- `tests/databricks/test_notebook_contracts.py:11` — NOTEBOOKS = REPO_ROOT/'databricks'/'notebooks' does not exist, so the notebook contract tests fail
- `.gitignore:37` — Still ignores docs/databricks/, .databricks/ and databricks-target-*/ although the Databricks implementation was removed (stale remnant)
- `.github/workflows/orchestrate.yml:90` — Uploads data/lake (pseudonymized PII lake) to Hugging Face dataset swadhinbiswas/eustream with no private/visibility setting
- `.github/workflows/orchestrate.yml:87` — Missing HF_TOKEN makes the upload step print a message and exit(0), so the pipeline reports success without publishing
- `.github/workflows/orchestrate.yml:5` — Workflow runs on cron every 4 hours and also on every push to master, writing to production Turso/HF with no environment or approval gate
- `.github/workflows/orchestrate.yml:18` — Cumulative warehouse (duckdb, events.db, pii_manifest.json) is persisted only in evictable actions/cache keyed on the manifest hash
- `.github/workflows/orchestrate.yml:42` — Kafka probe falls back to backend=sqlite on any exception, silently switching the event bus and diverging data
- `.github/workflows/deploy-space.yml:44` — upload_folder of '.' to the HF Space ignores only .git, .venv, site, notes, assets, data, so governance/, docs/, tests/ are published; deploys on every master push without approval
- `infra/main.tf:166` — subnet_ids defaults to [] and vpc_id has no default, so the MSK cluster (client_subnets) cannot be created as written
- `infra/main.tf:139` — MSK security group allows egress 0.0.0.0/0 on all ports and the cluster has no at-rest KMS key, auth, or logging config
- `infra/main.tf:5` — No terraform backend block (local state) and environment defaults to prod, so there is no environment separation; Terraform covers only AWS while runtime uses Render/HF/Turso/Aiven
- `render.yaml:5` — Render service eurostream-api runs plan free with autoDeploy true and receives HF_TOKEN and EUROSTREAM_PII_SALT, no environment separation
- `Dockerfile:41` — Image exposes/serves port 7860 but docker-compose.yml maps 8000:8000 and healthchecks localhost:8000, so compose api is unreachable/unhealthy
- `site/deploy.sh:19` — Uses grep -oP (GNU-only) to parse wrangler.toml, failing on macOS
