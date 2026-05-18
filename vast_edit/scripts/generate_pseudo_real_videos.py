"""Generate small pseudo-real source videos for VAST-Edit smoke pilots."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable, List, Tuple

import cv2
import numpy as np


SceneFn = Callable[[int, int, int, int], np.ndarray]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate VAST-Edit pseudo-real source videos")
    parser.add_argument("--output_dir", required=True, help="Directory for generated videos")
    parser.add_argument("--num_videos", type=int, default=5, help="Number of videos to generate, max 5")
    parser.add_argument("--fps", type=int, default=16, help="Output frames per second")
    parser.add_argument("--duration_sec", type=float, default=4.0, help="Output duration in seconds")
    return parser.parse_args()


def _noise(shape: Tuple[int, int, int], seed: int, strength: int = 5) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(-strength, strength + 1, shape, dtype=np.int16)


def _clip(frame: np.ndarray) -> np.ndarray:
    return np.clip(frame, 0, 255).astype(np.uint8)


def _draw_shadow(frame: np.ndarray, center: Tuple[int, int], axes: Tuple[int, int], alpha: float = 0.18) -> None:
    overlay = frame.copy()
    cv2.ellipse(overlay, center, axes, 0, 0, 360, (30, 25, 20), -1, cv2.LINE_AA)
    cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, dst=frame)


def _desktop_scene(index: int, total: int, width: int, height: int) -> np.ndarray:
    shift = int(6 * np.sin(index / total * 2 * np.pi))
    frame = np.full((height, width, 3), (168, 142, 105), dtype=np.uint8)
    for y in range(0, height, 18):
        cv2.line(frame, (0, y + shift), (width, y + shift), (156, 130, 96), 1)
    _draw_shadow(frame, (82 + shift, 154), (30, 9))
    cv2.ellipse(frame, (82 + shift, 132), (18, 27), 0, 0, 360, (230, 232, 224), -1, cv2.LINE_AA)
    cv2.ellipse(frame, (82 + shift, 116), (17, 7), 0, 0, 360, (250, 250, 245), -1, cv2.LINE_AA)
    cv2.ellipse(frame, (104 + shift, 130), (7, 12), 0, 280, 75, (230, 232, 224), 3, cv2.LINE_AA)
    _draw_shadow(frame, (196 - shift, 160), (46, 10))
    cv2.ellipse(frame, (196 - shift, 134), (42, 18), 0, 0, 360, (215, 215, 205), -1, cv2.LINE_AA)
    cv2.circle(frame, (207 - shift, 128), 14, (88, 130, 195), -1, cv2.LINE_AA)
    cv2.rectangle(frame, (135 + shift, 78), (236 + shift, 126), (56, 88, 122), -1)
    cv2.rectangle(frame, (142 + shift, 84), (229 + shift, 120), (202, 214, 194), -1)
    cv2.rectangle(frame, (247 - shift, 72), (292 - shift, 112), (245, 222, 112), -1)
    return _clip(frame.astype(np.int16) + _noise(frame.shape, 1000 + index, 4))


def _street_scene(index: int, total: int, width: int, height: int) -> np.ndarray:
    t = index / max(1, total - 1)
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:120, :] = (196, 222, 240)
    frame[120:, :] = (88, 91, 92)
    cv2.rectangle(frame, (0, 112), (width, 134), (128, 142, 118), -1)
    for x, color in [(18, (150, 166, 180)), (72, (185, 174, 150)), (230, (170, 185, 192)), (276, (146, 157, 172))]:
        cv2.rectangle(frame, (x, 48), (x + 42, 120), color, -1)
        for wy in range(58, 108, 18):
            cv2.rectangle(frame, (x + 9, wy), (x + 17, wy + 8), (228, 232, 222), -1)
            cv2.rectangle(frame, (x + 25, wy), (x + 33, wy + 8), (228, 232, 222), -1)
    road_poly = np.array([[115, 120], [205, 120], [290, height], [30, height]], np.int32)
    cv2.fillPoly(frame, [road_poly], (64, 66, 68))
    cv2.line(frame, (160, 128), (160, height), (238, 220, 125), 2)
    car_x = int(-55 + t * (width + 80))
    _draw_shadow(frame, (car_x + 38, 202), (36, 7))
    cv2.rectangle(frame, (car_x, 176), (car_x + 70, 202), (190, 68, 58), -1)
    cv2.rectangle(frame, (car_x + 16, 160), (car_x + 52, 178), (205, 220, 232), -1)
    cv2.circle(frame, (car_x + 16, 204), 8, (30, 30, 34), -1)
    cv2.circle(frame, (car_x + 56, 204), 8, (30, 30, 34), -1)
    cv2.rectangle(frame, (250, 96), (279, 112), (235, 210, 92), -1)
    cv2.line(frame, (265, 112), (265, 150), (80, 82, 80), 2)
    return _clip(frame.astype(np.int16) + _noise(frame.shape, 2000 + index, 5))


def _kitchen_scene(index: int, total: int, width: int, height: int) -> np.ndarray:
    pulse = int(5 * np.sin(index / total * 2 * np.pi))
    frame = np.full((height, width, 3), (210, 215, 205), dtype=np.uint8)
    cv2.rectangle(frame, (0, 128), (width, height), (170, 152, 126), -1)
    for x in range(0, width, 32):
        cv2.line(frame, (x + pulse, 128), (x + pulse, height), (155, 138, 115), 1)
    cv2.rectangle(frame, (34, 64), (92, 126), (110, 135, 150), -1)
    cv2.rectangle(frame, (42, 72), (84, 118), (220, 226, 224), -1)
    _draw_shadow(frame, (154 + pulse, 178), (42, 9))
    cv2.ellipse(frame, (154 + pulse, 154), (40, 20), 0, 0, 360, (235, 235, 230), -1, cv2.LINE_AA)
    cv2.ellipse(frame, (154 + pulse, 149), (34, 12), 0, 0, 360, (132, 172, 218), -1, cv2.LINE_AA)
    cv2.rectangle(frame, (226 - pulse, 89), (250 - pulse, 162), (78, 132, 96), -1)
    cv2.ellipse(frame, (238 - pulse, 88), (12, 5), 0, 0, 360, (100, 160, 118), -1)
    cv2.circle(frame, (92, 168), 15, (58, 154, 92), -1, cv2.LINE_AA)
    cv2.circle(frame, (115, 166), 14, (220, 116, 62), -1, cv2.LINE_AA)
    cv2.rectangle(frame, (268, 150), (302, 184), (196, 185, 82), -1)
    return _clip(frame.astype(np.int16) + _noise(frame.shape, 3000 + index, 4))


def _garden_scene(index: int, total: int, width: int, height: int) -> np.ndarray:
    t = index / max(1, total - 1)
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:105, :] = (188, 225, 242)
    frame[105:, :] = (90, 168, 86)
    for x in range(0, width, 10):
        top = 114 + int(8 * np.sin((x + index * 2) / 16))
        cv2.line(frame, (x, height), (x + 3, top), (72, 145, 70), 1)
    cv2.rectangle(frame, (55, 83), (76, 153), (96, 78, 45), -1)
    cv2.circle(frame, (65, 64), 32, (58, 132, 72), -1, cv2.LINE_AA)
    cv2.circle(frame, (42, 82), 25, (70, 148, 78), -1, cv2.LINE_AA)
    cv2.circle(frame, (88, 82), 25, (66, 142, 76), -1, cv2.LINE_AA)
    cv2.rectangle(frame, (222, 136), (278, 176), (176, 132, 78), -1)
    ball_x = int(36 + t * 210)
    ball_y = int(190 + 7 * np.sin(t * 2 * np.pi))
    _draw_shadow(frame, (ball_x, ball_y + 17), (20, 5))
    cv2.circle(frame, (ball_x, ball_y), 18, (62, 108, 220), -1, cv2.LINE_AA)
    cv2.circle(frame, (245, 94), 14, (235, 210, 86), -1, cv2.LINE_AA)
    return _clip(frame.astype(np.int16) + _noise(frame.shape, 4000 + index, 5))


def _workspace_scene(index: int, total: int, width: int, height: int) -> np.ndarray:
    shift = int(5 * np.sin(index / total * 2 * np.pi))
    frame = np.full((height, width, 3), (126, 112, 95), dtype=np.uint8)
    cv2.rectangle(frame, (54 + shift, 36), (207 + shift, 128), (36, 40, 44), -1)
    cv2.rectangle(frame, (66 + shift, 48), (195 + shift, 113), (70, 104, 128), -1)
    cv2.rectangle(frame, (112 + shift, 128), (150 + shift, 139), (48, 48, 48), -1)
    cv2.rectangle(frame, (82 + shift, 140), (180 + shift, 150), (42, 42, 42), -1)
    for r in range(4):
        for c in range(10):
            cv2.rectangle(frame, (56 + c * 14, 172 + r * 10), (66 + c * 14, 178 + r * 10), (48, 50, 52), -1)
    cv2.ellipse(frame, (246 - shift, 178), (22, 34), 0, 0, 360, (66, 70, 73), -1, cv2.LINE_AA)
    cv2.rectangle(frame, (226 - shift, 65), (296 - shift, 126), (236, 232, 214), -1)
    cv2.line(frame, (236 - shift, 82), (286 - shift, 80), (190, 188, 172), 1)
    cv2.line(frame, (236 - shift, 96), (286 - shift, 95), (190, 188, 172), 1)
    cv2.rectangle(frame, (28 + shift, 70), (49 + shift, 116), (214, 76, 68), -1)
    return _clip(frame.astype(np.int16) + _noise(frame.shape, 5000 + index, 4))


SCENES: List[Tuple[str, SceneFn]] = [
    ("desktop_scene", _desktop_scene),
    ("street_scene", _street_scene),
    ("kitchen_scene", _kitchen_scene),
    ("garden_scene", _garden_scene),
    ("workspace_scene", _workspace_scene),
]


def _write_video(path: Path, scene_fn: SceneFn, fps: int, duration_sec: float) -> None:
    width, height = 320, 240
    num_frames = max(1, int(round(fps * duration_sec)))
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Failed to open video writer for {path}")
    for index in range(num_frames):
        writer.write(scene_fn(index, num_frames, width, height))
    writer.release()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    count = max(0, min(args.num_videos, len(SCENES)))
    for offset, (scene_name, scene_fn) in enumerate(SCENES[:count], start=1):
        path = output_dir / f"auto_{offset:03d}.mp4"
        _write_video(path, scene_fn, args.fps, args.duration_sec)
        print(f"Wrote {scene_name}: {path}")


if __name__ == "__main__":
    main()
