"""Generate Block 2 spec diagrams as PNGs using matplotlib."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# ── Shared styling ───────────────────────────────────────────────────────────

COLORS = {
    "local":     "#E8E8E8",   # grey — local machine
    "s3":        "#FFF3CD",   # warm yellow — S3 storage
    "glue":      "#D4EDDA",   # green — Glue compute
    "catalog":   "#CCE5FF",   # blue — Glue Catalog / Athena
    "gate":      "#F8D7DA",   # red — hard gate
    "terraform": "#E2D9F3",   # purple — IaC
    "iam":       "#FCE4EC",   # pink — IAM
    "arrow":     "#555555",
}
FONT = "Segoe UI"
TITLE_SIZE = 14
LABEL_SIZE = 9
BOX_PAD = 0.3


def _box(ax, x, y, w, h, text, color, fontsize=LABEL_SIZE, bold=False):
    """Draw a rounded box with centered text."""
    box = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.15",
        facecolor=color, edgecolor="#888888", linewidth=1.2,
    )
    ax.add_patch(box)
    weight = "bold" if bold else "normal"
    ax.text(x, y, text, ha="center", va="center",
            fontsize=fontsize, fontfamily=FONT, weight=weight,
            linespacing=1.4)


def _arrow(ax, x1, y1, x2, y2, style="-|>", color=COLORS["arrow"], lw=1.5):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw))


def _dashed_arrow(ax, x1, y1, x2, y2, color=COLORS["arrow"]):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.2,
                                linestyle="dashed"))


# ── Diagram 1: Architecture ─────────────────────────────────────────────────

def draw_architecture():
    fig, ax = plt.subplots(figsize=(10, 14))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis("off")
    ax.set_title("Block 2 — Cloud ETL Architecture", fontsize=TITLE_SIZE,
                 fontfamily=FONT, fontweight="bold", pad=15)

    # ── Local machine section ──
    local_rect = mpatches.FancyBboxPatch(
        (0.3, 11.8), 3.8, 1.8,
        boxstyle="round,pad=0.2", facecolor=COLORS["local"],
        edgecolor="#AAAAAA", linewidth=1.5, linestyle="dashed",
    )
    ax.add_patch(local_rect)
    ax.text(2.2, 13.3, "Local Machine", ha="center", fontsize=10,
            fontfamily=FONT, fontweight="bold", color="#666666")

    _box(ax, 1.5, 12.5, 1.8, 0.7,
         "Block 1\ndata/raw/*.csv", COLORS["local"], fontsize=8)
    _box(ax, 3.2, 12.5, 1.5, 0.7,
         "upload\nscript", COLORS["local"], fontsize=8)

    _arrow(ax, 2.4, 12.5, 2.45, 12.5)

    # ── AWS section ──
    aws_rect = mpatches.FancyBboxPatch(
        (0.3, 0.3), 9.4, 11.2,
        boxstyle="round,pad=0.2", facecolor="#FAFAFA",
        edgecolor="#FF9900", linewidth=2.0,
    )
    ax.add_patch(aws_rect)
    ax.text(5.0, 11.2, "AWS", ha="center", fontsize=12,
            fontfamily=FONT, fontweight="bold", color="#FF9900")

    # S3 raw
    _box(ax, 3.0, 10.0, 3.0, 1.0,
         "S3 — Landing Zone\ns3://bucket/raw/\n6 OMOP-style CSVs",
         COLORS["s3"], fontsize=8)

    # Upload arrow
    _arrow(ax, 3.2, 12.1, 3.0, 10.55)

    # Glue job
    _box(ax, 3.0, 8.0, 3.5, 1.2,
         "AWS Glue Job\n(PySpark ETL)\netl_job.py",
         COLORS["glue"], fontsize=9, bold=True)

    _arrow(ax, 3.0, 9.45, 3.0, 8.65)

    # Pipeline stages (right side)
    stages = [
        ("1 · Read CSVs\nfrom S3", COLORS["glue"]),
        ("2 · Validate raw\ndetection · log-only", COLORS["glue"]),
        ("3 · Clean\ndrop dirty rows", COLORS["glue"]),
        ("4 · Validate cleaned\nHard gate", COLORS["gate"]),
        ("5 · Build\nanalytic_person", COLORS["glue"]),
        ("6 · Write Parquet\nto S3", COLORS["glue"]),
        ("7 · Write metrics\nto S3", COLORS["glue"]),
    ]
    stage_x = 7.5
    stage_top = 10.2
    stage_h = 0.65
    stage_gap = 0.85
    for i, (label, color) in enumerate(stages):
        sy = stage_top - i * stage_gap
        _box(ax, stage_x, sy, 2.8, stage_h, label, color, fontsize=7)
        if i > 0:
            _arrow(ax, stage_x, sy + stage_h / 2 + 0.12,
                   stage_x, sy + stage_h / 2 + 0.08)

    # Connect Glue job to stages
    _dashed_arrow(ax, 4.75, 8.0, 6.1, 10.2)

    # S3 processed
    _box(ax, 3.0, 5.5, 3.2, 1.2,
         "S3 — Processed Zone\ns3://bucket/processed/\nanalytic_person/\npipeline_metrics.json",
         COLORS["s3"], fontsize=8)

    _arrow(ax, 3.0, 7.35, 3.0, 6.15)

    # Glue Catalog
    _box(ax, 3.0, 3.5, 3.0, 0.9,
         "Glue Data Catalog\nomop_cloud_etl database\nanalytic_person table",
         COLORS["catalog"], fontsize=8)

    _arrow(ax, 3.0, 4.85, 3.0, 4.0)

    # Athena
    _box(ax, 3.0, 1.8, 2.5, 0.9,
         "Amazon Athena\nSQL queries",
         COLORS["catalog"], fontsize=9, bold=True)

    _arrow(ax, 3.0, 3.0, 3.0, 2.3)

    # Terraform label
    _box(ax, 7.5, 2.0, 2.8, 1.4,
         "Terraform\nAll resources\ndefined as code",
         COLORS["terraform"], fontsize=9, bold=True)

    _dashed_arrow(ax, 6.1, 2.5, 4.55, 3.5)
    _dashed_arrow(ax, 6.1, 1.8, 4.25, 1.8)
    _dashed_arrow(ax, 7.5, 3.0, 4.55, 5.5)
    _dashed_arrow(ax, 8.0, 3.0, 5.0, 8.0)

    # IAM role
    _box(ax, 7.5, 5.5, 2.5, 0.8,
         "IAM Role\nGlue execution\nS3 + Catalog + Logs",
         COLORS["iam"], fontsize=7)

    _dashed_arrow(ax, 7.5, 6.0, 4.75, 7.6)

    plt.tight_layout()
    plt.savefig("docs/architecture.png", dpi=150, bbox_inches="tight",
                facecolor="white")
    plt.close()
    print("  OK architecture.png")


# ── Diagram 2: Data Flow ────────────────────────────────────────────────────

def draw_data_flow():
    fig, ax = plt.subplots(figsize=(5, 13))
    ax.set_xlim(0, 5)
    ax.set_ylim(0, 13)
    ax.axis("off")
    ax.set_title("Block 2 — Data Flow", fontsize=TITLE_SIZE,
                 fontfamily=FONT, fontweight="bold", pad=15)

    steps = [
        ("Block 1\ndata/raw/*.csv\n(local)", COLORS["local"]),
        ("Upload to S3\nscripts/upload_raw.py", COLORS["local"]),
        ("S3 Landing Zone\ns3://bucket/raw/\n6 OMOP-style CSVs", COLORS["s3"]),
        ("Validate Raw\ndetection · results\nsaved to metrics", COLORS["glue"]),
        ("Clean\ndrop dirty rows\nlog before/after counts", COLORS["glue"]),
        ("Hard Gate\nvalidate cleaned\n0 violations required", COLORS["gate"]),
        ("Build analytic_person\njoin · aggregate\none row per person", COLORS["glue"]),
        ("S3 Processed Zone\npartitioned Parquet\npipeline_metrics.json", COLORS["s3"]),
        ("Glue Data Catalog\nomop_cloud_etl\nanalytic_person table", COLORS["catalog"]),
        ("Amazon Athena\nSQL queries", COLORS["catalog"]),
    ]

    x = 2.5
    top = 12.2
    h = 0.85
    gap = 1.15

    for i, (label, color) in enumerate(steps):
        y = top - i * gap
        _box(ax, x, y, 3.5, h, label, color, fontsize=8)
        if i > 0:
            _arrow(ax, x, y + h / 2 + 0.22, x, y + h / 2 + 0.08)

    plt.tight_layout()
    plt.savefig("docs/data_flow.png", dpi=150, bbox_inches="tight",
                facecolor="white")
    plt.close()
    print("  OK data_flow.png")


# ── Diagram 3: Terraform Resources ──────────────────────────────────────────

def draw_terraform():
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")
    ax.set_title("Block 2 — Terraform Resource Map", fontsize=TITLE_SIZE,
                 fontfamily=FONT, fontweight="bold", pad=15)

    # Terraform root
    _box(ax, 5.0, 6.0, 3.0, 0.7,
         "terraform/", COLORS["terraform"], fontsize=10, bold=True)

    # Row 1: S3, IAM, Glue, Athena
    modules = [
        (1.5, 4.2, "s3.tf\nBucket\nVersioning\nLifecycle", COLORS["s3"]),
        (4.0, 4.2, "iam.tf\nGlue Role\nPolicy", COLORS["iam"]),
        (6.5, 4.2, "glue.tf\nDatabase\nTable\nJob", COLORS["glue"]),
        (9.0, 4.2, "athena.tf\nWorkgroup\nResult location", COLORS["catalog"]),
    ]
    for mx, my, label, color in modules:
        _box(ax, mx, my, 2.2, 1.1, label, color, fontsize=8)
        _arrow(ax, 5.0, 5.6, mx, 4.8)

    # Row 2: Supporting files
    support = [
        (2.5, 2.0, "variables.tf\nbucket name\nregion · tags", COLORS["terraform"]),
        (5.0, 2.0, "outputs.tf\nbucket ARN\njob name\nworkgroup", COLORS["terraform"]),
        (7.5, 2.0, "main.tf\nprovider\nbackend", COLORS["terraform"]),
    ]
    for sx, sy, label, color in support:
        _box(ax, sx, sy, 2.2, 0.9, label, color, fontsize=8)

    plt.tight_layout()
    plt.savefig("docs/terraform_resources.png", dpi=150, bbox_inches="tight",
                facecolor="white")
    plt.close()
    print("  OK terraform_resources.png")


# ── Diagram 4: S3 Bucket Layout ─────────────────────────────────────────────

def draw_s3_layout():
    fig, ax = plt.subplots(figsize=(7, 8))
    ax.set_xlim(0, 7)
    ax.set_ylim(0, 8)
    ax.axis("off")
    ax.set_title("Block 2 — S3 Bucket Layout", fontsize=TITLE_SIZE,
                 fontfamily=FONT, fontweight="bold", pad=15)

    # Bucket
    _box(ax, 3.5, 7.0, 4.0, 0.7,
         "s3://<bucket>/", COLORS["s3"], fontsize=10, bold=True)

    # Three prefixes
    prefixes = [
        (1.5, 5.5, "raw/", COLORS["s3"],
         "person.csv\nvisit_occurrence.csv\ncondition_occurrence.csv\n"
         "drug_exposure.csv\nmeasurement.csv\nnote.csv"),
        (3.5, 5.5, "processed/", COLORS["glue"],
         "analytic_person/\n  year_of_birth_band=1940s/\n"
         "  year_of_birth_band=1950s/\n  ...\npipeline_metrics.json"),
        (5.5, 5.5, "scripts/", COLORS["catalog"],
         "etl_job.py"),
    ]

    for px, py, title, color, contents in prefixes:
        _box(ax, px, py, 1.6, 0.6, title, color, fontsize=9, bold=True)
        _arrow(ax, 3.5, 6.6, px, 5.85)

        # Contents below
        ax.text(px, py - 0.55, contents, ha="center", va="top",
                fontsize=7, fontfamily=FONT, color="#444444",
                linespacing=1.5,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                          edgecolor="#CCCCCC", linewidth=0.8))

    plt.tight_layout()
    plt.savefig("docs/s3_layout.png", dpi=150, bbox_inches="tight",
                facecolor="white")
    plt.close()
    print("  OK s3_layout.png")


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating Block 2 diagrams...")
    draw_architecture()
    draw_data_flow()
    draw_terraform()
    draw_s3_layout()
    print("Done.")
