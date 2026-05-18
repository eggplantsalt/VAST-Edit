#!/usr/bin/env python3
"""Inspect curated real-video sources and license manifest."""
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path
from typing import List
import cv2

def read_jsonl(path: Path) -> List[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def probe(path: Path) -> dict:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {"ok": False, "error": "could_not_open"}
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    cap.release()
    return {"ok": True, "fps": fps, "num_frames": frames, "width": width, "height": height, "duration_sec": frames / fps if fps else None}

def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect real-video source manifest.")
    parser.add_argument("--real_video_manifest", required=True)
    parser.add_argument("--license_manifest", required=True)
    args = parser.parse_args()
    rows = read_jsonl(Path(args.real_video_manifest))
    licenses = read_jsonl(Path(args.license_manifest))
    license_ids = {r.get("clip_id") for r in licenses}
    missing_license = []
    probes = []
    for row in rows:
        if row.get("clip_id") not in license_ids:
            missing_license.append(row.get("clip_id"))
        meta = probe(Path(row["video_path"]))
        probes.append({**row, **meta})
    summary = {
        "videos": len(rows),
        "licenses": len(licenses),
        "missing_license": missing_license,
        "ok_videos": sum(1 for p in probes if p.get("ok")),
        "datasets": Counter(r.get("source_dataset") for r in rows),
        "durations_sec": [round(p["duration_sec"], 3) for p in probes if p.get("duration_sec") is not None],
        "resolutions": Counter(f"{p.get('width')}x{p.get('height')}" for p in probes if p.get("ok")),
    }
    print(json.dumps(summary, indent=2, default=dict))
    return 0 if not missing_license and summary["ok_videos"] == len(rows) else 2
if __name__ == "__main__":
    raise SystemExit(main())