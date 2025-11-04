"""User APIs."""

from asyncio import run
from json import dumps

from prerequisite import Action, ActionReturn, ChatRole, Context

from pydantic import Field


class Mini(Action):
    """This Assistant is for replying to good byes."""

    async def fallback(self, context: Context, content: str) -> ActionReturn:
        """Execute fallback process."""
        await context.add_response(self, content)

        return ActionReturn.END


class Nano(Action):
    """This Assistant is for replying to greetings."""

    async def pre(self, context: Context) -> ActionReturn:
        """Execute nano process."""
        await context.add_response(self, "Hello")

        return ActionReturn.END


class Deep(Action):
    """This Assistant is for replying to a Joke."""

    class Funny(Action):
        """This Assistant is if you find the joke funny."""

        async def pre(self, context: Context) -> ActionReturn:
            """Execute main process."""
            await context.add_message(ChatRole.ASSISTANT, "your funny")
            return ActionReturn.END

    class NotFunny(Action):
        """This Assistant is if you find the joke not funny."""

        async def pre(self, context: Context) -> ActionReturn:
            """Execute main process."""
            await context.add_message(ChatRole.ASSISTANT, "your not funny")
            return ActionReturn.END


class GeneralChat(Action):
    """Casual Generic Chat."""

    class Joke(Deep):
        """This Assistant is for replying to a Joke."""

    class Goodbyes(Mini):
        """This Assistant is for replying to good byes."""

    class Greetings(Nano):
        """This Assistant is for replying to greetings."""

    class MathProblem(Action):
        """This Assistant is used when user's inquiry is related to Math Problem."""

        answer: str = Field(description="Your mathematical answer to the math problem")

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            await context.add_response(self, self.answer)
            return ActionReturn.GO

    class Translation(Action):
        """This Assistant is used when user's inquiry is related to Food Recipe."""

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            message = await context.llm.ainvoke(context.prompts)
            context.add_usage(self, context.llm, message.usage_metadata)

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

Your primary focus is to prioritize tool usage and efficiently handle multiple tool calls, including invoking the same tool multiple times if necessary.
Ensure that all relevant tools are effectively utilized and properly sequenced to accurately and comprehensively address the user's inquiry.
""".strip(),
            },
            {
                "role": ChatRole.USER,
                # -------------------------------------------------------#
                # Triggers Greetings
                "content": "hello",
                #
                # Triggers Goodbyes
                # "content": "goodbyes",
                #
                # Triggers Joke -> Funny
                # "content": "why 6 scared of 7? because 7 ate 9",
                #
                # Triggers MathProblem
                # "content": "4 x 4",
                #
                # Triggers Translation
                # "content": "What's the english for kamusta",
                #
                # Triggers MathProblem then Translation
                # "content": "4 x 4 and explain your answer in filipino",
                # -------------------------------------------------------#
            },
        ],
    )
    action, result = await context.start(GeneralChat)

    print(dumps(context.prompts, indent=4))
    print(dumps(action.serialize(), indent=4))


run(test())
