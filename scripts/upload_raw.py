"""Upload Block 1 raw CSVs to S3 landing zone."""

import argparse
from pathlib import Path

import boto3

from config import DEFAULT_BUCKET
DEFAULT_PREFIX = "raw/"
DEFAULT_BLOCK1_DIR = Path(__file__).resolve().parent.parent.parent / "genai-block1-batch-pipeline"


def upload(block1_dir: Path, bucket: str, prefix: str) -> None:
    raw_dir = block1_dir / "data" / "raw"
    if not raw_dir.is_dir():
        raise FileNotFoundError(f"Block 1 raw data directory not found: {raw_dir}")

    csvs = sorted(raw_dir.glob("*.csv"))
    if not csvs:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")

    s3 = boto3.client("s3")

    for csv_path in csvs:
        key = f"{prefix}{csv_path.name}"
        local_size = csv_path.stat().st_size

        try:
            resp = s3.head_object(Bucket=bucket, Key=key)
            if resp["ContentLength"] == local_size:
                print(f"  skip {csv_path.name} (already uploaded, same size)")
                continue
        except s3.exceptions.ClientError:
            pass

        print(f"  upload {csv_path.name} ({local_size:,} bytes) -> s3://{bucket}/{key}")
        s3.upload_file(str(csv_path), bucket, key)

    print(f"\nDone. {len(csvs)} CSVs processed to s3://{bucket}/{prefix}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload raw CSVs to S3")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET, help=f"S3 bucket (default: {DEFAULT_BUCKET})")
    parser.add_argument("--prefix", default=DEFAULT_PREFIX, help=f"S3 key prefix (default: {DEFAULT_PREFIX})")
    parser.add_argument("--block1-dir", type=Path, default=DEFAULT_BLOCK1_DIR,
                        help=f"Path to Block 1 repo (default: {DEFAULT_BLOCK1_DIR})")
    args = parser.parse_args()
    upload(args.block1_dir, args.bucket, args.prefix)
