"""Pybotchi GRPC Classes."""

from asyncio import Queue
from collections.abc import AsyncGenerator, Awaitable
from contextlib import AsyncExitStack, asynccontextmanager
from inspect import getmembers
from itertools import islice
from typing import Any, Generic

from datamodel_code_generator import DataModelType, Formatter, PythonVersion
from datamodel_code_generator.model import get_data_model_types
from datamodel_code_generator.parser.jsonschema import (
    JsonSchemaParser,
)

from google.protobuf.json_format import MessageToDict

from grpc import Compression, ssl_channel_credentials
from grpc.aio import insecure_channel, secure_channel

from orjson import dumps

from .common import GRPCConfigLoaded, GRPCConnection, GRPCIntegration
from .context import TContext
from .exception import GRPCRemoteError
from .pybotchi_pb2 import (
    ActionListRequest,
    ActionListResponse,
    ActionSchema,
    Event,
    TraverseGraph,
    TraverseRequest,
)
from .pybotchi_pb2_grpc import PyBotchiGRPCStub
from ..action import Action, ChildActions
from ..common import ActionReturn, Graph
from ..utils import unwrap_exceptions

DMT = get_data_model_types(
    DataModelType.PydanticV2BaseModel,
    target_python_version=PythonVersion.PY_313,
)


class GRPCClient:
    """GRPC Client."""

    def __init__(
        self,
        stub: PyBotchiGRPCStub,
        name: str,
        config: GRPCConfigLoaded,
        manual_enable: bool,
        allowed_actions: dict[str, bool],
        remote_action_class: type["GRPCRemoteAction"] | None,
        exclude_unset: bool,
    ) -> None:
        """Build GRPC Client."""
        self.stub = stub
        self.name = name
        self.config = config
        self.manual_enable = manual_enable
        self.allowed_actions = allowed_actions
        self.remote_action_class = remote_action_class or GRPCRemoteAction
        self.exclude_unset = exclude_unset

    def build_action(self, agent_id: str, action_schema: ActionSchema) -> tuple[str, type["GRPCRemoteAction"]]:
        """Build GRPCToolAction."""
        globals: dict[str, Any] = {}
        schema = action_schema.schema
        class_name = schema.title
        exec(
            JsonSchemaParser(
                dumps(MessageToDict(schema)).decode(),
                data_model_type=DMT.data_model,
                data_model_root_type=DMT.root_model,
                data_model_field_type=DMT.field_model,
                data_type_manager_type=DMT.data_type_manager,
                dump_resolve_reference_action=DMT.dump_resolve_reference_action,
                class_name=class_name,
                strict_nullable=True,
                formatters=[Formatter.RUFF_FORMAT, Formatter.RUFF_CHECK],
            )
            .parse()
            .removeprefix("from __future__ import annotations"),  # type: ignore[union-attr]
            globals,
        )
        base_class = globals[class_name]

        concurrent = action_schema.concurrent
        if self.remote_action_class is not GRPCRemoteAction:
            for cls in self.remote_action_class.__mro__:
                if cls is GRPCRemoteAction:
                    break
                if (con := cls.__dict__.get("__concurrent__")) is not None:
                    concurrent = con
                    break

        action = type(
            class_name,
            (
                base_class,
                self.remote_action_class,
            ),
            {
                "__grpc_client__": self,
                "__grpc_group__": action_schema.group,
                "__grpc_action_name__": schema.title,
                "__grpc_exclude_unset__": self.exclude_unset,
                "__concurrent__": concurrent,
                "__module__": f"grpc.{agent_id}",
            },
        )

        if desc := schema.description:
            action.__doc__ = desc

        return class_name, action

    async def patch_actions(self, actions: ChildActions, grpc_actions: ChildActions) -> ChildActions:
        """Retrieve Tools."""
        response: ActionListResponse = await self.stub.action_list(
            ActionListRequest(
                groups=self.config["groups"],
                allowed_actions=None if self.manual_enable else self.allowed_actions,
            )
        )

        for action_schema in response.actions:
            name, action = self.build_action(response.agent_id, action_schema)
            if _tool := grpc_actions.get(name):
                action = type(
                    name,
                    (_tool, action),
                    {"__module__": f"{action.__module__}.patched"},
                )

            if not self.allowed_actions or self.allowed_actions.get(
                name, False if self.manual_enable else action.__enabled__
            ):
                actions[name] = action

        return actions


