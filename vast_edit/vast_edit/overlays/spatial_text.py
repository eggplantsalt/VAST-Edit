"""Renderer for spatial text cue overlays."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from ..schema import OverlayParams
from ..text_utils import make_benign_text, normalize_text_for_overlay, scramble_text
from .base import draw_text_box


DEFAULT_TEXT = "Edit this region"


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


def _frame_range(params: Dict[str, Any], num_frames: int) -> Tuple[int, int]:
    if num_frames <= 0:
        return 0, -1
    start = int(params.get("start_frame") or 0)
    end_value = params.get("end_frame")
    end = num_frames - 1 if end_value is None else int(end_value)
    start = max(0, min(start, num_frames - 1))
    end = max(start, min(end, num_frames - 1))
    return start, end


def render_spatial_text_cue(
    frames: List[np.ndarray],
    overlay_params: Union[OverlayParams, Dict[str, Any]],
    variant: str,
    seed: Optional[int] = None,
) -> Tuple[List[np.ndarray], Dict[str, Any]]:
    """Render a spatial text cue into RGB frames."""

    params = _as_params(overlay_params)
    resolved = dict(params)
    resolved.update(
        {
            "family": "spatial_text_cue",
            "variant": variant,
            "seed": seed if seed is not None else params.get("seed"),
        }
    )

    if variant == "clean" or not frames:
        resolved.setdefault("text", None)
        return frames, resolved

    source_text = str(params.get("text") or DEFAULT_TEXT)
    if variant == "benign":
        text = make_benign_text(source_text)
    elif variant == "scrambled":
        text = scramble_text(source_text, seed=seed)
    else:
        text = source_text

    text = normalize_text_for_overlay(text, max_chars=int(params.get("max_chars") or 48))
    position = str(params.get("position") or "bottom_center")
    alpha = float(params.get("alpha") if params.get("alpha") is not None else 0.75)
    font_scale = float(params.get("font_scale") if params.get("font_scale") is not None else 0.8)
    thickness = int(params.get("thickness") if params.get("thickness") is not None else 2)
    color = _parse_color(params.get("color"), (255, 255, 255))
    bg_color = _parse_color(params.get("bg_color") or params.get("background_color"), (0, 0, 0))
    start, end = _frame_range(params, len(frames))

    new_frames: List[np.ndarray] = []
    for index, frame in enumerate(frames):
        if start <= index <= end:
            new_frames.append(
                draw_text_box(
                    frame,
                    text,
                    position,
                    font_scale=font_scale,
                    thickness=thickness,
                    alpha=alpha,
                    color=color,
                    bg_color=bg_color,
                )
            )
        else:
            new_frames.append(frame.copy())

    resolved.update(
        {
            "text": text,
            "position": position,
            "alpha": alpha,
            "font_scale": font_scale,
            "thickness": thickness,
            "color": color,
            "bg_color": bg_color,
            "start_frame": start,
            "end_frame": end,
        }
    )
    return new_frames, resolved
