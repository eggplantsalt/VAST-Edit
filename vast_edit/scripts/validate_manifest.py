"""Lightweight manifest validation for VAST-Edit JSONL files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PARENT = REPO_ROOT / "vast_edit"
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))

from vast_edit.io_utils import read_jsonl  # noqa: E402


INPUT_REQUIRED = (
    "source_video",
    "source_video_name",
    "source_prompt",
    "authorized_instruction",
    "target_prompt",
    "attack_family",
    "attack_intent",
    "expected_behavior",
    "safety_rule",
)

SAMPLES_REQUIRED = (
    "sample_id",
    "base_id",
    "source_video",
    "source_video_name",
    "source_prompt",
    "authorized_instruction",
    "target_prompt",
    "attack_family",
    "attack_intent",
    "variant",
    "overlay_params",
    "expected_behavior",
    "safety_rule",
    "output_video",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a VAST-Edit manifest")
    parser.add_argument("manifest_positional", nargs="?", help="Path to input manifest or samples JSONL")
    parser.add_argument("--manifest", dest="manifest_option", help="Path to input manifest or samples JSONL")
    parser.add_argument("--mode", choices=("input", "samples"), required=True)
    args = parser.parse_args()
    args.manifest = args.manifest_option or args.manifest_positional
    if not args.manifest:
        parser.error("manifest path is required as a positional argument or --manifest")
    return args


def _validate_record(record: Dict, index: int, required: tuple) -> List[str]:
    issues: List[str] = []
    if "id" not in record and "sample_id" not in record and "base_id" not in record:
        issues.append(f"line {index}: missing id/sample_id/base_id")
    for field in required:
        if field not in record or record[field] in (None, ""):
            issues.append(f"line {index}: missing required field `{field}`")
    return issues


def main() -> None:
    args = parse_args()
    records = read_jsonl(args.manifest)
    required = INPUT_REQUIRED if args.mode == "input" else SAMPLES_REQUIRED
    issues: List[str] = []
    for index, record in enumerate(records, start=1):
        issues.extend(_validate_record(record, index, required))
        if args.mode == "samples" and not isinstance(record.get("overlay_params"), dict):
            issues.append(f"line {index}: overlay_params must be an object")

    if issues:
        print(f"Found {len(issues)} issue(s):")
        for issue in issues:
            print(f"- {issue}")
    else:
        print(f"No issues found in {len(records)} record(s).")


if __name__ == "__main__":
    main()
