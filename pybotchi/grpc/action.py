"""Pybotchi GRPC Classes."""

from asyncio import Queue
from collections import OrderedDict
from collections.abc import AsyncGenerator, Awaitable
from contextlib import AsyncExitStack, asynccontextmanager, suppress
from inspect import getdoc, getmembers
from itertools import islice
from os import getenv
from typing import Any, Callable, Generic

from datamodel_code_generator import DataModelType, PythonVersion
from datamodel_code_generator.model import get_data_model_types
from datamodel_code_generator.parser.base import title_to_class_name
from datamodel_code_generator.parser.jsonschema import (
    JsonSchemaParser,
)

from google.protobuf.json_format import MessageToJson

from grpc.aio import insecure_channel

from orjson import dumps

from starlette.applications import AppType

from .common import GRPCConfig, GRPCConnection, GRPCIntegration
from .context import TContext
from .pybotchi_pb2 import ActionListRequest, ActionListResponse, Event, JSONSchema
from .pybotchi_pb2_grpc import PyBotchiGRPCStub
from ..action import Action, ChildActions
from ..common import ActionReturn, ChatRole, Graph
from ..utils import is_camel_case

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
        config: GRPCConfig,
        allowed_actions: set[str],
        exclude_unset: bool,
    ) -> None:
        """Build GRPC Client."""
        self.stub = stub
        self.name = name
        self.config = config
        self.allowed_actions = allowed_actions
        self.exclude_unset = exclude_unset

    def build_action(self, schema: JSONSchema) -> tuple[str, type["GRPCRemoteAction"]]:
        """Build GRPCToolAction."""
        globals: dict[str, Any] = {}
        class_name = (
            f"{schema.title[0].upper()}{schema.title[1:]}"
            if is_camel_case(schema.title)
            else title_to_class_name(schema.title)
        )
        exec(
            JsonSchemaParser(
                dumps(MessageToJson(schema)).decode(),
                data_model_type=DMT.data_model,
                data_model_root_type=DMT.root_model,
                data_model_field_type=DMT.field_model,
                data_type_manager_type=DMT.data_type_manager,
                dump_resolve_reference_action=DMT.dump_resolve_reference_action,
                class_name=class_name,
                strict_nullable=True,
            )
            .parse()
            .removeprefix("from __future__ import annotations"),  # type: ignore[union-attr]
            globals,
        )
        base_class = globals[class_name]
        action = type(
            class_name,
            (
                base_class,
                GRPCRemoteAction,
            ),
            {
                "__grpc_action_name__": schema.title,
                "__grpc_client__": self,
                "__grpc_exclude_unset__": getattr(
                    base_class, "__grpc_exclude_unset__", self.exclude_unset
                ),
                "__module__": f"grpc.{self.name}",
            },
        )

        if desc := schema.description:
            action.__doc__ = desc

        return class_name, action

    async def patch_actions(
        self, actions: ChildActions, grpc_actions: ChildActions
    ) -> ChildActions:
        """Retrieve Tools."""
        response: ActionListResponse = await self.stub.action_list(
            ActionListRequest(group=self.config["group"])
        )
        for action in response.actions:
            name, action = self.build_action(action)
            if not self.allowed_actions or name in self.allowed_actions:
                if _tool := grpc_actions.get(name):
                    action = type(
                        name,
                        (_tool, action),
                        {"__module__": f"grpc.{self.name}.patched"},
                    )
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
    def __init_child_actions__(cls, **kwargs: Any) -> None:
        """Initialize defined child actions."""
        cls.__grpc_tool_actions__ = OrderedDict()
        cls.__child_actions__ = OrderedDict()
        for _, attr in getmembers(cls):
            if isinstance(attr, type):
                if getattr(attr, "__grpc_action__", False):
                    cls.__grpc_tool_actions__[attr.__name__] = attr
                elif issubclass(attr, Action):
                    cls.__child_actions__[attr.__name__] = attr

    async def pre_grpc(self, context: TContext) -> ActionReturn:
        """Execute pre grpc process."""
        return ActionReturn.GO

    async def execute(
        self, context: TContext, parent: Action | None = None
    ) -> ActionReturn:
        """Execute main process."""
        self._parent = parent
        parent_context = context
        try:
            if self.__detached__:
                context = await context.detach_context()

            if context.check_self_recursion(self):
                return ActionReturn.END

            if (
                self.__has_pre_grpc__
                and (result := await self.pre_grpc(context)).is_break
            ):
                return result

            async with multi_grpc_clients(
                context.integrations, self.__grpc_connections__
            ) as clients:
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
                raise exception
            elif (result := await self.on_error(context, exception)).is_break:
                return result
            return ActionReturn.GO
        finally:
            if self.__to_commit__ and self.__detached__:
                await self.commit_context(parent_context, context)

    async def get_child_actions(self, context: TContext) -> ChildActions:
        """Retrieve child Actions."""
        normal_tools = await super().get_child_actions(context)
        [
            await client.patch_actions(normal_tools, self.__grpc_tool_actions__)
            for client in self.__grpc_clients__.values()
        ]
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
    __grpc_action_name__: str
    __grpc_exclude_unset__: bool
    __grpc_queue__: Queue[Event]

    async def grpc_queue(self) -> AsyncGenerator[Event]:
        """Stream event queue."""
        while que := await self.__grpc_queue__.get():
            yield que

    async def grpc_connect(self, context: TContext) -> None:
        """Trigger grpc connect."""
        self.__grpc_queue__ = Queue()

        if metadata := self.__grpc_client__.config.get("metadata"):
            data: dict[str, Any] | None = metadata.get("connect")
        else:
            data = None

        await self.__grpc_queue__.put(Event(name="connect", data=data))
        await self.__grpc_queue__.put(
            Event(
                name="trigger",
                data={
                    "group": self.__grpc_client__.config["group"],
                    "name": self.__grpc_action_name__,
                    "args": self.model_dump(exclude_unset=self.__grpc_exclude_unset__),
                },
            )
        )

        async for response in self.__grpc_client__.stub.connect(self.grpc_queue()):
            print(response)

    async def pre(self, context: TContext) -> ActionReturn:
        """Execute pre process."""
        await context.notify(
            {
                "event": "grpc-connect",
                "class": self.__class__.__name__,
                "type": self.__grpc_action_name__,
                "status": "started",
                "data": action_args,
            }
        )

        result = await self.__grpc_client__.call_tool(
            self.__grpc_action_name__,
            action_args,
            progress_callback=self.build_progress_callback(context),
        )

        content = "\n\n---\n\n".join(self.clean_content(c) for c in result.content)

        await context.notify(
            {
                "event": "grpc-call-tool",
                "class": self.__class__.__name__,
                "type": self.__grpc_action_name__,
                "status": "completed",
                "data": content,
            }
        )
        await context.add_response(self, content)

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

            overrided_config = conn.get_config(integration.get("config"))
            if integration.get("mode", conn.mode) == GRPCMode.SSE:
                overrided_config.pop("terminate_on_close", None)
                client_builder: Callable = sse_client
            else:
                client_builder = streamablehttp_client
            _allowed_tools = integration.get("allowed_tools") or set[str]()
            if conn.allowed_tools:
                allowed_tools = set(
                    {tool for tool in _allowed_tools if tool in conn.allowed_tools}
                    if _allowed_tools
                    else conn.allowed_tools
                )
            else:
                allowed_tools = _allowed_tools
            streams = await stack.enter_async_context(
                client_builder(**overrided_config)
            )
            client = await stack.enter_async_context(
                ClientSession(*islice(streams, 0, 2))
            )
            await client.initialize()
            clients[conn.name] = GRPCClient(
                client,
                conn.name,
                overrided_config,
                allowed_tools,
                integration.get(
                    "exclude_unset",
                    conn.exclude_unset,
                ),
            )

        yield clients


