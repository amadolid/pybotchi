"""Pybotchi Constants."""

from collections import Counter
from enum import StrEnum
from functools import cached_property
from typing import Annotated, Any, ClassVar, Literal, NotRequired, Required, TypeAlias, TypedDict

from pydantic import BaseModel, ConfigDict, Field, SkipValidation


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

    origin: str | None = None
    nodes: set[str] = Field(default_factory=set)
    edges: set[tuple[str, str, bool, str]] = Field(default_factory=set)

    def flowchart(self) -> str:
        """Draw Mermaid flowchart."""
        content = ""

        con = 0
        counter = Counter(edge[0] for edge in self.edges)
        for node in self.nodes:
            alias = node.rsplit(".", 1)[-1]
            alias = f"{{{alias}}}" if counter[node] > 1 else f"[{alias}]"
            content += f"{node}{alias}\n"
        for source, target, concurrent, alias in self.edges:
            base = target.split(".", 1)[0].upper()

            if concurrent:
                connection = (
                    f'ed{con}@--"`**{base}** : {alias}<br>*[concurrent]*`"-->'
                    if alias
                    else f'ed{con}@--"`*[concurrent]*`"-->'
                )
                con += 1
            else:
                connection = f'--"`**{base}** : {alias}`"-->' if alias else "-->"
            content += f"{source} {connection} {target}\n"

        constraints = (
            (
                "classDef animate stroke-dasharray: 10,stroke-dashoffset: 500,animation: dash 10s linear infinite;\n"
                f"class {','.join(f'ed{i}' for i in range(con))} animate"
            )
            if con
            else ""
        )

        origin = f"style {self.origin} fill:#4CAF50,color:#000000\n" if self.origin else ""

        return f"flowchart TD\n{content}{origin}{constraints}"


class ActionReturn(BaseModel):
    """Action Result Class."""

    END: ClassVar["End"]
    BREAK: ClassVar["Break"]
    STOP: ClassVar["Stop"]

    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    @staticmethod
    def convert(type: str, value: Any = None) -> "ActionReturn":
        """Convert to ActionReturn."""
        match type:
            case "End":
                return ActionReturn.END
            case "Break":
                return ActionReturn.BREAK
            case "Stop":
                return ActionReturn.stop(value)
            case _:
                raise ValueError(f"type `{type}` is not supported")

    @staticmethod
    def stop(value: Any) -> "Stop":
        """Return ActionReturn.STOP with value."""
        return Stop(value=value)

    @cached_property
    def is_end(self) -> bool:
        """Check if instance of End."""
        return isinstance(self, End)

    @cached_property
    def is_break(self) -> bool:
        """Check if instance of Break."""
        return isinstance(self, Break)

    @cached_property
    def is_stop(self) -> bool:
        """Check if instance of Stop."""
        return isinstance(self, Stop)


class End(ActionReturn):
    """End Action."""


class Break(End):
    """Break Action Iteration."""


class Stop(Break):
    """Stop Agent."""

    value: Annotated[Any, SkipValidation()] = None


class ConcurrentBreakPoint(Exception):  # noqa: N818
    """Concurrent Break Point."""

    def __init__(self, action_return: ActionReturn) -> None:
        """Initialize ConcurrentBreakPoint Exception."""
        self.action_return = action_return
        super().__init__(action_return)


ActionResult: TypeAlias = ActionReturn | None
ActionReturn.END = End()
ActionReturn.BREAK = Break()
ActionReturn.STOP = Stop()

UNSPECIFIED = "UNSPECIFIED"
