"""Aggregate VAST-Edit judge scores into offline metrics."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PARENT = REPO_ROOT / "vast_edit"
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))

from vast_edit.eval.aggregation import (  # noqa: E402
    aggregate_scores,
    read_judge_scores,
    write_per_group_csv,
    write_per_sample_csv,
    write_summary_json,
)
from vast_edit.io_utils import ensure_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate VAST-Edit judge scores")
    parser.add_argument("--judge_scores", required=True, help="Path to judge_scores.jsonl")
    parser.add_argument("--output_dir", required=True, help="Output metrics directory")
    parser.add_argument("--quality_threshold", type=float, default=3.0)
    parser.add_argument("--score_threshold", type=float, default=3.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = read_judge_scores(args.judge_scores)
    summary = aggregate_scores(
        records,
        score_threshold=args.score_threshold,
        quality_threshold=args.quality_threshold,
    )
    output_dir = ensure_dir(args.output_dir)
    write_summary_json(summary, output_dir / "summary.json")
    write_per_sample_csv(records, output_dir / "per_sample_scores.csv")
    write_per_group_csv(summary["per_group_cals"], output_dir / "per_group_cals.csv")
    print(f"Aggregated {len(records)} judge score records into {output_dir}")


if __name__ == "__main__":
    main()
