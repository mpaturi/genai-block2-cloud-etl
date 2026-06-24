"""Upload smoke_test.py, run it as a temporary Glue job, stream logs, clean up."""

import argparse
import sys
import time

import boto3

DEFAULT_BUCKET = "genai-block2-omop-623756711801"
SMOKE_JOB_NAME = "omop-smoke-test"
SMOKE_SCRIPT_KEY = "scripts/smoke_test.py"
ROLE_NAME = "omop-cloud-etl-glue-role"
POLL_INTERVAL = 15


def get_role_arn(iam) -> str:
    return iam.get_role(RoleName=ROLE_NAME)["Role"]["Arn"]


def upload_script(s3, bucket: str) -> None:
    local_path = str(__import__("pathlib").Path(__file__).resolve().parent.parent / "glue" / "smoke_test.py")
    print(f"Uploading smoke_test.py -> s3://{bucket}/{SMOKE_SCRIPT_KEY}")
    s3.upload_file(local_path, bucket, SMOKE_SCRIPT_KEY)


def create_job(glue, bucket: str, role_arn: str) -> None:
    print(f"Creating temporary Glue job: {SMOKE_JOB_NAME}")
    glue.create_job(
        Name=SMOKE_JOB_NAME,
        Role=role_arn,
        GlueVersion="5.0",
        WorkerType="G.1X",
        NumberOfWorkers=2,
        Command={
            "Name": "glueetl",
            "ScriptLocation": f"s3://{bucket}/{SMOKE_SCRIPT_KEY}",
            "PythonVersion": "3",
        },
        DefaultArguments={
            "--extra-py-files": f"s3://{bucket}/scripts/pipeline_lib.zip",
            "--job-bookmark-option": "job-bookmark-disable",
            "--enable-continuous-cloudwatch-log": "true",
        },
    )


def run_and_poll(glue) -> dict:
    print(f"Starting job run...")
    run_id = glue.start_job_run(JobName=SMOKE_JOB_NAME)["JobRunId"]
    print(f"Job run ID: {run_id}")

    while True:
        time.sleep(POLL_INTERVAL)
        run = glue.get_job_run(JobName=SMOKE_JOB_NAME, RunId=run_id)["JobRun"]
        state = run["JobRunState"]
        print(f"  status: {state}")
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
            events = logs.get_log_events(
                logGroupName=log_group,
                logStreamName=stream["logStreamName"],
                startFromHead=True,
            )["events"]
            for event in events:
                print(event["message"].rstrip())
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


def cleanup(glue, s3, bucket: str) -> None:
    print("\nCleaning up...")
    try:
        glue.delete_job(JobName=SMOKE_JOB_NAME)
        print(f"  deleted Glue job: {SMOKE_JOB_NAME}")
    except Exception as e:
        print(f"  warning: failed to delete Glue job: {e}")
    try:
        s3.delete_object(Bucket=bucket, Key=SMOKE_SCRIPT_KEY)
        print(f"  deleted s3://{bucket}/{SMOKE_SCRIPT_KEY}")
    except Exception as e:
        print(f"  warning: failed to delete S3 object: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Glue smoke test")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--region", default="us-east-2")
    args = parser.parse_args()

    s3 = boto3.client("s3", region_name=args.region)
    glue = boto3.client("glue", region_name=args.region)
    iam = boto3.client("iam", region_name=args.region)
    logs = boto3.client("logs", region_name=args.region)

    role_arn = get_role_arn(iam)
    upload_script(s3, args.bucket)
    create_job(glue, args.bucket, role_arn)

    try:
        run = run_and_poll(glue)
        fetch_logs(logs, run)

        if run["JobRunState"] == "SUCCEEDED":
            duration = int((run["CompletedOn"] - run["StartedOn"]).total_seconds())
            print(f"\nSmoke test PASSED ({duration}s)")
        else:
            print(f"\nSmoke test FAILED: {run.get('ErrorMessage', 'unknown error')}")
            sys.exit(1)
    finally:
        cleanup(glue, s3, args.bucket)


if __name__ == "__main__":
    main()
