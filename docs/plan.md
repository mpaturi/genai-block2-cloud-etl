# Block 2 Plan

## Acceptance criteria (from study plan)

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

The Glue job script. Adapts Block 1's pipeline logic for S3-backed I/O.

Responsibilities:
- read raw CSVs from S3 with explicit schemas
- run validation checks on raw data (detection pass, log violations)
- clean dirty rows, log before/after row counts
- run validation on cleaned data (hard gate — fail job if violations remain)
- build `analytic_person` via joins and aggregations
- write partitioned Parquet to S3
- write `pipeline_metrics.json` to S3

Uses Glue's built-in PySpark runtime. Block 1's validation and transform logic is ported inline (not imported from a separate package) to keep the Glue job self-contained.

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

## Porting strategy

Block 1's PySpark logic ports to Glue with these changes:

| Block 1 | Block 2 |
|---|---|
| `io_utils.read_*()` — local CSV reads | `spark.read.csv("s3://...")` with same schemas |
| `io_utils.write_parquet()` — local write | `df.write.parquet("s3://...")` with overwrite mode |
| `config.py` paths | Glue job parameters (`--S3_BUCKET`, `--RAW_PREFIX`, `--PROCESSED_PREFIX`) |
| `pipeline.py` orchestration | `etl_job.py` — same stage order, adapted for S3 I/O |
| `validations.py` logic | Ported inline into `etl_job.py` |
| `transforms.py` logic | Ported inline into `etl_job.py` |
| `schemas.py` definitions | Ported inline into `etl_job.py` |

The validation and transform logic stays functionally identical. The main differences are S3 paths instead of local paths, and Glue job parameters instead of config constants.

## Idempotency

- Glue job uses Spark `mode="overwrite"` — re-runs replace the previous output
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
