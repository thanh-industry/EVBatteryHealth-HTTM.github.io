"""
Shared presentation helpers for user-facing values.

Centralized so every screen formats timestamps and algorithm names the same
way instead of each page printing a raw ISO8601 string or a raw snake_case
metadata value. Pure functions, no Streamlit dependency, so they are unit
testable and reusable from deployment/verify_model.py's output too if ever
needed.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def format_timestamp(value: Optional[str], include_timezone: bool = True) -> str:
    """Format an ISO8601 timestamp (as stored in the DB or bundle metadata)
    into a human-readable string, e.g. '01 Nov 2026, 05:10 UTC'.

    Never raises: a value that cannot be parsed is returned unchanged so a
    display glitch never becomes a crash.
    """
    if value is None:
        return "n/a"
    text = str(value).strip()
    if not text:
        return "n/a"
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
        suffix = " UTC" if include_timezone else ""
        return dt.strftime("%d %b %Y, %H:%M") + suffix
    return dt.strftime("%d %b %Y, %H:%M")


def format_algorithm_name(raw: Optional[str]) -> str:
    """Turn a snake_case algorithm identifier (e.g. 'logistic_regression',
    'svm', 'random_forest') into a readable label, e.g. 'Logistic
    Regression', 'SVM', 'Random Forest'.

    Deliberately not a hardcoded {raw: label} lookup table, so an algorithm
    name this app has never seen before still degrades to a reasonable
    label instead of falling back to the raw identifier: short (<=3 letter)
    alphabetic tokens are treated as acronyms and upper-cased, everything
    else is capitalized word by word.
    """
    if not raw:
        return "n/a"
    words = [w for w in str(raw).replace("-", "_").split("_") if w]
    if not words:
        return str(raw)
    parts = [w.upper() if len(w) <= 3 and w.isalpha() else w[:1].upper() + w[1:].lower() for w in words]
    return " ".join(parts)
