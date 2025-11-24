"""Pybotchi MCP Context."""

from copy import deepcopy
from typing import Any, Generic, TypeVar

from pydantic import Field

from .common import MCPIntegration
from ..context import Context, TLLM

TContext = TypeVar("TContext", bound="MCPContext")


class MCPContext(Context[TLLM], Generic[TLLM]):
    """MCP Context."""

    integrations: dict[str, MCPIntegration] = Field(default_factory=dict)

    def detached_kwargs(self, **kwargs: Any) -> dict[str, Any]:
        """Retrieve detached kwargs."""
        return super().detached_kwargs(integrations=deepcopy(self.integrations))
