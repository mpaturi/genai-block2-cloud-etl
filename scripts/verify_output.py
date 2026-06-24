"""Verify Glue job output: Parquet partitions, pipeline metrics, and Athena query."""

import argparse
import json
import sys
import time

import boto3

from config import DEFAULT_BUCKET, DEFAULT_REGION
WORKGROUP = "omop-cloud-etl"
DATABASE = "omop_cloud_etl"
TABLE = "analytic_person"


def check_parquet(s3, bucket: str) -> bool:
    prefix = "processed/analytic_person/"
    print(f"\n=== Check 1: Parquet partitions in s3://{bucket}/{prefix} ===")
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter="/")
    prefixes = [p["Prefix"] for p in resp.get("CommonPrefixes", [])]

    if not prefixes:
        print("  FAIL: no partition directories found")
        return False

    print(f"  Found {len(prefixes)} partition(s):")
    for p in sorted(prefixes):
        partition = p.replace(prefix, "").rstrip("/")
        print(f"    {partition}")
    print("  PASS")
    return True


def check_metrics(s3, bucket: str) -> bool:
    key = "processed/pipeline_metrics.json"
    print(f"\n=== Check 2: Pipeline metrics at s3://{bucket}/{key} ===")
    try:
        resp = s3.get_object(Bucket=bucket, Key=key)
        metrics = json.loads(resp["Body"].read().decode("utf-8"))
    except s3.exceptions.NoSuchKey:
        print("  FAIL: pipeline_metrics.json not found")
        return False

    row_counts = metrics.get("row_counts", {})
    print("  Row counts (raw):")
    for table, count in row_counts.get("raw", {}).items():
        print(f"    {table:30s}  {count:>6}")
    print("  Row counts (cleaned):")
    for table, count in row_counts.get("cleaned", {}).items():
        print(f"    {table:30s}  {count:>6}")
    print(f"  analytic_person rows: {row_counts.get('analytic_person', 'MISSING')}")

    clean_violations = metrics.get("validation", {}).get("cleaned", [])
    has_violations = any(v.get("violations", 0) > 0 for v in clean_violations)
    if has_violations:
        print("  WARN: cleaned data has violations recorded in metrics")

    print("  PASS")
    return True


def check_athena(athena, bucket: str) -> bool:
    query = f"SELECT year_of_birth_band, COUNT(*) as cnt FROM {DATABASE}.{TABLE} GROUP BY 1 ORDER BY 1"

    print(f"\n=== Check 3: Athena query ===")
    print(f"  Query: {query}")

    execution = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": DATABASE},
        WorkGroup=WORKGROUP,
    )
    execution_id = execution["QueryExecutionId"]
    print(f"  Execution ID: {execution_id}")

    deadline = time.time() + 120
    while True:
        time.sleep(2)
        status = athena.get_query_execution(QueryExecutionId=execution_id)
        state = status["QueryExecution"]["Status"]["State"]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        if time.time() > deadline:
            print("  FAIL: Athena query timed out after 120s")
            return False

    if state != "SUCCEEDED":
        reason = status["QueryExecution"]["Status"].get("StateChangeReason", "unknown")
        print(f"  FAIL: Athena query {state}: {reason}")
        return False

    results = athena.get_query_results(QueryExecutionId=execution_id)
    rows = results["ResultSet"]["Rows"]
    print(f"  Results ({len(rows) - 1} partitions):")
    for row in rows[1:]:
        band = row["Data"][0].get("VarCharValue", "")
        count = row["Data"][1].get("VarCharValue", "")
        print(f"    {band:20s}  {count:>6}")

    print("  PASS")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Glue job output")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--region", default=DEFAULT_REGION)
    args = parser.parse_args()

    s3 = boto3.client("s3", region_name=args.region)
    athena = boto3.client("athena", region_name=args.region)

    results = [
        check_parquet(s3, args.bucket),
        check_metrics(s3, args.bucket),
        check_athena(athena, args.bucket),
    ]

    print(f"\n{'=' * 40}")
    passed = sum(results)
    total = len(results)
    print(f"Verification: {passed}/{total} checks passed")
    if not all(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