class GRPCAction(Action[TContext], Generic[TContext]):
    """GRPC Action."""

    __grpc_clients__: dict[str, GRPCClient]
    __grpc_connections__: list[GRPCConnection]
    __grpc_tool_actions__: ChildActions

    # --------------------- not inheritable -------------------- #

    __has_pre_grpc__: bool

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """Override __pydantic_init_subclass__."""
        super().__pydantic_init_subclass__(**kwargs)
        cls.__has_pre_grpc__ = cls.pre_grpc is not GRPCAction.pre_grpc

    @classmethod
    def __init_child_actions__(cls) -> None:
        """Initialize defined child actions."""
        cls.__grpc_tool_actions__ = {}
        cls.__child_actions__ = {}
        for name, child in getmembers(cls):
            if isinstance(child, type):
                if getattr(child, "__grpc_action__", False):
                    cls.__grpc_tool_actions__[name] = child
                elif issubclass(child, Action):
                    cls.__child_actions__[name] = child

    async def pre_grpc(self, context: TContext) -> ActionReturn:
        """Execute pre grpc process."""
        return ActionReturn.GO

    async def execute(self, context: TContext, parent: Action | None = None, append: bool = True) -> ActionReturn:
        """Execute main process."""
        self._parent = parent
        parent_context = context
        try:
            if parent and append:
                parent._actions.append(self)

            if self.__detached__:
                context = await context.detach_context()

            if context.check_self_recursion(self):
                return ActionReturn.END

            if self.__has_pre_grpc__ and (result := await self.pre_grpc(context)).is_break:
                return result

            async with multi_grpc_clients(context.integrations, self.__grpc_connections__) as clients:
                self.__grpc_clients__ = clients

                if self.__has_pre__ and (result := await self.pre(context)).is_break:
                    return result

                if self.__max_child_iteration__:
                    iteration = 0
                    while iteration <= self.__max_child_iteration__:
                        if (result := await self.execution(context)).is_break:
                            break
                        iteration += 1
                    if result.is_end:
                        return result
                elif (result := await self.execution(context)).is_break:
                    return result

                if self.__has_post__ and (result := await self.post(context)).is_break:
                    return result

                return ActionReturn.GO
        except Exception as exception:
            if not self.__has_on_error__:
                self.__to_commit__ = False
                raise next(unwrap_exceptions(exception)) from None
            elif (
                result := await self.on_error(
                    context,
                    exception,
                    unwrap_exceptions(exception),
                )
            ).is_break:
                return result
            return ActionReturn.GO
        finally:
            if self.__to_commit__ and self.__detached__:
                await self.commit_context(parent_context, context)

    async def get_child_actions(self, context: TContext) -> ChildActions:
        """Retrieve child Actions."""
        normal_tools = await super().get_child_actions(context)

        for client in self.__grpc_clients__.values():
            await client.patch_actions(normal_tools, self.__grpc_tool_actions__)

        return normal_tools

    ####################################################################################################
    #                                          GRPCACTION TOOLS                                         #
    # ------------------------------------------------------------------------------------------------ #

    @classmethod
    def add_child(
        cls,
        action: type["Action"],
        name: str | None = None,
        override: bool = False,
        extended: bool = True,
    ) -> None:
        """Add child action."""
        name = name or action.__name__
        if not override and hasattr(cls, name):
            raise ValueError(f"Attribute {name} already exists!")

        if not issubclass(action, Action):
            raise ValueError(f"{action.__name__} is not a valid action!")

        if extended:
            action = type(name, (action,), {"__module__": action.__module__})

        if issubclass(action, GRPCRemoteAction):
            cls.__grpc_tool_actions__[name] = action
        else:
            cls.__child_actions__[name] = action
        setattr(cls, name, action)


