"""Pybotchi GRPC Context."""

from copy import deepcopy
from typing import Any, Generic, TypeVar

from pydantic import Field

from .common import GRPCIntegration
from ..context import Context, TLLM


TContext = TypeVar("TContext", bound="GRPCContext")


class GRPCContext(Context[TLLM], Generic[TLLM]):
    """GRPC Context."""

    integrations: dict[str, GRPCIntegration] = Field(default_factory=dict)

    def detached_kwargs(self, **kwargs: Any) -> dict[str, Any]:
        """Retrieve detached kwargs."""
        return super().detached_kwargs(integrations=deepcopy(self.integrations))
