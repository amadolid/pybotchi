"""Pybotchi GRPC Context."""

from asyncio import Queue
from copy import deepcopy
from typing import Any, Generic, TypeVar

from pydantic import Field, PrivateAttr

from .common import GRPCIntegration
from .pybotchi_pb2 import Event
from ..common import ToolCall
from ..context import Action, ChatRole, Context, TLLM
from ..utils import uuid


TContext = TypeVar("TContext", bound="GRPCContext")


class GRPCContext(Context[TLLM], Generic[TLLM]):
    """GRPC Client Context."""

    integrations: dict[str, GRPCIntegration] = Field(default_factory=dict)

    source_id: str | None = Field(default=None)
    context_id: str = Field(default_factory=lambda: str(uuid()))

    _response_queue: Queue[Event] | None = PrivateAttr(default=None)
    _request_queues: dict[str, Queue] = PrivateAttr(default_factory=dict)

    def grpc_dump(self) -> dict[str, Any]:
        """Dump model for GRPC."""
        return self.model_dump(mode="json")

    def grpc_sharing_dump(self) -> dict[str, Any]:
        """Dump model for GRPC sharing."""
        dump = self.model_dump(mode="json", exclude={"source_id", "context_id"})
        dump["source_id"] = self.context_id
        dump["context_id"] = str(uuid)
        return dump

    async def grpc_send_up(
        self,
        source_id: str | None,
        name: str,
        data: dict[str, Any],
    ) -> None:
        """Send GRPC event to the left."""
        if self._response_queue and self.source_id and self.source_id != source_id:
            await self._response_queue.put(Event(name=name, data=data))

    async def grpc_send_down(
        self,
        source_id: str | None,
        name: str,
        data: dict[str, Any],
    ) -> None:
        """Send GRPC event to the right."""
        if not source_id:
            for queue in self._request_queues.values():
                await queue.put(Event(name=name, data=data))
        else:
            for target_context_id, queue in self._request_queues.items():
                if target_context_id != source_id:
                    await queue.put(Event(name=name, data=data))

    def detached_kwargs(self, **kwargs: Any) -> dict[str, Any]:
        """Retrieve detached kwargs."""
        return super().detached_kwargs(integrations=deepcopy(self.integrations))

    async def add_message(
        self,
        role: ChatRole,
        content: str,
        metadata: dict[str, Any] | None = None,
        source_id: str | None = None,
    ) -> None:
        """Add message."""
        await super().add_message(role, content, metadata)
        await self.grpc_send_up(
            source_id,
            "update",
            {
                "target": "context",
                "attrs": ["add_message"],
                "args": [
                    role,
                    content,
                    metadata,
                    self.context_id,
                ],
            },
        )
        await self.grpc_send_down(
            source_id,
            "update",
            {
                "target": "context",
                "attrs": ["add_message"],
                "args": [
                    role,
                    content,
                    metadata,
                    self.context_id,
                ],
            },
        )

    async def add_response(
        self,
        action: Action | ToolCall,
        content: str,
        metadata: dict[str, Any] | None = None,
        source_id: str | None = None,
    ) -> None:
        """Add tool."""
        if isinstance(action, Action):
            action = action._tool_call

        await super().add_response(action, content, metadata)
        await self.grpc_send_up(
            source_id,
            "update",
            {
                "target": "context",
                "attrs": ["add_response"],
                "args": [
                    action,
                    content,
                    metadata,
                    self.context_id,
                ],
            },
        )
        await self.grpc_send_down(
            source_id,
            "update",
            {
                "target": "context",
                "attrs": ["add_response"],
                "args": [
                    action,
                    content,
                    metadata,
                    self.context_id,
                ],
            },
        )

    async def set_metadata(
        self,
        *paths: Any,
        value: Any,
        update: bool = False,
        source_id: str | None = None
    ) -> None:
        """Override metadata value."""
        await super().set_metadata(*paths, value=value, update=update)
        await self.grpc_send_up(
            source_id,
            "update",
            {
                "target": "context",
                "attrs": ["set_metadata"],
                "args": [
                    *paths,
                    value,
                    update,
                    self.context_id,
                ],
            },
        )
        await self.grpc_send_down(
            source_id,
            "update",
            {
                "target": "context",
                "attrs": ["set_metadata"],
                "args": [
                    *paths,
                    value,
                    update,
                    self.context_id,
                ],
            },
        )

    async def notify(self, message: dict[str, Any]) -> None:
        """Notify Client."""
        await self.grpc_send_up(
            None,
            "update",
            {
                "target": "context",
                "attrs": ["notify"],
                "args": [message],
            },
        )
