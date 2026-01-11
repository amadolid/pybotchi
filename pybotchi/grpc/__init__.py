"""Pybotchi GRPC."""

from sys import argv

try:
    from .action import GRPCAction, GRPCRemoteAction, graph
    from .common import GRPCConfig, GRPCConnection, GRPCIntegration
    from .context import GRPCContext

    __all__ = [
        "GRPCAction",
        "GRPCRemoteAction",
        "graph",
        "GRPCConfig",
        "GRPCConnection",
        "GRPCIntegration",
        "GRPCContext",
    ]
except TypeError:
    if not any(arg.endswith("pybotchi-grpc-compile") for arg in argv):
        raise
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        """GRPC feature not installed. Please install pybotchi with the `grpc` extra dependency.
Try: pip install pybotchi[grpc]
From Source: poetry install --extras grpc"""
    ) from e
