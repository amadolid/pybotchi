"""Pybotchi MCP Common."""

from datetime import timedelta
from enum import StrEnum
from typing import Any, Literal, TypedDict

from httpx import Auth

from mcp.client.streamable_http import McpHttpClientFactory, create_mcp_http_client


class MCPMode(StrEnum):
    """MCP Mode."""

    SSE = "SSE"
    SHTTP = "SHTTP"


class MCPConfig(TypedDict, total=False):
    """MCP Config."""

    url: str
    headers: dict[str, str] | None
    timeout: float | timedelta
    sse_read_timeout: float | timedelta
    terminate_on_close: bool
    httpx_client_factory: Any
    auth: Any


class MCPIntegration(TypedDict, total=False):
    """MCP Integration."""

    mode: MCPMode | Literal["SSE", "SHTTP"]
    config: MCPConfig
    allowed_tools: set[str]
    exclude_unset: bool


class MCPConnection:
    """MCP Connection configurations."""

    def __init__(
        self,
        name: str,
        mode: MCPMode | Literal["SSE", "SHTTP"],
        url: str = "",
        headers: dict[str, str] | None = None,
        timeout: float | timedelta = 30.0,
        sse_read_timeout: float | timedelta = 300.0,
        terminate_on_close: bool = True,
        httpx_client_factory: McpHttpClientFactory = create_mcp_http_client,
        auth: Auth | None = None,
        allowed_tools: set[str] | None = None,
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
        self.allowed_tools = set[str]() if allowed_tools is None else allowed_tools
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
            }

        url = override.get("url", self.url)
        timeout = override.get("timeout", self.timeout)
        sse_read_timeout = override.get("sse_read_timeout", self.sse_read_timeout)
        terminate_on_close = override.get("terminate_on_close", self.terminate_on_close)
        httpx_client_factory = override.get(
            "httpx_client_factory", self.httpx_client_factory
        )
        auth = override.get("auth", self.auth)

        headers: dict[str, str] | None
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
