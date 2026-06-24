"""AWS Glue ETL job — mirrors Block 1 pipeline.py with S3 I/O."""

import json
import sys
import time

import boto3
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext

import schemas
import transforms
import validations

# ---- Glue bootstrap --------------------------------------------------------

args = getResolvedOptions(sys.argv, ["JOB_NAME", "S3_BUCKET", "RAW_PREFIX", "PROCESSED_PREFIX"])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

BUCKET = args["S3_BUCKET"]
RAW_PREFIX = args["RAW_PREFIX"]
PROCESSED_PREFIX = args["PROCESSED_PREFIX"]

RAW_PATH = f"s3://{BUCKET}/{RAW_PREFIX}"
PROCESSED_PATH = f"s3://{BUCKET}/{PROCESSED_PREFIX}"


# ---- Helpers ----------------------------------------------------------------

def log(msg):
    print(msg, flush=True)


def read_csv(name, schema):
    path = f"{RAW_PATH}{name}.csv"
    log(f"Reading {path}")
    return spark.read.csv(path, header=True, schema=schema)


def validation_to_dict(results):
    return [{"table": r.table, "check": r.check, "violations": r.count} for r in results]


# ---- Pipeline stages --------------------------------------------------------

t_start = time.time()

# 1. Read raw CSVs
log("Stage 1: Reading raw CSVs from S3")
person = read_csv("person", schemas.PERSON)
visit = read_csv("visit_occurrence", schemas.VISIT_OCCURRENCE)
condition = read_csv("condition_occurrence", schemas.CONDITION_OCCURRENCE)
drug = read_csv("drug_exposure", schemas.DRUG_EXPOSURE)
measurement = read_csv("measurement", schemas.MEASUREMENT)
note = read_csv("note", schemas.NOTE)

# 2. Validate raw (detection pass — log and continue)
log("Stage 2: Validating raw tables")
t_val_raw = time.time()
raw_results = validations.validate_all(person, visit, condition, drug, measurement, note)
t_val_raw_done = time.time()

violations = [r for r in raw_results if r.count > 0]
if violations:
    log(f"  {len(violations)} check(s) with violations:")
    for r in violations:
        log(f"    {r.table:30s}  {r.check:35s}  count={r.count}")
else:
    log("  All raw validation checks passed")

# 3. Clean
log("Stage 3: Cleaning tables")
t_clean = time.time()
tables, cleaning_metrics = transforms.clean_all(person, visit, condition, drug, measurement, note)
t_clean_done = time.time()

log("  Cleaning summary (before -> after):")
for table_name, before in cleaning_metrics.before.items():
    after = cleaning_metrics.after[table_name]
    log(f"    {table_name:30s}  {before:6d} -> {after:6d}  (dropped {before - after})")

# 4. Validate cleaned (hard gate — fail job if violations remain)
log("Stage 4: Validating cleaned tables (hard gate)")
t_val_clean = time.time()
clean_results = validations.validate_all(
    tables.person, tables.visit, tables.condition,
    tables.drug, tables.measurement, tables.note,
)
t_val_clean_done = time.time()

clean_violations = [r for r in clean_results if r.count > 0]
if clean_violations:
    summary = ", ".join(f"{r.table}.{r.check}={r.count}" for r in clean_violations)
    msg = f"HARD GATE FAILED: cleaned tables still have {len(clean_violations)} violation(s): {summary}"
    log(msg)
    raise RuntimeError(msg)
log("  All cleaned validation checks passed")

# 5. Build analytic_person
log("Stage 5: Building analytic_person")
t_build = time.time()
analytic = transforms.build_analytic_person(
    tables.person, tables.visit, tables.condition,
    tables.drug, tables.measurement,
)

# 6. Write partitioned Parquet to S3
output_path = f"{PROCESSED_PATH}analytic_person/"
log(f"Stage 6: Writing partitioned Parquet to {output_path}")
analytic.write.partitionBy("year_of_birth_band").mode("overwrite").parquet(output_path)
analytic_count = spark.read.parquet(output_path).count()
log(f"  Wrote {analytic_count} rows")
t_build_done = time.time()

# 7. Write pipeline_metrics.json to S3
t_total = time.time() - t_start

metrics = {
    "row_counts": {
        "raw": cleaning_metrics.before,
        "cleaned": cleaning_metrics.after,
        "dropped": {
            t: cleaning_metrics.before[t] - cleaning_metrics.after[t]
            for t in cleaning_metrics.before
        },
        "analytic_person": analytic_count,
    },
    "validation": {
        "raw": validation_to_dict(raw_results),
        "cleaned": validation_to_dict(clean_results),
    },
    "timings_seconds": {
        "validation_raw": round(t_val_raw_done - t_val_raw, 2),
        "cleaning": round(t_clean_done - t_clean, 2),
        "validation_cleaned": round(t_val_clean_done - t_val_clean, 2),
        "build_and_write": round(t_build_done - t_build, 2),
        "total": round(t_total, 2),
    },
}

metrics_key = f"{PROCESSED_PREFIX}pipeline_metrics.json"
log(f"Stage 7: Writing pipeline_metrics.json to s3://{BUCKET}/{metrics_key}")
s3 = boto3.client("s3")
s3.put_object(
    Bucket=BUCKET,
    Key=metrics_key,
    Body=json.dumps(metrics, indent=2),
    ContentType="application/json",
)

log(f"Pipeline completed in {t_total:.1f}s")
job.commit()