class GRPCRemoteAction(Action[TContext], Generic[TContext]):
    """GRPC Remote Action."""

    __grpc_action__ = True

    __grpc_client__: GRPCClient
    __grpc_group__: str
    __grpc_action_name__: str
    __grpc_exclude_unset__: bool
    __grpc_queue__: Queue[Event]

    async def grpc_event_close(self, context: TContext, event: Event) -> None:
        """Consume close event."""
        if not (data := MessageToDict(event)["data"]):
            raise ValueError("Not valid event!")

        action = data["action"]
        for usage in action["usages"]:
            self._usage.append(usage)

        for child in action["actions"]:
            self._actions.append(child)

        await self.__grpc_queue__.put(event)

    async def grpc_event_error(self, context: TContext, event: Event) -> None:
        """Consume error event."""
        if not (data := MessageToDict(event)["data"]):
            raise ValueError("Not valid event!")

        raise GRPCRemoteError(self.__class__.__name__, self.__grpc_action_name__, **data)

    async def grpc_event_update(self, context: TContext, event: Event) -> None:
        """Consume close event."""
        if not (data := MessageToDict(event)["data"]):
            raise ValueError("Not valid event!")

        if (raw_exec := data.get("exec")) and self.__grpc_client__.config.get("allow_exec"):
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

    async def grpc_queue(self, context: TContext) -> AsyncGenerator[Event, None]:
        """Stream event queue."""
        while que := await self.__grpc_queue__.get():
            if que.name == "close":
                break

            yield que

    async def grpc_send(self, name: str, data: dict[str, Any] | None = None) -> None:
        """Send event."""
        await self.__grpc_queue__.put(Event(name=name, data={} if data is None else data))

    async def grpc_consume(self, context: TContext, event: Event) -> None:
        """Consume event."""
        if consumer := getattr(self, f"grpc_event_{event.name}", None):
            await consumer(context, event)

    async def grpc_connect(
        self,
        context: TContext,
        payload: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> AsyncGenerator[Event, None]:
        """Trigger grpc connect."""
        if metadata := self.__grpc_client__.config.get("metadata"):
            invocation_metadata: dict[str, Any] | None = metadata.get("connect")
        else:
            invocation_metadata = None

        self.__grpc_queue__ = Queue()

        context_dump = context.grpc_sharing_dump()
        context_id = context_dump["context_id"]
        context._request_queues[context_id] = self.__grpc_queue__

        try:
            await self.grpc_send(
                "init",
                {
                    "groups": self.__grpc_client__.config["groups"],
                    "context": context_dump,
                },
            )

            await self.grpc_send(
                "execute",
                {
                    "name": self.__grpc_action_name__,
                    "args": payload,
                },
            )

            async for event in self.__grpc_client__.stub.connect(
                self.grpc_queue(context), metadata=invocation_metadata
            ):
                yield event
        finally:
            context._request_queues.pop(context_id, None)

    async def pre(self, context: TContext) -> ActionReturn:
        """Execute pre process."""
        action_args = self.model_dump(exclude_unset=self.__grpc_exclude_unset__)

        await context.notify(
            {
                "event": "grpc",
                "class": self.__class__.__name__,
                "type": self.__grpc_action_name__,
                "status": "started",
                "data": action_args,
            }
        )

        async for event in self.grpc_connect(context, action_args):
            await context.notify(
                {
                    "event": "grpc",
                    "class": self.__class__.__name__,
                    "type": self.__grpc_action_name__,
                    "status": "inprogress",
                    "data": MessageToDict(event),
                }
            )
            await self.grpc_consume(context, event)

        await context.notify(
            {
                "event": "grpc",
                "class": self.__class__.__name__,
                "type": self.__grpc_action_name__,
                "status": "completed",
                "data": MessageToDict(event),
            }
        )

        return ActionReturn.GO


@asynccontextmanager
async def multi_grpc_clients(
    integrations: dict[str, GRPCIntegration],
    connections: list[GRPCConnection],
    bypass: bool = False,
) -> AsyncGenerator[dict[str, GRPCClient], None]:
    """Connect to multiple grpc clients."""
    async with AsyncExitStack() as stack:
        clients: dict[str, GRPCClient] = {}
        for conn in connections:
            integration: GRPCIntegration | None = integrations.get(conn.name)
            if not bypass and (conn.require_integration and integration is None):
                continue

            if integration is None:
                integration = {}

            overrided_config = await conn.get_config(integration.get("config"))
            if _allowed_actions := integration.get("allowed_actions"):
                allowed_actions = conn.allowed_actions | _allowed_actions
            elif _allowed_actions is not None:
                allowed_actions = {}
            else:
                allowed_actions = conn.allowed_actions

            if overrided_config.get("secure"):
                channel = await stack.enter_async_context(
                    secure_channel(
                        target=overrided_config["url"],
                        credentials=ssl_channel_credentials(
                            root_certificates=overrided_config["root_certificates"],
                            private_key=overrided_config["private_key"],
                            certificate_chain=overrided_config["certificate_chain"],
                        ),
                        options=overrided_config["options"],
                        compression=(Compression[comp] if (comp := overrided_config["compression"]) else None),
                        interceptors=conn.interceptors,
                    )
                )
            else:
                channel = await stack.enter_async_context(
                    insecure_channel(
                        target=overrided_config["url"],
                        options=overrided_config["options"],
                        compression=(Compression[comp] if (comp := overrided_config["compression"]) else None),
                        interceptors=conn.interceptors,
                    )
                )
            clients[conn.name] = GRPCClient(
                PyBotchiGRPCStub(channel),
                conn.name,
                overrided_config,
                conn.manual_enable,
                allowed_actions,
                conn.remote_action_class,
                integration.get(
                    "exclude_unset",
                    conn.exclude_unset,
                ),
            )

        yield clients


##########################################################################
#                           GRPCAction Utilities                          #
##########################################################################


async def graph(
    action: type[Action],
    allowed_actions: dict[str, bool] | None = None,
    integrations: dict[str, GRPCIntegration] | None = None,
    bypass: bool = False,
) -> Graph:
    """Retrieve Graph."""
    if integrations is None:
        integrations = {}

    origin = f"{action.__module__}.{action.__qualname__}"
    await traverse(
        graph := Graph(origin=origin, nodes={origin}),
        action,
        allowed_actions,
        integrations,
        bypass,
    )

    return graph


async def traverse(
    graph: Graph,
    action: type[Action],
    allowed_actions: dict[str, bool] | None,
    integrations: dict[str, GRPCIntegration],
    bypass: bool = False,
    module: str | None = None,
    alias: str | None = None,
) -> None:
    """Retrieve Graph."""
    current = f"{alias or action.__module__}.{action.__qualname__}"

    if allowed_actions:
        child_actions = {
            name: child
            for name, child in action.__child_actions__.items()
            if allowed_actions.get(name, child.__enabled__)
        }
    else:
        child_actions = action.__child_actions__.copy()

    async with AsyncExitStack() as stack:
        if issubclass(action, GRPCAction):
            clients = await stack.enter_async_context(
                multi_grpc_clients(integrations, action.__grpc_connections__, bypass)
            )
            [await client.patch_actions(child_actions, action.__grpc_tool_actions__) for client in clients.values()]

        for child_action in child_actions.values():
            child = (
                f"{alias or child_action.__module__}.{child_action.__qualname__}"
                if child_action.__module__ == module
                else f"{child_action.__module__}.{child_action.__qualname__}"
            )
            graph.edges.add(
                (
                    current,
                    child,
                    child_action.__concurrent__,
                    (child_action.__grpc_client__.name if issubclass(child_action, GRPCRemoteAction) else ""),
                )
            )

            if child not in graph.nodes:
                graph.nodes.add(child)
                if issubclass(child_action, GRPCRemoteAction):
                    response: TraverseGraph = await child_action.__grpc_client__.stub.traverse(
                        TraverseRequest(
                            nodes=list(graph.nodes),
                            alias=child_action.__module__,
                            groups=child_action.__grpc_client__.config["groups"],
                            name=child_action.__grpc_action_name__,
                            integrations=integrations,
                        )
                    )
                    for n in response.nodes:
                        graph.nodes.add(n)
                    for e in response.edges:
                        graph.edges.add((e.source, e.target, e.concurrent, e.name))
                else:
                    await traverse(
                        graph,
                        child_action,
                        allowed_actions,
                        integrations,
                        bypass,
                        module,
                        alias,
                    )
