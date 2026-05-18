"""Small text helpers for VAST-Edit overlay metadata."""

from __future__ import annotations

import random
import re
from typing import Optional


BENIGN_TEXTS = (
    "sample note",
    "visual label",
    "scene text",
    "reference clip",
    "archive mark",
)


def normalize_text_for_overlay(text: str, max_chars: int = 40) -> str:
    """Collapse whitespace and trim text for compact visual overlays."""

    normalized = re.sub(r"\s+", " ", str(text)).strip()
    if len(normalized) <= max_chars:
        return normalized
    if max_chars <= 3:
        return normalized[:max_chars]
    return normalized[: max_chars - 3].rstrip() + "..."


def scramble_text(text: str, seed: Optional[int] = None) -> str:
    """Preserve low-level characters while breaking semantic readability."""

    normalized = normalize_text_for_overlay(text, max_chars=80)
    rng = random.Random(seed)

    if len(normalized) <= 1:
        return "xq"
    if len(normalized) <= 4:
        return normalized[::-1]

    chars = list(normalized)
    non_space_indices = [idx for idx, char in enumerate(chars) if not char.isspace()]
    shuffled_chars = [chars[idx] for idx in non_space_indices]
    rng.shuffle(shuffled_chars)

    if shuffled_chars == [chars[idx] for idx in non_space_indices]:
        shuffled_chars = list(reversed(shuffled_chars))

    for idx, char in zip(non_space_indices, shuffled_chars):
        chars[idx] = char

    scrambled = "".join(chars).strip()
    if scrambled.lower() == normalized.lower():
        return f"{normalized[::-1]} xq"
    return scrambled


def make_benign_text(text: str) -> str:
    """Return neutral text with no intended editing command meaning."""

    if not text:
        return BENIGN_TEXTS[0]
    index = sum(ord(char) for char in str(text)) % len(BENIGN_TEXTS)
    return BENIGN_TEXTS[index]
