from ..context import Context as Context, TLLM as TLLM
from .common import MCPIntegration as MCPIntegration
from typing import Any, Generic, TypeVar

TContext = TypeVar('TContext', bound='MCPContext')

class MCPContext(Context[TLLM], Generic[TLLM]):
    integrations: dict[str, MCPIntegration]
    def detached_kwargs(self, **kwargs: Any) -> dict[str, Any]: ...
