"""Pybotchi MCP Common."""

from collections.abc import Callable, Mapping, Sequence
from enum import StrEnum
from typing import Any, Literal, TypedDict

from httpx import Auth
from httpx._types import CertTypes, PrimitiveData

from mcp.client.streamable_http import McpHttpClientFactory, create_mcp_http_client


class MCPMode(StrEnum):
    """MCP Mode."""

    SSE = "SSE"
    SHTTP = "SHTTP"


######################################################################
#         need to improve this to make it more serializable.         #
######################################################################
class AsyncClientArgs(TypedDict, total=False):
    """Async Client Config."""

    auth: tuple[str | bytes, str | bytes] | None
    params: (
        Mapping[str, PrimitiveData | Sequence[PrimitiveData]]
        | list[tuple[str, PrimitiveData]]
        | tuple[tuple[str, PrimitiveData], ...]
        | str
        | bytes
        | None
    )
    headers: (
        Mapping[str, str]
        | Mapping[bytes, bytes]
        | Sequence[tuple[str, str]]
        | Sequence[tuple[bytes, bytes]]
        | None
    )
    cookies: dict[str, str] | list[tuple[str, str]] | None
    verify: str | bool
    cert: CertTypes | None
    http1: bool
    http2: bool
    proxy: str | None
    timeout: (
        float
        | None
        | tuple[float | None, float | None, float | None, float | None]
        | None
    )
    max_redirects: int
    base_url: str
    trust_env: bool
    default_encoding: str


class MCPConfig(TypedDict, total=False):
    """MCP Config."""

    url: str
    headers: dict[str, str] | None
    timeout: float
    sse_read_timeout: float
    terminate_on_close: bool
    httpx_client_factory: Any
    auth: Any
    async_client_args: AsyncClientArgs


class MCPIntegration(TypedDict, total=False):
    """MCP Integration."""

    mode: MCPMode | Literal["SSE", "SHTTP"]
    config: MCPConfig
    allowed_tools: dict[str, bool]
    exclude_unset: bool


class MCPConnection:
    """MCP Connection configurations."""

    def __init__(
        self,
        name: str,
        mode: MCPMode | Literal["SSE", "SHTTP"],
        url: str = "",
        headers: dict[str, str] | None = None,
        timeout: float = 5.0,
        sse_read_timeout: float = 300.0,
        terminate_on_close: bool = True,
        httpx_client_factory: McpHttpClientFactory = create_mcp_http_client,
        auth: Auth | None = None,
        on_session_created: Callable[[str], None] | None = None,
        async_client_args: AsyncClientArgs | None = None,
        manual_enable: bool = False,
        allowed_tools: dict[str, bool] | None = None,
        exclude_unset: bool = True,
        require_integration: bool = True,
    ) -> None:
        """Build MCP Connection."""
        self.name = name
        self.mode = mode
        self.url = url
        self.headers = headers
        self.timeout = timeout
        self.sse_read_timeout = sse_read_timeout
        self.terminate_on_close = terminate_on_close
        self.httpx_client_factory = httpx_client_factory
        self.auth = auth
        self.on_session_created = on_session_created
        self.async_client_args: AsyncClientArgs = (
            {} if async_client_args is None else async_client_args
        )
        self.manual_enable = manual_enable
        self.allowed_tools = {} if allowed_tools is None else allowed_tools
        self.exclude_unset = exclude_unset
        self.require_integration = require_integration

    def get_config(self, override: MCPConfig | None) -> MCPConfig:
        """Generate config."""
        if override is None:
            return {
                "url": self.url,
                "headers": self.headers,
                "timeout": self.timeout,
                "sse_read_timeout": self.sse_read_timeout,
                "terminate_on_close": self.terminate_on_close,
                "httpx_client_factory": self.httpx_client_factory,
                "auth": self.auth,
                "async_client_args": self.async_client_args,
            }

        url = override.get("url", self.url)

        headers: dict[str, str] | None
        if _headers := override.get("headers"):
            if self.headers is None:
                headers = _headers
            else:
                headers = self.headers | _headers
        else:
            headers = self.headers

        timeout = override.get("timeout", self.timeout)
        sse_read_timeout = override.get("sse_read_timeout", self.sse_read_timeout)
        terminate_on_close = override.get("terminate_on_close", self.terminate_on_close)
        httpx_client_factory = override.get(
            "httpx_client_factory", self.httpx_client_factory
        )
        auth = override.get("auth", self.auth)

        if _async_client_args := override.get("async_client_args"):
            async_client_args = self.async_client_args | _async_client_args
        else:
            async_client_args = self.async_client_args

        return {
            "url": url,
            "headers": headers,
            "timeout": timeout,
            "sse_read_timeout": sse_read_timeout,
            "terminate_on_close": terminate_on_close,
            "httpx_client_factory": httpx_client_factory,
            "auth": auth,
            "async_client_args": async_client_args,
        }
