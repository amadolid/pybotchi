"""MCP Client Action."""

from asyncio import run
from json import dumps
from typing import Any

from mcp_prerequisite import (
    ActionResult,
    ChatRole,
    MCPAction,
    MCPConnection,
    MCPContext,
    MCPIntegration,
    MCPToolAction,
    graph,
)


class GeneralChat(MCPAction):
    """Casual Generic Chat."""

    __mcp_connections__ = [MCPConnection("testing", "SHTTP", "http://localhost:8000/group-1/mcp")]

    async def pre_mcp(self, context: MCPContext) -> None:
        """Execute pre mcp execution."""
        print("Trigger anything here before mcp client connection")
        print("Build context.integrations['testing']['config']")
        print("Refresh tokens")
        print("etc ...")

    class MathProblem(MCPToolAction):  # noqa: D106
        async def consume_result_meta(self, context: MCPContext, meta: dict[str, Any]) -> ActionResult:
            """Execute pre process."""
            print(f"Printing tool result context: {meta.get('context')}")
            return await super().consume_result_meta(context, meta)

        async def pre(self, context: MCPContext) -> ActionResult:
            """Execute pre process."""
            print("#####################################")
            return await super().pre(context)


async def test() -> None:
    """Chat."""
    integrations: dict[str, MCPIntegration] = {"testing": {}}
    context = MCPContext(
        prompts=[
            {
                "role": ChatRole.SYSTEM,
                "content": "",
            },
            {
                "role": ChatRole.USER,
                "content": "What is 4 x 4 and what is the english of `Kamusta?`",
                # "content": "Tell me a joke and incorporate it on a very short story",
            },
        ],
        integrations=integrations,
    )
    action, result = await context.start(GeneralChat)
    print(result)
    print(dumps(context.prompts, indent=4))
    print(dumps(action.serialize(), indent=4))

    general_chat_graph = await graph(GeneralChat, {"IgnoredAction": False}, integrations)
    print(general_chat_graph.flowchart())


run(test())
