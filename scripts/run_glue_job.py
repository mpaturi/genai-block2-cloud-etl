"""Start the Glue ETL job and poll until completion."""

import argparse
import sys
import time

import boto3

from config import DEFAULT_REGION

JOB_NAME = "omop-cloud-etl"
POLL_INTERVAL = 15


def run_and_poll(glue, job_name: str) -> dict:
    print(f"Starting Glue job: {job_name}")
    run_id = glue.start_job_run(JobName=job_name)["JobRunId"]
    print(f"Job run ID: {run_id}")

    while True:
        time.sleep(POLL_INTERVAL)
        run = glue.get_job_run(JobName=job_name, RunId=run_id)["JobRun"]
        state = run["JobRunState"]
        elapsed = ""
        if "StartedOn" in run:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            elapsed = f" ({int((now - run['StartedOn']).total_seconds())}s elapsed)"
        print(f"  status: {state}{elapsed}")
        if state in ("SUCCEEDED", "FAILED", "STOPPED", "ERROR", "TIMEOUT"):
            return run


def _print_log_group(logs, log_group: str, run_id: str) -> None:
    print(f"\n--- CloudWatch logs ({log_group}) ---")
    try:
        streams = logs.describe_log_streams(
            logGroupName=log_group,
            logStreamNamePrefix=run_id,
        )["logStreams"]
        for stream in streams:
            token = None
            while True:
                kwargs = dict(
                    logGroupName=log_group,
                    logStreamName=stream["logStreamName"],
                    startFromHead=True,
                )
                if token:
                    kwargs["nextToken"] = token
                resp = logs.get_log_events(**kwargs)
                for event in resp["events"]:
                    print(event["message"].rstrip())
                if resp["nextForwardToken"] == token:
                    break
                token = resp["nextForwardToken"]
    except logs.exceptions.ResourceNotFoundException:
        print("(no log streams found)")


def fetch_logs(logs, run: dict) -> None:
    run_id = run["Id"]
    failed = run["JobRunState"] != "SUCCEEDED"
    log_groups = ["/aws-glue/jobs/output"]
    if failed:
        log_groups.append("/aws-glue/jobs/error")
    for log_group in log_groups:
        _print_log_group(logs, log_group, run_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Glue ETL job and poll for completion")
    parser.add_argument("--job-name", default=JOB_NAME, help=f"Glue job name (default: {JOB_NAME})")
    parser.add_argument("--region", default=DEFAULT_REGION)
    args = parser.parse_args()

    glue = boto3.client("glue", region_name=args.region)
    logs = boto3.client("logs", region_name=args.region)

    run = run_and_poll(glue, args.job_name)
    fetch_logs(logs, run)

    if run["JobRunState"] == "SUCCEEDED":
        duration = int((run["CompletedOn"] - run["StartedOn"]).total_seconds())
        print(f"\nJob SUCCEEDED ({duration}s)")
    else:
        print(f"\nJob FAILED: {run.get('ErrorMessage', 'unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
