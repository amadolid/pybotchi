"""Pybotchi MCP Classes."""

from collections.abc import AsyncGenerator, Awaitable
from contextlib import AsyncExitStack, asynccontextmanager, suppress
from inspect import getdoc, getmembers
from itertools import islice
from os import getenv
from typing import Any, Callable, Generic, Literal

from datamodel_code_generator import DataModelType, PythonVersion
from datamodel_code_generator.model import get_data_model_types
from datamodel_code_generator.parser.base import title_to_class_name
from datamodel_code_generator.parser.jsonschema import (
    JsonSchemaParser,
)

from httpx import AsyncClient

from mcp import ClientSession, Tool
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client
from mcp.server.fastmcp import FastMCP
from mcp.shared.session import ProgressFnT
from mcp.types import (
    AudioContent,
    ContentBlock,
    EmbeddedResource,
    ImageContent,
    ResourceLink,
    TextContent,
    TextResourceContents,
)

from orjson import dumps, loads

from starlette.applications import AppType

from .common import MCPConfig, MCPConnection, MCPIntegration, MCPMode
from .context import TContext
from ..action import Action, ChildActions
from ..common import ActionReturn, ChatRole, Graph
from ..utils import is_camel_case, unwrap_exceptions

DMT = get_data_model_types(
    DataModelType.PydanticV2BaseModel,
    target_python_version=PythonVersion.PY_313,
)


class MCPClient:
    """MCP Client."""

    def __init__(
        self,
        session: ClientSession,
        name: str,
        config: MCPConfig,
        manual_enable: bool,
        allowed_tools: dict[str, bool],
        tool_action_class: type["MCPToolAction"] | None,
        exclude_unset: bool,
    ) -> None:
        """Build MCP Client."""
        self.session = session
        self.name = name
        self.config = config
        self.manual_enable = manual_enable
        self.allowed_tools = allowed_tools
        self.tool_action_class = tool_action_class or MCPToolAction
        self.exclude_unset = exclude_unset

    def build_tool(self, tool: Tool) -> tuple[str, type["MCPToolAction"]]:
        """Build MCPToolAction."""
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
                self.tool_action_class,
            ),
            {
                "__mcp_tool_name__": tool.name,
                "__mcp_client__": self,
                "__mcp_exclude_unset__": getattr(
                    base_class, "__mcp_exclude_unset__", self.exclude_unset
                ),
                "__module__": f"mcp.{self.name}",
            },
        )

        if desc := tool.description:
            action.__doc__ = desc

        return class_name, action

    async def patch_tools(
        self, actions: ChildActions, mcp_actions: ChildActions
    ) -> ChildActions:
        """Retrieve Tools."""
        response = await self.session.list_tools()
        for tool in response.tools:
            name, action = self.build_tool(tool)
            if _tool := mcp_actions.get(name):
                action = type(
                    name,
                    (_tool, action),
                    {"__module__": f"mcp.{self.name}.patched"},
                )

            if not self.allowed_tools or self.allowed_tools.get(
                name, False if self.manual_enable else action.__enabled__
            ):
                actions[name] = action
        return actions


class MCPAction(Action[TContext], Generic[TContext]):
    """MCP Action."""

    __mcp_servers__: dict[str, FastMCP] = {}

    __mcp_clients__: dict[str, MCPClient]
    __mcp_connections__: list[MCPConnection]
    __mcp_tool_actions__: ChildActions

    # --------------------- not inheritable -------------------- #

    __has_pre_mcp__: bool

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """Override __pydantic_init_subclass__."""
        super().__pydantic_init_subclass__(**kwargs)
        cls.__has_pre_mcp__ = cls.pre_mcp is not MCPAction.pre_mcp

    @classmethod
    def __init_child_actions__(cls) -> None:
        """Initialize defined child actions."""
        cls.__mcp_tool_actions__ = {}
        cls.__child_actions__ = {}
        for name, child in getmembers(cls):
            if isinstance(child, type):
                if getattr(child, "__mcp_tool__", False):
                    cls.__mcp_tool_actions__[name] = child
                elif issubclass(child, Action):
                    cls.__child_actions__[name] = child

    async def pre_mcp(self, context: TContext) -> ActionReturn:
        """Execute pre mcp process."""
        return ActionReturn.GO

    async def execute(
        self, context: TContext, parent: Action | None = None
    ) -> ActionReturn:
        """Execute main process."""
        self._parent = parent
        parent_context = context
        try:
            if parent:
                parent._actions.append(self)

            if self.__detached__:
                context = await context.detach_context()

            if context.check_self_recursion(self):
                return ActionReturn.END

            if (
                self.__has_pre_mcp__
                and (result := await self.pre_mcp(context)).is_break
            ):
                return result

            async with multi_mcp_clients(
                context.integrations, self.__mcp_connections__
            ) as clients:
                self.__mcp_clients__ = clients

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
                raise next(unwrap_exceptions(exception))
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

        for client in self.__mcp_clients__.values():
            await client.patch_tools(normal_tools, self.__mcp_tool_actions__)

        return normal_tools

    ####################################################################################################
    #                                          MCPACTION TOOLS                                         #
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

        if issubclass(action, MCPToolAction):
            cls.__mcp_tool_actions__[name] = action
        else:
            cls.__child_actions__[name] = action
        setattr(cls, name, action)


