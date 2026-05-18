"""Renderer for spatial text cue overlays."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from ..schema import OverlayParams
from ..text_utils import make_benign_text, normalize_text_for_overlay, scramble_text
from .base import draw_text_box


DEFAULT_TEXT = "Edit this region"
STYLE_BY_TEMPLATE = {
    "subtitle_command": "subtitle",
    "sticky_note_command": "sticky_note",
    "ui_caption_command": "screen_label",
}
STYLE_POSITIONS = {
    "subtitle": "bottom_center",
    "sticky_note": "top_left",
    "poster_label": "top_right",
    "screen_label": "top_center",
}


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


def _text_style(params: Dict[str, Any]) -> str:
    requested = params.get("text_style")
    if requested:
        style = str(requested)
    else:
        style = STYLE_BY_TEMPLATE.get(str(params.get("template_name") or ""), "subtitle")
    if style not in {"subtitle", "sticky_note", "poster_label", "screen_label"}:
        style = "subtitle"
    return style


def _style_defaults(style: str, width: int, height: int) -> Dict[str, Any]:
    scale = max(0.36, min(0.62, width / 640.0))
    padding = max(4, min(8, width // 48))
    base = {
        "font_scale": scale,
        "thickness": 1 if width <= 480 else 2,
        "padding": padding,
        "alpha": 0.62,
        "max_width_ratio": 0.68,
        "max_lines": 2,
        "line_spacing": 1.28,
        "corner_radius": max(0, width // 90),
        "color": (245, 245, 238),
        "bg_color": (28, 28, 28),
        "border_color": None,
        "border_thickness": 0,
    }
    if style == "sticky_note":
        base.update(
            {
                "font_scale": max(0.34, min(0.54, width / 760.0)),
                "alpha": 0.72,
                "max_width_ratio": 0.34,
                "color": (42, 38, 28),
                "bg_color": (244, 224, 122),
                "border_color": (190, 170, 92),
                "border_thickness": 1,
                "corner_radius": 2,
            }
        )
    elif style == "poster_label":
        base.update(
            {
                "font_scale": max(0.34, min(0.56, width / 720.0)),
                "alpha": 0.68,
                "max_width_ratio": 0.42,
                "color": (40, 48, 56),
                "bg_color": (230, 235, 226),
                "border_color": (116, 132, 132),
                "border_thickness": 1,
            }
        )
    elif style == "screen_label":
        base.update(
            {
                "font_scale": max(0.32, min(0.52, width / 760.0)),
                "alpha": 0.66,
                "max_width_ratio": 0.52,
                "color": (225, 238, 235),
                "bg_color": (32, 58, 70),
                "border_color": (82, 122, 130),
                "border_thickness": 1,
            }
        )
    return base


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
    height, width = frames[0].shape[:2]
    text_style = _text_style(params)
    defaults = _style_defaults(text_style, width, height)
    position = str(params.get("position") or STYLE_POSITIONS[text_style])
    alpha = float(params.get("alpha") if params.get("alpha") is not None else defaults["alpha"])
    font_scale = float(
        params.get("font_scale") if params.get("font_scale") is not None else defaults["font_scale"]
    )
    thickness = int(
        params.get("thickness") if params.get("thickness") is not None else defaults["thickness"]
    )
    padding = int(params.get("padding") if params.get("padding") is not None else defaults["padding"])
    color = _parse_color(params.get("color"), defaults["color"])
    bg_color = _parse_color(params.get("bg_color") or params.get("background_color"), defaults["bg_color"])
    border_color = _parse_color(params.get("border_color"), defaults["border_color"]) if defaults["border_color"] else None
    border_thickness = int(
        params.get("border_thickness")
        if params.get("border_thickness") is not None
        else defaults["border_thickness"]
    )
    max_width_ratio = float(params.get("max_width_ratio") or defaults["max_width_ratio"])
    max_lines = int(params.get("max_lines") or defaults["max_lines"])
    line_spacing = float(params.get("line_spacing") or defaults["line_spacing"])
    corner_radius = int(params.get("corner_radius") if params.get("corner_radius") is not None else defaults["corner_radius"])
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
                    padding=padding,
                    color=color,
                    bg_color=bg_color,
                    border_color=border_color,
                    border_thickness=border_thickness,
                    max_width_ratio=max_width_ratio,
                    max_lines=max_lines,
                    line_spacing=line_spacing,
                    corner_radius=corner_radius,
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
            "padding": padding,
            "color": color,
            "bg_color": bg_color,
            "border_color": border_color,
            "border_thickness": border_thickness,
            "max_width_ratio": max_width_ratio,
            "max_lines": max_lines,
            "line_spacing": line_spacing,
            "corner_radius": corner_radius,
            "start_frame": start,
            "end_frame": end,
            "text_style": text_style,
            "placement_policy": f"{text_style}:{position}",
            "visible_frame_ranges": [[start, end]],
        }
    )
    return new_frames, resolved
