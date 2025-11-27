"""PyBotchi Handler."""

from asyncio import Queue, create_task
from collections.abc import AsyncGenerator
from typing import Generic

from click import echo

from google.protobuf.json_format import MessageToDict

from grpc import StatusCode  # type:ignore[attr-defined] # mypy issue
from grpc.aio import Metadata, ServicerContext, UsageError

from .context import GRPCContext, TContext
from .pybotchi_pb2 import ActionListRequest, ActionListResponse, Event, JSONSchema
from .pybotchi_pb2_grpc import PyBotchiGRPCServicer
from ..action import Action


class PyBotchiGRPC(PyBotchiGRPCServicer, Generic[TContext]):
    """PyBotchiGRPC Handler."""

    __context_class__: type[TContext] = GRPCContext  # type: ignore[assignment]

    def __init__(self, groups: dict[str, dict[str, type[Action]]]) -> None:
        """Initialize Handler."""
        self.groups = groups
        self.__has_validate_metadata__ = (
            self.__class__.validate_metadata is not PyBotchiGRPC.validate_metadata
        )

    async def validate_metadata(self, metadata: Metadata | None) -> None:
        """Validate invocation metadata."""
        pass

    async def consume(
        self, context: TContext, group: str, events: AsyncGenerator[Event]
    ) -> None:
        """Consume event."""
        try:
            async for event in events:
                if consumer := getattr(self, f"grpc_event_{event.name}", None):
                    await consumer(context, group, event)
        except UsageError as e:
            echo(f"Closing consumer. Reason {e}")

    async def grpc_event_execute(
        self, context: TContext, group: str, event: Event
    ) -> None:
        """Consume grpc `execute` event."""
        data = MessageToDict(event)["data"]
        action, action_return = await context.start(
            self.groups[group][data["name"]], **data.get("args", {})
        )
        await context.grpc_send(
            "close",
            {
                "action": action.serialize(),
                "return": action_return.value,
                "context": context.grpc_dump(),
            },
        )

    async def accept(
        self, events: AsyncGenerator[Event], context: ServicerContext
    ) -> Queue[Event]:
        """Accept connect execution."""
        event = await anext(events)
        if event.name != "init" or not event.data:
            await context.abort(StatusCode.FAILED_PRECONDITION)

        event_dict = MessageToDict(event)
        agent_context = self.__context_class__(
            **event_dict["data"]["context"],
        )
        create_task(self.consume(agent_context, event.data["group"], events))
        return agent_context._response_queue

    ##############################################################################################
    #                                      EXECUTION METHODS                                     #
    ##############################################################################################

    async def execute_connect(
        self, request_iterator: AsyncGenerator[Event], context: ServicerContext
    ) -> AsyncGenerator[Event]:
        """Execute `connect` method."""
        queue = await self.accept(request_iterator, context)
        while True:
            que = await queue.get()
            yield que

            if que.name == "close":
                break

    ##############################################################################################
    #                                       BASE CONSUMERS                                       #
    ##############################################################################################

    async def connect(
        self, request_iterator: AsyncGenerator[Event], context: ServicerContext
    ) -> AsyncGenerator[Event]:
        """Consume `connect` method."""
        if self.__has_validate_metadata__ and self.validate_metadata(
            context.invocation_metadata()
        ):
            await context.abort(StatusCode.FAILED_PRECONDITION)

        async for event in self.execute_connect(request_iterator, context):
            yield event

    async def action_list(
        self, request: ActionListRequest, context: ServicerContext
    ) -> ActionListResponse:
        """Consume `action_list` method."""
        if self.__has_validate_metadata__ and self.validate_metadata(
            context.invocation_metadata()
        ):
            await context.abort(StatusCode.FAILED_PRECONDITION)

        return ActionListResponse(
            actions=(
                [
                    JSONSchema(**action.model_json_schema())
                    for action in actions.values()
                ]
                if (actions := self.groups.get(request.group))
                else []
            )
        )
