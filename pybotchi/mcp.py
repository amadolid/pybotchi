"""Pybotchi MCP Classes."""

from collections.abc import AsyncGenerator, Awaitable
from contextlib import AsyncExitStack, asynccontextmanager, suppress
from datetime import timedelta
from inspect import getdoc
from os import getenv
from typing import Any, Callable, TYPE_CHECKING

from datamodel_code_generator import DataModelType, PythonVersion
from datamodel_code_generator.model import get_data_model_types
from datamodel_code_generator.parser.base import title_to_class_name
from datamodel_code_generator.parser.jsonschema import (
    JsonSchemaParser,
)

from fastapi import FastAPI

from httpx import Auth

from mcp import ClientSession, Tool
from mcp.client.streamable_http import (
    McpHttpClientFactory,
    create_mcp_http_client,
    streamablehttp_client,
)
from mcp.server.fastmcp import FastMCP
from mcp.shared.session import ProgressFnT
from mcp.types import ContentBlock, TextContent

from orjson import dumps, loads

from .action import Action, ActionReturn, ChildActions
from .constants import ChatRole

if TYPE_CHECKING:
    from .context import Context


DMT = get_data_model_types(
    DataModelType.PydanticV2BaseModel,
    target_python_version=PythonVersion.PY_313,
)


