"""Package Block 1 PySpark modules into a zip for Glue --extra-py-files."""

import argparse
import zipfile
from pathlib import Path

MODULES = ["validations.py", "transforms.py", "schemas.py", "concepts.py"]
DEFAULT_BLOCK1_DIR = Path(__file__).resolve().parent.parent.parent / "genai-block1-batch-pipeline"
OUTPUT_ZIP = Path(__file__).resolve().parent.parent / "glue" / "pipeline_lib.zip"


def package(block1_dir: Path, output: Path) -> None:
    src_dir = block1_dir / "src"
    if not src_dir.is_dir():
        raise FileNotFoundError(f"Block 1 src directory not found: {src_dir}")

    missing = [m for m in MODULES if not (src_dir / m).exists()]
    if missing:
        raise FileNotFoundError(f"Missing modules in {src_dir}: {missing}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for module in MODULES:
            zf.write(src_dir / module, module)

    print(f"Created {output} with {len(MODULES)} modules:")
    for m in MODULES:
        print(f"  - {m}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Package Block 1 modules into pipeline_lib.zip")
    parser.add_argument("--block1-dir", type=Path, default=DEFAULT_BLOCK1_DIR,
                        help=f"Path to Block 1 repo (default: {DEFAULT_BLOCK1_DIR})")
    parser.add_argument("--output", type=Path, default=OUTPUT_ZIP,
                        help=f"Output zip path (default: {OUTPUT_ZIP})")
    args = parser.parse_args()
    package(args.block1_dir, args.output)
