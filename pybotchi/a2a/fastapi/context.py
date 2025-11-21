"""Pybotchi A2A Context."""

from copy import deepcopy
from typing import Any, Generic, TypeVar

from pydantic import Field

from .common import A2AIntegration
from ...context import Context, TLLM

TContext = TypeVar("TContext", bound="A2AContext")


class A2AContext(Context[TLLM], Generic[TLLM]):
    """A2A Context."""

    integrations: dict[str, A2AIntegration] = Field(default_factory=dict)

    def detached_kwargs(self, **kwargs: Any) -> dict[str, Any]:
        """Retrieve detached kwargs."""
        return super().detached_kwargs(integrations=deepcopy(self.integrations))
