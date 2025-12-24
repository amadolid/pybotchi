"""Pybotchi Constants."""

from collections import Counter
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

    audio: float
    cache_creation: float
    cache_read: float


class OutputTokenDetails(TypedDict, total=False):
    """Output Token Details."""

    audio: float
    reasoning: float


class UsageMetadata(TypedDict):
    """Usage Metadata."""

    input_tokens: float
    output_tokens: float
    total_tokens: float
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

    origin: str | None = None
    nodes: set[tuple[str, str]] = Field(default_factory=set)
    edges: set[tuple[str, str, bool, str]] = Field(default_factory=set)

    def flowchart(self) -> str:
        """Draw Mermaid flowchart."""
        content = ""

        con = 0
        counter = Counter(edge[0] for edge in self.edges)
        for node, alias in self.nodes:
            alias = f"{{{alias}}}" if counter[node] > 1 else f"[{alias}]"
            content += f"{node}{alias}\n"
        for source, target, concurrent, alias in self.edges:
            base = target.split(".", 1)[0].upper()

            if concurrent:
                connection = (
                    f"ed{con}@--**{base}** : {alias}<br>*[concurrent]*-->"
                    if alias
                    else f"ed{con}@--*[concurrent]*-->"
                )
                con += 1
            else:
                connection = f"--**{base}** : {alias}-->" if alias else "-->"
            content += f"{source} {connection} {target}\n"

        constraints = (
            (
                "classDef animate stroke-dasharray: 10,stroke-dashoffset: 500,animation: dash 10s linear infinite;\n"
                f"class {",".join(f"ed{i}"for i in range(con))} animate"
            )
            if con
            else ""
        )

        origin = (
            f"style {self.origin} fill:#4CAF50,color:#000000\n" if self.origin else ""
        )

        return f"flowchart TD\n{content}{origin}{constraints}"


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
