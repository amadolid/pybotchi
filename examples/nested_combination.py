"""Nested Action."""

from asyncio import run
from json import dumps
from os import getenv

from dotenv import load_dotenv

from langchain_openai import AzureChatOpenAI

from pybotchi import Action, ActionReturn, ChatRole, Context as BaseContext, LLM, graph

from pydantic import Field


load_dotenv()

LLM.add(
    base=AzureChatOpenAI(
        api_key=getenv("CHAT_KEY"),  # type: ignore[arg-type]
        azure_endpoint=getenv("CHAT_ENDPOINT"),
        azure_deployment=getenv("CHAT_DEPLOYMENT"),
        model=getenv("CHAT_MODEL"),
        api_version=getenv("CHAT_VERSION"),
        temperature=int(getenv("CHAT_TEMPERATURE", "1")),
        stream_usage=True,
    )
)

Context = BaseContext[AzureChatOpenAI]


class Mini(Action):
    """This Assistant is for replying to good byes."""

    async def fallback(self, context: Context, content: str) -> ActionReturn:
        """Execute fallback process."""
        await context.add_response(self, content)

        return ActionReturn.STOP


class Nano(Action):
    """This Assistant is for replying to greetings."""

    async def pre(self, context: Context) -> ActionReturn:
        """Execute nano process."""
        await context.add_response(self, "Hello")

        return ActionReturn.STOP


class Deep(Action):
    """This Assistant is for replying to a Joke."""

    class Funny(Action):
        """This Assistant is if you find the joke funny."""

        async def pre(self, context: Context) -> ActionReturn:
            """Execute main process."""
            await context.add_message(ChatRole.ASSISTANT, "your funny")
            return ActionReturn.STOP

    class NotFunny(Action):
        """This Assistant is if you find the joke not funny."""

        async def pre(self, context: Context) -> ActionReturn:
            """Execute main process."""
            await context.add_message(ChatRole.ASSISTANT, "your not funny")
            return ActionReturn.STOP


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

        async def pre(self, context: Context) -> None:
            """Execute pre process."""
            await context.add_response(self, self.answer)

    class Translation(Action):
        """This Assistant is used when user's inquiry is related to Food Recipe."""

        async def pre(self, context: Context) -> None:
            """Execute pre process."""
            message = await context.llm.ainvoke(context.prompts)
            await context.add_usage(self, context.llm.model, message.usage_metadata)

            await context.add_response(self, message.text)


async def test() -> None:
    """Chat."""
    context = Context(
        prompts=[
            {
                "role": ChatRole.SYSTEM,
                "content": "",
            },
            {
                "role": ChatRole.USER,
                # -------------------------------------------------------#
                # Triggers Greetings
                "content": "Hello!",
                #
                # Triggers Goodbyes
                # "content": "Good Bye!",
                #
                # Triggers Joke -> Funny
                # "content": "I used to be a banker, but I lost interest.",
                #
                # Triggers Joke -> Not Funny
                # "content": "What will you react if I tell a racist joke",
                #
                # Triggers MathProblem
                # "content": "4 x 4",
                #
                # Triggers Translation
                # "content": "What's the english for kamusta",
                #
                # Triggers MathProblem then Translation
                # "content": "4 x 4 and translate `kamusta` in english",
                # -------------------------------------------------------#
            },
        ],
    )
    action, result = await context.start(GeneralChat)

    print("######################################################")
    print("#                   Nested Approach                  #")
    print("######################################################")
    print(dumps(context.prompts, indent=4))
    print(dumps(action.serialize(), indent=4))
    print("# ----------------- Final Response ----------------- #")
    print(context.prompts[-1]["content"])
    print("# -------------------------------------------------- #")

    general_chat_graph = await graph(GeneralChat)
    print(general_chat_graph.flowchart())


run(test())
