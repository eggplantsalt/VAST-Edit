"""OpenCV-based video IO helpers for VAST-Edit.

Frames returned by this module are RGB numpy arrays. OpenCV reads and writes
BGR internally, so conversions happen at the module boundary.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np


PathLike = Union[str, Path]


def _path_str(path: PathLike) -> str:
    return str(Path(path))


def _ensure_parent(path: PathLike) -> None:
    parent = Path(path).parent
    if parent:
        parent.mkdir(parents=True, exist_ok=True)


def probe_video(path: PathLike) -> Dict[str, float]:
    """Return basic video metadata.

    Raises:
        FileNotFoundError: if the video path does not exist.
        ValueError: if OpenCV cannot open or probe the video.
    """

    video_path = Path(path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(_path_str(video_path))
    try:
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration_sec = float(num_frames / fps) if fps > 0 else 0.0

        if width <= 0 or height <= 0:
            raise ValueError(f"Could not read video dimensions: {video_path}")

        return {
            "fps": fps,
            "width": width,
            "height": height,
            "num_frames": num_frames,
            "duration_sec": duration_sec,
        }
    finally:
        cap.release()


def read_video_frames(
    path: PathLike,
    max_frames: Optional[int] = None,
    stride: int = 1,
) -> Tuple[List[np.ndarray], Dict[str, float]]:
    """Read RGB frames sequentially from a video."""

    if stride < 1:
        raise ValueError("stride must be >= 1")
    if max_frames is not None and max_frames < 0:
        raise ValueError("max_frames must be >= 0 or None")
    if max_frames == 0:
        return [], probe_video(path)

    video_path = Path(path)
    metadata = probe_video(video_path)
    cap = cv2.VideoCapture(_path_str(video_path))
    frames: List[np.ndarray] = []
    frame_index = 0

    try:
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        while True:
            ok, frame_bgr = cap.read()
            if not ok:
                break

            if frame_index % stride == 0:
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
                if max_frames is not None and len(frames) >= max_frames:
                    break

            frame_index += 1
    finally:
        cap.release()

    metadata = dict(metadata)
    metadata["read_num_frames"] = len(frames)
    metadata["stride"] = stride
    return frames, metadata


def write_video_frames(
    frames: List[np.ndarray],
    path: PathLike,
    fps: float,
    codec: str = "mp4v",
) -> None:
    """Write RGB frames to a video file."""

    if not frames:
        raise ValueError("Cannot write video with no frames")
    if fps <= 0:
        raise ValueError("fps must be > 0")
    if len(codec) != 4:
        raise ValueError("codec must be a four-character code, e.g. 'mp4v'")

    width, height = frame_resolution(frames)
    output_path = Path(path)
    _ensure_parent(output_path)

    fourcc = cv2.VideoWriter_fourcc(*codec)
    writer = cv2.VideoWriter(_path_str(output_path), fourcc, float(fps), (width, height))
    try:
        if not writer.isOpened():
            raise ValueError(f"Could not open video writer: {output_path}")

        for index, frame_rgb in enumerate(frames):
            if frame_rgb.shape[0] != height or frame_rgb.shape[1] != width:
                raise ValueError(
                    f"Frame {index} has resolution "
                    f"{frame_rgb.shape[1]}x{frame_rgb.shape[0]}, expected {width}x{height}"
                )
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            writer.write(frame_bgr)
    finally:
        writer.release()


def copy_video(src: PathLike, dst: PathLike) -> None:
    """Copy a video file while creating the destination parent directory."""

    src_path = Path(src)
    if not src_path.exists():
        raise FileNotFoundError(f"Source video file not found: {src_path}")
    dst_path = Path(dst)
    _ensure_parent(dst_path)
    shutil.copy2(src_path, dst_path)


def frame_resolution(frames: List[np.ndarray]) -> Tuple[int, int]:
    """Return ``(width, height)`` for a non-empty frame list."""

    if not frames:
        raise ValueError("Cannot determine resolution from empty frame list")
    frame = frames[0]
    if not hasattr(frame, "shape") or len(frame.shape) < 2:
        raise ValueError("Frame must be a numpy array with shape (height, width, channels)")
    height, width = frame.shape[:2]
    return int(width), int(height)
