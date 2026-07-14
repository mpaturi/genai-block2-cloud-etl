"""Upload the Glue job script and pipeline_lib.zip to S3, independent of Terraform."""

import argparse
from pathlib import Path

import boto3

from config import DEFAULT_BUCKET

GLUE_DIR = Path(__file__).resolve().parent.parent / "glue"
FILES = ("etl_job.py", "pipeline_lib.zip")


def upload_glue_scripts(bucket: str) -> None:
    s3 = boto3.client("s3")
    for name in FILES:
        local = GLUE_DIR / name
        if not local.exists():
            raise FileNotFoundError(f"Expected Glue script not found: {local}")
        key = f"scripts/{name}"
        print(f"  upload {name} -> s3://{bucket}/{key}")
        s3.upload_file(str(local), bucket, key)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload Glue job script and pipeline_lib.zip to S3")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET, help=f"S3 bucket (default: {DEFAULT_BUCKET})")
    args = parser.parse_args()
    upload_glue_scripts(args.bucket)
