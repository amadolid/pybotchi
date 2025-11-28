"""User APIs."""

from asyncio import run
from json import dumps

from prerequisite import Action, ActionReturn, ChatRole, Context


class GeneralChat(Action):
    """Casual Generic Chat."""

    class Joke(Action):
        """This Assistant is used when user's inquiry is related to generating a joke."""

        __concurrent__ = True

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            print("Executing Joke...")
            message = await context.llm.ainvoke("generate very short joke")
            await context.add_usage(
                self, context.llm.model_name, message.usage_metadata
            )

            await context.add_response(self, message.text)
            print("Done executing Joke...")
            return ActionReturn.GO

    class StoryTelling(Action):
        """This Assistant is used when user's inquiry is related to generating stories."""

        __concurrent__ = True

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            print("Executing StoryTelling...")
            message = await context.llm.ainvoke("generate a very short story")
            await context.add_usage(
                self, context.llm.model_name, message.usage_metadata
            )

            await context.add_response(self, message.text)
            print("Done executing StoryTelling...")
            return ActionReturn.GO

    async def post(self, context: Context) -> ActionReturn:
        """Execute pre process."""
        print("Executing post...")
        message = await context.llm.ainvoke(context.prompts)
        await context.add_usage(
            self, context.llm.model_name, message.usage_metadata, "combine"
        )

        await context.add_message(ChatRole.ASSISTANT, message.text)
        print("Done executing post...")
        return ActionReturn.END


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
                "content": "Tell me a joke and incorporate it on a very short story",
            },
        ],
    )
    action, result = await context.start(GeneralChat)

    print(dumps(context.prompts, indent=4))
    print(dumps(action.serialize(), indent=4))


run(test())
