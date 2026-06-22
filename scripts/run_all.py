"""Run the full pipeline: package -> terraform apply -> upload -> Glue job -> verify."""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPTS_DIR.parent
TERRAFORM_DIR = PROJECT_DIR / "terraform"

DEFAULT_BLOCK1_DIR = PROJECT_DIR.parent / "genai-block1-batch-pipeline"
DEFAULT_BUCKET = "genai-block2-omop-623756711801"
DEFAULT_REGION = "us-east-2"
TERRAFORM = "terraform"


def run_step(name: str, cmd: list[str], cwd: Path | None = None) -> None:
    print(f"\n{'=' * 60}")
    print(f"  STEP: {name}")
    print(f"{'=' * 60}\n")
    result = subprocess.run(cmd, cwd=cwd, shell=True)
    if result.returncode != 0:
        print(f"\nFAILED at step: {name} (exit code {result.returncode})")
        sys.exit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full pipeline end-to-end")
    parser.add_argument("--skip-terraform", action="store_true",
                        help="Skip terraform apply (infra already exists)")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--block1-dir", type=Path, default=DEFAULT_BLOCK1_DIR)
    parser.add_argument("--terraform", default=TERRAFORM,
                        help=f"Path to terraform executable (default: {TERRAFORM})")
    args = parser.parse_args()

    py = sys.executable

    run_step("Package pipeline_lib.zip",
             [py, str(SCRIPTS_DIR / "package_lib.py"),
              "--block1-dir", str(args.block1_dir)])

    if not args.skip_terraform:
        run_step("Terraform apply",
                 [args.terraform, "apply", "-auto-approve"],
                 cwd=TERRAFORM_DIR)
    else:
        print("\n  (skipping terraform apply)")

    run_step("Upload raw CSVs to S3",
             [py, str(SCRIPTS_DIR / "upload_raw.py"),
              "--bucket", args.bucket,
              "--block1-dir", str(args.block1_dir)])

    run_step("Run Glue ETL job",
             [py, str(SCRIPTS_DIR / "run_glue_job.py"),
              "--region", args.region])

    run_step("Verify output",
             [py, str(SCRIPTS_DIR / "verify_output.py"),
              "--bucket", args.bucket,
              "--region", args.region])

    print(f"\n{'=' * 60}")
    print("  ALL STEPS PASSED")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
