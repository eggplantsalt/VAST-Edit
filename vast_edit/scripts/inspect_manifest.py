"""Inspect a VAST-Edit samples.jsonl file without reading video contents."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PARENT = REPO_ROOT / "vast_edit"
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))

from vast_edit.io_utils import read_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect VAST-Edit samples.jsonl")
    parser.add_argument("samples_jsonl", help="Path to generated samples.jsonl")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = Path(args.samples_jsonl)
    records = read_jsonl(path)
    variants = Counter(record.get("variant", "") for record in records)
    families = Counter(record.get("attack_family", "") for record in records)
    missing = 0
    for record in records:
        output_video = record.get("output_video")
        if output_video and not Path(output_video).exists():
            missing += 1

    print(f"Total samples: {len(records)}")
    print(f"Variant distribution: {dict(variants)}")
    print(f"Attack family distribution: {dict(families)}")
    print(f"Missing output video paths: {missing}")
    print("First 5 samples:")
    for record in records[:5]:
        print(
            {
                "sample_id": record.get("sample_id"),
                "base_id": record.get("base_id"),
                "variant": record.get("variant"),
                "attack_family": record.get("attack_family"),
                "output_video": record.get("output_video"),
            }
        )


if __name__ == "__main__":
    main()