class MCPClient:
    """MCP Client."""

    def __init__(
        self,
        name: str,
        kwargs: dict[str, Any],
        allowed_tools: set[str],
        client: ClientSession,
    ) -> None:
        """Build MCP Client."""
        self.name = name
        self.kwargs = kwargs
        self.allowed_tools = allowed_tools
        self.client = client

    def build_tool(self, tool: Tool) -> tuple[str, type[Action]]:
        """Build MCPToolAction."""
        globals: dict[str, Any] = {}
        class_name = title_to_class_name(tool.name)
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
            globals=globals,
        )
        action = type(
            class_name,
            (
                globals[class_name],
                MCPToolAction,
            ),
            {
                "__mcp_tool_name__": tool.name,
                "__mcp_client__": self.client,
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
        response = await self.client.list_tools()
        for tool in response.tools:
            name, action = self.build_tool(tool)
            if not self.allowed_tools or name in self.allowed_tools:
                if _tool := mcp_actions.get(name):
                    action = type(
                        name,
                        (_tool, action),
                        {"__module__": f"mcp.{self.name}.patched"},
                    )
                actions[name] = action
        return actions


class MCPConnection:
    """MCP Connection configurations."""

    def __init__(
        self,
        name: str,
        url: str = "",
        headers: dict[str, Any] | None = None,
        timeout: timedelta = timedelta(seconds=30),
        sse_read_timeout: timedelta = timedelta(seconds=60 * 5),
        terminate_on_close: bool = True,
        httpx_client_factory: McpHttpClientFactory = create_mcp_http_client,
        auth: Auth | None = None,
        allowed_tools: set[str] | None = None,
        require_integration: bool = True,
    ) -> None:
        """Build MCP Connection."""
        self.name = name
        self.url = url
        self.headers = headers
        self.timeout = timeout
        self.sse_read_timeout = sse_read_timeout
        self.terminate_on_close = terminate_on_close
        self.httpx_client_factory = httpx_client_factory
        self.auth = auth
        self.allowed_tools: set[str] = set() if allowed_tools is None else allowed_tools
        self.require_integration = require_integration

    def get_kwargs(self, override: dict[str, Any]) -> dict[str, Any]:
        """Generate config."""
        url = override.get("url", self.url)
        timeout = override.get("timeout", self.timeout)
        sse_read_timeout = override.get("sse_read_timeout", self.sse_read_timeout)
        terminate_on_close = override.get("terminate_on_close", self.terminate_on_close)
        httpx_client_factory = override.get(
            "httpx_client_factory", self.httpx_client_factory
        )
        auth = override.get("auth", self.auth)

        if _headers := override.get("headers"):
            if self.headers is None:
                headers = _headers
            else:
                headers = self.headers | _headers
        else:
            headers = self.headers

        return {
            "url": url,
            "headers": headers,
            "timeout": timeout,
            "sse_read_timeout": sse_read_timeout,
            "terminate_on_close": terminate_on_close,
            "httpx_client_factory": httpx_client_factory,
            "auth": auth,
        }


class MCPAction(Action):
    """MCP Tool Action."""

    __mcp_clients__: dict[str, MCPClient]
    __mcp_connections__: list[MCPConnection]

    async def execute(self, context: "Context") -> ActionReturn:
        """Execute main process."""
        parent = context
        to_commit = True
        try:
            if self.__detached__:
                context = await context.detach_context()

            if context.check_self_recursion(self):
                return ActionReturn.END

            async with multi_streamable_clients(
                context.integration, self.__mcp_connections__
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
        except Exception:
            to_commit = False
            raise
        finally:
            if to_commit and self.__detached__:
                await self.commit_context(parent, context)

    async def get_child_actions(self, context: "Context") -> ChildActions:
        """Retrieve child Actions."""
        normal_tools = await super().get_child_actions(context)
        [
            await client.patch_tools(normal_tools, self.__mcp_tool_actions__)
            for client in self.__mcp_clients__.values()
        ]
        return normal_tools


class MCPToolAction(Action):
    """MCP Tool Action."""

    __mcp_tool__ = True

    __mcp_client__: ClientSession
    __mcp_tool_name__: str

    def build_progress_callback(self, context: "Context") -> ProgressFnT:
        """Generate progress callback function."""
        tool_name = self.__class__.__name__
        event = f"mcp-{self.__mcp_tool_name__}"

        async def progress_callback(
            progress: float, total: float | None, message: str | None
        ) -> None:
            await context.notify(
                {
                    "event": event,
                    "type": tool_name,
                    "status": "inprogress",
                    "data": {"progress": progress, "total": total, "message": message},
                }
            )

        return progress_callback

    def clean_content(self, content: ContentBlock) -> ContentBlock:
        """Clean text if json."""
        if isinstance(content, TextContent):
            with suppress(Exception):
                if content.text:
                    content.text = dumps(loads(content.text.strip().encode())).decode()
        return content

    async def pre(self, context: "Context") -> ActionReturn:
        """Execute pre process."""
        tool_args = self.model_dump()
        event = f"mcp-{self.__mcp_tool_name__}"

        await context.notify(
            {
                "event": event,
                "type": self.__mcp_tool_name__,
                "status": "started",
                "data": tool_args,
            }
        )
        result = await self.__mcp_client__.call_tool(
            self.__mcp_tool_name__,
            tool_args,
            progress_callback=self.build_progress_callback(context),
        )
        content = dumps(
            [self.clean_content(c).model_dump() for c in result.content]
        ).decode()
        await context.notify(
            {
                "event": event,
                "type": self.__mcp_tool_name__,
                "status": "completed",
                "data": content,
            }
        )
        await context.add_response(self, content)

        return ActionReturn.GO


@asynccontextmanager
async def multi_streamable_clients(
    integration: dict[str, dict[str, Any]],
    connections: list[MCPConnection],
    bypass: bool = False,
) -> AsyncGenerator[dict[str, MCPClient], None]:
    """Connect to multiple streamable clients."""
    async with AsyncExitStack() as stack:
        clients: dict[str, MCPClient] = {}
        for conn in connections:
            config = integration.get(conn.name)
            if not bypass and (conn.require_integration and config is None):
                continue

            if config is None:
                config = {}

            kwargs = conn.get_kwargs(config or {})
            _allowed_tools: list[str] | None = config.get("allowed_tools")
            if conn.allowed_tools:
                allowed_tools = (
                    {tool for tool in _allowed_tools if tool in conn.allowed_tools}
                    if _allowed_tools
                    else conn.allowed_tools
                )
            elif _allowed_tools is None:
                allowed_tools = set[str]()
            else:
                allowed_tools = set(_allowed_tools)

            read_stream, write_stream, _ = await stack.enter_async_context(
                streamablehttp_client(**kwargs)
            )
            client = await stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await client.initialize()
            clients[conn.name] = MCPClient(conn.name, kwargs, allowed_tools, client)

        yield clients


async def start_mcp_servers(app: FastAPI, stack: AsyncExitStack) -> None:
    """Start MCP Servers."""
    queue = Action.__subclasses__()
    while queue:
        que = queue.pop()
        if que.__mcp_groups__:
            entry = build_mcp_entry(que)
            for group in que.__mcp_groups__:
                await add_mcp_server(group.lower(), que, entry)
        queue.extend(que.__subclasses__())

    for server, mcp in Action.__mcp_servers__.items():
        app.mount(f"/{server}", mcp.streamable_http_app())
        await stack.enter_async_context(mcp.session_manager.run())


def build_mcp_entry(action: type["Action"]) -> Callable[..., Awaitable[str]]:
    """Build MCP Entry."""
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


async def add_mcp_server(
    group: str, action: type["Action"], entry: Callable[..., Awaitable[str]]
) -> None:
    """Add action."""
    if not (server := Action.__mcp_servers__.get(group)):
        server = Action.__mcp_servers__[group] = FastMCP(
            f"mcp-{group}",
            stateless_http=True,
            log_level=getenv("MCP_LOGGER_LEVEL", "WARNING"),
        )
    server.add_tool(entry, action.__name__, getdoc(action))
