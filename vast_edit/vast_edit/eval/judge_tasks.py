"""Judge task construction for VAST-Edit.

This module only builds JSON-serializable task records. It does not call any
MLLM, human labeling service, or model API.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from ..io_utils import stable_id


def _record_dict(sample_record: Any) -> Dict[str, Any]:
    if hasattr(sample_record, "to_dict"):
        return sample_record.to_dict()
    return dict(sample_record)


def _template(prompt_templates: Mapping[str, Any], name: str) -> Dict[str, str]:
    value = prompt_templates.get(name) or {}
    if isinstance(value, str):
        return {"system": "", "user": value}
    return {
        "system": str(value.get("system", "")),
        "user": str(value.get("user", "")),
    }


def _format_user(template: str, values: Mapping[str, Any]) -> str:
    try:
        return template.format(**values)
    except KeyError:
        return template


def _single_prompt_task(
    sample: Dict[str, Any],
    model_output_video: str,
    prompt_templates: Mapping[str, Any],
    task_type: str,
) -> Dict[str, Any]:
    template = _template(prompt_templates, task_type)
    values = {
        **sample,
        "input_video": sample.get("output_video", ""),
        "model_output_video": model_output_video,
    }
    task_id = "judge_" + stable_id(sample.get("sample_id"), task_type, model_output_video, length=16)
    return {
        "task_id": task_id,
        "task_type": task_type,
        "sample_id": sample.get("sample_id"),
        "base_id": sample.get("base_id"),
        "variant": sample.get("variant"),
        "attack_family": sample.get("attack_family"),
        "input_video": sample.get("output_video"),
        "model_output_video": model_output_video,
        "authorized_instruction": sample.get("authorized_instruction"),
        "target_prompt": sample.get("target_prompt"),
        "attack_intent": sample.get("attack_intent"),
        "expected_behavior": sample.get("expected_behavior"),
        "safety_rule": sample.get("safety_rule"),
        "prompt": {
            "system": template["system"],
            "user": _format_user(template["user"], values),
        },
    }


def build_single_video_judge_task(
    sample_record: Any,
    model_output_video: str,
    prompt_templates: Mapping[str, Any],
) -> Dict[str, Any]:
    """Build single-video judge tasks for one edited output.

    The returned object contains three subtasks:
    `authorized_edit_compliance`, `unauthorized_edit_detection`, and
    `quality_gate`.
    """

    sample = _record_dict(sample_record)
    subtasks = [
        _single_prompt_task(sample, model_output_video, prompt_templates, "authorized_edit_compliance"),
        _single_prompt_task(sample, model_output_video, prompt_templates, "unauthorized_edit_detection"),
        _single_prompt_task(sample, model_output_video, prompt_templates, "quality_gate"),
    ]
    return {
        "task_id": "single_" + stable_id(sample.get("sample_id"), model_output_video, length=16),
        "task_type": "single_video_bundle",
        "sample_id": sample.get("sample_id"),
        "base_id": sample.get("base_id"),
        "variant": sample.get("variant"),
        "attack_family": sample.get("attack_family"),
        "model_output_video": model_output_video,
        "subtasks": subtasks,
    }


def build_pairwise_authority_task(
    grouped_records: List[Any],
    model_outputs_by_sample: Mapping[str, str],
    prompt_templates: Mapping[str, Any],
) -> Optional[Dict[str, Any]]:
    """Build one pairwise authority-leakage task for a base sample group."""

    records = [_record_dict(record) for record in grouped_records]
    by_variant = {record.get("variant"): record for record in records}
    if "attack" not in by_variant:
        return None

    attack_record = by_variant["attack"]
    attack_output = model_outputs_by_sample.get(str(attack_record.get("sample_id")))
    if not attack_output:
        return None

    control_variants = [variant for variant in ("clean", "benign", "scrambled") if variant in by_variant]
    control_outputs = {
        variant: model_outputs_by_sample.get(str(by_variant[variant].get("sample_id")))
        for variant in control_variants
    }
    control_outputs = {variant: path for variant, path in control_outputs.items() if path}
    if not control_outputs:
        return None

    template = _template(prompt_templates, "pairwise_authority_leakage")
    values = {
        **attack_record,
        "attack_output_video": attack_output,
        "control_outputs": control_outputs,
        "variant_a": "attack",
        "variant_b": ",".join(control_outputs.keys()),
    }
    task_id = "pairwise_" + stable_id(
        attack_record.get("base_id"),
        attack_record.get("attack_family"),
        attack_output,
        control_outputs,
        length=16,
    )
    return {
        "task_id": task_id,
        "task_type": "pairwise_authority_leakage",
        "base_id": attack_record.get("base_id"),
        "attack_family": attack_record.get("attack_family"),
        "attack_sample_id": attack_record.get("sample_id"),
        "attack_output_video": attack_output,
        "control_outputs": control_outputs,
        "authorized_instruction": attack_record.get("authorized_instruction"),
        "target_prompt": attack_record.get("target_prompt"),
        "attack_intent": attack_record.get("attack_intent"),
        "expected_behavior": attack_record.get("expected_behavior"),
        "safety_rule": attack_record.get("safety_rule"),
        "prompt": {
            "system": template["system"],
            "user": _format_user(template["user"], values),
        },
    }


def default_model_output_path(model_output_root: str, variant: str, sample_id: str) -> str:
    """Return the conventional model output path for a sample."""

    return str(Path(model_output_root) / variant / f"{sample_id}.mp4")
