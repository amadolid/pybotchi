"""User APIs."""

from asyncio import run
from json import dumps

from prerequisite import Action, ActionReturn, ChatRole, Context

from pydantic import Field


class GeneralChat(Action):
    """Casual Generic Chat."""

    __max_child_iteration__ = 4

    async def fallback(self, context: Context, content: str) -> ActionReturn:
        """Execute fallback."""
        return ActionReturn.BREAK

    class MathProblem(Action):
        """This Assistant is used when user's inquiry is related to Math Problem."""

        answer: str = Field(description="Your answer to the math problem")

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            await context.add_response(self, self.answer)
            return ActionReturn.GO

    class Translation(Action):
        """This Assistant is used when user's inquiry is related to Translation."""

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            message = await context.llm.ainvoke(context.prompts)
            await context.add_usage(self, context.llm, message.usage_metadata)

            await context.add_response(self, message.text)
            return ActionReturn.GO


async def test() -> None:
    """Chat."""
    context = Context(
        prompts=[
            {
                "role": ChatRole.SYSTEM,
                "content": """
You're an AI the can solve math problem and translate any request.

You follow this steps to comprehensively answer user query.

Your plan is to solve the math problem first by calling `MathProblem` tool.
If the math problem is already solved.
You need to translate user's query to specified language by calling `Translation` tool.

""".strip(),
            },
            {
                "role": ChatRole.USER,
                "content": "4 x 4 and explain your answer in filipino",
            },
        ],
    )
    action, result = await context.start(GeneralChat)

    print(dumps(context.prompts, indent=4))
    print(dumps(action.serialize(), indent=4))


run(test())
