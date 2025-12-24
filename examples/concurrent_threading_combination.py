"""User APIs."""

from asyncio import run
from json import dumps

from prerequisite import Action, ActionReturn, ChatRole, Context, graph


class GeneralChat(Action):
    """Casual Generic Chat."""

    class Joke(Action):
        """This Assistant is used when user's inquiry is related to generating a joke."""

        __concurrent__ = True

        def additional_sync_execution(
            self, arg1: int, arg2: str, kwarg1: int = 1, kwarg2: str = ""
        ) -> None:
            """Execute additional sync function."""
            print(
                f"Additional function1 - arg1: {arg1} , arg2: {arg2} , kwarg1: {kwarg1} , kwarg2: {kwarg2}"
            )

        async def your_function_name(self, context: Context) -> ActionReturn:
            """Execute other function."""
            print("Executing Joke...")
            message = await context.llm.ainvoke("generate very short joke")
            await context.add_usage(
                self, context.llm.model_name, message.usage_metadata
            )

            await context.add_response(self, message.text)
            print("Done executing Joke...")
            return ActionReturn.GO

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            # Without waiting
            context.run_func_in_thread(
                self.additional_sync_execution, None, 1, "a", kwarg1=1, kwarg2="a"
            )
            # With wait
            await context.run_func_in_thread(
                self.additional_sync_execution, None, 2, "b", kwarg1=2, kwarg2="b"
            )
            return await context.run_task_in_thread(self.your_function_name(context))

    class StoryTelling(Action):
        """This Assistant is used when user's inquiry is related to generating stories."""

        __concurrent__ = True

        def additional_sync_execution(
            self, arg1: int, arg2: str, kwarg1: int = 0, kwarg2: str = ""
        ) -> None:
            """Execute additional sync function."""
            print(
                f"Additional function2 - arg1: {arg1} , arg2: {arg2} , kwarg1: {kwarg1} , kwarg2: {kwarg2}"
            )

        async def your_function_name(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            print("Executing StoryTelling...")
            message = await context.llm.ainvoke("generate a very short story")
            await context.add_usage(
                self, context.llm.model_name, message.usage_metadata
            )

            await context.add_response(self, message.text)
            print("Done executing StoryTelling...")
            return ActionReturn.GO

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            # Without waiting
            context.run_func_in_thread(
                self.additional_sync_execution, None, 1, "a", kwarg1=1, kwarg2="a"
            )
            # With wait
            await context.run_func_in_thread(
                self.additional_sync_execution, None, 2, "b", kwarg1=2, kwarg2="b"
            )
            return await context.run_task_in_thread(self.your_function_name(context))

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

    general_chat_graph = await graph(GeneralChat)
    print(general_chat_graph.flowchart())


run(test())