async def mount_grpc_groups(app: AppType, stack: AsyncExitStack) -> None:
    """Start GRPC Servers."""
    queue = Action.__subclasses__()
    while queue:
        que = queue.pop()
        if que.__groups__ and (grpc_groups := que.__groups__.get("grpc")):
            entry = build_grpc_entry(que)
            for group in grpc_groups:
                await add_grpc_server(group.lower(), que, entry)
        queue.extend(que.__subclasses__())

    for server, grpc in GRPCAction.__grpc_servers__.items():
        app.mount(f"/{server}", grpc.streamable_http_app())
        await stack.enter_async_context(grpc.session_manager.run())


def build_grpc_entry(action: type["Action"]) -> Callable[..., Awaitable[str]]:
    """Build GRPC Entry."""
    from .context import Context

    async def process(data: dict[str, Any]) -> str:
        context = Context(
            prompts=[
                {
                    "role": ChatRole.SYSTEM,
                    "content": getdoc(action) or action.__system_prompt__ or "",
                }
            ],
        )
        await context.start(action, **data)
        return context.prompts[-1]["content"]

    globals: dict[str, Any] = {"process": process}
    kwargs: list[str] = []
    data: list[str] = []
    for key, val in action.model_fields.items():
        if val.annotation is None:
            kwargs.append(f"{key}: None")
            data.append(f'"{key}": {key}')
        else:
            globals[val.annotation.__name__] = val.annotation
            kwargs.append(f"{key}: {val.annotation.__name__}")
            data.append(f'"{key}": {key}')

    exec(
        f"""
async def tool({", ".join(kwargs)}):
    return await process({{{", ".join(data)}}})
""".strip(),
        globals,
    )

    return globals["tool"]


