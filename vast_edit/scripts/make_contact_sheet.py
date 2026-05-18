"""Create contact-sheet PNGs for quick VAST-Edit overlay inspection."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PARENT = REPO_ROOT / "vast_edit"
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))

from vast_edit.io_utils import ensure_dir, read_jsonl  # noqa: E402


VARIANT_ORDER = ("clean", "benign", "attack", "scrambled")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create VAST-Edit contact sheets")
    parser.add_argument("--samples_jsonl", required=True, help="Path to generated samples.jsonl")
    parser.add_argument("--output_dir", required=True, help="Directory for contact-sheet PNGs")
    parser.add_argument("--frame_index", type=int, default=0, help="Frame index to sample from each video")
    parser.add_argument("--cell_width", type=int, default=320, help="Rendered cell image width")
    parser.add_argument("--cell_height", type=int, default=240, help="Rendered cell image height")
    return parser.parse_args()


def _read_frame(video_path: str, frame_index: int) -> np.ndarray:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return _placeholder(f"unreadable\n{Path(video_path).name}")
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_index))
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        return _placeholder(f"missing frame\n{Path(video_path).name}")
    return frame


def _placeholder(text: str) -> np.ndarray:
    image = np.full((240, 320, 3), 235, dtype=np.uint8)
    for i, line in enumerate(text.splitlines()):
        cv2.putText(image, line[:32], (16, 90 + i * 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 40, 40), 1, cv2.LINE_AA)
    return image


def _fit_cell(frame: np.ndarray, width: int, height: int, label: str) -> np.ndarray:
    image = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
    band_h = 34
    band = image.copy()
    cv2.rectangle(band, (0, 0), (width, band_h), (0, 0, 0), -1)
    image = cv2.addWeighted(band, 0.48, image, 0.52, 0)
    lines = label.splitlines()
    for i, line in enumerate(lines[:2]):
        cv2.putText(
            image,
            line[:64],
            (8, 14 + i * 16),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
    return image


def _video_frame_count(video_path: str) -> int:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return max(0, count)


def _visible_ranges(record: Dict) -> List[Tuple[int, int]]:
    params = record.get("overlay_params") or {}
    ranges = params.get("visible_frame_ranges") or params.get("temporal_segments") or []
    parsed = []
    for item in ranges:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            start, end = int(item[0]), int(item[1])
            parsed.append((min(start, end), max(start, end)))
    if parsed:
        return parsed
    start = params.get("start_frame")
    end = params.get("end_frame")
    if start is not None and end is not None:
        return [(int(start), int(end))]
    return []


def _single_frame_index(record: Dict, requested_frame: int) -> int:
    ranges = _visible_ranges(record)
    if ranges:
        start, end = ranges[len(ranges) // 2]
        return max(0, (start + end) // 2)
    return max(0, requested_frame)


def _multi_frame_indices(record: Dict, requested_frame: int) -> List[int]:
    ranges = _visible_ranges(record)
    if len(ranges) >= 3:
        selected = [ranges[0], ranges[len(ranges) // 2], ranges[-1]]
        return [max(0, (start + end) // 2) for start, end in selected]
    if len(ranges) == 2:
        first, second = ranges
        return [
            max(0, (first[0] + first[1]) // 2),
            max(0, (first[1] + second[0]) // 2),
            max(0, (second[0] + second[1]) // 2),
        ]
    count = _video_frame_count(str(record.get("output_video")))
    if count > 2:
        return [max(0, count // 5), max(0, count // 2), max(0, count * 4 // 5)]
    return [max(0, requested_frame)] * 3


def _select_records(records: List[Dict]) -> Dict[Tuple[str, str], Dict]:
    selected: Dict[Tuple[str, str], Dict] = {}
    for record in records:
        family = str(record.get("attack_family", ""))
        variant = str(record.get("variant", ""))
        key = (family, variant)
        if family and variant and key not in selected:
            selected[key] = record
    return selected


def _make_overview(records: List[Dict], output_dir: Path, frame_index: int, cell_width: int, cell_height: int) -> Path:
    families = sorted({str(record.get("attack_family")) for record in records if record.get("attack_family")})
    selected = _select_records(records)
    rows = []
    for family in families:
        cells = []
        for variant in VARIANT_ORDER:
            record = selected.get((family, variant))
            if record:
                frame = _read_frame(str(record.get("output_video")), _single_frame_index(record, frame_index))
                label = f"{family} | {variant}\n{record.get('sample_id')}"
            else:
                frame = _placeholder("missing sample")
                label = f"{family} | {variant}\nmissing"
            cells.append(_fit_cell(frame, cell_width, cell_height, label))
        rows.append(np.concatenate(cells, axis=1))
    sheet = np.concatenate(rows, axis=0)
    output_path = output_dir / "contact_sheet_overview.png"
    cv2.imwrite(str(output_path), sheet)
    return output_path


def _make_family_sheets(records: List[Dict], output_dir: Path, frame_index: int, cell_width: int, cell_height: int) -> List[Path]:
    by_family: Dict[str, List[Dict]] = defaultdict(list)
    for record in records:
        by_family[str(record.get("attack_family"))].append(record)
    paths = []
    for family, family_records in sorted(by_family.items()):
        selected = _select_records(family_records)
        cells = []
        for variant in VARIANT_ORDER:
            record = selected.get((family, variant))
            if record:
                frame = _read_frame(str(record.get("output_video")), _single_frame_index(record, frame_index))
                label = f"{variant}\n{record.get('sample_id')}"
            else:
                frame = _placeholder("missing sample")
                label = f"{variant}\nmissing"
            cells.append(_fit_cell(frame, cell_width, cell_height, label))
        sheet = np.concatenate(cells, axis=1)
        path = output_dir / f"contact_sheet_{family}.png"
        cv2.imwrite(str(path), sheet)
        paths.append(path)
    return paths


def _make_temporal_multiframe_sheet(
    records: List[Dict],
    output_dir: Path,
    frame_index: int,
    cell_width: int,
    cell_height: int,
) -> Path | None:
    temporal_records = [
        record for record in records if record.get("attack_family") == "temporal_cue_chain"
    ]
    if not temporal_records:
        return None
    selected = _select_records(temporal_records)
    rows = []
    for variant in VARIANT_ORDER:
        record = selected.get(("temporal_cue_chain", variant))
        cells = []
        for label_name, frame_idx in zip(("early", "middle", "late"), _multi_frame_indices(record or {}, frame_index)):
            if record:
                frame = _read_frame(str(record.get("output_video")), frame_idx)
                label = f"temporal_cue_chain | {variant} | {label_name} f{frame_idx}\n{record.get('sample_id')}"
            else:
                frame = _placeholder("missing sample")
                label = f"temporal_cue_chain | {variant} | {label_name}\nmissing"
            cells.append(_fit_cell(frame, cell_width, cell_height, label))
        rows.append(np.concatenate(cells, axis=1))
    sheet = np.concatenate(rows, axis=0)
    output_path = output_dir / "contact_sheet_temporal_cue_chain_multiframe.png"
    cv2.imwrite(str(output_path), sheet)
    return output_path


def main() -> None:
    args = parse_args()
    records = read_jsonl(args.samples_jsonl)
    output_dir = ensure_dir(args.output_dir)
    overview = _make_overview(records, output_dir, args.frame_index, args.cell_width, args.cell_height)
    family_sheets = _make_family_sheets(records, output_dir, args.frame_index, args.cell_width, args.cell_height)
    temporal_sheet = _make_temporal_multiframe_sheet(
        records,
        output_dir,
        args.frame_index,
        args.cell_width,
        args.cell_height,
    )
    print(f"Wrote overview contact sheet: {overview}")
    for path in family_sheets:
        print(f"Wrote family contact sheet: {path}")
    if temporal_sheet is not None:
        print(f"Wrote temporal multi-frame contact sheet: {temporal_sheet}")


if __name__ == "__main__":
    main()
