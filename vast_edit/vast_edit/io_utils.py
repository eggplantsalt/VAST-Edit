"""JSONL and filesystem helpers for VAST-Edit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Union

from .schema import InputExample, SampleRecord


PathLike = Union[str, Path]


def ensure_dir(path: PathLike) -> Path:
    """Create a directory if needed and return it as a Path."""

    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def read_jsonl(path: PathLike) -> List[Dict[str, Any]]:
    """Read non-empty JSON lines from a file."""

    jsonl_path = Path(path)
    records: List[Dict[str, Any]] = []
    with jsonl_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {jsonl_path}") from exc
    return records


def _record_to_dict(record: Any) -> Dict[str, Any]:
    if hasattr(record, "to_dict"):
        return record.to_dict()
    if isinstance(record, dict):
        return record
    raise TypeError(f"Cannot serialize record of type {type(record).__name__}")


def write_jsonl(records: Iterable[Any], path: PathLike) -> None:
    """Write dictionaries or dataclass-like records with ``to_dict`` to JSONL."""

    jsonl_path = Path(path)
    if jsonl_path.parent:
        ensure_dir(jsonl_path.parent)
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            data = _record_to_dict(record)
            handle.write(json.dumps(data, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def read_input_manifest(path: PathLike) -> List[InputExample]:
    """Read an input manifest JSONL file into InputExample objects."""

    return [InputExample.from_dict(record) for record in read_jsonl(path)]


def write_sample_records(records: Iterable[SampleRecord], path: PathLike) -> None:
    """Write generated sample records to JSONL."""

    write_jsonl(records, path)


def stable_id(*parts: Any, length: int = 12) -> str:
    """Create a deterministic short ID from arbitrary JSON-serializable parts."""

    payload = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return digest[:length]
