"""User APIs."""

from grpc_prerequisite import Action, ActionReturn, ChatRole, Context

from pydantic import Field


class MathProblem(Action):
    """Solve the math problem."""

    __groups__ = {"grpc": {"group-1"}}

    answer: str = Field(description="Your answer to the math problem")

    async def pre(self, context: Context) -> ActionReturn:
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

    async def pre(self, context: Context) -> ActionReturn:
        """Execute pre process."""
        message = await context.llm.ainvoke(context.prompts)
        await context.add_usage(self, context.llm, message.usage_metadata)
        await context.add_response(self, message.text)

        return ActionReturn.GO


class Joke(Action):
    """This Assistant is used when user's inquiry is related to generating a joke."""

    __groups__ = {"grpc": {"group-2"}}

    async def pre(self, context: Context) -> ActionReturn:
        """Execute pre process."""
        print("Executing Joke...")
        message = await context.llm.ainvoke("generate very short joke")
        await context.add_usage(self, context.llm, message.usage_metadata)

        await context.add_response(self, message.text)
        print("Done executing Joke...")
        return ActionReturn.GO


class StoryTelling(Action):
    """This Assistant is used when user's inquiry is related to generating stories."""

    __groups__ = {"grpc": {"group-2"}}

    async def pre(self, context: Context) -> ActionReturn:
        """Execute pre process."""
        print("Executing StoryTelling...")
        message = await context.llm.ainvoke("generate a very short story")
        await context.add_usage(self, context.llm, message.usage_metadata)

        await context.add_response(self, message.text)
        print("Done executing StoryTelling...")
        return ActionReturn.GO
