"""Expand a base VAST-Edit manifest into attack-family-specific records."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PARENT = REPO_ROOT / "vast_edit"
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))

from vast_edit.io_utils import read_jsonl  # noqa: E402
from vast_edit.manifest_expansion import attack_family_counts, expand_manifest_file  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Expand a VAST-Edit base manifest")
    parser.add_argument("--base_manifest", required=True, help="Path to base manifest JSONL")
    parser.add_argument("--output_manifest", required=True, help="Path to expanded output manifest JSONL")
    parser.add_argument(
        "--attack_families",
        nargs="+",
        default=None,
        help="Optional attack families to use for all rows",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_records = read_jsonl(args.base_manifest)
    expanded = expand_manifest_file(
        args.base_manifest,
        args.output_manifest,
        default_attack_families=args.attack_families,
    )
    print(f"Input records: {len(input_records)}")
    print(f"Output records: {len(expanded)}")
    print(f"Attack family distribution: {attack_family_counts(expanded)}")
    print(f"Wrote expanded manifest: {args.output_manifest}")


if __name__ == "__main__":
    main()
