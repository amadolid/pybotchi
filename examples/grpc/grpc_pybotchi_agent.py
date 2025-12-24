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

    equation: str = Field(
        description="The mathematical equation to solve (e.g., '2x + 5')"
    )

    async def pre(self, context: GRPCContext) -> ActionReturn:
        """Execute pre process."""
        message = await context.llm.ainvoke(f"Solve `{self.equation}`")
        await context.add_usage(self, context.llm.model_name, message.usage_metadata)
        await context.add_message(
            ChatRole.ASSISTANT,
            "Adding additional message",
            metadata={"additional": True},
        )
        await context.add_response(self, message.text)
        return ActionReturn.GO


class Translation(Action):
    """Translate to specific language."""

    __groups__ = {"grpc": {"group-1"}}

    message: str = Field(description="The text content to be translated.")
    language: str = Field(description="The ISO code or name of the target language.")

    async def pre(self, context: GRPCContext) -> ActionReturn:
        """Execute pre process."""
        message = await context.llm.ainvoke(
            f"Translate `{self.message}` to {self.language}"
        )
        await context.add_usage(self, context.llm.model_name, message.usage_metadata)

        await context.add_message(
            ChatRole.ASSISTANT,
            "Adding additional message",
            metadata={"additional": True},
        )
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
    """Generate a joke."""

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

    # Example deeper recursion
    class Nested(GRPCAction):
        """Additional Child Action."""

        __grpc_connections__ = [
            GRPCConnection("testing2", "localhost:50051", "group-1")
        ]


class StoryTelling(Action):
    """Tell a story."""

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