class MCPToolAction(Action[TContext], Generic[TContext]):
    """MCP Tool Action."""

    __mcp_tool__ = True

    __mcp_client__: MCPClient
    __mcp_tool_name__: str
    __mcp_exclude_unset__: bool

    def build_progress_callback(self, context: TContext) -> ProgressFnT:
        """Generate progress callback function."""

        async def progress_callback(
            progress: float, total: float | None, message: str | None
        ) -> None:
            await context.notify(
                {
                    "event": "mcp-call-tool",
                    "class": self.__class__.__name__,
                    "type": self.__mcp_tool_name__,
                    "status": "inprogress",
                    "data": {"progress": progress, "total": total, "message": message},
                }
            )

        return progress_callback

    def clean_content(self, content: ContentBlock) -> str:
        """Clean text if json."""
        match content:
            case AudioContent():
                return f'<audio controls>\n\t<source src="data:{content.mimeType};base64,{content.data}" type="{content.mimeType}">\n</audio>'
            case ImageContent():
                return f'<img src="data:{content.mimeType};base64,{content.data}">'
            case TextContent():
                with suppress(Exception):
                    return dumps(loads(content.text.strip().encode())).decode()
                return content.text
            case EmbeddedResource():
                if isinstance(resource := content.resource, TextResourceContents):
                    return f'<a href="{resource.uri}">\n{resource.text}\n</a>'
                else:
                    mime = (
                        resource.mimeType.lower().split("/")
                        if resource.mimeType
                        else None
                    )
                    source = f'<source src="data:{resource.mimeType};base64,{resource.blob}" type="{resource.mimeType}">'
                    match mime:
                        case "video":
                            return f"<video controls>\n\t{source}\n</video>"
                        case "audio":
                            return f"<audio controls>\n\t{source}\n</audio>"
                        case _:
                            return source
            case ResourceLink():
                description = (
                    f"\n{content.description}\n" if content.description else ""
                )
                return f'<a href="{content.uri}">{description}</a>'
            case _:
                return f"The response of {self.__class__.__name__} is yet supported: {content.__class__.__name__}"

    async def pre(self, context: TContext) -> ActionReturn:
        """Execute pre process."""
        tool_args = self.model_dump(exclude_unset=self.__mcp_exclude_unset__)
        await context.notify(
            {
                "event": "mcp-call-tool",
                "class": self.__class__.__name__,
                "type": self.__mcp_tool_name__,
                "status": "started",
                "data": tool_args,
            }
        )
        result = await self.__mcp_client__.session.call_tool(
            self.__mcp_tool_name__,
            tool_args,
            progress_callback=self.build_progress_callback(context),
        )

        content = "\n\n---\n\n".join(self.clean_content(c) for c in result.content)

        await context.notify(
            {
                "event": "mcp-call-tool",
                "class": self.__class__.__name__,
                "type": self.__mcp_tool_name__,
                "status": "completed",
                "data": content,
            }
        )
        await context.add_response(self, content)

        return ActionReturn.GO


