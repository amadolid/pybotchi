"""Pybotchi MCP."""

try:
    from .action import MCPAction, MCPToolAction, build_mcp_app, graph, mount_mcp_app
    from .common import MCPConfig, MCPConnection, MCPIntegration, MCPMode
    from .context import MCPContext

    __all__ = [
        "MCPAction",
        "MCPToolAction",
        "build_mcp_app",
        "graph",
        "mount_mcp_app",
        "MCPConfig",
        "MCPConnection",
        "MCPIntegration",
        "MCPMode",
        "MCPContext",
    ]
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        """MCP feature not installed. Please install pybotchi with the `mcp` extra dependency.
Try: pip install pybotchi[mcp]
From Source: poetry install --extras mcp"""
    ) from e
