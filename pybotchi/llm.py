"""Pybotchi LLMs."""

from typing import Any, TypeVar, overload

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
    def get(cls, llm: str, type: type[T]) -> T:
        """Get LLM."""

    @overload
    @classmethod
    def get(cls, llm: str) -> Any:
        """Get LLM."""

    @classmethod
    def get(cls, llm: str, type: type[T] | None = None) -> T | None:
        """Get LLM."""
        instance = cls.__instances__.get(llm)
        if type is None:
            return instance

        if isinstance(instance, type):
            return instance

        raise Exception(f"LLM {llm} is not a valid {type}: {instance}")
