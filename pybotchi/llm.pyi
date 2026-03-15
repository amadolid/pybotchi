from typing import Any, Literal, TypeVar, overload

T = TypeVar('T')

class LLM:
    __instances__: dict[str, Any]
    @classmethod
    def add(cls, **llms: Any) -> None: ...
    @classmethod
    def base(cls, _: type[T] | None = None) -> T: ...
    @overload
    @classmethod
    def get(cls, llm: str, type: type[T], throw: Literal[True]) -> T: ...
    @overload
    @classmethod
    def get(cls, llm: str, type: type[T]) -> T: ...
    @overload
    @classmethod
    def get(cls, llm: str, type: type[T], throw: Literal[False]) -> T | None: ...
    @overload
    @classmethod
    def get(cls, llm: str) -> Any: ...
