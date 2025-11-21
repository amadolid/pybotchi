"""Pybotchi A2A Classes."""

from collections import OrderedDict
from collections.abc import AsyncGenerator, Awaitable
from contextlib import AsyncExitStack, asynccontextmanager, suppress
from inspect import getdoc, getmembers
from itertools import islice
from os import getenv
from typing import Any, Callable, Generic, Unpack

from a2a.client import A2ACardResolver, A2AClient as BaseA2AClient
from a2a.types import AgentCard

from datamodel_code_generator import DataModelType, PythonVersion
from datamodel_code_generator.model import get_data_model_types
from datamodel_code_generator.parser.base import title_to_class_name
from datamodel_code_generator.parser.jsonschema import (
    JsonSchemaParser,
)

from httpx import AsyncClient

from orjson import dumps

from starlette.applications import AppType

from .common import A2ACard, A2AConfig, A2AConnection, A2AIntegration
from .context import TContext
from ...action import Action, ChildActions
from ...common import ActionReturn, ChatRole, Graph
from ...utils import is_camel_case


DMT = get_data_model_types(
    DataModelType.PydanticV2BaseModel,
    target_python_version=PythonVersion.PY_313,
)


class A2AClient:
    """A2A Client."""

    def __init__(
        self,
        client: AsyncClient,
        name: str,
        config: A2AConfig,
        allowed_tools: set[str],
        exclude_unset: bool,
    ) -> None:
        """Build A2A Client."""
        self.client = client
        self.card_resolver = A2ACardResolver(
            httpx_client=client,
            base_url=config["base_url"],
            agent_card_path=config["agent_card_path"],
        )
        self.name = name
        self.config = config
        self.allowed_tools = allowed_tools
        self.exclude_unset = exclude_unset
        self._cached_card: dict[
            str, tuple[str | None, dict[str, str] | None, AgentCard]
        ] = {}
        self._cached_client: dict[int, BaseA2AClient] = {}

    async def well_known_card(self, **kwargs: Unpack[A2ACard]) -> AgentCard:
        """Get well know AgentCard."""
        return await self.card(".well-known", **kwargs)

    async def extended_card(self, **kwargs: Unpack[A2ACard]) -> AgentCard:
        """Get extended AgentCard."""
        return await self.card(".extended", **kwargs)

    async def card(self, name: str = "", **kwargs: Unpack[A2ACard]) -> AgentCard:
        """Get AgentCard by name."""
        if (card_configs := self.config.get("cards")) and (
            card_config := card_configs.get(name)
        ):
            if headers := card_config.get("headers"):
                if override := kwargs.get("headers"):
                    headers = headers | override
            else:
                headers = kwargs.get("headers")
            path = kwargs.get("path", card_config.get("path"))
        else:
            headers = kwargs.get("headers")
            path = kwargs.get("path")

        if (
            (card := self._cached_card.get(name))
            and card[0] == path
            and card[1] == headers
        ):
            return card[2]

        card = await self.card_resolver.get_agent_card(path, headers)
        self._cached_card[name] = (path, headers, card)
        return card

    async def card_client(
        self, name: str = "", **kwargs: Unpack[A2ACard]
    ) -> BaseA2AClient:
        """Get A2AClient by AgentCard."""
        card = await self.card(name, **kwargs)
        if client := self._cached_client.get(card_id := id(card)):
            return client

        self._cached_client[card_id] = client = BaseA2AClient(
            httpx_client=self.client, agent_card=card
        )
        return client

    def build_tool(self, tool: Any) -> tuple[str, type["A2AToolAction"]]:
        """Build A2AToolAction."""
        import pdb

        pdb.set_trace()
        globals: dict[str, Any] = {}
        class_name = (
            f"{tool.name[0].upper()}{tool.name[1:]}"
            if is_camel_case(tool.name)
            else title_to_class_name(tool.name)
        )
        exec(
            JsonSchemaParser(
                dumps(tool.inputSchema).decode(),
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
                A2AToolAction,
            ),
            {
                "__a2a_tool_name__": tool.name,
                "__a2a_client__": self.client,
                "__a2a_exclude_unset__": getattr(
                    base_class, "__a2a_exclude_unset__", self.exclude_unset
                ),
                "__module__": f"a2a.{self.name}",
            },
        )

        if desc := tool.description:
            action.__doc__ = desc

        return class_name, action

    async def patch_tools(
        self, actions: ChildActions, a2a_actions: ChildActions
    ) -> ChildActions:
        """Retrieve Tools."""
        client = await self.well_known_card()
        import pdb

        await pdb.set_trace_async()
        response = await self.client.list_tools()
        for tool in response.tools:
            name, action = self.build_tool(tool)
            if not self.allowed_tools or name in self.allowed_tools:
                if _tool := a2a_actions.get(name):
                    action = type(
                        name,
                        (_tool, action),
                        {"__module__": f"a2a.{self.name}.patched"},
                    )
                actions[name] = action
        return actions


