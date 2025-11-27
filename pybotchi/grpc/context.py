"""Pybotchi GRPC Context."""

from asyncio import Queue
from copy import deepcopy
from typing import Any, Generic, TypeVar

from pydantic import Field, PrivateAttr

from .common import GRPCIntegration
from .pybotchi_pb2 import Event
from ..context import Action, Context, TLLM, UsageMetadata


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

    async def merge_to_usages(self, model: str, usage: UsageMetadata) -> None:
        """Merge usage to usages."""
        await super().merge_to_usages(model, usage)
        await self.grpc_send(
            "update",
            {
                "target": "context",
                "attrs": ["merge_to_usages"],
                "args": [model, usage],
            },
        )

    async def add_response(
        self,
        action: "Action",
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add tool."""
        await super().add_response(action, content, metadata)
        await self.grpc_send(
            "update",
            {
                "target": "context",
                "attrs": ["add_response"],
                "args": ["${self}", content, metadata],
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
