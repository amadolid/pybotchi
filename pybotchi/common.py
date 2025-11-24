"""Pybotchi Constants."""

from enum import StrEnum
from functools import cached_property
from typing import Annotated, Any, ClassVar, Literal, NotRequired, Required, TypedDict

from pydantic import BaseModel, Field, SkipValidation


class ChatRole(StrEnum):
    """Chat Role Enum."""

    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"
    TOOL = "tool"
    DEVELOPER = "developer"


class InputTokenDetails(TypedDict, total=False):
    """Input Token Details."""

    audio: int
    cache_creation: int
    cache_read: int


class OutputTokenDetails(TypedDict, total=False):
    """Output Token Details."""

    audio: int
    reasoning: int


class UsageMetadata(TypedDict):
    """Usage Metadata."""

    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_token_details: NotRequired[InputTokenDetails]
    output_token_details: NotRequired[OutputTokenDetails]


class UsageData(TypedDict):
    """Usage Response."""

    name: str | None
    model: str
    usage: UsageMetadata


class ActionItem(TypedDict):
    """Action Item.."""

    name: str
    args: dict[str, Any]
    usages: list[UsageData]


class ActionEntry(ActionItem):
    """Action Entry.."""

    actions: list["ActionEntry"]


class Groups(TypedDict, total=False):
    """Action Groups."""

    grpc: set[str]
    mcp: set[str]
    a2a: set[str]


class Function(TypedDict, total=False):
    """Tool Function."""

    arguments: Required[str]
    name: Required[str]


class ToolCall(TypedDict, total=False):
    """Tool Call."""

    id: Required[str]
    function: Required[Function]
    type: Required[Literal["function"]]


class Graph(BaseModel):
    """Action Result Class."""

    nodes: set[str] = Field(default_factory=set)
    edges: set[tuple[str, str, bool]] = Field(default_factory=set)

    def flowchart(self) -> str:
        """Draw Mermaid flowchart."""
        content = ""
        for node in self.nodes:
            content += f"{node}[{node}]\n"
        for source, target, concurrent in self.edges:
            content += f'{source} -->{"|Concurrent|" if concurrent else ""} {target}\n'

        return f"flowchart TD\n{content}"


class ActionReturn(BaseModel):
    """Action Result Class."""

    value: Annotated[Any, SkipValidation()] = None

    GO: ClassVar["Go"]
    BREAK: ClassVar["Break"]
    END: ClassVar["End"]

    class Config:
        """Model Config."""

        arbitrary_types_allowed = True

    @staticmethod
    def end(value: Any) -> "End":
        """Return ActionReturn.END with value."""
        return End(value=value)

    @staticmethod
    def go(value: Any) -> "Go":
        """Return ActionReturn.GO with value."""
        return Go(value=value)

    @cached_property
    def is_break(self) -> bool:
        """Check if instance of End."""
        return isinstance(self, Break)

    @cached_property
    def is_end(self) -> bool:
        """Check if instance of End."""
        return isinstance(self, End)


class Go(ActionReturn):
    """Continue Action."""


class Break(ActionReturn):
    """Break Action Iteration."""


class End(Break):
    """End Action."""


ActionReturn.GO = Go()
ActionReturn.END = End()
ActionReturn.BREAK = Break()

UNSPECIFIED = "UNSPECIFIED"
