"""PyBotchi Handler."""

from asyncio import Queue, create_task
from collections.abc import AsyncGenerator, Awaitable
from contextlib import suppress
from itertools import islice
from typing import Generic

from google.protobuf.json_format import MessageToDict

from grpc import StatusCode  # type: ignore[attr-defined] # mypy issue
from grpc.aio import Metadata, ServicerContext, UsageError

from .action import graph
from .context import GRPCContext, TContext
from .pybotchi_pb2 import (
    ActionListRequest,
    ActionListResponse,
    ActionSchema,
    Edge,
    Event,
    JSONSchema,
    TraverseRequest,
    TraverseResponse,
)
from .pybotchi_pb2_grpc import PyBotchiGRPCServicer
from ..action import Action


class PyBotchiGRPC(PyBotchiGRPCServicer, Generic[TContext]):
    """PyBotchiGRPC Handler."""

    __context_class__: type[TContext] = GRPCContext  # type: ignore[assignment]
    __allow_exec__: bool = False

    def __init__(self, module: str, groups: dict[str, dict[str, type[Action]]]) -> None:
        """Initialize Handler."""
        self.module = module
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
        with suppress(UsageError):
            async for event in events:
                if consumer := getattr(self, f"grpc_event_{event.name}", None):
                    await consumer(context, group, event)

    async def grpc_event_execute(
        self, context: TContext, group: str, event: Event
    ) -> None:
        """Consume grpc `execute` event."""
        data = MessageToDict(event)["data"]
        action, action_return = await context.start(
            self.groups[group][data["name"]], **data.get("args", {})
        )
        await context.grpc_send_up(
            context.context_id,
            "close",
            {
                "action": action.serialize(),
                "return": action_return.value,
                "context": context.grpc_dump(),
            },
        )

    async def grpc_event_update(
        self, context: TContext, group: str, event: Event
    ) -> None:
        """Consume grpc `execute` event."""
        if not (data := MessageToDict(event)["data"]):
            raise ValueError("Not valid event!")

        if (raw_exec := data.get("exec")) and self.__allow_exec__:
            exec(raw_exec, None, {"self": self, "context": context, "event": event})
        elif target := locals().get(data["target"]):
            attrs = data["attrs"]
            if set := data.get("set"):
                last_attr = attrs[-1]
                for attr in islice(attrs, 0, len(attrs) - 1):
                    target = getattr(target, attr)
                if set:
                    setattr(target, last_attr, *data["args"])
                elif hasattr(target, last_attr):
                    delattr(target, last_attr)
            else:
                for attr in attrs:
                    target = getattr(target, attr)

                ref = {"${self}": self, "${context}": context, "${event}": event}
                args = (
                    [
                        ref.get(arg, arg) if isinstance(arg, str) else arg
                        for arg in _args
                    ]
                    if (_args := data.get("args"))
                    else []
                )
                kwargs = (
                    {
                        key: ref.get(value, value) if isinstance(value, str) else value
                        for key, value in _kwargs.items()
                    }
                    if (_kwargs := data.get("kwargs"))
                    else {}
                )
                ret = target(*args, **kwargs)
                if isinstance(ret, Awaitable):
                    await ret

    async def accept(
        self, events: AsyncGenerator[Event], context: ServicerContext
    ) -> Queue[Event]:
        """Accept connect execution."""
        event = await anext(events)
        if event.name != "init" or not event.data:
            await context.abort(StatusCode.FAILED_PRECONDITION)

        data = MessageToDict(event)["data"]
        agent_context = self.__context_class__(
            **data["context"],
        )
        queue = agent_context._response_queue = Queue[Event]()
        create_task(self.consume(agent_context, data["group"], events))
        return queue

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
                    ActionSchema(
                        concurrent=action.__concurrent__,
                        schema=JSONSchema(**action.model_json_schema()),
                    )
                    for action in actions.values()
                ]
                if (actions := self.groups.get(request.group))
                else []
            )
        )

    async def traverse(
        self, request: TraverseRequest, context: ServicerContext
    ) -> TraverseResponse:
        """Consume `action_list` method."""
        if self.__has_validate_metadata__ and self.validate_metadata(
            context.invocation_metadata()
        ):
            await context.abort(StatusCode.FAILED_PRECONDITION)

        remote_graph = await graph(
            self.groups[request.group][request.name],
            dict(request.allowed_actions),
            MessageToDict(request.integrations),
            request.bypass,
            request.alias,
        )

        return TraverseResponse(
            nodes=[
                node.replace(self.module, request.alias, 1)
                for node in remote_graph.nodes
            ],
            edges=[
                Edge(
                    source=edge[0].replace(self.module, request.alias, 1),
                    target=edge[1].replace(self.module, request.alias, 1),
                    concurrent=edge[2],
                )
                for edge in remote_graph.edges
            ],
        )