async def add_grpc_server(
    group: str, action: type["Action"], entry: Callable[..., Awaitable[str]]
) -> None:
    """Add action."""
    if not (server := GRPCAction.__grpc_servers__.get(group)):
        server = GRPCAction.__grpc_servers__[group] = FastGRPC(
            f"grpc-{group}",
            stateless_http=True,
            log_level=getenv("GRPC_LOGGER_LEVEL", "WARNING"),  # type: ignore[arg-type]
        )
    server.add_tool(entry, action.__name__, getdoc(action))


##########################################################################
#                           GRPCAction Utilities                          #
##########################################################################


async def graph(
    action: type[Action],
    allowed_actions: dict[str, bool] | None = None,
    integrations: dict[str, GRPCIntegration] | None = None,
    bypass: bool = False,
) -> str:
    """Retrieve Graph."""
    if integrations is None:
        integrations = {}

    await traverse(
        graph := Graph(nodes={f"{action.__module__}.{action.__qualname__}"}),
        action,
        allowed_actions,
        integrations,
        bypass,
    )

    return graph.flowchart()


async def traverse(
    graph: Graph,
    action: type[Action],
    allowed_actions: dict[str, bool] | None,
    integrations: dict[str, GRPCIntegration],
    bypass: bool = False,
) -> None:
    """Retrieve Graph."""
    parent = f"{action.__module__}.{action.__qualname__}"

    if allowed_actions:
        child_actions = OrderedDict(
            item
            for item in action.__child_actions__.items()
            if allowed_actions.get(item[0], item[1].__enabled__)
        )
    else:
        child_actions = action.__child_actions__.copy()

    if issubclass(action, GRPCAction):
        async with multi_grpc_clients(
            integrations, action.__grpc_connections__, bypass
        ) as clients:
            [
                await client.patch_actions(child_actions, action.__grpc_tool_actions__)
                for client in clients.values()
            ]

    for child_action in child_actions.values():
        node = f"{child_action.__module__}.{child_action.__qualname__}"
        graph.edges.add((parent, node, child_action.__concurrent__))
        if node not in graph.nodes:
            graph.nodes.add(node)
            await traverse(graph, child_action, allowed_actions, integrations, bypass)


async def connect() -> None:
    """Test connect."""
    async with insecure_channel("localhost:50051") as channel:
        stub = PyBotchiGRPCStub(channel)

        queue = Queue[Event]()
        await queue.put(Event(name="connect", data={}))

        async for response in stub.connect(stream(queue)):
            print(response)

        a: ActionListResponse = await stub.action_list(ActionListRequest(group="test"))
        print(a.actions)
        a = await stub.action_list(ActionListRequest(group="test2"))
        print(a.actions)
