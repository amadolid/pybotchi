from _typeshed import Incomplete
from collections.abc import Generator
from typing import Any, Callable
from uuid import UUID

PLACEHOLDERS: Incomplete
CAMEL_CASE: Incomplete

def apply_placeholders(target: str, **placeholders: Any) -> str: ...
def is_camel_case(data: str) -> bool: ...
def unwrap_exceptions(exception: Exception) -> Generator[Exception, None, None]: ...

uuid: Callable[[], UUID]
