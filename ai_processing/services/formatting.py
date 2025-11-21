"""
Utility helpers for working with BBCode-rich summaries.
"""

import re
from typing import Pattern

BB_CODE_PATTERN: Pattern = re.compile(r"\[[^\]]+\]")


def strip_bbcode(text: str) -> str:
    """Remove BBCode-like markers and collapse whitespace."""
    if not text:
        return ""

    cleaned = BB_CODE_PATTERN.sub("", text)
    # Normalize line breaks
    cleaned = re.sub(r"\r\n?", "\n", cleaned)
    cleaned = re.sub(r"\n{2,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned.strip()
