# Block 2 Tasks

## Documentation

- [x] Write Block 2 scope and acceptance criteria in `docs/spec.md`
- [x] Generate architecture, data flow, S3 layout, and Terraform diagrams
- [x] Write implementation approach in `docs/plan.md`
- [x] Write task breakdown in `docs/tasks.md`
- [ ] Keep `README.md` aligned with implementation

## Repo and environment

- [x] Initialize git repo and `.gitignore`
- [ ] Create Python virtual environment
- [ ] Install dependencies (`boto3`, `awscli`)
- [ ] Capture pinned dependencies in `requirements.txt`
- [ ] Install Terraform locally
- [ ] Confirm AWS CLI is configured with credentials

## Terraform infrastructure

- [ ] Write `terraform/main.tf` — provider and backend config
- [ ] Write `terraform/variables.tf` — bucket name, region, tags
- [ ] Write `terraform/s3.tf` — S3 bucket, versioning, lifecycle
- [ ] Write `terraform/iam.tf` — Glue execution role and policy (include Athena StartQueryExecution + GetQueryExecution for MSCK REPAIR TABLE)
- [ ] Write `terraform/glue.tf` — Glue database, catalog table, ETL job
- [ ] Configure `--extra-py-files = s3://bucket/scripts/pipeline_lib.zip` in `aws_glue_job` default arguments in `glue.tf`
- [ ] Write `terraform/athena.tf` — Athena workgroup
- [ ] Write `terraform/outputs.tf` — bucket ARN, job name, workgroup
- [ ] Run `terraform validate` successfully
- [ ] Run `terraform plan` and review resource graph
- [ ] Run `terraform apply` and confirm all resources created

## Upload script

- [ ] Implement `scripts/upload_raw.py` using `boto3`
- [ ] Support `--bucket` and `--prefix` arguments
- [ ] Upload all 6 CSVs from Block 1 `data/raw/` to S3
- [ ] Verify files exist in S3 after upload

## Pipeline library packaging

- [ ] Implement `scripts/package_lib.py` to zip Block 1 modules
- [ ] Run `scripts/package_lib.py` to package `validations.py`, `transforms.py`, `schemas.py`, `concepts.py` into `glue/pipeline_lib.zip`
- [ ] Verify Terraform `aws_s3_object` uploads `pipeline_lib.zip` to `s3://bucket/scripts/`
- [ ] Verify modules are importable from the zip in a Glue job

## Glue ETL job

- [ ] Implement `glue/etl_job.py` — S3 I/O and orchestration (mirrors `pipeline.py`)
- [ ] Import `validations`, `transforms`, `schemas` from `--extra-py-files` zip
- [ ] Implement S3 CSV read with explicit schemas
- [ ] Implement S3 Parquet write with `year_of_birth_band` partitioning
- [ ] Implement hard gate (fail job if cleaned data has violations)
- [ ] Write `pipeline_metrics.json` to S3
- [ ] Run `MSCK REPAIR TABLE` via Athena after writing output
- [ ] Accept job parameters (`--S3_BUCKET`, `--RAW_PREFIX`, `--PROCESSED_PREFIX`)
- [ ] Verify Terraform `aws_s3_object` uploads `etl_job.py` to `s3://bucket/scripts/`

## Job trigger script

- [ ] Implement `scripts/run_glue_job.py` — start job and poll for completion
- [ ] Print job status and duration on completion
- [ ] Exit with error code on job failure

## Verification

- [ ] Run Glue job end-to-end and confirm it succeeds
- [ ] Verify partitioned Parquet exists in `s3://bucket/processed/analytic_person/`
- [ ] Verify `pipeline_metrics.json` row counts match Block 1 expected values
- [ ] Query `analytic_person` via Athena and confirm results
- [ ] Re-run Glue job and confirm output is identical (idempotency)
- [ ] Run `terraform destroy` and confirm clean teardown

## README and polish

- [ ] Write README with architecture diagram
- [ ] Document setup and prerequisites
- [ ] Document cost estimate
- [ ] Add AI-assisted workflow note
- [ ] Review all docs for accuracy against implementation
