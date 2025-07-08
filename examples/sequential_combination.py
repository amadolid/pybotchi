"""User APIs."""

from asyncio import run
from json import dumps

from prerequisite import Action, ActionReturn, ChatRole, Context

from pydantic import Field


class GeneralChat(Action):
    """Casual Generic Chat."""

    class MathProblem(Action):
        """This Assistant is used when user's inquiry is related to Math Problem."""

        answer: str = Field(description="You answer to the math problem")

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            await context.add_response(self, self.answer)
            return ActionReturn.GO

    class Translation(Action):
        """This Assistant is used when user's inquiry is related to Translation."""

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            message = await context.llm.ainvoke(context.prompts)
            context.add_usage(self, context.llm, message.usage_metadata)
            await context.add_response(self, message.content)
            return ActionReturn.GO


async def test() -> None:
    """Chat."""
    context = Context(
        prompts=[
            {
                "role": ChatRole.SYSTEM,
                "content": """
You're an AI the can solve math problem and translate any request.

Your primary focus is to prioritize tool usage and efficiently handle multiple tool calls, including invoking the same tool multiple times if necessary.
Ensure that all relevant tools are effectively utilized and properly sequenced to accurately and comprehensively address the user's inquiry.
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
