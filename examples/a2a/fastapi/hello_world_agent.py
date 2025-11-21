"""A2A Hello World Example."""

from asyncio import run
from json import dumps

from prerequisite import (
    A2AAction,
    A2AConnection,
    A2AContext,
    A2AIntegration,
    A2AToolAction,
    Action,
    ActionReturn,
    ChatRole,
    graph,
)


class GeneralChat(A2AAction):
    """Casual Generic Chat."""

    __a2a_connections__ = [
        A2AConnection("hello-world", "http://localhost:9999", require_integration=False)
    ]
    __max_child_iteration__ = 5
    # __detached__ = True

    async def pre_a2a(self, context: A2AContext) -> ActionReturn:
        """Execute pre a2a execution."""
        print("Trigger anything here before a2a client connection")
        print("Build context.integrations['jira']['config']")
        print("Refresh tokens")
        print("etc ...")
        return ActionReturn.GO

    class JiraSearch(A2AToolAction):  # noqa: D106
        async def pre(self, context: A2AContext) -> ActionReturn:
            """Execute pre execution."""
            print("#####################################")
            return await super().pre(context)

    class FinalResponse(Action):
        """Finalize Response."""

        async def pre(self, context: A2AContext) -> ActionReturn:
            """Test."""
            message = await context.llm.ainvoke(context.prompts)
            context.add_usage(self, context.llm, message.usage_metadata)

            await context.add_response(self, message.text)

            return ActionReturn.BREAK

    class IgnoredAction(Action):
        """Ignored Action."""

    async def commit_context(self, parent: A2AContext, child: A2AContext) -> None:
        """Execute commit context if it's detached."""
        await super().commit_context(parent, child)
        await parent.add_response(self, child.prompts[-1]["content"])


async def test() -> None:
    """Chat."""
    integrations: dict[str, A2AIntegration] = {
        "jira": {
            # ----------------------------------------- #
            # OVERRIDE BASE CONNECTION
            # ----------------------------------------- #
            # "mode": "SHTTP",
            # "config": {
            #     "url": "http://localhost:9000/a2a",
            # },
            # ----------------------------------------- #
            "allowed_tools": {"JiraSearch", "JiraGetIssue"},
        }
    }
    context = A2AContext(
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
