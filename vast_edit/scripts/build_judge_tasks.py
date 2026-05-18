"""Build VAST-Edit judge task JSONL files without invoking any judge model."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PARENT = REPO_ROOT / "vast_edit"
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))

from vast_edit.config import load_yaml  # noqa: E402
from vast_edit.eval.judge_tasks import (  # noqa: E402
    build_pairwise_authority_task,
    build_single_video_judge_task,
    default_model_output_path,
)
from vast_edit.io_utils import ensure_dir, read_jsonl, write_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build VAST-Edit judge task files")
    parser.add_argument("--samples_jsonl", required=True, help="Path to generated samples.jsonl")
    parser.add_argument("--model_name", required=True, help="Model or method name")
    parser.add_argument("--model_output_root", required=True, help="Root directory of model outputs")
    parser.add_argument(
        "--model_outputs_manifest",
        default=None,
        help="Optional JSONL manifest with sample_id and output_video fields",
    )
    parser.add_argument("--judge_prompts", required=True, help="Path to judge prompts YAML")
    parser.add_argument("--output_dir", required=True, help="Directory for judge task JSONL outputs")
    return parser.parse_args()


def _load_model_outputs(args: argparse.Namespace, samples):
    if args.model_outputs_manifest:
        manifest = read_jsonl(args.model_outputs_manifest)
        return {str(row.get("sample_id")): str(row.get("output_video")) for row in manifest}
    outputs = {}
    for sample in samples:
        sample_id = str(sample.get("sample_id"))
        variant = str(sample.get("variant"))
        outputs[sample_id] = default_model_output_path(args.model_output_root, variant, sample_id)
    return outputs


def main() -> None:
    args = parse_args()
    samples = read_jsonl(args.samples_jsonl)
    prompts = load_yaml(args.judge_prompts)
    model_outputs = _load_model_outputs(args, samples)
    output_dir = ensure_dir(args.output_dir)

    single_tasks = []
    for sample in samples:
        sample_id = str(sample.get("sample_id"))
        model_output = model_outputs.get(sample_id)
        if not model_output:
            continue
        task = build_single_video_judge_task(sample, model_output, prompts)
        task["model_name"] = args.model_name
        single_tasks.append(task)

    grouped = defaultdict(list)
    for sample in samples:
        grouped[(sample.get("base_id"), sample.get("attack_family"))].append(sample)

    pairwise_tasks = []
    for records in grouped.values():
        task = build_pairwise_authority_task(records, model_outputs, prompts)
        if task is not None:
            task["model_name"] = args.model_name
            pairwise_tasks.append(task)

    single_path = output_dir / "judge_tasks.single.jsonl"
    pairwise_path = output_dir / "judge_tasks.pairwise.jsonl"
    write_jsonl(single_tasks, single_path)
    write_jsonl(pairwise_tasks, pairwise_path)
    print(f"Wrote {len(single_tasks)} single-video judge tasks to {single_path}")
    print(f"Wrote {len(pairwise_tasks)} pairwise judge tasks to {pairwise_path}")


if __name__ == "__main__":
    main()
