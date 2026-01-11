"""PyBotchi GRPC Handler."""

from asyncio import Queue, create_task
from collections.abc import AsyncGenerator, Awaitable
from itertools import islice
from sys import exc_info
from traceback import format_exception
from typing import Generic

from google.protobuf.json_format import MessageToDict

from grpc import StatusCode
from grpc.aio import Metadata, ServicerContext, UsageError

from .action import traverse
from .context import GRPCContext, TContext
from .exception import GRPCRemoteError
from .pybotchi_pb2 import (
    ActionListRequest,
    ActionListResponse,
    ActionSchema,
    Edge,
    Event,
    JSONSchema,
    TraverseGraph,
    TraverseRequest,
)
from .pybotchi_pb2_grpc import PyBotchiGRPCServicer
from ..action import Action
from ..common import Graph
from ..utils import uuid


class PyBotchiGRPC(PyBotchiGRPCServicer, Generic[TContext]):
    """PyBotchiGRPC Handler."""

    __context_class__: type[TContext] = GRPCContext  # type: ignore[assignment]
    __allow_exec__: bool = False

    def __init__(self, id: str, module: str, groups: dict[str, dict[str, type[Action]]]) -> None:
        """Initialize Handler."""
        self.id = id
        self.module = module
        self.groups = groups
        self.__has_validate_metadata__ = self.__class__.validate_metadata is not PyBotchiGRPC.validate_metadata

    async def validate_metadata(self, metadata: Metadata | None) -> None:
        """Validate invocation metadata."""
        pass

    async def consume(self, context: TContext, groups: list[str], events: AsyncGenerator[Event, None]) -> None:
        """Consume event."""
        try:
            async for event in events:
                if consumer := getattr(self, f"grpc_event_{event.name}", None):
                    await consumer(context, groups, event)
        except UsageError:
            pass
        except GRPCRemoteError as e:
            await context.grpc_send_up(
                context.context_id,
                "error",
                {
                    "type": e.type,
                    "message": e.message,
                    "tracebacks": e.tracebacks,
                },
            )
            raise e
        except Exception as e:
            exc_type, exc_value, exc_tb = exc_info()
            await context.grpc_send_up(
                context.context_id,
                "error",
                {
                    "type": exc_type.__name__ if exc_type else "Exception",
                    "message": str(exc_value) if exc_value else str(e),
                    "tracebacks": format_exception(exc_type, exc_value, exc_tb),
                },
            )
            raise e

    async def grpc_event_execute(self, context: TContext, groups: list[str], event: Event) -> None:
        """Consume grpc `execute` event."""
        data = MessageToDict(event)["data"]
        action, action_return = await context.start(
            next(a for group in groups if (a := self.groups[group].get(data["name"]))),
            **data.get("args", {}),
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

    async def grpc_event_update(self, context: TContext, groups: list[str], event: Event) -> None:
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
                    [ref.get(arg, arg) if isinstance(arg, str) else arg for arg in _args]
                    if (_args := data.get("args"))
                    else []
                )
                kwargs = (
                    {key: ref.get(value, value) if isinstance(value, str) else value for key, value in _kwargs.items()}
                    if (_kwargs := data.get("kwargs"))
                    else {}
                )
                ret = target(*args, **kwargs)
                if isinstance(ret, Awaitable):
                    await ret

    async def accept(self, events: AsyncGenerator[Event, None], context: ServicerContext) -> Queue[Event]:
        """Accept connect execution."""
        event = await anext(events)
        if event.name != "init" or not event.data:
            await context.abort(StatusCode.FAILED_PRECONDITION)

        data = MessageToDict(event)["data"]
        data_context = data["context"]
        if "source_id" not in data_context:
            data_context["source_id"] = str(uuid())

        agent_context = self.__context_class__(
            **data_context,
        )
        queue = agent_context._response_queue = Queue[Event]()
        create_task(self.consume(agent_context, data["groups"], events))
        return queue

    ##############################################################################################
    #                                      EXECUTION METHODS                                     #
    ##############################################################################################

    async def execute_connect(
        self, request_iterator: AsyncGenerator[Event, None], context: ServicerContext
    ) -> AsyncGenerator[Event, None]:
        """Execute `connect` method."""
        queue = await self.accept(request_iterator, context)
        while True:
            que = await queue.get()
            yield que

            if que.name == "close" or que.name == "error":
                break

    ##############################################################################################
    #                                       BASE CONSUMERS                                       #
    ##############################################################################################

    async def connect(
        self, request_iterator: AsyncGenerator[Event, None], context: ServicerContext
    ) -> AsyncGenerator[Event, None]:
        """Consume `connect` method."""
        if self.__has_validate_metadata__ and self.validate_metadata(context.invocation_metadata()):
            await context.abort(StatusCode.FAILED_PRECONDITION)

        async for event in self.execute_connect(request_iterator, context):
            yield event

    async def action_list(self, request: ActionListRequest, context: ServicerContext) -> ActionListResponse:
        """Consume `action_list` method."""
        if self.__has_validate_metadata__ and self.validate_metadata(context.invocation_metadata()):
            await context.abort(StatusCode.FAILED_PRECONDITION)

        actions: dict[type[Action], str] = {}
        for group in request.groups:
            if not (action_group := self.groups.get(group)):
                continue

            for action in action_group.values():
                if (
                    not request.allowed_actions or request.allowed_actions.get(action.__name__, action.__enabled__)
                ) and action not in actions:
                    actions[action] = group

        return ActionListResponse(
            agent_id=self.id,
            actions=(
                [
                    ActionSchema(
                        concurrent=action.__concurrent__,
                        group=group,
                        schema=JSONSchema(**action.model_json_schema()),
                    )
                    for action, group in actions.items()
                ]
            ),
        )

    async def traverse(self, request: TraverseRequest, context: ServicerContext) -> TraverseGraph:
        """Consume `action_list` method."""
        if self.__has_validate_metadata__ and self.validate_metadata(context.invocation_metadata()):
            await context.abort(StatusCode.FAILED_PRECONDITION)

        nodes = set(request.nodes)
        old_nodes = nodes.copy()

        await traverse(
            graph := Graph(nodes=nodes),
            next(a for group in request.groups if (a := self.groups[group].get(request.name))),
            dict(request.allowed_actions),
            MessageToDict(request.integrations),
            request.bypass,
            self.module,
            request.alias,
        )

        return TraverseGraph(
            nodes=[node for node in graph.nodes if node not in old_nodes],
            edges=[
                Edge(
                    source=edge[0],
                    target=edge[1],
                    concurrent=edge[2],
                    name=edge[3],
                )
                for edge in graph.edges
            ],
        )
