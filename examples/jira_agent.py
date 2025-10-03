"""User APIs."""

from asyncio import run
from json import dumps


from prerequisite import (
    Action,
    ActionReturn,
    ChatRole,
    Context,
    MCPAction,
    MCPConnection,
    MCPIntegration,
    MCPToolAction,
    graph,
)


class GeneralChat(MCPAction):
    """Casual Generic Chat."""

    __mcp_connections__ = [MCPConnection("jira", "SSE", "http://localhost:9000/sse")]
    __max_child_iteration__ = 5
    # __detached__ = True

    async def pre_mcp(self, context: Context) -> ActionReturn:
        """Execute pre mcp execution."""
        print("Trigger anything here before mcp client connection")
        print("Build context.integrations['jira']['config']")
        print("Refresh tokens")
        print("etc ...")
        return ActionReturn.GO

    class JiraSearch(MCPToolAction):  # noqa: D106
        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre execution."""
            print("#####################################")
            return await super().pre(context)

    class FinalResponse(Action):
        """Finalize Response."""

        async def pre(self, context: Context) -> ActionReturn:
            """Test."""
            message = await context.llm.ainvoke(context.prompts)
            context.add_usage(self, context.llm, message.usage_metadata)

            await context.add_response(self, message.text())

            return ActionReturn.BREAK

    class IgnoredAction(Action):
        """Ignored Action."""

    async def commit_context(self, parent: Context, child: Context) -> None:
        """Execute commit context if it's detached."""
        await super().commit_context(parent, child)
        await parent.add_response(self, child.prompts[-1]["content"])


async def test() -> None:
    """Chat."""
    integrations: dict[str, MCPIntegration] = {
        "jira": {
            # ----------------------------------------- #
            # OVERRIDE BASE CONNECTION
            # ----------------------------------------- #
            # "mode": "SHTTP",
            # "config": {
            #     "url": "http://localhost:9000/mcp",
            # },
            # ----------------------------------------- #
            "allowed_tools": {"JiraSearch", "JiraGetIssue"},
        }
    }
    context = Context(
        prompts=[
            {
                "role": ChatRole.SYSTEM,
                "content": (
                    "Use Jira Tool until user's request is addressed. Use FinalResponse"
                    " tool to make the response more human readable."
                ),
            },
            {
                "role": ChatRole.USER,
                "content": "give me one inprogress ticket currently assigned to me?",
            },
        ],
        allowed_actions={"IgnoredAction": True},
        integrations=integrations,
    )
    action, result = await context.start(GeneralChat)
    print(dumps(context.prompts, indent=4))
    print(dumps(action.serialize(), indent=4))
    print(await graph(GeneralChat, {"IgnoredAction": False}, integrations))


run(test())
