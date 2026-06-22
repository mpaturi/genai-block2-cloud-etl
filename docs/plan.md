# Block 2 Plan

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

### `scripts/package_lib.py`

Copies `validations.py`, `transforms.py`, `schemas.py`, and `concepts.py` from the Block 1 repo into a zip file (`glue/pipeline_lib.zip`). The zip is uploaded to S3 by Terraform (`aws_s3_object`), not by this script.

### `glue/smoke_test.py`

Minimal Glue job that prints Python/Spark versions, imports all 4 modules (`validations`, `transforms`, `schemas`, `concepts`), and prints "imports OK". Run once after `terraform apply` to verify the zip works in the Glue runtime. Deleted from S3 after passing.

### `scripts/upload_raw.py`

Uploads Block 1's `data/raw/*.csv` to the S3 landing zone using `boto3`.

### `terraform/`

All AWS infrastructure defined as Terraform HCL:

- `main.tf` — provider config, backend
- `s3.tf` — bucket, lifecycle rules (no versioning — pipeline is idempotent and output is reproducible from source)
- `iam.tf` — Glue execution role with least-privilege policy: `s3:GetObject` (raw/*, scripts/*), `s3:PutObject`/`s3:DeleteObject` (processed/*, processed_$folder$), `s3:ListBucket` — all scoped to pipeline bucket ARN; Glue Catalog scoped to `omop_cloud_etl` database; CloudWatch Logs
- `glue.tf` — Glue database, catalog table (with partition projection for `year_of_birth_band`), ETL job (pinned to `glue_version = "5.0"` for Spark 3.5.4 / Python 3.11), `aws_s3_object` for `etl_job.py` and `pipeline_lib.zip`
- `athena.tf` — Athena workgroup with query result location
- `variables.tf` — parameterized inputs (bucket name, region, tags)
- `outputs.tf` — bucket ARN, Glue job name, Athena workgroup name

### `scripts/run_glue_job.py`

Triggers the Glue job via `boto3` and polls for completion. Provides a single local command to kick off the cloud pipeline after upload.

### `scripts/verify_output.py`

Verifies the Glue job output: checks that partitioned Parquet exists in S3, downloads and prints `pipeline_metrics.json`, and runs an Athena query against `analytic_person`.

### `scripts/run_all.py`

Chains all pipeline steps in order: package → terraform apply → upload → run Glue job → verify. Accepts `--skip-terraform` for re-runs where infrastructure already exists.

## Run order

1. `python scripts/package_lib.py` — create `glue/pipeline_lib.zip` from Block 1 modules
2. `terraform apply` — create all AWS resources and upload job script + zip to S3
3. Run `glue/smoke_test.py` as a one-off Glue job — verify all 4 modules import correctly in the Glue runtime and confirm Python/Spark versions
4. `python scripts/upload_raw.py` — upload Block 1 CSVs to S3 landing zone
5. `python scripts/run_glue_job.py` — trigger the Glue job and poll for completion
6. `python scripts/verify_output.py` — verify Parquet, metrics, and Athena query

Or run all steps (except smoke test) with `python scripts/run_all.py`.

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

## Testing strategy

Block 2 testing differs from Block 1. The PySpark logic is already tested in Block 1 (103 tests). Block 2 testing focuses on:

1. **Terraform validation**: `terraform validate` and `terraform plan` confirm the infrastructure is syntactically correct and produces the expected resource graph.
2. **Smoke test**: run `glue/smoke_test.py` as a one-off Glue job after `terraform apply` to verify all 4 modules import correctly and confirm the Glue runtime reports Python 3.11 / Spark 3.5.4 as expected.
3. **End-to-end cloud test**: upload CSVs → run Glue job → verify output exists in S3 → query via Athena.
4. **Idempotency test**: run the Glue job twice, confirm output is identical.
5. **Metrics verification**: compare `pipeline_metrics.json` from S3 against Block 1's expected metrics (row counts should match).

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

