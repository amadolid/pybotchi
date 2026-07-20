"""Pybotchi MCP Context."""

from copy import deepcopy
from typing import Any, TypeVar

from mcp.server.fastmcp import Context as FastMCPContext

from pydantic import Field, PrivateAttr

from .common import MCPIntegration
from ..context import Context, TLLM
from ..utils import uuid


TContext = TypeVar("TContext", bound="MCPContext")


class MCPContext(Context[TLLM]):
    """MCP Context."""

    integrations: dict[str, MCPIntegration] = Field(default_factory=dict)

    source_id: str | None = Field(default=None)
    context_id: str = Field(default_factory=lambda: str(uuid()))

    _request_context: FastMCPContext | None = PrivateAttr(None)

    def mcp_dump(self) -> dict[str, Any]:
        """Dump model for mcp."""
        return self.model_dump(mode="json")

    def mcp_sharing_dump(self) -> dict[str, Any]:
        """Dump model for MCP sharing."""
        dump = self.model_dump(mode="json", exclude={"source_id", "context_id"})
        dump["source_id"] = self.context_id
        dump["context_id"] = str(uuid())
        return dump

    def detached_kwargs(self, **kwargs: Any) -> dict[str, Any]:
        """Retrieve detached kwargs."""
        return super().detached_kwargs(integrations=deepcopy(self.integrations))
