"""Pilot dataset builder for VAST-Edit v0.1."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .config import load_attack_templates, load_pilot_config
from .io_utils import ensure_dir, read_input_manifest, stable_id, write_jsonl, write_sample_records
from .overlays import (
    render_spatial_target_cue,
    render_spatial_text_cue,
    render_temporal_cue_chain,
)
from .schema import ATTACK_FAMILIES, VARIANT_NAMES, InputExample, OverlayParams, SampleRecord
from .video_io import copy_video, frame_resolution, probe_video, read_video_frames, write_video_frames


RENDERERS = {
    "spatial_text_cue": render_spatial_text_cue,
    "spatial_target_cue": render_spatial_target_cue,
    "temporal_cue_chain": render_temporal_cue_chain,
}


def _select_template(
    template_config: Dict[str, Any],
    family: str,
    input_example: Optional[InputExample] = None,
) -> Tuple[Dict[str, Any], Optional[int], str]:
    family_config = template_config.get(family, template_config)
    templates = family_config.get("templates") if isinstance(family_config, dict) else None
    if isinstance(templates, list) and templates:
        extra = input_example.extra if input_example is not None else {}
        requested_name = extra.get("template_name")
        if requested_name:
            for index, template in enumerate(templates):
                if template.get("name") == requested_name:
                    return dict(template), index, "template_name"

        requested_index = extra.get("template_index")
        if requested_index is not None:
            try:
                index = int(requested_index) % len(templates)
                return dict(templates[index]), index, "template_index"
            except (TypeError, ValueError):
                pass

        stable_key = input_example.id if input_example is not None else family
        index = int(stable_id(stable_key, family, length=8), 16) % len(templates)
        return dict(templates[index]), index, "stable_hash"
    if isinstance(family_config, dict):
        return dict(family_config), None, "family_fallback"
    return {}, None, "empty_fallback"


def _variant_params(template: Dict[str, Any], variant: str) -> Dict[str, Any]:
    params = template.get("default_variant_params") or {}
    if isinstance(params, dict):
        variant_params = params.get(variant) or {}
        if isinstance(variant_params, dict):
            return dict(variant_params)
    return {}


def _color_for_variant(template: Dict[str, Any], variant: str) -> Optional[str]:
    if variant == "benign":
        return template.get("benign_color") or template.get("default_color")
    return template.get("default_color")


def _template_text(input_example: InputExample, template: Dict[str, Any], variant: str) -> Tuple[Optional[str], str]:
    default_text = template.get("default_text")
    if variant == "benign":
        if template.get("benign_text"):
            return str(template["benign_text"]), "template_benign_text"
        return "scene text", "fallback_text"
    if variant == "clean":
        return None, "clean_no_overlay"
    if input_example.extra.get("overlay_text"):
        return str(input_example.extra["overlay_text"]), "extra_overlay_text"
    if input_example.attack_intent:
        return str(input_example.attack_intent), "input_attack_intent"
    if default_text:
        return str(default_text), "template_default_text"
    return "Edit this region", "fallback_text"


def _sample_id(base_id: str, family: str, variant: str, seed: Optional[int]) -> str:
    suffix = stable_id(base_id, family, variant, seed, length=10)
    safe_base = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in base_id)
    return f"vast_{safe_base}_{family}_{variant}_{suffix}"


def _source_path(input_example: InputExample) -> Path:
    source = Path(input_example.source_video)
    if source.is_absolute():
        return source
    manifest_dir = input_example.extra.get("_manifest_dir")
    if manifest_dir:
        candidate = Path(manifest_dir) / source
        if candidate.exists():
            return candidate
    return source


def _render_output_path(output_dir: Union[str, Path], variant: str, sample_id: str) -> Path:
    return Path(output_dir) / "videos" / variant / f"{sample_id}.mp4"


def _read_config_value(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    if key in config:
        return config[key]
    video_config = config.get("video") or {}
    if key == "default_max_frames":
        return video_config.get("max_frames", default)
    if key == "default_stride":
        return video_config.get("stride", default)
    if key == "output_video_codec":
        return video_config.get("codec", default)
    return default


def build_overlay_params(
    input_example: InputExample,
    family: str,
    variant: str,
    template_config: Dict[str, Any],
    seed: Optional[int] = None,
) -> OverlayParams:
    """Create overlay parameters for one input example and variant."""

    template, template_index, selection_policy = _select_template(
        template_config, family, input_example
    )
    params = _variant_params(template, variant)
    schedule = template.get("schedule") or {}
    text, text_source = _template_text(input_example, template, variant)

    extra: Dict[str, Any] = {
        "template_name": template.get("name"),
        "template_index": template_index,
        "template_selection_policy": selection_policy,
        "text_source": text_source,
        "template_default_text": template.get("default_text"),
        "attack_intent_text": input_example.attack_intent,
        "text_policy": params.get("text_policy"),
    }
    for key in (
        "cue_type",
        "benign_cue_type",
        "chain_type",
        "target_semantics",
        "text_style",
        "font_scale",
        "padding",
        "max_width_ratio",
        "max_lines",
        "placement_policy",
    ):
        if key in params:
            extra[key] = params[key]

    if schedule:
        extra["schedule"] = schedule

    return OverlayParams(
        family=family,
        variant=variant,
        text=text,
        position=template.get("default_position"),
        color=_color_for_variant(template, variant),
        alpha=template.get("default_alpha"),
        start_frame=params.get("start_frame"),
        end_frame=params.get("end_frame"),
        seed=seed,
        extra=extra,
    )


def _sample_record(
    input_example: InputExample,
    sample_id: str,
    variant: str,
    overlay_params: OverlayParams,
    output_video: Path,
    metadata: Dict[str, Any],
    render_num_frames: Optional[int],
    render_resolution: Optional[List[int]],
) -> SampleRecord:
    return SampleRecord(
        sample_id=sample_id,
        base_id=input_example.id,
        source_video=input_example.source_video,
        source_video_name=input_example.source_video_name,
        source_prompt=input_example.source_prompt,
        authorized_instruction=input_example.authorized_instruction,
        target_prompt=input_example.target_prompt,
        attack_family=input_example.attack_family,
        attack_intent=input_example.attack_intent,
        variant=variant,
        overlay_params=overlay_params,
        expected_behavior=input_example.expected_behavior,
        safety_rule=input_example.safety_rule,
        output_video=str(output_video),
        source_fps=metadata.get("fps"),
        source_num_frames=metadata.get("num_frames"),
        render_num_frames=render_num_frames,
        render_resolution=render_resolution,
    )


def render_variant(
    input_example: InputExample,
    variant: str,
    config: Dict[str, Any],
    templates: Dict[str, Any],
    output_dir: Union[str, Path],
    seed: Optional[int] = None,
) -> SampleRecord:
    """Render or copy one VAST-Edit variant and return its metadata record."""

    if variant not in VARIANT_NAMES:
        raise ValueError(f"Unsupported variant: {variant}")

    family = input_example.attack_family
    if family not in ATTACK_FAMILIES:
        raise ValueError(f"Unsupported attack_family: {family}")
    if family not in RENDERERS:
        raise ValueError(f"No renderer registered for attack_family: {family}")

    source_path = _source_path(input_example)
    metadata = probe_video(source_path)
    sample_id = _sample_id(input_example.id, family, variant, seed)
    output_video = _render_output_path(output_dir, variant, sample_id)
    overwrite = bool(config.get("overwrite", False))

    if output_video.exists() and not overwrite:
        raise FileExistsError(f"Output video exists and overwrite is false: {output_video}")

    overlay_params = build_overlay_params(input_example, family, variant, templates, seed=seed)

    if variant == "clean" and bool(config.get("clean_copy", True)):
        copy_video(source_path, output_video)
        render_resolution = [int(metadata["width"]), int(metadata["height"])]
        return _sample_record(
            input_example,
            sample_id,
            variant,
            overlay_params,
            output_video,
            metadata,
            int(metadata.get("num_frames") or 0),
            render_resolution,
        )

    max_frames = _read_config_value(config, "default_max_frames", None)
    stride = int(_read_config_value(config, "default_stride", 1) or 1)
    frames, read_metadata = read_video_frames(source_path, max_frames=max_frames, stride=stride)
    renderer = RENDERERS[family]
    rendered_frames, resolved_params = renderer(frames, overlay_params, variant, seed=seed)
    overlay_params = OverlayParams.from_dict(resolved_params)

    fps = float(read_metadata.get("fps") or metadata.get("fps") or 24.0)
    codec = str(_read_config_value(config, "output_video_codec", "mp4v") or "mp4v")
    write_video_frames(rendered_frames, output_video, fps=fps, codec=codec)

    width, height = frame_resolution(rendered_frames)
    return _sample_record(
        input_example,
        sample_id,
        variant,
        overlay_params,
        output_video,
        metadata,
        len(rendered_frames),
        [width, height],
    )


def _prepare_output_dirs(output_dir: Path, variants: List[str]) -> None:
    for variant in variants:
        ensure_dir(output_dir / "videos" / variant)
    ensure_dir(output_dir / "metadata")
    ensure_dir(output_dir / "logs")


def build_pilot_dataset(
    input_manifest_path: Union[str, Path],
    output_dir: Union[str, Path],
    config_path: Union[str, Path],
    templates_path: Union[str, Path],
    limit: Optional[int] = None,
    overwrite: bool = False,
    seed: int = 0,
) -> List[SampleRecord]:
    """Build a VAST-Edit v0.1 pilot dataset."""

    output_root = Path(output_dir)
    config = load_pilot_config(config_path)
    templates = load_attack_templates(templates_path)
    config["overwrite"] = bool(overwrite or config.get("overwrite", False))

    variants = list(config.get("variants") or VARIANT_NAMES)
    _prepare_output_dirs(output_root, variants)

    input_manifest = Path(input_manifest_path)
    examples = read_input_manifest(input_manifest)
    if limit is not None:
        examples = examples[: max(0, int(limit))]

    for example in examples:
        example.extra.setdefault("_manifest_dir", str(input_manifest.parent))

    records: List[SampleRecord] = []
    for example_index, example in enumerate(examples):
        for variant_index, variant in enumerate(variants):
            variant_seed = seed + example_index * 1009 + variant_index
            record = render_variant(
                example,
                variant,
                config,
                templates,
                output_root,
                seed=variant_seed,
            )
            records.append(record)

    samples_path = output_root / "metadata" / "samples.jsonl"
    write_sample_records(records, samples_path)

    snapshot_path = output_root / "metadata" / "input_manifest.snapshot.jsonl"
    shutil.copy2(input_manifest, snapshot_path)

    summary = {
        "input_manifest": str(input_manifest),
        "output_dir": str(output_root),
        "num_input_examples": len(examples),
        "num_sample_records": len(records),
        "variants": variants,
        "seed": seed,
        "samples_jsonl": str(samples_path),
    }
    summary_path = output_root / "logs" / "build_summary.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2, sort_keys=True)

    return records
