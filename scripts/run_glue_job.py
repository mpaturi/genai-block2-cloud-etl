"""Start the Glue ETL job and poll until completion."""

import argparse
import sys
import time

import boto3

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


def fetch_logs(logs, run: dict) -> None:
    log_group = "/aws-glue/jobs/output"
    run_id = run["Id"]
    print(f"\n--- CloudWatch logs ({log_group}) ---")
    try:
        streams = logs.describe_log_streams(
            logGroupName=log_group,
            logStreamNamePrefix=run_id,
        )["logStreams"]
        for stream in streams:
            events = logs.get_log_events(
                logGroupName=log_group,
                logStreamName=stream["logStreamName"],
                startFromHead=True,
            )["events"]
            for event in events:
                print(event["message"].rstrip())
    except logs.exceptions.ResourceNotFoundException:
        print("(no log streams found)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Glue ETL job and poll for completion")
    parser.add_argument("--job-name", default=JOB_NAME, help=f"Glue job name (default: {JOB_NAME})")
    parser.add_argument("--region", default="us-east-2")
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
