"""Pybotchi LLMs."""

from typing import Any, Literal, TypeVar, overload

T = TypeVar("T")


class LLM:
    """LLM Handler."""

    __instances__: dict[str, Any] = {}

    @classmethod
    def add(cls, **llms: Any) -> None:
        """Add multiple llms."""
        for key, llm in llms.items():
            cls.__instances__[key] = llm

    @classmethod
    def base(cls, _: type[T] | None = None) -> T:
        """Get base LLM."""
        if not (base := cls.__instances__.get("base")):
            raise NotImplementedError("`base` LLM is not yet available!")
        return base

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

    @classmethod
    def get(cls, llm: str, type: type[T] | None = None, throw: bool = True) -> T | None:
        """Get LLM."""
        instance = cls.__instances__.get(llm)
        if type is None:
            return instance

        if isinstance(instance, type):
            return instance

        if throw:
            raise Exception(f"LLM `{llm}` is not a valid {type}: {instance}")
        else:
            return None
