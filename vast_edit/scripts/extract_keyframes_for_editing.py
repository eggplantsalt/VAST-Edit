#!/usr/bin/env python3
"""Build a balanced image-edit pilot subset and extract one keyframe per sample."""
from __future__ import annotations
import argparse, json, sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List
import cv2
REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PARENT = REPO_ROOT / "vast_edit"
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))
FAMILIES = ["spatial_text_cue", "spatial_target_cue", "temporal_cue_chain"]
VARIANTS = ["clean", "benign", "attack", "scrambled"]

def read_jsonl(path: Path) -> List[dict]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def write_jsonl(records: Iterable[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")

def base_scene_key(base_id: str, attack_family: str) -> str:
    suffix = "__" + attack_family
    if base_id.endswith(suffix):
        return base_id[: -len(suffix)]
    return base_id.rsplit("__", 1)[0]

def select_balanced_records(model_inputs: List[dict], samples_by_id: Dict[str, dict], scene_count: int) -> List[dict]:
    by_scene = defaultdict(dict)
    for rec in model_inputs:
        sample = samples_by_id.get(rec["sample_id"], {})
        family = rec.get("attack_family") or sample.get("attack_family")
        variant = rec.get("variant") or sample.get("variant")
        base = rec.get("base_id") or sample.get("base_id")
        if family not in FAMILIES or variant not in VARIANTS or not base:
            continue
        scene = base_scene_key(base, family)
        by_scene[scene][(family, variant)] = rec
    complete = []
    for scene, keyed in by_scene.items():
        if all((family, variant) in keyed for family in FAMILIES for variant in VARIANTS):
            complete.append(scene)
    complete.sort()
    chosen_scenes = complete[:scene_count]
    if len(chosen_scenes) < scene_count:
        raise RuntimeError(f"Need {scene_count} complete scenes, found {len(chosen_scenes)}: {complete}")
    selected = []
    for scene in chosen_scenes:
        keyed = by_scene[scene]
        for family in FAMILIES:
            for variant in VARIANTS:
                selected.append(keyed[(family, variant)])
    return selected

def extract_keyframe(video_path: Path, output_path: Path, frame_policy: str = "middle") -> dict:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    index = 0 if frame_policy == "first" or total <= 1 else max(0, total // 2)
    cap.set(cv2.CAP_PROP_POS_FRAMES, index)
    ok, frame = cap.read()
    if not ok or frame is None:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ok, frame = cap.read()
        index = 0
    cap.release()
    if not ok or frame is None:
        raise RuntimeError(f"Could not read keyframe from video: {video_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), frame):
        raise RuntimeError(f"Could not write keyframe: {output_path}")
    return {"keyframe_index": index, "source_num_frames": total}

def main() -> int:
    parser = argparse.ArgumentParser(description="Extract VAST-Edit keyframes for image-edit pilot.")
    parser.add_argument("--model_inputs_jsonl", required=True)
    parser.add_argument("--samples_jsonl", required=True)
    parser.add_argument("--output_jsonl", required=True)
    parser.add_argument("--keyframe_dir", required=True)
    parser.add_argument("--scene_count", type=int, default=2)
    parser.add_argument("--frame_policy", choices=["first", "middle"], default="middle")
    args = parser.parse_args()
    model_inputs = read_jsonl(Path(args.model_inputs_jsonl))
    samples = read_jsonl(Path(args.samples_jsonl))
    samples_by_id = {s["sample_id"]: s for s in samples}
    selected = select_balanced_records(model_inputs, samples_by_id, args.scene_count)
    out_records = []
    keyframe_dir = Path(args.keyframe_dir)
    for rec in selected:
        sample = samples_by_id[rec["sample_id"]]
        variant = rec["variant"]
        keyframe_path = keyframe_dir / variant / f"{rec['sample_id']}.png"
        meta = extract_keyframe(Path(rec["input_video"]), keyframe_path, args.frame_policy)
        out = dict(rec)
        out.update({
            "attack_intent": sample.get("attack_intent"),
            "input_keyframe": str(keyframe_path),
            "keyframe_index": meta["keyframe_index"],
            "source_num_frames": meta["source_num_frames"],
            "image_edit_prompt": rec.get("authorized_instruction"),
            "prompt_policy": "authorized_instruction_only",
        })
        out_records.append(out)
    write_jsonl(out_records, Path(args.output_jsonl))
    print(json.dumps({
        "input_records": len(model_inputs),
        "selected_records": len(out_records),
        "scene_count": args.scene_count,
        "variant_counts": Counter(r["variant"] for r in out_records),
        "attack_family_counts": Counter(r["attack_family"] for r in out_records),
        "output_jsonl": args.output_jsonl,
        "keyframe_dir": args.keyframe_dir,
    }, indent=2, default=dict))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())