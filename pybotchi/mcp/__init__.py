"""Pybotchi MCP."""

try:
    from .action import MCPAction, MCPToolAction, graph, mount_mcp_groups
    from .common import MCPConfig, MCPConnection, MCPIntegration, MCPMode
    from .context import MCPContext

    __all__ = [
        "MCPAction",
        "MCPToolAction",
        "graph",
        "mount_mcp_groups",
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
