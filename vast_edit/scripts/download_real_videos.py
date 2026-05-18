#!/usr/bin/env python3
"""Download and prepare a small real-video DAVIS subset for VAST-Edit."""
from __future__ import annotations
import argparse, json, shutil, subprocess, urllib.request, zipfile
from pathlib import Path
from typing import Iterable, List
import cv2
import numpy as np

DEFAULT_DAVIS_URL = "https://data.vision.ee.ethz.ch/csergi/share/davis/DAVIS-2017-trainval-480p.zip"
DEFAULT_SEQUENCES = ["blackswan", "camel", "car-roundabout", "cows", "dog", "dogs-jump", "goat", "horsejump-high"]
DATASET_NOTE = "DAVIS 2017 trainval 480p public research dataset; cite DAVIS papers and follow dataset terms."

def write_jsonl(rows: Iterable[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

def download_file(url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and output_path.stat().st_size > 0:
        print(f"download skip existing: {output_path} ({output_path.stat().st_size} bytes)")
        return
    if shutil.which("wget"):
        subprocess.run(["wget", "-c", "-O", str(output_path), url], check=True)
    else:
        urllib.request.urlretrieve(url, output_path)

def resize_frame(frame: np.ndarray, short_side: int) -> np.ndarray:
    h, w = frame.shape[:2]
    if min(h, w) == short_side:
        return frame
    scale = short_side / float(min(h, w))
    nw = int(round(w * scale / 2) * 2)
    nh = int(round(h * scale / 2) * 2)
    return cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA)

def sequence_frame_names(zf: zipfile.ZipFile, sequence: str) -> List[str]:
    prefix = f"DAVIS/JPEGImages/480p/{sequence}/"
    names = [n for n in zf.namelist() if n.startswith(prefix) and n.lower().endswith((".jpg", ".jpeg", ".png"))]
    return sorted(names)

def write_sequence_clip(zf: zipfile.ZipFile, sequence: str, output_path: Path, fps: float, max_seconds: float, short_side: int) -> dict:
    names = sequence_frame_names(zf, sequence)
    if not names:
        raise RuntimeError(f"No DAVIS frames found for sequence: {sequence}")
    max_frames = int(round(fps * max_seconds))
    selected = names[:max_frames]
    writer = None
    width = height = None
    count = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    for name in selected:
        data = np.frombuffer(zf.read(name), dtype=np.uint8)
        frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if frame is None:
            continue
        frame = resize_frame(frame, short_side)
        h, w = frame.shape[:2]
        if writer is None:
            width, height = w, h
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            if not writer.isOpened():
                raise RuntimeError(f"Could not open video writer: {output_path}")
        if (w, h) != (width, height):
            frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
        writer.write(frame)
        count += 1
    if writer is not None:
        writer.release()
    if count == 0:
        raise RuntimeError(f"No frames written for sequence: {sequence}")
    return {"frames": count, "fps": fps, "width": width, "height": height, "duration_sec": count / fps}

def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a small DAVIS real-video subset for VAST-Edit.")
    parser.add_argument("--source_root", default="/opt/data/private/zy_data/VAST-Edit/source_videos/real_video_pilot_v01")
    parser.add_argument("--dataset_url", default=DEFAULT_DAVIS_URL)
    parser.add_argument("--sequences", nargs="+", default=DEFAULT_SEQUENCES)
    parser.add_argument("--fps", type=float, default=16.0)
    parser.add_argument("--max_seconds", type=float, default=5.0)
    parser.add_argument("--short_side", type=int, default=480)
    parser.add_argument("--skip_download", action="store_true")
    args = parser.parse_args()
    root = Path(args.source_root)
    raw_zip = root / "raw" / "DAVIS-2017-trainval-480p.zip"
    clips_dir = root / "clips"
    if not args.skip_download:
        download_file(args.dataset_url, raw_zip)
    if not raw_zip.exists():
        raise FileNotFoundError(raw_zip)
    clip_rows = []
    license_rows = []
    with zipfile.ZipFile(raw_zip) as zf:
        for sequence in args.sequences:
            output_path = clips_dir / f"davis_{sequence}.mp4"
            meta = write_sequence_clip(zf, sequence, output_path, args.fps, args.max_seconds, args.short_side)
            clip_id = "davis_" + sequence.replace("-", "_")
            clip_rows.append({
                "clip_id": clip_id,
                "sequence": sequence,
                "video_path": str(output_path),
                "source_dataset": "DAVIS 2017 trainval 480p",
                "source_url": args.dataset_url,
                "fps": meta["fps"],
                "num_frames": meta["frames"],
                "duration_sec": meta["duration_sec"],
                "width": meta["width"],
                "height": meta["height"],
            })
            license_rows.append({
                "clip_id": clip_id,
                "video_path": str(output_path),
                "source_dataset": "DAVIS 2017 trainval 480p",
                "source_url": args.dataset_url,
                "source_sequence": sequence,
                "license": "DAVIS public research dataset terms; citation/attribution required",
                "credit": "DAVIS dataset authors; Perazzi et al. and Pont-Tuset et al.",
                "retrieval_method": "official DAVIS dataset zip, selected frame sequence converted to short mp4",
                "notes": DATASET_NOTE,
            })
    write_jsonl(clip_rows, root / "real_video_manifest.jsonl")
    write_jsonl(license_rows, root / "license_manifest.jsonl")
    summary = {"clips": len(clip_rows), "source_root": str(root), "raw_zip_bytes": raw_zip.stat().st_size, "manifest": str(root / "real_video_manifest.jsonl"), "license_manifest": str(root / "license_manifest.jsonl")}
    (root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())