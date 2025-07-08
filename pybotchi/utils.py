"""Pybotchi Utilities."""

from re import compile
from typing import Any

from orjson import loads

PLACEHOLDERS = compile(r"(\${\s*([^:\s]+)\s*(?:\:\s*([\S\s]*?))?\s*})")


def apply_placeholders(target: str, **placeholders: Any) -> str:
    """Apply placeholders on target string."""
    for placeholder in set(PLACEHOLDERS.findall(target)):
        prefix = placeholder[1]
        default = loads((placeholder[2] or '""').encode())
        current = placeholders.get(prefix, default)
        target = target.replace(placeholder[0], str(current))
    return target.strip()
