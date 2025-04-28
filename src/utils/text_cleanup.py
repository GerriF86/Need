"""
text_cleanup.py – centralised helpers for turning *anything* that looks like
text into something nice, compact and ready for LLM ingestion.

The functions are intentionally dependency-light:
* Only the Python standard-library is required.
* `beautifulsoup4` is optional – when installed we use it to strip HTML tags.

Typical usage
-------------
>>> from src.utils.text_cleanup import clean_text
>>> clean_text("<h1>Hello&nbsp;World</h1>")
'Hello World'
"""

from __future__ import annotations

import html
import re
import unicodedata
from typing import Callable, Sequence

# --------------------------------------------------------------------------- #
# Low-level helpers
# --------------------------------------------------------------------------- #
def _strip_html(raw: str) -> str:
    """Remove *most* HTML tags while keeping inner text."""
    try:
        # Only import if the user actually needs HTML stripping
        from bs4 import BeautifulSoup  # heavyweight import, keep lazy
    except ImportError:
        # Fallback – blunt removal of <>… tags
        return re.sub(r"<[^>]+>", "", raw)

    soup = BeautifulSoup(raw, "html.parser")
    return soup.get_text(separator=" ")

def _collapse_ws(text: str) -> str:
    """Collapse all runs of whitespace (incl. newlines) → single space."""
    return re.sub(r"\s+", " ", text, flags=re.UNICODE).strip()

def _normalise_unicode(text: str) -> str:
    """Use NFC normalisation and convert fancy quotes/ellipses to ASCII."""
    text = unicodedata.normalize("NFC", text)
    # Very small ASCII replacement table – extend if you like
    replacements = {
        "\u201c": '"',  # left “
        "\u201d": '"',  # right ”
        "\u2018": "'",  # left ‘
        "\u2019": "'",  # right ’
        "\u2026": "...",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text

# --------------------------------------------------------------------------- #
# Public façade
# --------------------------------------------------------------------------- #
def clean_text(
    raw: str,
    *,
    steps: Sequence[Callable[[str], str]] | None = None,
) -> str:
    """
    Run *raw* through the default cleanup pipeline (or a custom one).

    Default pipeline:
        1. Unescape HTML entities (&amp; → &)
        2. Strip HTML tags (if any)
        3. Unicode normalisation + smart→ascii quotes
        4. Collapse whitespace

    Parameters
    ----------
    raw :
        The untrusted, messy text to be cleaned.
    steps :
        Optional sequence of callables, each receiving and returning `str`.
        If *None*, the default pipeline above is used.
    """
    if raw is None:
        return ""

    pipeline = steps or (
        lambda s: html.unescape(s),
        _strip_html,
        _normalise_unicode,
        _collapse_ws,
    )

    cleaned = raw
    for fn in pipeline:
        cleaned = fn(cleaned)
    return cleaned


# --------------------------------------------------------------------------- #
# Convenience – very rough token estimate (≈4 chars per token for English)
# --------------------------------------------------------------------------- #
def estimated_token_count(text: str) -> int:
    """Cheap heuristic: #tokens ≈ len(text) / 4."""
    return max(1, len(text) // 4)
