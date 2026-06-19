# Block 2 Plan

## Acceptance criteria

> **Project — Lift the pipeline to AWS**
> Acceptance criteria (done = all true):
> Raw data lands in S3, is transformed by Glue (or equivalent), and is query-ready; all infrastructure defined as code (Terraform/CDK), not clicked in the console; pipeline is idempotent (re-runs produce the same result); a cost estimate is documented in the README.

## Objective

Lift the Block 1 PySpark batch pipeline to AWS. Raw CSVs go to S3, an AWS Glue job runs the same validate/clean/transform logic, output lands as query-ready partitioned Parquet, and all infrastructure is defined in Terraform.

## Architecture overview

The Block 2 flow:

1. Upload Block 1's `data/raw/*.csv` to an S3 landing zone via a Python upload script.
2. An AWS Glue PySpark job reads the CSVs from S3.
3. The job runs the same pipeline stages as Block 1: validate raw → clean → validate cleaned (hard gate) → build `analytic_person`.
4. Output is written as partitioned Parquet to `s3://bucket/processed/analytic_person/`.
5. Pipeline metrics are written to `s3://bucket/processed/pipeline_metrics.json`.
6. A Glue Data Catalog table makes the output queryable by Athena.

### Prerequisites

- AWS account with permissions to create S3, Glue, IAM, and Athena resources
- Terraform installed locally
- AWS CLI configured with credentials
- Block 1 `data/raw/` CSVs generated locally (from the Block 1 repo)

## Planned modules

### `glue/etl_job.py`

The Glue job script. Handles S3 I/O and orchestration — mirrors `pipeline.py` from Block 1.

Responsibilities:
- read raw CSVs from S3 with explicit schemas
- call `validations.validate_all()` on raw data (detection pass, log violations)
- call `transforms.clean_all()` to drop dirty rows, log before/after row counts
- call `validations.validate_all()` on cleaned data (hard gate — fail job if violations remain)
- call `transforms.build_analytic_person()` for joins and aggregations
- write partitioned Parquet to S3
- write `pipeline_metrics.json` to S3

### `glue/pipeline_lib.zip`

Block 1's core modules packaged as a zip for Glue's `--extra-py-files`:
- `validations.py` — all validation checks (null, range, FK, date-order, duplicate)
- `transforms.py` — cleaning functions, `build_analytic_person()` joins/aggregations
- `schemas.py` — StructType definitions for all 6 tables + `analytic_person`
- `concepts.py` — concept ID lookup dictionaries

These modules are imported unchanged from Block 1. No adaptation, no inlining. This keeps the tested logic intact and reusable in later blocks (e.g., Block 8 capstone).

### `scripts/package_lib.py`

Copies `validations.py`, `transforms.py`, `schemas.py`, and `concepts.py` from the Block 1 repo into a zip file (`glue/pipeline_lib.zip`). The zip is uploaded to S3 by Terraform (`aws_s3_object`), not by this script.

### `scripts/upload_raw.py`

Uploads Block 1's `data/raw/*.csv` to the S3 landing zone using `boto3`.

### `terraform/`

All AWS infrastructure defined as Terraform HCL:

- `main.tf` — provider config, backend
- `s3.tf` — bucket, versioning, lifecycle rules
- `iam.tf` — Glue execution role with S3 + Catalog + CloudWatch Logs permissions
- `glue.tf` — Glue database, catalog table, ETL job
- `athena.tf` — Athena workgroup with query result location
- `variables.tf` — parameterized inputs (bucket name, region, tags)
- `outputs.tf` — bucket ARN, Glue job name, Athena workgroup name

### `scripts/run_glue_job.py`

Triggers the Glue job via `boto3` and polls for completion. Provides a single local command to kick off the cloud pipeline after upload.

## Run order

1. `python scripts/package_lib.py` — create `glue/pipeline_lib.zip` from Block 1 modules
2. `terraform apply` — create all AWS resources and upload job script + zip to S3
3. `python scripts/upload_raw.py` — upload Block 1 CSVs to S3 landing zone
4. `python scripts/run_glue_job.py` — trigger the Glue job and poll for completion

## Porting strategy

Block 1's PySpark logic ports to Glue with these changes:

| Block 1 | Block 2 |
|---|---|
| `io_utils.read_*()` — local CSV reads | `etl_job.py` reads from S3 with same schemas |
| `io_utils.write_parquet()` — local write | `etl_job.py` writes to S3 with overwrite mode |
| `config.py` paths | Glue job parameters (`--S3_BUCKET`, `--RAW_PREFIX`, `--PROCESSED_PREFIX`) |
| `pipeline.py` orchestration | `etl_job.py` — same stage order, S3 I/O |
| `validations.py` | Imported unchanged via `--extra-py-files` zip |
| `transforms.py` | Imported unchanged via `--extra-py-files` zip |
| `schemas.py` | Imported unchanged via `--extra-py-files` zip |
| `concepts.py` | Imported unchanged via `--extra-py-files` zip |

The core PySpark modules are not modified. `etl_job.py` imports and calls them exactly as `pipeline.py` does in Block 1, with S3 paths replacing local paths.

## Idempotency

- Glue job bookmarks disabled (`--job-bookmark-option=job-bookmark-disable`) to ensure all input files are always processed on every run
- `partitionBy` + `mode="overwrite"` uses Spark's default static overwrite — clears the entire table directory before writing, which is intentional
- Same input CSVs + same job logic = same output (no random state, no timestamps in output)
- Upload script overwrites S3 raw prefix on each run

## Testing strategy

Block 2 testing differs from Block 1. The PySpark logic is already tested in Block 1 (103 tests). Block 2 testing focuses on:

1. **Terraform validation**: `terraform validate` and `terraform plan` confirm the infrastructure is syntactically correct and produces the expected resource graph.
2. **End-to-end cloud test**: upload CSVs → run Glue job → verify output exists in S3 → query via Athena.
3. **Idempotency test**: run the Glue job twice, confirm output is identical.
4. **Metrics verification**: compare `pipeline_metrics.json` from S3 against Block 1's expected metrics (row counts should match).

## Block boundaries

### Included in Block 2
- S3 bucket with raw and processed zones
- Glue PySpark ETL job
- Glue Data Catalog database and table
- Athena workgroup for querying output
- Terraform for all infrastructure
- Upload and job-trigger scripts
- Cost estimate in README
- Idempotent pipeline design

### Deferred to later blocks
- Streaming / real-time ingestion
- Orchestration (Step Functions, Airflow)
- CI/CD pipeline
- Multi-environment (dev/staging/prod)
- Monitoring and alerting
- New tables or schema changes

## Completion criteria

This plan is complete when:
- Terraform creates all AWS resources from code
- Raw CSVs are uploaded to S3
- The Glue job runs the full pipeline and writes partitioned Parquet to S3
- Athena can query the processed output
- Pipeline metrics match Block 1's expected values
- Re-running the job produces identical output
- Cost estimate is documented in the README
- `terraform destroy` tears down everything cleanly
