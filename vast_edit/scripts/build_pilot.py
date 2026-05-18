"""Command-line entrypoint for building a VAST-Edit pilot dataset."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PARENT = REPO_ROOT / "vast_edit"
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))

from vast_edit.builder import build_pilot_dataset  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build VAST-Edit v0.1 pilot data")
    parser.add_argument("--input_manifest", required=True, help="Path to input manifest JSONL")
    parser.add_argument("--output_dir", required=True, help="Output directory for generated data")
    parser.add_argument("--config", required=True, help="Path to pilot YAML config")
    parser.add_argument("--templates", required=True, help="Path to attack templates YAML")
    parser.add_argument("--limit", type=int, default=None, help="Optional number of input rows")
    parser.add_argument("--seed", type=int, default=0, help="Base random seed")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output videos")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = build_pilot_dataset(
        input_manifest_path=args.input_manifest,
        output_dir=args.output_dir,
        config_path=args.config,
        templates_path=args.templates,
        limit=args.limit,
        overwrite=args.overwrite,
        seed=args.seed,
    )
    variants = {}
    for record in records:
        variants[record.variant] = variants.get(record.variant, 0) + 1
    print(f"Built {len(records)} VAST-Edit samples")
    print(f"Output: {args.output_dir}")
    print(f"Variant distribution: {variants}")


if __name__ == "__main__":
    main()
