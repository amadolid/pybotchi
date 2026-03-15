from _typeshed import Incomplete
from enum import StrEnum
from functools import cached_property as cached_property
from pydantic import BaseModel, ConfigDict, SkipValidation as SkipValidation
from typing import Annotated, Any, ClassVar, Literal, NotRequired, Required, TypedDict

class ChatRole(StrEnum):
    USER = 'user'
    SYSTEM = 'system'
    ASSISTANT = 'assistant'
    TOOL = 'tool'
    DEVELOPER = 'developer'

class InputTokenDetails(TypedDict, total=False):
    audio: float
    cache_creation: float
    cache_read: float

class OutputTokenDetails(TypedDict, total=False):
    audio: float
    reasoning: float

class UsageMetadata(TypedDict):
    input_tokens: float
    output_tokens: float
    total_tokens: float
    input_token_details: NotRequired[InputTokenDetails]
    output_token_details: NotRequired[OutputTokenDetails]

class UsageData(TypedDict):
    name: str | None
    model: str
    usage: UsageMetadata

class ActionItem(TypedDict):
    name: str
    args: dict[str, Any]
    usages: list[UsageData]

class ActionEntry(ActionItem):
    actions: list['ActionEntry']

class Groups(TypedDict, total=False):
    grpc: set[str]
    mcp: set[str]
    a2a: set[str]

class Function(TypedDict, total=False):
    arguments: Required[str]
    name: Required[str]

class ToolCall(TypedDict, total=False):
    id: Required[str]
    function: Required[Function]
    type: Required[Literal['function']]

class Graph(BaseModel):
    origin: str | None
    nodes: set[str]
    edges: set[tuple[str, str, bool, str]]
    def flowchart(self) -> str: ...

class ActionReturn(BaseModel):
    value: Annotated[Any, None]
    GO: ClassVar['Go']
    BREAK: ClassVar['Break']
    END: ClassVar['End']
    model_config: ClassVar[ConfigDict]
    @staticmethod
    def end(value: Any) -> End: ...
    @staticmethod
    def go(value: Any) -> Go: ...
    @cached_property
    def is_break(self) -> bool: ...
    @cached_property
    def is_end(self) -> bool: ...

class Go(ActionReturn): ...
class Break(ActionReturn): ...
class End(Break): ...

class ConcurrentBreakPoint(Exception):
    action_return: Incomplete
    def __init__(self, action_return: ActionReturn) -> None: ...

UNSPECIFIED: str
