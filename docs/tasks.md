# Block 2 Tasks

## Phase 0 — Documentation

- [x] Write Block 2 scope and acceptance criteria in `docs/spec.md`
- [x] Generate architecture, data flow, S3 layout, and Terraform diagrams
- [x] Write implementation approach in `docs/plan.md`
- [x] Write task breakdown in `docs/tasks.md`

## Phase 1 — Foundation (Terraform + Environment)

- [x] Initialize git repo and `.gitignore`
- [x] Create Python virtual environment
- [x] Install dependencies (`boto3`, `awscli`)
- [x] Capture pinned dependencies in `requirements.txt`
- [x] Install Terraform locally
- [x] Confirm AWS CLI is configured with credentials
- [x] Write `terraform/main.tf` — provider and backend config
- [x] Write `terraform/variables.tf` — bucket name, region, tags
- [x] Write `terraform/s3.tf` — S3 bucket, lifecycle (no versioning — pipeline is idempotent)
- [x] Write `terraform/iam.tf` — Glue execution role and policy (S3 + Catalog + CloudWatch Logs)
- [x] Scope IAM policy to pipeline bucket ARN with specific S3 actions per prefix (`raw/`, `scripts/` → `GetObject`/`ListBucket`; `processed/` → `PutObject`/`DeleteObject`)
- [x] Write `terraform/glue.tf` — Glue database, catalog table, ETL job (pin `glue_version = "5.0"` for Spark 3.5.4 / Python 3.11)
- [x] Configure partition projection properties on `aws_glue_catalog_table` in `glue.tf`
- [x] Configure `--extra-py-files = s3://bucket/scripts/pipeline_lib.zip` in `aws_glue_job` default arguments in `glue.tf`
- [x] Set `--job-bookmark-option = job-bookmark-disable` in `aws_glue_job` default arguments
- [x] Write `terraform/athena.tf` — Athena workgroup
- [x] Write `terraform/outputs.tf` — bucket ARN, job name, workgroup
- [x] Run `terraform validate` successfully
- [x] Run `terraform plan` and review resource graph

## Phase 2 — Packaging, Apply & Upload

- [x] Implement `scripts/package_lib.py` to zip Block 1 modules
- [x] Run `scripts/package_lib.py` to package `validations.py`, `transforms.py`, `schemas.py`, `concepts.py` into `glue/pipeline_lib.zip`
- [x] Implement `scripts/upload_raw.py` using `boto3`
- [x] Support `--bucket` and `--prefix` arguments
- [x] Run `terraform apply` — creates all resources, uploads `etl_job.py` + `pipeline_lib.zip` to S3 (bucket must exist before uploading CSVs)
- [x] Verify Terraform `aws_s3_object` uploads `pipeline_lib.zip` to `s3://bucket/scripts/`
- [x] Upload all 6 CSVs from Block 1 `data/raw/` to S3
- [x] Verify files exist in S3 after upload

## Phase 3 — Smoke Test

- [x] Write `glue/smoke_test.py` — minimal Glue job that prints Python/Spark versions, imports all 4 modules, and prints "imports OK"
- [x] Write `scripts/run_smoke_test.py` — uploads smoke_test.py, creates temp Glue job, runs it, streams logs, cleans up (deletes job + S3 object)
- [x] Fix `scripts/package_lib.py` — rewrite `from src.*` imports to flat imports and inline `REFERENCE_DATE` from config
- [x] Run `python scripts/run_smoke_test.py` — PASSED (Python 3.11.14, Spark 3.5.4, "imports OK")
- [x] Cleanup confirmed — temp Glue job and smoke_test.py deleted from S3

## Phase 4 — ETL Job + Trigger

- [x] Implement `glue/etl_job.py` — S3 I/O and orchestration (mirrors `pipeline.py`)
- [x] Import `validations`, `transforms`, `schemas`, `concepts` from `--extra-py-files` zip
- [x] Implement S3 CSV read with explicit schemas
- [x] Implement S3 Parquet write with `year_of_birth_band` partitioning
- [x] Implement hard gate (fail job if cleaned data has violations)
- [x] Write `pipeline_metrics.json` to S3
- [x] Accept job parameters (`--S3_BUCKET`, `--RAW_PREFIX`, `--PROCESSED_PREFIX`)
- [x] Verify Terraform `aws_s3_object` uploads `etl_job.py` to `s3://bucket/scripts/`
- [x] Implement `scripts/run_glue_job.py` — start job and poll for completion
- [x] Print job status and duration on completion
- [x] Exit with error code on job failure

## Phase 5 — Verification & Polish

- [x] Run Glue job end-to-end and confirm it succeeds
- [x] Verify partitioned Parquet exists in `s3://bucket/processed/analytic_person/`
- [x] Verify `pipeline_metrics.json` row counts match Block 1 expected values
- [x] Query `analytic_person` via Athena and confirm results
- [x] Re-run Glue job and confirm output is identical (idempotency)
- [x] Run `terraform destroy` and confirm clean teardown
- [x] Write README with architecture diagram
- [x] Document setup and prerequisites
- [x] Document cost estimate
- [x] Keep `README.md` aligned with implementation
- [x] (optional) Add `run_all.py` chaining all run-order steps into a single command
- [x] Review all docs for accuracy against implementation
