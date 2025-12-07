"""GRPC PyBotchi Client."""

from asyncio import run
from json import dumps

from grpc_prerequisite import (
    Action,
    ActionReturn,
    ChatRole,
    GRPCAction,
    GRPCConnection,
    GRPCContext,
    GRPCIntegration,
    GRPCRemoteAction,
    graph,
)


class GeneralChat(GRPCAction):
    """Casual Generic Chat."""

    __grpc_connections__ = [GRPCConnection("testing", "localhost:50051", "group-1")]

    async def pre_grpc(self, context: GRPCContext) -> ActionReturn:
        """Execute pre grpc execution."""
        print("Trigger anything here before grpc client connection")
        print("Build context.integrations['testing']['config']")
        print("Refresh tokens")
        print("etc ...")
        return ActionReturn.GO

    class MathProblem(GRPCRemoteAction):  # noqa: D106
        async def pre(self, context: GRPCContext) -> ActionReturn:
            """Execute pre execution."""
            print("#####################################")
            return await super().pre(context)

    class RequestValidator(Action):
        """Validate request concurrently."""

        __concurrent__ = True

        async def pre(self, context: GRPCContext) -> ActionReturn:
            """Execute pre execution."""
            await context.add_response(self, "testing222")
            return ActionReturn.GO

    class IgnoredAction(Action):
        """Ignored Action."""


async def test() -> None:
    """Chat."""
    integrations: dict[str, GRPCIntegration] = {"testing": {}, "testing2": {}}
    context = GRPCContext(
        prompts=[
            {
                "role": ChatRole.SYSTEM,
                "content": """
You're an AI the can solve math problem and translate any request.

Your primary focus is to prioritize tool usage and efficiently handle multiple tool calls, including invoking the same tool multiple times if necessary.
Ensure that all relevant tools are effectively utilized and properly sequenced to accurately and comprehensively address the user's inquiry.

Always include RequestValidator in your selection as first tool.
""".strip(),
            },
            {
                "role": ChatRole.USER,
                "content": "4 x 4 and explain your answer in filipino",
                # "content": "Tell me a joke and incorporate it on a very short story",
            },
        ],
        allowed_actions={"IgnoredAction": True},
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
