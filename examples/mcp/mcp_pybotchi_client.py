"""MCP Client Action."""

from asyncio import run
from json import dumps

from mcp_prerequisite import (
    ActionReturn,
    ChatRole,
    MCPAction,
    MCPConnection,
    MCPContext,
    MCPIntegration,
    graph,
)


class GeneralChat(MCPAction):
    """Casual Generic Chat."""

    __mcp_connections__ = [
        MCPConnection("testing", "SHTTP", "http://localhost:8000/group-1/mcp")
    ]

    async def pre_mcp(self, context: MCPContext) -> ActionReturn:
        """Execute pre mcp execution."""
        print("Trigger anything here before mcp client connection")
        print("Build context.integrations['testing']['config']")
        print("Refresh tokens")
        print("etc ...")
        return ActionReturn.GO


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
    print(dumps(context.prompts, indent=4))
    print(dumps(action.serialize(), indent=4))

    general_chat_graph = await graph(
        GeneralChat, {"IgnoredAction": False}, integrations
    )
    print(general_chat_graph.flowchart())


run(test())
