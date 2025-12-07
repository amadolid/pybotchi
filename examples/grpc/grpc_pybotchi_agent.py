"""User APIs."""

from grpc_prerequisite import (
    Action,
    ActionReturn,
    ChatRole,
    GRPCAction,
    GRPCConnection,
    GRPCContext,
)

from pydantic import Field


class MathProblem(Action):
    """Solve the math problem."""

    __groups__ = {"grpc": {"group-1"}}

    answer: str = Field(description="Your answer to the math problem")

    async def pre(self, context: GRPCContext) -> ActionReturn:
        """Execute pre process."""
        await context.add_message(
            ChatRole.ASSISTANT,
            "Adding additional message",
            metadata={"additional": True},
        )
        await context.add_response(self, self.answer)
        return ActionReturn.GO


class Translation(Action):
    """Translate to specific language."""

    __groups__ = {"grpc": {"group-1"}}

    async def pre(self, context: GRPCContext) -> ActionReturn:
        """Execute pre process."""
        message = await context.llm.ainvoke(context.prompts)
        await context.add_usage(self, context.llm.model_name, message.usage_metadata)
        await context.add_response(self, message.text)

        return ActionReturn.GO


class JokeWithStoryTelling(GRPCAction):
    """Tell Joke or Story."""

    __groups__ = {"grpc": {"group-1"}}
    __grpc_connections__ = [GRPCConnection("testing2", "localhost:50051", "group-2")]

    async def post(self, context: GRPCContext) -> ActionReturn:
        """Execute pre process."""
        print("Executing post...")
        message = await context.llm.ainvoke(context.prompts)
        await context.add_usage(
            self, context.llm.model_name, message.usage_metadata, "combine"
        )

        await context.add_message(ChatRole.ASSISTANT, message.text)
        print("Done executing post...")
        return ActionReturn.END


class Joke(Action):
    """This Assistant is used when user's inquiry is related to generating a joke."""

    __concurrent__ = True
    __groups__ = {"grpc": {"group-2"}}

    async def pre(self, context: GRPCContext) -> ActionReturn:
        """Execute pre process."""
        print("Executing Joke...")
        message = await context.llm.ainvoke("generate very short joke")
        await context.add_usage(self, context.llm.model_name, message.usage_metadata)

        await context.add_response(self, message.text)
        print("Done executing Joke...")
        return ActionReturn.GO

    class Nested(Action):
        """Additional Child Action."""


class StoryTelling(Action):
    """This Assistant is used when user's inquiry is related to generating stories."""

    __concurrent__ = True
    __groups__ = {"grpc": {"group-2"}}

    async def pre(self, context: GRPCContext) -> ActionReturn:
        """Execute pre process."""
        print("Executing StoryTelling...")
        message = await context.llm.ainvoke("generate a very short story")
        await context.add_usage(self, context.llm.model_name, message.usage_metadata)

        await context.add_response(self, message.text)
        print("Done executing StoryTelling...")
        return ActionReturn.GO
