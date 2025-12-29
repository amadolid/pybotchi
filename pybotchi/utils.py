"""Pybotchi Utilities."""

from collections import deque
from collections.abc import Generator
from contextlib import suppress
from importlib import import_module
from re import compile
from typing import Any, Callable
from uuid import UUID

from orjson import loads

PLACEHOLDERS = compile(r"(\${\s*([^:\s]+)\s*(?:\:\s*([\S\s]*?))?\s*})")
CAMEL_CASE = compile(r"^[a-z]+(?:[A-Z][a-z0-9]*)*$")


def apply_placeholders(target: str, **placeholders: Any) -> str:
    """Apply placeholders on target string."""
    for placeholder in set(PLACEHOLDERS.findall(target)):
        prefix = placeholder[1]
        default = loads((placeholder[2] or '""').encode())
        current = placeholders.get(prefix, default)
        target = target.replace(placeholder[0], str(current))
    return target.strip()


def is_camel_case(data: str) -> bool:
    """Check if string is in camel case."""
    return CAMEL_CASE.fullmatch(data) is not None


def unwrap_exceptions(
    exception: Exception,
) -> Generator[Exception, None, None]:
    """Extract root exceptions."""
    if isinstance(exception, ExceptionGroup):
        queue = deque[Exception](exception.exceptions)
        while queue:
            que = queue.popleft()
            if isinstance(que, ExceptionGroup):
                queue.extend(que.exceptions)
            else:
                yield que
    else:
        yield exception


for module, attr in (("uuid", "uuid7"), ("uuid6", "uuid7"), ("uuid", "uuid4")):
    with suppress(ImportError, AttributeError):
        uuid: Callable[[], UUID] = getattr(import_module(module), attr)
