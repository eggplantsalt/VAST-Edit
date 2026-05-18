#!/usr/bin/env python3
"""Run a real open-source image editing model on VAST-Edit keyframes."""
from __future__ import annotations
import argparse, json, os
from pathlib import Path
from typing import Iterable, List
import torch
from PIL import Image
from diffusers import StableDiffusionInstructPix2PixPipeline, EulerAncestralDiscreteScheduler

def read_jsonl(path: Path) -> List[dict]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def append_jsonl(records: Iterable[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")

def load_done(path: Path) -> set:
    if not path.exists():
        return set()
    done = set()
    for rec in read_jsonl(path):
        if rec.get("status") == "ok":
            done.add(rec.get("sample_id"))
    return done

def prepare_image(path: Path, resolution: int) -> Image.Image:
    image = Image.open(path).convert("RGB")
    image.thumbnail((resolution, resolution), Image.Resampling.LANCZOS)
    w, h = image.size
    w = max(64, (w // 8) * 8)
    h = max(64, (h // 8) * 8)
    return image.resize((w, h), Image.Resampling.LANCZOS)

def main() -> int:
    parser = argparse.ArgumentParser(description="Run InstructPix2Pix on VAST-Edit pilot keyframes.")
    parser.add_argument("--model_inputs_jsonl", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--model_id", default="timbrooks/instruct-pix2pix")
    parser.add_argument("--model_name", default="instruct_pix2pix")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resolution", type=int, default=256)
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument("--guidance_scale", type=float, default=7.5)
    parser.add_argument("--image_guidance_scale", type=float, default=1.5)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--enable_cpu_offload", action="store_true")
    args = parser.parse_args()
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    output_dir = Path(args.output_dir)
    result_path = output_dir / "metadata" / f"image_edit_results.{args.model_name}.jsonl"
    records = read_jsonl(Path(args.model_inputs_jsonl))
    if args.limit is not None:
        records = records[: args.limit]
    done = load_done(result_path) if args.resume else set()
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    pipe = StableDiffusionInstructPix2PixPipeline.from_pretrained(
        args.model_id,
        torch_dtype=dtype,
        safety_checker=None,
        cache_dir=os.environ.get("HF_HOME"),
    )
    pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)
    if torch.cuda.is_available():
        if args.enable_cpu_offload:
            pipe.enable_model_cpu_offload()
        else:
            pipe.to("cuda")
    else:
        pipe.to("cpu")
    generator_device = "cuda" if torch.cuda.is_available() else "cpu"
    results = []
    for index, rec in enumerate(records):
        sample_id = rec["sample_id"]
        if sample_id in done:
            continue
        variant = rec["variant"]
        output_image = output_dir / "model_outputs" / args.model_name / variant / f"{sample_id}.png"
        output_image.parent.mkdir(parents=True, exist_ok=True)
        prompt = rec.get("authorized_instruction") or ""
        result = {
            "sample_id": sample_id,
            "base_id": rec.get("base_id"),
            "variant": variant,
            "attack_family": rec.get("attack_family"),
            "authorized_instruction": prompt,
            "attack_intent": rec.get("attack_intent"),
            "input_keyframe": rec.get("input_keyframe"),
            "output_image": str(output_image),
            "model_name": args.model_name,
            "model_id": args.model_id,
            "seed": args.seed,
            "status": "pending",
            "error": None,
            "prompt_policy": "authorized_instruction_only",
            "num_inference_steps": args.steps,
            "resolution": args.resolution,
        }
        try:
            image = prepare_image(Path(rec["input_keyframe"]), args.resolution)
            generator = torch.Generator(device=generator_device).manual_seed(args.seed + index)
            edited = pipe(
                prompt=prompt,
                image=image,
                num_inference_steps=args.steps,
                image_guidance_scale=args.image_guidance_scale,
                guidance_scale=args.guidance_scale,
                generator=generator,
            ).images[0]
            edited.save(output_image)
            result["status"] = "ok"
        except Exception as exc:
            result["status"] = "error"
            result["error"] = f"{type(exc).__name__}: {exc}"
        append_jsonl([result], result_path)
        results.append(result)
        print(json.dumps({"index": index, "sample_id": sample_id, "status": result["status"], "error": result["error"]}))
    ok = sum(1 for r in results if r["status"] == "ok")
    err = sum(1 for r in results if r["status"] != "ok")
    print(json.dumps({"processed": len(results), "ok": ok, "error": err, "results": str(result_path)}, indent=2))
    return 0 if err == 0 else 2
if __name__ == "__main__":
    raise SystemExit(main())