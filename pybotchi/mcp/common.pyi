from .action import MCPToolAction as MCPToolAction
from _typeshed import Incomplete
from collections.abc import Callable as Callable, Mapping, Sequence
from enum import StrEnum
from httpx import Auth as Auth
from httpx._types import CertTypes as CertTypes, PrimitiveData as PrimitiveData
from mcp.client.streamable_http import McpHttpClientFactory as McpHttpClientFactory
from typing import Any, Literal, TypedDict

class MCPMode(StrEnum):
    SSE = 'SSE'
    SHTTP = 'SHTTP'

class AsyncClientArgs(TypedDict, total=False):
    auth: tuple[str | bytes, str | bytes] | None
    params: Mapping[str, PrimitiveData | Sequence[PrimitiveData]] | list[tuple[str, PrimitiveData]] | tuple[tuple[str, PrimitiveData], ...] | str | bytes | None
    headers: Mapping[str, str] | Mapping[bytes, bytes] | Sequence[tuple[str, str]] | Sequence[tuple[bytes, bytes]] | None
    cookies: dict[str, str] | list[tuple[str, str]] | None
    verify: str | bool
    cert: CertTypes | None
    http1: bool
    http2: bool
    proxy: str | None
    timeout: float | None | tuple[float | None, float | None, float | None, float | None] | None
    max_redirects: int
    base_url: str
    trust_env: bool
    default_encoding: str

class MCPConfig(TypedDict, total=False):
    url: str
    headers: dict[str, str] | None
    timeout: float
    sse_read_timeout: float
    terminate_on_close: bool
    httpx_client_factory: Any
    auth: Any
    async_client_args: AsyncClientArgs

class MCPIntegration(TypedDict, total=False):
    mode: MCPMode | Literal['SSE', 'SHTTP']
    config: MCPConfig
    allowed_tools: dict[str, bool]
    exclude_unset: bool

class MCPConnection:
    name: Incomplete
    mode: Incomplete
    url: Incomplete
    headers: Incomplete
    timeout: Incomplete
    sse_read_timeout: Incomplete
    terminate_on_close: Incomplete
    httpx_client_factory: Incomplete
    auth: Incomplete
    on_session_created: Incomplete
    async_client_args: AsyncClientArgs
    manual_enable: Incomplete
    allowed_tools: Incomplete
    tool_action_class: Incomplete
    exclude_unset: Incomplete
    require_integration: Incomplete
    def __init__(self, name: str, mode: MCPMode | Literal['SSE', 'SHTTP'], url: str = '', headers: dict[str, str] | None = None, timeout: float = 5.0, sse_read_timeout: float = 300.0, terminate_on_close: bool = True, httpx_client_factory: McpHttpClientFactory = ..., auth: Auth | None = None, on_session_created: Callable[[str], None] | None = None, async_client_args: AsyncClientArgs | None = None, manual_enable: bool = False, allowed_tools: dict[str, bool] | None = None, tool_action_class: type['MCPToolAction'] | None = None, exclude_unset: bool = True, require_integration: bool = True) -> None: ...
    def get_config(self, override: MCPConfig | None) -> MCPConfig: ...
