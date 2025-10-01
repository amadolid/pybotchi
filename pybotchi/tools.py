"""Pybotchi Tools."""

from collections import OrderedDict
from collections.abc import Generator

from .action import Action
from .constants import Graph
from .mcp import MCPAction, MCPIntegration, multi_streamable_clients


def all_agents() -> Generator[type["Action"]]:
    """Agent Generator."""
    queue: list[type[Action]] = [Action]
    while queue and (cls := queue.pop(0)):
        if cls.__agent__:
            yield cls

        for scls in cls.__subclasses__():
            queue.append(scls)


async def graph(
    action: type[Action],
    allowed_actions: dict[str, bool] | None = None,
    integrations: dict[str, MCPIntegration] | None = None,
    bypass: bool = False,
) -> str:
    """Retrieve Graph."""
    graph = Graph()
    graph.nodes.add(f"{action.__module__}.{action.__qualname__}")

    if allowed_actions is None:
        allowed_actions = {}

    if integrations is None:
        integrations = {}

    await traverse(graph, action, allowed_actions, integrations, bypass)

    content = ""
    for node in graph.nodes:
        content += f"{node}[{node}]\n"
    for source, target, concurrent in graph.edges:
        content += f'{source} -->{"|Concurrent|" if concurrent else ""} {target}\n'

    return f"flowchart TD\n{content}"


async def traverse(
    graph: Graph,
    action: type[Action],
    allowed_actions: dict[str, bool],
    integrations: dict[str, MCPIntegration],
    bypass: bool = False,
) -> None:
    """Retrieve Graph."""
    parent = f"{action.__module__}.{action.__qualname__}"

    if allowed_actions:
        child_actions = OrderedDict(
            item
            for item in action.__child_actions__.items()
            if allowed_actions.get(item[0], item[1].__enabled__)
        )
    else:
        child_actions = action.__child_actions__.copy()

    if issubclass(action, MCPAction):
        async with multi_streamable_clients(
            integrations, action.__mcp_connections__, bypass
        ) as clients:
            [
                await client.patch_tools(child_actions, action.__mcp_tool_actions__)
                for client in clients.values()
            ]

    for child_action in child_actions.values():
        node = f"{child_action.__module__}.{child_action.__qualname__}"
        graph.edges.add((parent, node, child_action.__concurrent__))
        if node not in graph.nodes:
            graph.nodes.add(node)
            await traverse(graph, child_action, allowed_actions, integrations, bypass)
