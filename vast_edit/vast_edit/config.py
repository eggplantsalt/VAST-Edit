"""Configuration loading helpers for VAST-Edit."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Union


PathLike = Union[str, Path]


def load_yaml(path: PathLike) -> Dict[str, Any]:
    """Load a YAML file with PyYAML.

    PyYAML is intentionally imported lazily so the package can still be
    inspected in lightweight environments.
    """

    try:
        import yaml
    except ImportError as exc:
        raise ImportError(
            "PyYAML is required to read VAST-Edit YAML configs. "
            "Install it with `pip install pyyaml` in the runtime environment."
        ) from exc

    yaml_path = Path(path)
    with yaml_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data or {}


def load_pilot_config(path: PathLike) -> Dict[str, Any]:
    """Load a pilot run configuration from an explicit path."""

    return load_yaml(path)


def load_attack_templates(path: PathLike) -> Dict[str, Any]:
    """Load attack template configuration from an explicit path."""

    return load_yaml(path)
