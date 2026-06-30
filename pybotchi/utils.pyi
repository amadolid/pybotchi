from collections.abc import Generator
from re import Pattern
from typing import Any, Callable
from uuid import UUID

PLACEHOLDERS: Pattern
CAMEL_CASE: Pattern

def apply_placeholders(target: str, **placeholders: Any) -> str: ...
def is_camel_case(data: str) -> bool: ...
def unwrap_exceptions(exception: Exception) -> Generator[Exception, None, None]: ...

uuid: Callable[[], UUID]
