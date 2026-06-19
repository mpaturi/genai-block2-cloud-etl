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
- [ ] Write `terraform/iam.tf` — Glue execution role and policy
- [ ] Write `terraform/glue.tf` — Glue database, catalog table, ETL job
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

## Glue ETL job

- [ ] Port Block 1 schemas into `glue/etl_job.py`
- [ ] Port Block 1 validation logic (null, range, FK, date-order, duplicate checks)
- [ ] Port Block 1 cleaning logic (drop dirty rows, before/after counts)
- [ ] Port Block 1 transform logic (joins, aggregations, `analytic_person`)
- [ ] Implement S3 CSV read with explicit schemas
- [ ] Implement S3 Parquet write with `year_of_birth_band` partitioning
- [ ] Implement hard gate (fail job if cleaned data has violations)
- [ ] Write `pipeline_metrics.json` to S3
- [ ] Accept job parameters (`--S3_BUCKET`, `--RAW_PREFIX`, `--PROCESSED_PREFIX`)
- [ ] Upload job script to `s3://bucket/scripts/etl_job.py`

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