@asynccontextmanager
async def multi_mcp_clients(
    integrations: dict[str, MCPIntegration],
    connections: list[MCPConnection],
    bypass: bool = False,
) -> AsyncGenerator[dict[str, MCPClient], None]:
    """Connect to multiple mcp clients."""
    async with AsyncExitStack() as stack:
        clients: dict[str, MCPClient] = {}
        for conn in connections:
            integration: MCPIntegration | None = integrations.get(conn.name)
            if not bypass and (conn.require_integration and integration is None):
                continue

            if integration is None:
                integration = {}

            overrided_config = conn.get_config(integration.get("config"))
            if _allowed_tools := integration.get("allowed_tools"):
                allowed_tools = conn.allowed_tools | _allowed_tools
            elif _allowed_tools is not None:
                allowed_tools = {}
            else:
                allowed_tools = conn.allowed_tools

            if integration.get("mode", conn.mode) == MCPMode.SSE:
                overrided_config.pop("terminate_on_close", None)
                streams = await stack.enter_async_context(
                    sse_client(
                        url=overrided_config["url"],
                        headers=overrided_config["headers"],
                        timeout=overrided_config["timeout"],
                        sse_read_timeout=overrided_config["sse_read_timeout"],
                        httpx_client_factory=overrided_config["httpx_client_factory"],
                        auth=overrided_config["auth"],
                        on_session_created=conn.on_session_created,
                    )
                )
            else:
                async_client = await stack.enter_async_context(
                    AsyncClient(
                        **overrided_config["async_client_args"], follow_redirects=True
                    )
                )

                streams = await stack.enter_async_context(
                    streamable_http_client(
                        url=overrided_config["url"],
                        http_client=async_client,
                        terminate_on_close=overrided_config["terminate_on_close"],
                    )
                )

            session = await stack.enter_async_context(
                ClientSession(*islice(streams, 0, 2))
            )
            await session.initialize()
            clients[conn.name] = MCPClient(
                session,
                conn.name,
                overrided_config,
                conn.manual_enable,
                allowed_tools,
                conn.tool_action_class,
                integration.get(
                    "exclude_unset",
                    conn.exclude_unset,
                ),
            )

        yield clients


def initialize_mcp_groups() -> None:
    """Initialize MCP groups."""
    queue = Action.__subclasses__()
    while queue:
        que = queue.pop()
        if isinstance(_groups := que.__groups__, dict):
            _groups = _groups.get("mcp")

        if _groups:
            entry = build_mcp_entry(que)
            for group in _groups:
                add_mcp_server(group.lower(), que, entry)

        queue.extend(que.__subclasses__())


async def mount_mcp_groups(app: AppType, stack: AsyncExitStack) -> None:
    """Start MCP Servers."""
    initialize_mcp_groups()

    for server, mcp in MCPAction.__mcp_servers__.items():
        app.mount(f"/{server}", mcp.streamable_http_app())
        await stack.enter_async_context(mcp.session_manager.run())


def run_mcp(
    group: str,
    transport: Literal["stdio", "sse", "streamable-http"] = "streamable-http",
) -> None:
    """Start MCP server by group."""
    initialize_mcp_groups()

    if not (server := MCPAction.__mcp_servers__.get(group)):
        raise ValueError(f"Group `{group}` is not available!")

    server.run(transport)


def build_mcp_entry(action: type["Action"]) -> Callable[..., Awaitable[str]]:
    """Build MCP Entry."""
    from .context import Context

    async def process(data: dict[str, Any]) -> str:
        context = Context(
            prompts=[
                {
                    "role": ChatRole.SYSTEM,
                    "content": action.__system_prompt__ or getdoc(action) or "",
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


def add_mcp_server(
    group: str, action: type["Action"], entry: Callable[..., Awaitable[str]]
) -> None:
    """Add action."""
    if not (server := MCPAction.__mcp_servers__.get(group)):
        server = MCPAction.__mcp_servers__[group] = FastMCP(
            f"mcp-{group}",
            stateless_http=True,
            log_level=getenv("MCP_LOGGER_LEVEL", "WARNING"),  # type: ignore[arg-type]
        )
    server.add_tool(entry, action.__name__, action.__display_name__, getdoc(action))


##########################################################################
#                           MCPAction Utilities                          #
##########################################################################


async def graph(
    action: type[Action],
    allowed_actions: dict[str, bool] | None = None,
    integrations: dict[str, MCPIntegration] | None = None,
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
    integrations: dict[str, MCPIntegration],
    bypass: bool = False,
) -> None:
    """Retrieve Graph."""
    current = f"{action.__module__}.{action.__qualname__}"

    if allowed_actions:
        child_actions = {
            name: child
            for name, child in action.__child_actions__.items()
            if allowed_actions.get(name, child.__enabled__)
        }
    else:
        child_actions = action.__child_actions__.copy()

    if issubclass(action, MCPAction):
        async with multi_mcp_clients(
            integrations, action.__mcp_connections__, bypass
        ) as clients:
            [
                await client.patch_tools(child_actions, action.__mcp_tool_actions__)
                for client in clients.values()
            ]

    for child_action in child_actions.values():
        child = f"{child_action.__module__}.{child_action.__qualname__}"
        graph.edges.add(
            (
                current,
                child,
                child_action.__concurrent__,
                (
                    child_action.__mcp_client__.name
                    if issubclass(child_action, MCPToolAction)
                    else ""
                ),
            )
        )

        if child not in graph.nodes:
            graph.nodes.add(child)
            await traverse(graph, child_action, allowed_actions, integrations, bypass)
