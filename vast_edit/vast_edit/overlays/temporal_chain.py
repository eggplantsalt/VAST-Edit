"""Renderer for temporal cue chain overlays."""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from ..schema import OverlayParams
from ..text_utils import make_benign_text, normalize_text_for_overlay, scramble_text
from .base import draw_box, draw_circle, draw_polyline, draw_text_box


Point = Tuple[int, int]


def _as_params(params: Union[OverlayParams, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(params, OverlayParams):
        return params.to_dict()
    return dict(params or {})


def _parse_color(value: Any, default: Tuple[int, int, int]) -> Tuple[int, int, int]:
    if value is None:
        return default
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("#") and len(text) == 7:
            return tuple(int(text[i : i + 2], 16) for i in (1, 3, 5))
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return tuple(int(max(0, min(255, channel))) for channel in value)
    return default


def _segments(num_frames: int, count: int) -> List[Tuple[int, int]]:
    if num_frames <= 0:
        return []
    count = max(1, min(count, num_frames))
    segments: List[Tuple[int, int]] = []
    for i in range(count):
        start = int(round(i * num_frames / count))
        end = int(round((i + 1) * num_frames / count)) - 1
        segments.append((start, max(start, min(end, num_frames - 1))))
    return segments


def _text_fragments(text: str, min_parts: int = 2, max_parts: int = 5) -> List[str]:
    words = str(text).split()
    if len(words) >= min_parts:
        count = max(min_parts, min(max_parts, len(words)))
        chunks = [[] for _ in range(count)]
        for index, word in enumerate(words):
            chunks[index % count].append(word)
        return [" ".join(chunk) for chunk in chunks if chunk]

    compact = str(text).replace(" ", "")
    if not compact:
        return ["cue", "chain"]
    count = max(min_parts, min(max_parts, len(compact)))
    step = max(1, len(compact) // count)
    return [compact[i : i + step] for i in range(0, len(compact), step)][:max_parts]


def _default_box(width: int, height: int) -> Tuple[Point, Point]:
    box_w = max(32, width // 4)
    box_h = max(32, height // 4)
    center = (width // 2, height // 2)
    return (center[0] - box_w // 2, center[1] - box_h // 2), (
        center[0] + box_w // 2,
        center[1] + box_h // 2,
    )


def _trajectory(width: int, height: int, reverse: bool = False) -> List[Point]:
    points = [
        (width // 6, height * 2 // 3),
        (width // 3, height // 2),
        (width // 2, height // 3),
        (width * 2 // 3, height // 2),
        (width * 5 // 6, height // 3),
    ]
    return list(reversed(points)) if reverse else points


def _render_fragmented_text(
    frames: List[np.ndarray],
    fragments: List[str],
    variant: str,
    color: Tuple[int, int, int],
    alpha: float,
    seed: Optional[int],
) -> Tuple[List[np.ndarray], Dict[str, Any]]:
    if variant == "scrambled":
        rng = random.Random(seed)
        rng.shuffle(fragments)

    segments = _segments(len(frames), len(fragments))
    output = [frame.copy() for frame in frames]
    positions = ["top_left", "top_center", "top_right", "bottom_center", "center"]
    for index, (start, end) in enumerate(segments):
        fragment = fragments[index]
        position = positions[index % len(positions)]
        for frame_index in range(start, end + 1):
            output[frame_index] = draw_text_box(
                output[frame_index],
                fragment,
                position,
                font_scale=0.8,
                alpha=alpha,
                color=color,
            )
    return output, {"fragments": fragments, "segments": segments}


def _render_progressive_target_binding(
    frames: List[np.ndarray],
    text: str,
    variant: str,
    color: Tuple[int, int, int],
    alpha: float,
) -> Tuple[List[np.ndarray], Dict[str, Any]]:
    if not frames:
        return frames, {}

    height, width = frames[0].shape[:2]
    top_left, bottom_right = _default_box(width, height)
    center = (width // 2, height // 2)
    midpoint = max(1, len(frames) // 2)
    output = [frame.copy() for frame in frames]

    for index in range(0, midpoint):
        if variant == "benign":
            output[index] = draw_circle(output[index], (width // 10, height // 10), 8, color, alpha=alpha)
        else:
            output[index] = draw_box(output[index], top_left, bottom_right, color, alpha=alpha)
    for index in range(midpoint, len(frames)):
        output[index] = draw_text_box(output[index], text, "bottom_center", alpha=alpha, color=color)

    return output, {"target_box": [top_left, bottom_right], "target_center": center, "split": midpoint}


def _render_motion_trajectory(
    frames: List[np.ndarray],
    variant: str,
    color: Tuple[int, int, int],
    alpha: float,
) -> Tuple[List[np.ndarray], Dict[str, Any]]:
    if not frames:
        return frames, {}

    height, width = frames[0].shape[:2]
    reverse = variant == "scrambled"
    points = _trajectory(width, height, reverse=reverse)
    output = [frame.copy() for frame in frames]
    segments = _segments(len(frames), len(points))

    for index, (start, end) in enumerate(segments):
        visible_points = points[: index + 1]
        for frame_index in range(start, end + 1):
            if variant == "benign":
                output[frame_index] = draw_circle(
                    output[frame_index], visible_points[-1], 5, color, thickness=2, alpha=alpha
                )
            else:
                output[frame_index] = draw_polyline(output[frame_index], visible_points, color, alpha=alpha)
    return output, {"trajectory": points, "segments": segments}


def render_temporal_cue_chain(
    frames: List[np.ndarray],
    overlay_params: Union[OverlayParams, Dict[str, Any]],
    variant: str,
    seed: Optional[int] = None,
) -> Tuple[List[np.ndarray], Dict[str, Any]]:
    """Render visual cues distributed over time."""

    params = _as_params(overlay_params)
    resolved = dict(params)
    resolved.update(
        {
            "family": "temporal_cue_chain",
            "variant": variant,
            "seed": seed if seed is not None else params.get("seed"),
        }
    )

    if variant == "clean" or not frames:
        return frames, resolved

    source_text = str(params.get("text") or "change target color")
    if variant == "benign":
        text = make_benign_text(source_text)
    elif variant == "scrambled":
        text = scramble_text(source_text, seed=seed)
    else:
        text = source_text
    text = normalize_text_for_overlay(text, max_chars=int(params.get("max_chars") or 48))

    chain_type = str(params.get("chain_type") or "fragmented_text")
    if chain_type not in {"fragmented_text", "progressive_target_binding", "motion_trajectory"}:
        chain_type = "fragmented_text"

    color = _parse_color(params.get("color"), (255, 0, 0))
    if variant == "benign":
        color = _parse_color(params.get("benign_color"), (255, 255, 255))
    alpha = float(params.get("alpha") if params.get("alpha") is not None else 0.85)

    if chain_type == "progressive_target_binding":
        new_frames, details = _render_progressive_target_binding(frames, text, variant, color, alpha)
    elif chain_type == "motion_trajectory":
        new_frames, details = _render_motion_trajectory(frames, variant, color, alpha)
    else:
        fragments = _text_fragments(text)
        new_frames, details = _render_fragmented_text(frames, fragments, variant, color, alpha, seed)

    resolved.update({"chain_type": chain_type, "text": text, "color": color, "alpha": alpha})
    resolved.update(details)
    return new_frames, resolved
