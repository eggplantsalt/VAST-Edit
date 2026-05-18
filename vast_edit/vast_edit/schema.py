"""Lightweight data structures for VAST-Edit metadata.

The module intentionally uses only the Python standard library. Validation is
kept small: required fields are checked, while unknown fields are preserved in
``extra`` for forward compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple


VARIANT_CLEAN = "clean"
VARIANT_BENIGN = "benign"
VARIANT_ATTACK = "attack"
VARIANT_SCRAMBLED = "scrambled"

VARIANT_NAMES = (
    VARIANT_CLEAN,
    VARIANT_BENIGN,
    VARIANT_ATTACK,
    VARIANT_SCRAMBLED,
)

VariantName = Literal["clean", "benign", "attack", "scrambled"]


ATTACK_SPATIAL_TEXT_CUE = "spatial_text_cue"
ATTACK_SPATIAL_TARGET_CUE = "spatial_target_cue"
ATTACK_TEMPORAL_CUE_CHAIN = "temporal_cue_chain"

ATTACK_FAMILIES = (
    ATTACK_SPATIAL_TEXT_CUE,
    ATTACK_SPATIAL_TARGET_CUE,
    ATTACK_TEMPORAL_CUE_CHAIN,
)

AttackFamily = Literal[
    "spatial_text_cue",
    "spatial_target_cue",
    "temporal_cue_chain",
]


def _require(data: Dict[str, Any], fields: Tuple[str, ...]) -> None:
    missing = [name for name in fields if name not in data or data[name] is None]
    if missing:
        raise ValueError(f"Missing required field(s): {', '.join(missing)}")


def _extra_fields(data: Dict[str, Any], known: Tuple[str, ...]) -> Dict[str, Any]:
    return {key: value for key, value in data.items() if key not in known}


@dataclass
class InputExample:
    """One source video plus one authorized edit instruction."""

    id: str
    source_video: str
    source_video_name: str
    source_prompt: str
    authorized_instruction: str
    target_prompt: str
    attack_family: str
    attack_intent: str
    expected_behavior: str
    safety_rule: str
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "source_video": self.source_video,
            "source_video_name": self.source_video_name,
            "source_prompt": self.source_prompt,
            "authorized_instruction": self.authorized_instruction,
            "target_prompt": self.target_prompt,
            "attack_family": self.attack_family,
            "attack_intent": self.attack_intent,
            "expected_behavior": self.expected_behavior,
            "safety_rule": self.safety_rule,
        }
        data.update(self.extra)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InputExample":
        known = (
            "id",
            "sample_id",
            "source_video",
            "source_video_name",
            "source_prompt",
            "authorized_instruction",
            "target_prompt",
            "attack_family",
            "attack_intent",
            "expected_behavior",
            "safety_rule",
            "extra",
        )
        normalized = dict(data)
        if "id" not in normalized and "sample_id" in normalized:
            normalized["id"] = normalized["sample_id"]
        _require(
            normalized,
            (
                "id",
                "source_video",
                "source_video_name",
                "source_prompt",
                "authorized_instruction",
                "target_prompt",
                "attack_family",
                "attack_intent",
                "expected_behavior",
                "safety_rule",
            ),
        )
        extra = _extra_fields(normalized, known)
        extra.update(normalized.get("extra") or {})
        return cls(
            id=str(normalized["id"]),
            source_video=str(normalized["source_video"]),
            source_video_name=str(normalized["source_video_name"]),
            source_prompt=str(normalized["source_prompt"]),
            authorized_instruction=str(normalized["authorized_instruction"]),
            target_prompt=str(normalized["target_prompt"]),
            attack_family=str(normalized["attack_family"]),
            attack_intent=str(normalized["attack_intent"]),
            expected_behavior=str(normalized["expected_behavior"]),
            safety_rule=str(normalized["safety_rule"]),
            extra=extra,
        )


@dataclass
class OverlayParams:
    """Concrete overlay settings for one rendered variant."""

    family: str
    variant: str
    text: Optional[str] = None
    position: Optional[str] = None
    box: Optional[List[float]] = None
    color: Optional[str] = None
    alpha: Optional[float] = None
    start_frame: Optional[int] = None
    end_frame: Optional[int] = None
    trajectory: Optional[List[Any]] = None
    seed: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "family": self.family,
            "variant": self.variant,
            "text": self.text,
            "position": self.position,
            "box": self.box,
            "color": self.color,
            "alpha": self.alpha,
            "start_frame": self.start_frame,
            "end_frame": self.end_frame,
            "trajectory": self.trajectory,
            "seed": self.seed,
        }
        data.update(self.extra)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OverlayParams":
        known = (
            "family",
            "variant",
            "text",
            "position",
            "box",
            "color",
            "alpha",
            "start_frame",
            "end_frame",
            "trajectory",
            "seed",
            "extra",
        )
        _require(data, ("family", "variant"))
        extra = _extra_fields(data, known)
        extra.update(data.get("extra") or {})
        return cls(
            family=str(data["family"]),
            variant=str(data["variant"]),
            text=None if data.get("text") is None else str(data.get("text")),
            position=None if data.get("position") is None else str(data.get("position")),
            box=data.get("box"),
            color=None if data.get("color") is None else str(data.get("color")),
            alpha=None if data.get("alpha") is None else float(data.get("alpha")),
            start_frame=None
            if data.get("start_frame") is None
            else int(data.get("start_frame")),
            end_frame=None if data.get("end_frame") is None else int(data.get("end_frame")),
            trajectory=data.get("trajectory"),
            seed=None if data.get("seed") is None else int(data.get("seed")),
            extra=extra,
        )


@dataclass
class SampleRecord:
    """One generated VAST-Edit variant record."""

    sample_id: str
    base_id: str
    source_video: str
    source_video_name: str
    source_prompt: str
    authorized_instruction: str
    target_prompt: str
    attack_family: str
    attack_intent: str
    variant: str
    overlay_params: OverlayParams
    expected_behavior: str
    safety_rule: str
    output_video: str
    source_fps: Optional[float] = None
    source_num_frames: Optional[int] = None
    render_num_frames: Optional[int] = None
    render_resolution: Optional[List[int]] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "sample_id": self.sample_id,
            "base_id": self.base_id,
            "source_video": self.source_video,
            "source_video_name": self.source_video_name,
            "source_prompt": self.source_prompt,
            "authorized_instruction": self.authorized_instruction,
            "target_prompt": self.target_prompt,
            "attack_family": self.attack_family,
            "attack_intent": self.attack_intent,
            "variant": self.variant,
            "overlay_params": self.overlay_params.to_dict(),
            "expected_behavior": self.expected_behavior,
            "safety_rule": self.safety_rule,
            "output_video": self.output_video,
            "source_fps": self.source_fps,
            "source_num_frames": self.source_num_frames,
            "render_num_frames": self.render_num_frames,
            "render_resolution": self.render_resolution,
        }
        data.update(self.extra)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SampleRecord":
        known = (
            "sample_id",
            "base_id",
            "source_video",
            "source_video_name",
            "source_prompt",
            "authorized_instruction",
            "target_prompt",
            "attack_family",
            "attack_intent",
            "variant",
            "overlay_params",
            "expected_behavior",
            "safety_rule",
            "output_video",
            "source_fps",
            "source_num_frames",
            "render_num_frames",
            "render_resolution",
            "extra",
        )
        _require(
            data,
            (
                "sample_id",
                "base_id",
                "source_video",
                "source_video_name",
                "source_prompt",
                "authorized_instruction",
                "target_prompt",
                "attack_family",
                "attack_intent",
                "variant",
                "overlay_params",
                "expected_behavior",
                "safety_rule",
                "output_video",
            ),
        )
        overlay = data["overlay_params"]
        if isinstance(overlay, OverlayParams):
            overlay_params = overlay
        elif isinstance(overlay, dict):
            overlay_params = OverlayParams.from_dict(overlay)
        else:
            raise ValueError("overlay_params must be a dict or OverlayParams")

        extra = _extra_fields(data, known)
        extra.update(data.get("extra") or {})
        resolution = data.get("render_resolution")
        return cls(
            sample_id=str(data["sample_id"]),
            base_id=str(data["base_id"]),
            source_video=str(data["source_video"]),
            source_video_name=str(data["source_video_name"]),
            source_prompt=str(data["source_prompt"]),
            authorized_instruction=str(data["authorized_instruction"]),
            target_prompt=str(data["target_prompt"]),
            attack_family=str(data["attack_family"]),
            attack_intent=str(data["attack_intent"]),
            variant=str(data["variant"]),
            overlay_params=overlay_params,
            expected_behavior=str(data["expected_behavior"]),
            safety_rule=str(data["safety_rule"]),
            output_video=str(data["output_video"]),
            source_fps=None if data.get("source_fps") is None else float(data["source_fps"]),
            source_num_frames=None
            if data.get("source_num_frames") is None
            else int(data["source_num_frames"]),
            render_num_frames=None
            if data.get("render_num_frames") is None
            else int(data["render_num_frames"]),
            render_resolution=None if resolution is None else list(resolution),
            extra=extra,
        )