class A2AAction(Action[TContext], Generic[TContext]):
    """A2A Tool Action."""

    __a2a_servers__: dict[str, Any] = {}

    __a2a_clients__: dict[str, A2AClient]
    __a2a_connections__: list[A2AConnection]
    __a2a_tool_actions__: ChildActions

    # --------------------- not inheritable -------------------- #

    __has_pre_a2a__: bool

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """Override __pydantic_init_subclass__."""
        super().__pydantic_init_subclass__(**kwargs)
        cls.__has_pre_a2a__ = cls.pre_a2a is not A2AAction.pre_a2a

    @classmethod
    def __init_child_actions__(cls, **kwargs: Any) -> None:
        """Initialize defined child actions."""
        cls.__a2a_tool_actions__ = OrderedDict()
        cls.__child_actions__ = OrderedDict()
        for _, attr in getmembers(cls):
            if isinstance(attr, type):
                if issubclass(attr, A2AAction):
                    cls.__a2a_tool_actions__[attr.__name__] = attr
                elif issubclass(attr, Action):
                    cls.__child_actions__[attr.__name__] = attr

    async def pre_a2a(self, context: TContext) -> ActionReturn:
        """Execute pre a2a process."""
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
                self.__has_pre_a2a__
                and (result := await self.pre_a2a(context)).is_break
            ):
                return result

            async with multi_a2a_clients(
                context.integrations, self.__a2a_connections__
            ) as clients:
                self.__a2a_clients__ = clients

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
            await client.patch_tools(normal_tools, self.__a2a_tool_actions__)
            for client in self.__a2a_clients__.values()
        ]
        return normal_tools

    ####################################################################################################
    #                                          A2AACTION TOOLS                                         #
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

        if issubclass(action, A2AToolAction):
            cls.__a2a_tool_actions__[name] = action
        else:
            cls.__child_actions__[name] = action
        setattr(cls, name, action)


class A2AToolAction(Action):
    """A2A Tool Action."""

    __a2a_client__: AsyncClient
    __a2a_tool_name__: str
    __a2a_exclude_unset__: bool

    async def pre(self, context: TContext) -> ActionReturn:
        """Execute pre process."""
        tool_args = self.model_dump(exclude_unset=self.__a2a_exclude_unset__)
        await context.notify(
            {
                "event": "a2a-call-tool",
                "class": self.__class__.__name__,
                "type": self.__a2a_tool_name__,
                "status": "started",
                "data": tool_args,
            }
        )
        result = await self.__a2a_client__.call_tool(
            self.__a2a_tool_name__,
            tool_args,
            progress_callback=self.build_progress_callback(context),
        )

        content = "\n\n---\n\n".join(self.clean_content(c) for c in result.content)

        await context.notify(
            {
                "event": "a2a-call-tool",
                "class": self.__class__.__name__,
                "type": self.__a2a_tool_name__,
                "status": "completed",
                "data": content,
            }
        )
        await context.add_response(self, content)

        return ActionReturn.GO


@asynccontextmanager
async def multi_a2a_clients(
    integrations: dict[str, A2AIntegration],
    connections: list[A2AConnection],
    bypass: bool = False,
) -> AsyncGenerator[dict[str, A2AClient], None]:
    """Connect to multiple streamable clients."""
    async with AsyncExitStack() as stack:
        clients: dict[str, A2AClient] = {}
        for conn in connections:
            integration: A2AIntegration | None = integrations.get(conn.name)
            if not bypass and (conn.require_integration and integration is None):
                continue

            if integration is None:
                integration = {}

            _allowed_tools = integration.get("allowed_tools") or set[str]()
            if conn.allowed_tools:
                allowed_tools = set(
                    {tool for tool in _allowed_tools if tool in conn.allowed_tools}
                    if _allowed_tools
                    else conn.allowed_tools
                )
            else:
                allowed_tools = _allowed_tools

            overrided_config = conn.get_config(integration.get("config"))

            clients[conn.name] = A2AClient(
                await stack.enter_async_context(
                    AsyncClient(
                        base_url=overrided_config["base_url"],
                        headers=overrided_config["headers"],
                    )
                ),
                conn.name,
                overrided_config,
                allowed_tools,
                exclude_unset=integration.get(
                    "exclude_unset",
                    conn.exclude_unset,
                ),
            )

        yield clients


async def mount_a2a_groups(app: AppType, stack: AsyncExitStack) -> None:
    """Start A2A Servers."""
    queue = Action.__subclasses__()
    while queue:
        que = queue.pop()
        if que.__groups__ and (a2a_groups := que.__groups__.get("a2a")):
            entry = build_a2a_entry(que)
            for group in a2a_groups:
                await add_a2a_server(group.lower(), que, entry)
        queue.extend(que.__subclasses__())

    for server, a2a in A2AAction.__a2a_servers__.items():
        app.mount(f"/{server}", a2a.streamable_http_app())
        await stack.enter_async_context(a2a.session_manager.run())


def build_a2a_entry(action: type["Action"]) -> Callable[..., Awaitable[str]]:
    """Build A2A Entry."""
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


async def add_a2a_server(
    group: str, action: type["Action"], entry: Callable[..., Awaitable[str]]
) -> None:
    """Add action."""
    if not (server := A2AAction.__a2a_servers__.get(group)):
        server = A2AAction.__a2a_servers__[group] = FastA2A(
            f"a2a-{group}",
            stateless_http=True,
            log_level=getenv("A2A_LOGGER_LEVEL", "WARNING"),  # type: ignore[arg-type]
        )
    server.add_tool(entry, action.__name__, getdoc(action))


##########################################################################
#                           A2AAction Utilities                          #
##########################################################################


async def graph(
    action: type[Action],
    allowed_actions: dict[str, bool] | None = None,
    integrations: dict[str, A2AIntegration] | None = None,
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
    integrations: dict[str, A2AIntegration],
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

    if issubclass(action, A2AAction):
        async with multi_a2a_clients(
            integrations, action.__a2a_connections__, bypass
        ) as clients:
            [
                await client.patch_tools(child_actions, action.__a2a_tool_actions__)
                for client in clients.values()
            ]

    for child_action in child_actions.values():
        node = f"{child_action.__module__}.{child_action.__qualname__}"
        graph.edges.add((parent, node, child_action.__concurrent__))
        if node not in graph.nodes:
            graph.nodes.add(node)
            await traverse(graph, child_action, allowed_actions, integrations, bypass)
