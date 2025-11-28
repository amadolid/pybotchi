"""Pybotchi GRPC Context."""

from asyncio import Queue
from copy import deepcopy
from typing import Any, Generic, TypeVar

from pydantic import Field, PrivateAttr

from .common import GRPCIntegration
from .pybotchi_pb2 import Event
from ..common import ToolCall
from ..context import Action, ChatRole, Context, TLLM


TContext = TypeVar("TContext", bound="GRPCContext")


class GRPCContext(Context[TLLM], Generic[TLLM]):
    """GRPC Context."""

    integrations: dict[str, GRPCIntegration] = Field(default_factory=dict)

    _response_queue: Queue[Event] = PrivateAttr(default_factory=Queue)

    def grpc_dump(self) -> dict[str, Any]:
        """Dump model for GRPC."""
        return self.model_dump()

    async def grpc_send(self, name: str, data: dict[str, Any]) -> None:
        """Send GRPC event."""
        await self._response_queue.put(Event(name=name, data=data))

    async def add_message(
        self, role: ChatRole, content: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Add message."""
        await super().add_message(role, content, metadata)
        await self.grpc_send(
            "update",
            {
                "target": "context",
                "attrs": ["add_message"],
                "args": [role, content, metadata],
            },
        )

    async def add_response(
        self,
        action: "Action | ToolCall",
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add tool."""
        if isinstance(action, Action):
            action = action._tool_call

        await super().add_response(action, content, metadata)
        await self.grpc_send(
            "update",
            {
                "target": "context",
                "attrs": ["add_response"],
                "args": [action, content, metadata],
            },
        )

    async def notify(self, message: dict[str, Any]) -> None:
        """Notify Client."""
        await self.grpc_send(
            "update",
            {
                "target": "context",
                "attrs": ["notify"],
                "args": [message],
            },
        )

    def detached_kwargs(self, **kwargs: Any) -> dict[str, Any]:
        """Retrieve detached kwargs."""
        return super().detached_kwargs(integrations=deepcopy(self.integrations))
