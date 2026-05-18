"""Renderer for spatial target cue overlays."""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np

from ..schema import OverlayParams
from .base import blend_overlay, clamp_point, draw_arrow, draw_box, draw_circle


Point = Tuple[int, int]
Color = Tuple[int, int, int]


def _as_params(params: Union[OverlayParams, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(params, OverlayParams):
        return params.to_dict()
    return dict(params or {})


def _parse_color(value: Any, default: Color) -> Color:
    if value is None:
        return default
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("#") and len(text) == 7:
            return tuple(int(text[i : i + 2], 16) for i in (1, 3, 5))
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return tuple(int(max(0, min(255, channel))) for channel in value)
    return default


def _frame_range(params: Dict[str, Any], num_frames: int) -> Tuple[int, int]:
    if num_frames <= 0:
        return 0, -1
    start = int(params.get("start_frame") or 0)
    end_value = params.get("end_frame")
    end = num_frames - 1 if end_value is None else int(end_value)
    start = max(0, min(start, num_frames - 1))
    end = max(start, min(end, num_frames - 1))
    return start, end


def _default_geometry(width: int, height: int) -> Dict[str, Any]:
    center = (width // 2, height // 2)
    box_w = max(32, width // 4)
    box_h = max(32, height // 4)
    top_left = (center[0] - box_w // 2, center[1] - box_h // 2)
    bottom_right = (center[0] + box_w // 2, center[1] + box_h // 2)
    return {
        "start": (max(0, center[0] - width // 3), max(0, center[1] - height // 4)),
        "end": center,
        "top_left": top_left,
        "bottom_right": bottom_right,
        "center": center,
        "radius": max(18, min(width, height) // 8),
    }


def _point(value: Any, default: Point, width: int, height: int) -> Point:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return clamp_point(int(value[0]), int(value[1]), width, height)
    return clamp_point(*default, width, height)


def _scramble_geometry(
    geometry: Dict[str, Any],
    width: int,
    height: int,
    seed: Optional[int],
) -> Dict[str, Any]:
    rng = random.Random(seed)
    start = (rng.randint(0, max(0, width - 1)), rng.randint(0, max(0, height - 1)))
    end = (rng.randint(0, max(0, width - 1)), rng.randint(0, max(0, height - 1)))
    box_w = max(24, width // 5)
    box_h = max(24, height // 5)
    x1 = rng.randint(0, max(0, width - box_w))
    y1 = rng.randint(0, max(0, height - box_h))
    return {
        "start": start,
        "end": end,
        "top_left": (x1, y1),
        "bottom_right": (x1 + box_w, y1 + box_h),
        "center": end,
        "radius": geometry["radius"],
    }


def _draw_highlight(frame: np.ndarray, top_left: Point, bottom_right: Point, color: Color, alpha: float):
    output = frame.copy()
    height, width = output.shape[:2]
    left, top = clamp_point(*top_left, width, height)
    right, bottom = clamp_point(*bottom_right, width, height)
    left, right = sorted((left, right))
    top, bottom = sorted((top, bottom))
    overlay = output.copy()
    cv2.rectangle(overlay, (left, top), (right, bottom), color, thickness=-1)
    return blend_overlay(output, overlay, alpha)


def _draw_cue(
    frame: np.ndarray,
    cue_type: str,
    geometry: Dict[str, Any],
    color: Color,
    thickness: int,
    alpha: float,
) -> np.ndarray:
    if cue_type == "box":
        return draw_box(frame, geometry["top_left"], geometry["bottom_right"], color, thickness, alpha)
    if cue_type == "circle":
        return draw_circle(frame, geometry["center"], geometry["radius"], color, thickness, alpha)
    if cue_type == "highlight":
        return _draw_highlight(frame, geometry["top_left"], geometry["bottom_right"], color, alpha)
    return draw_arrow(frame, geometry["start"], geometry["end"], color, thickness, alpha)


def render_spatial_target_cue(
    frames: List[np.ndarray],
    overlay_params: Union[OverlayParams, Dict[str, Any]],
    variant: str,
    seed: Optional[int] = None,
) -> Tuple[List[np.ndarray], Dict[str, Any]]:
    """Render arrow, box, circle, or highlight spatial target cues."""

    params = _as_params(overlay_params)
    resolved = dict(params)
    resolved.update(
        {
            "family": "spatial_target_cue",
            "variant": variant,
            "seed": seed if seed is not None else params.get("seed"),
        }
    )

    if variant == "clean" or not frames:
        return frames, resolved

    height, width = frames[0].shape[:2]
    geometry = _default_geometry(width, height)
    geometry["start"] = _point(params.get("start"), geometry["start"], width, height)
    geometry["end"] = _point(params.get("end"), geometry["end"], width, height)
    geometry["top_left"] = _point(params.get("top_left"), geometry["top_left"], width, height)
    geometry["bottom_right"] = _point(
        params.get("bottom_right"), geometry["bottom_right"], width, height
    )
    geometry["center"] = _point(params.get("center"), geometry["center"], width, height)
    geometry["radius"] = int(params.get("radius") or geometry["radius"])

    if variant == "scrambled":
        geometry = _scramble_geometry(geometry, width, height, seed)

    cue_type = str(params.get("cue_type") or "arrow")
    if cue_type not in {"arrow", "box", "circle", "highlight"}:
        cue_type = "arrow"
    if variant == "benign":
        cue_type = str(params.get("benign_cue_type") or "circle")
        geometry["center"] = (max(12, width // 10), max(12, height // 10))
        geometry["radius"] = max(6, min(width, height) // 28)

    color = _parse_color(params.get("color"), (255, 0, 0))
    if variant == "benign":
        color = _parse_color(params.get("benign_color"), (120, 180, 255))
    alpha = float(params.get("alpha") if params.get("alpha") is not None else 0.85)
    thickness = int(params.get("thickness") if params.get("thickness") is not None else 4)
    start_frame, end_frame = _frame_range(params, len(frames))

    new_frames: List[np.ndarray] = []
    for index, frame in enumerate(frames):
        if start_frame <= index <= end_frame:
            new_frames.append(_draw_cue(frame, cue_type, geometry, color, thickness, alpha))
        else:
            new_frames.append(frame.copy())

    resolved.update(
        {
            "cue_type": cue_type,
            "color": color,
            "alpha": alpha,
            "thickness": thickness,
            "start_frame": start_frame,
            "end_frame": end_frame,
            **geometry,
        }
    )
    return new_frames, resolved
