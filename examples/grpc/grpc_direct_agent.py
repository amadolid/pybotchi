"""User APIs."""

from grpc_prerequisite import Action, ActionReturn, ChatRole, Context

from pydantic import Field


class SingleAction(Action):
    """You're an AI agent the generates random number."""

    __groups__ = {"grpc": {"test2"}}

    async def pre(self, context: Context) -> ActionReturn:
        """Run preperation."""
        await context.add_response(self, "10000")
        return ActionReturn.END


class NestedAgent(Action):
    """You're an AI the can solve math problem and translate any request."""

    query: str = Field(description="User question.")

    __groups__ = {"grpc": {"test", "test2"}}

    async def pre(self, context: Context) -> ActionReturn:
        """Run preperation."""
        await context.add_message(ChatRole.USER, self.query)
        return ActionReturn.GO

    class MathProblem(Action):
        """Solve the math problem."""

        answer: str = Field(description="Your answer to the math problem")

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            await context.add_response(self, self.answer)
            return ActionReturn.GO

    class Translation(Action):
        """Translate to specific language."""

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            message = await context.llm.ainvoke(context.prompts)
            context.add_usage(self, context.llm, message.usage_metadata)
            await context.add_response(self, message.text)

            return ActionReturn.GO
