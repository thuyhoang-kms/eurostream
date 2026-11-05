# infra, CI, deploy, config, tests/databricks

Status: ok

Result: The `databricks/` folder is gone, so `tests/databricks/*` are orphan tests. The AWS Terraform, Render, HF, Turso, Aiven and Cloudflare pieces are live, and the public HF dataset push is the main exposure.

Findings:
- `tests/databricks/test_bundle_contracts.py:6` — `ROOT/databricks/dab` is read, but no `databricks/` directory exists. The `ls databricks` check failed, and the only match for the glob `databricks*` was untracked `.velox/databricks.json`. Every test here would raise FileNotFoundError.
- `tests/databricks/test_critical_repairs.py:7` — Same orphan: `DATABRICKS_ROOT = databricks/`. It expects `sql/00_catalogs.sql` through `50_grants_and_tags.sql`, `dlt/*.py` and `notebooks/03_fraud_streaming.py`. None exist.
- `tests/databricks/test_notebook_contracts.py:12-13` — Expects `databricks/notebooks` and `databricks/sql`, and loads `notebooks/02_article17_erasure.py` at line 36. None exist. I read only the first 80 lines.
- `.github/workflows/ci.yml:32-50` — The `databricks-app` job sets `working-directory: databricks/app` and uses `databricks/app/package-lock.json`. That path is missing, so the job fails on every PR and push. It is also not in `docker.needs`.
- `.github/workflows/ci.yml:30` — `pytest` with no path would collect `tests/databricks/*` and fail. The commit "chore: remove dbx" removed the code but not the tests or the CI job. ruff covers `src tests` (`ci.yml:20-21`); mypy is strict but only on `src/eurostream` (`ci.yml:22`, `pyproject.toml:76`).
- `.github/workflows/orchestrate.yml:55-66` — Every 4 hours (and on every push to master) it uploads `data/lake` to the HF dataset `swadhinbiswas/eustream`. I did not check whether that dataset is public. The data is Silver/Gold output of a pipeline described as GDPR/PII (`Dockerfile:20`), so there is a likely public-exposure and residency risk. HF is not an EU-pinned host.
- `.github/workflows/orchestrate.yml:21-24` — The cache stores `data/eurocart.duckdb`, `data/events.db` and `governance/pii_manifest.json`. These hold warehouse and event data and a PII manifest, so PII-bearing data lands in the GitHub Actions cache. It is also restored by prefix key, so a stale cache is possible.
- `.github/workflows/orchestrate.yml:41-45` — On a failed Kafka probe it silently falls back to the sqlite bus. A green run can mean no Kafka was used. The cron comment (`:4`) describes Dhaka time, which is unrelated to the EU.
- `.github/workflows/orchestrate.yml:14` — Its actions are pinned to major tags only (`checkout@v4`, `setup-uv@v5`, `cache@v4`) and there is no `permissions:` block. Same in `ci.yml` and `deploy-space.yml`.
- `.github/workflows/deploy-space.yml:35,44` — It uploads the whole repo (minus a few ignore patterns) to the HF Space `swadhinbiswas/eurostream`. The ignore list does not exclude `governance/`, `tests/`, `.env*` or `infra/`. The Space is likely public, and the owner is a personal HF account.
- `.env.example:22` — The default `EUROSTREAM_PII_SALT=change-me-in-production` is a placeholder, not a real secret. There is no startup guard that rejects it, and `docker-compose.yml` sets no salt at all, so containers would use the code default.
- `infra/main.tf:107-123` — The MSK cluster sets no `at_rest` KMS key and no logging. `client_authentication` is unset, so access is network-only.
- `infra/main.tf:120-124` — The security group egress rule is open to `0.0.0.0/0`. `var.subnet_ids` defaults to `[]` (`:164-167`) and `vpc_id` has no default, so `apply` fails without inputs.
- `infra/main.tf:11-17` — No backend block, so Terraform state is local. There are no S3 lifecycle rules, no S3 access logging, no CMK, and no Terraform CI step.
- `infra/main.tf:1-3` — The header claims "no resource is created outside the EU", but Render, Turso, HF, Aiven and Cloudflare are not defined or verified here. Residency is only proven for AWS.
- `infra/main.tf:80-100` — The IAM role gives `s3:DeleteObject` on the whole lake, and it is assumed by `ec2.amazonaws.com`. No instance profile or EC2 resource is defined.
- `infra/main.tf:107-110` — The MSK cluster is `kafka.t3.small`, 3 brokers, and no topics are defined. No Terraform resource exists for `aws_msk_topic`. Topic retention and partitions are not defined anywhere in IaC.
- `render.yaml:5-6` — Render `plan: free`, region frankfurt (EU). Free plans have a cold start and an ephemeral disk, and `autoDeploy: true` has no gate.
- `render.yaml:13` — The backend is forced to Kafka (Aiven per `.env.example:5`), while the AWS MSK in `infra/main.tf` is a different Kafka. Two Kafka targets exist and neither is wired to the other. `render.yaml:30-31` also passes `HF_TOKEN` to the API service, which seems unnecessary at runtime.
- `Dockerfile:41-46` — The Dockerfile is non-root (`USER eurostream`), so no root finding. It is a slim image with no digest pin and no `--no-install-recommends` concern. The image runs on port 7860 (HF) but `docker-compose.yml:6,15` maps and health-checks 8000, while the compose `api` service uses no command override. The port mismatch breaks the compose healthcheck, and `render.yaml:8` sets `$PORT`. `Dockerfile:21` has the placeholder `your-org` source label.
- `Makefile:19` — `make gate` and CI skip `tests/databricks` handling, so the orphan tests fail the local gate too. `site/deploy.sh:19` uses `grep -oP`, which does not work on macOS.
- `site/wrangler.toml:10` — The docs site is public on `eurostream-docs.pages.dev`, which is global CDN (not EU-pinned). I did not read the content, so I can't say whether it leaks anything.
- `tests/conftest.py:7-12` — The fixtures target the local sqlite bus, duckdb and `eurostream` modules, which are the pre-migration stack. There are no Databricks fixtures.

