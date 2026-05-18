"""Basic RGB overlay drawing functions for VAST-Edit."""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

import cv2
import numpy as np


Point = Tuple[int, int]
Color = Tuple[int, int, int]


def clamp_point(x: int, y: int, width: int, height: int) -> Point:
    """Clamp a point to image bounds."""

    clamped_x = max(0, min(int(x), max(0, width - 1)))
    clamped_y = max(0, min(int(y), max(0, height - 1)))
    return clamped_x, clamped_y


def resolve_position(position_name: str, width: int, height: int, margin: int = 24) -> Point:
    """Resolve a named anchor position to pixel coordinates."""

    positions = {
        "top_left": (margin, margin),
        "top_right": (width - margin, margin),
        "bottom_left": (margin, height - margin),
        "bottom_right": (width - margin, height - margin),
        "center": (width // 2, height // 2),
        "bottom_center": (width // 2, height - margin),
        "top_center": (width // 2, margin),
    }
    if position_name not in positions:
        raise ValueError(f"Unsupported position_name: {position_name}")
    return clamp_point(*positions[position_name], width=width, height=height)


def blend_overlay(frame: np.ndarray, overlay: np.ndarray, alpha: float) -> np.ndarray:
    """Alpha-blend an overlay with an RGB frame."""

    if frame.shape != overlay.shape:
        raise ValueError("frame and overlay must have the same shape")
    alpha = max(0.0, min(float(alpha), 1.0))
    blended = cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0)
    return blended.astype(frame.dtype, copy=False)


def _copy_frame(frame: np.ndarray) -> np.ndarray:
    if frame is None or not hasattr(frame, "shape") or len(frame.shape) < 2:
        raise ValueError("frame must be a numpy array with shape (height, width, channels)")
    return frame.copy()


def _wrap_text(text: str, max_chars: int = 32) -> List[str]:
    words = str(text).split()
    if not words:
        return [""]

    lines: List[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            while len(word) > max_chars:
                lines.append(word[:max_chars])
                word = word[max_chars:]
            current = word
    if current:
        lines.append(current)
    return lines


def _text_origin_for_anchor(
    anchor: Point,
    box_width: int,
    box_height: int,
    frame_width: int,
    frame_height: int,
    padding: int,
) -> Tuple[int, int, int, int]:
    x, y = anchor
    left = x
    top = y

    if x > frame_width // 2:
        left = x - box_width
    elif abs(x - frame_width // 2) <= padding * 2:
        left = x - box_width // 2

    if y > frame_height // 2:
        top = y - box_height
    elif abs(y - frame_height // 2) <= padding * 2:
        top = y - box_height // 2

    left = max(0, min(left, max(0, frame_width - box_width)))
    top = max(0, min(top, max(0, frame_height - box_height)))
    return left, top, left + box_width, top + box_height


def draw_text_box(
    frame: np.ndarray,
    text: str,
    position: str,
    font_scale: float = 0.8,
    thickness: int = 2,
    alpha: float = 0.75,
    padding: int = 8,
    color: Color = (255, 255, 255),
    bg_color: Color = (0, 0, 0),
) -> np.ndarray:
    """Draw a wrapped text box on an RGB frame."""

    output = _copy_frame(frame)
    height, width = output.shape[:2]
    anchor = resolve_position(position, width, height)
    font = cv2.FONT_HERSHEY_SIMPLEX
    max_chars = max(12, min(48, width // 16))
    lines = _wrap_text(text, max_chars=max_chars)

    line_sizes = [cv2.getTextSize(line, font, font_scale, thickness)[0] for line in lines]
    line_height = int(max((size[1] for size in line_sizes), default=16) * 1.45)
    text_width = max((size[0] for size in line_sizes), default=1)
    box_width = min(width, text_width + padding * 2)
    box_height = min(height, line_height * len(lines) + padding * 2)
    left, top, right, bottom = _text_origin_for_anchor(
        anchor, box_width, box_height, width, height, padding
    )

    overlay = output.copy()
    cv2.rectangle(overlay, (left, top), (right, bottom), bg_color, thickness=-1)
    output = blend_overlay(output, overlay, alpha)

    baseline_y = top + padding + line_height - padding // 2
    for line in lines:
        cv2.putText(
            output,
            line,
            (left + padding, baseline_y),
            font,
            font_scale,
            color,
            thickness,
            cv2.LINE_AA,
        )
        baseline_y += line_height
        if baseline_y > bottom:
            break
    return output


def draw_arrow(
    frame: np.ndarray,
    start: Point,
    end: Point,
    color: Color = (255, 0, 0),
    thickness: int = 4,
    alpha: float = 0.85,
) -> np.ndarray:
    output = _copy_frame(frame)
    height, width = output.shape[:2]
    overlay = output.copy()
    cv2.arrowedLine(
        overlay,
        clamp_point(*start, width, height),
        clamp_point(*end, width, height),
        color,
        thickness,
        cv2.LINE_AA,
        tipLength=0.18,
    )
    return blend_overlay(output, overlay, alpha)


def draw_box(
    frame: np.ndarray,
    top_left: Point,
    bottom_right: Point,
    color: Color = (255, 0, 0),
    thickness: int = 4,
    alpha: float = 0.85,
) -> np.ndarray:
    output = _copy_frame(frame)
    height, width = output.shape[:2]
    overlay = output.copy()
    cv2.rectangle(
        overlay,
        clamp_point(*top_left, width, height),
        clamp_point(*bottom_right, width, height),
        color,
        thickness,
    )
    return blend_overlay(output, overlay, alpha)


def draw_circle(
    frame: np.ndarray,
    center: Point,
    radius: int,
    color: Color = (255, 0, 0),
    thickness: int = 4,
    alpha: float = 0.85,
) -> np.ndarray:
    output = _copy_frame(frame)
    height, width = output.shape[:2]
    overlay = output.copy()
    cv2.circle(
        overlay,
        clamp_point(*center, width, height),
        max(1, int(radius)),
        color,
        thickness,
        cv2.LINE_AA,
    )
    return blend_overlay(output, overlay, alpha)


def draw_polyline(
    frame: np.ndarray,
    points: Iterable[Point],
    color: Color = (255, 0, 0),
    thickness: int = 4,
    alpha: float = 0.85,
) -> np.ndarray:
    output = _copy_frame(frame)
    height, width = output.shape[:2]
    clamped_points = [clamp_point(x, y, width, height) for x, y in points]
    if len(clamped_points) < 2:
        return output

    overlay = output.copy()
    pts = np.array(clamped_points, dtype=np.int32).reshape((-1, 1, 2))
    cv2.polylines(overlay, [pts], isClosed=False, color=color, thickness=thickness)
    return blend_overlay(output, overlay, alpha)


def draw_ui_panel(
    frame: np.ndarray,
    text: str,
    box: Sequence[int],
    alpha: float = 0.8,
) -> np.ndarray:
    """Draw a simple UI-like panel with text inside a bounding box."""

    if len(box) != 4:
        raise ValueError("box must be [x1, y1, x2, y2]")
    output = _copy_frame(frame)
    height, width = output.shape[:2]
    x1, y1 = clamp_point(int(box[0]), int(box[1]), width, height)
    x2, y2 = clamp_point(int(box[2]), int(box[3]), width, height)
    left, right = sorted((x1, x2))
    top, bottom = sorted((y1, y2))

    overlay = output.copy()
    cv2.rectangle(overlay, (left, top), (right, bottom), (20, 20, 20), thickness=-1)
    cv2.rectangle(overlay, (left, top), (right, bottom), (255, 255, 255), thickness=2)
    output = blend_overlay(output, overlay, alpha)

    panel_width = max(1, right - left)
    panel_height = max(1, bottom - top)
    font_scale = max(0.45, min(0.8, panel_width / 360.0))
    font = cv2.FONT_HERSHEY_SIMPLEX
    padding = 8
    max_chars = max(10, panel_width // 14)
    lines = _wrap_text(text, max_chars=max_chars)
    line_height = int(cv2.getTextSize("Ag", font, font_scale, 2)[0][1] * 1.6)
    y = top + padding + line_height
    max_y = top + panel_height - padding

    for line in lines:
        if y > max_y:
            break
        cv2.putText(
            output,
            line,
            (left + padding, y),
            font,
            font_scale,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        y += line_height
    return output
