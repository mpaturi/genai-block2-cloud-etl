"""Package Block 1 PySpark modules into a zip for Glue --extra-py-files.

Rewrites 'from src.<mod>' imports to flat imports so modules work as
top-level files inside the zip (Glue adds --extra-py-files to sys.path).
Inlines REFERENCE_DATE from config.py since config.py is not packaged.
"""

import argparse
import importlib.util
import re
import zipfile
from datetime import date
from pathlib import Path

MODULES = ["validations.py", "transforms.py", "schemas.py", "concepts.py"]
DEFAULT_BLOCK1_DIR = Path(__file__).resolve().parent.parent.parent / "genai-block1-batch-pipeline"
OUTPUT_ZIP = Path(__file__).resolve().parent.parent / "glue" / "pipeline_lib.zip"

_CONFIG_RE = re.compile(r"^from src\.config import REFERENCE_DATE$")
_SRC_FROM_RE = re.compile(r"^from src\.(\w+) import")
_SRC_IMPORT_RE = re.compile(r"^from src import (\w+)$")


def _load_reference_date(block1_dir: Path) -> date:
    """Read the live REFERENCE_DATE from Block 1's config.py (respects BLOCK1_REFERENCE_DATE)."""
    spec = importlib.util.spec_from_file_location("block1_config", block1_dir / "src" / "config.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.REFERENCE_DATE


def _rewrite_imports(source: str, config_replacement: str) -> str:
    lines = source.splitlines(keepends=True)
    result = []
    for line in lines:
        stripped = line.strip()
        if _CONFIG_RE.match(stripped):
            result.append(config_replacement)
        elif _SRC_FROM_RE.match(stripped):
            result.append(_SRC_FROM_RE.sub(r"from \1 import", stripped) + "\n")
        elif _SRC_IMPORT_RE.match(stripped):
            result.append(_SRC_IMPORT_RE.sub(r"import \1", stripped) + "\n")
        else:
            result.append(line)
    return "".join(result)


def package(block1_dir: Path, output: Path) -> None:
    src_dir = block1_dir / "src"
    if not src_dir.is_dir():
        raise FileNotFoundError(f"Block 1 src directory not found: {src_dir}")

    missing = [m for m in MODULES if not (src_dir / m).exists()]
    if missing:
        raise FileNotFoundError(f"Missing modules in {src_dir}: {missing}")

    ref_date = _load_reference_date(block1_dir)
    config_replacement = (
        f"from datetime import date\nREFERENCE_DATE = date({ref_date.year}, {ref_date.month}, {ref_date.day})\n"
    )
    print(f"Inlining REFERENCE_DATE = {ref_date.isoformat()} (from {src_dir / 'config.py'})")

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for module in MODULES:
            source = (src_dir / module).read_text(encoding="utf-8")
            rewritten = _rewrite_imports(source, config_replacement)
            zf.writestr(module, rewritten)

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
