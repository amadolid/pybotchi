"""Pybotchi A2A FastAPI."""

try:
    from .action import A2AAction, A2AToolAction, graph, mount_a2a_groups
    from .common import A2AConfig, A2AConnection, A2AIntegration
    from .context import A2AContext

    __all__ = [
        "A2AAction",
        "A2AToolAction",
        "graph",
        "mount_a2a_groups",
        "A2AConfig",
        "A2AConnection",
        "A2AIntegration",
        "A2AContext",
    ]
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        """A2A FastAPI feature not installed. Please install pybotchi with the `a2a-fastapi` extra dependency.
Try: pip install pybotchi[a2a-fastapi]
From Source: poetry install --extras a2a-fastapi"""
    ) from e