**1. Source systems / platforms**
- AWS `eu-central-1` (Frankfurt) — `infra/main.tf:13-15`. S3 bucket `eurostream-prod-lake` is `${project}-${environment}-lake` (`:30,34-36`). IAM role `eurostream-prod-pipeline` (`:78-81`). Output `bootstrap_brokers_tls` feeds `EUROSTREAM_KAFKA_BOOTSTRAP_SERVERS` (`:149-152`).
- AWS MSK `eurostream-prod-events` — Kafka 3.6.0, 3 brokers, TLS listener port 9094 (`infra/main.tf:107-125`). `var.allowed_client_cidrs` defaults to `10.0.0.0/16` (`:141-145`). `vpc_id` and `subnet_ids` are inputs.
- Aiven Kafka (named in comment, `.env.example:5-7`) — SASL_SSL, SCRAM-SHA-256. Host, port and region are not in the repo. Env vars: `EUROSTREAM_KAFKA_BOOTSTRAP_SERVERS`, `_USERNAME`, `_PASSWORD`, `_SECURITY_PROTOCOL`, `_SASL_MECHANISM` (`.env.example:8-12`, `render.yaml:14-23`). CI secrets: `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_USERNAME`, `KAFKA_PASSWORD` (`orchestrate.yml:46-48`).
- Turso libSQL — env `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN` (`render.yaml:24-27`, `orchestrate.yml:49-50`). Host and region are not in the repo, so I can't say whether it is EU.
- Hugging Face dataset `swadhinbiswas/eustream` (`orchestrate.yml:61-65`), secret `HF_TOKEN`. Hugging Face Space `swadhinbiswas/eurostream` (`deploy-space.yml:35`), Docker with a Static fallback.
- Render web service `eurostream-api` — Docker, free plan, frankfurt, `/health` (`render.yaml:2-9`). Secret env vars: `EUROSTREAM_PII_SALT` (`:28`), plus the Kafka, Turso and HF ones above.
- Cloudflare Pages project `eurostream-docs`, `https://eurostream-docs.pages.dev` (`site/wrangler.toml:1,10`, `site/deploy.sh:19,28-31`). Deploy is manual (`wrangler login`).
- Docker Compose (`docker-compose.yml`) — Service `api` (build `.`, host port 8000, volume `eurostream-data:/app/data`, memory limit 1g, `restart: unless-stopped`). Service `demo` (profile `tools`, runs `eurostream demo` against `/app/data/demo.duckdb`). Embedded stores are DuckDB at `/app/data/eurocart.duckdb` and an SQLite bus (`events.db`).
- Databricks host — none found in scope. No workspace URL, host or `databricks.yml` exists.

**2. Workloads**
- `orchestrate` (`.github/workflows/orchestrate.yml:1-7`) — cron `0 */4 * * *` (UTC), plus push to master and manual dispatch. 15-minute timeout, concurrency group `orchestrate

## Findings

- `tests/databricks/test_bundle_contracts.py:6` — Reads files under ROOT/databricks/dab, but no databricks/ directory exists in the repo, so every test in this file is orphaned and would raise FileNotFoundError.
- `tests/databricks/test_critical_repairs.py:7` — DATABRICKS_ROOT points to a databricks/ folder (sql, dlt, notebooks) that does not exist in the repo, so these tests are orphaned.
- `tests/databricks/test_notebook_contracts.py:12` — NOTEBOOKS and SQL point to databricks/notebooks and databricks/sql, which do not exist, so the notebook contract tests are orphaned.
- `.github/workflows/ci.yml:32` — The databricks-app job uses working-directory databricks/app and databricks/app/package-lock.json, which do not exist, so the job fails on every run.
- `.github/workflows/orchestrate.yml:86` — Every 4-hour cron run and every push to master uploads data/lake to the HuggingFace dataset swadhinbiswas/eustream, a third-party host that is not EU-pinned and may be public, which is a data-exposure and residency risk.
- `.github/workflows/orchestrate.yml:21` — The Actions cache stores data/eurocart.duckdb, data/events.db and governance/pii_manifest.json, so warehouse and PII-manifest data persists in GitHub cache.
- `.github/workflows/deploy-space.yml:44` — upload_folder pushes the repo to the HF Space with an ignore list that does not exclude governance/, tests/, infra/ or .env* files.
- `infra/main.tf:47` — S3 versioning is Enabled on the lake bucket with no lifecycle rule expiring noncurrent versions, which conflicts with GDPR Art.17 physical deletion.
- `infra/main.tf:107` — The MSK cluster is defined but no Kafka topics, partitions or retention are declared in IaC, and no KMS key, client authentication or logging is configured.
- `docker-compose.yml:6` — The api service maps and health-checks port 8000, but the Dockerfile CMD serves uvicorn on port 7860, so the compose healthcheck fails.
- `render.yaml:13` — Render forces the Kafka backend with Aiven-style SASL credentials, while infra/main.tf provisions a different AWS MSK cluster; two Kafka targets exist and neither is wired to the other.
