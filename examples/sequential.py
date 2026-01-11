"""Sequential Action."""

from asyncio import run
from json import dumps

from prerequisite import Action, ActionReturn, ChatRole, Context, graph

from pydantic import Field


class MathProblemAction(Action):
    """Solve the math problem."""

    equation: str = Field(description="The mathematical equation to solve (e.g., '2x + 5')")

    async def pre(self, context: Context) -> ActionReturn:
        """Execute pre process."""
        message = await context.llm.ainvoke(f"Solve `{self.equation}`")
        await context.add_usage(self, context.llm.model_name, message.usage_metadata)
        await context.add_response(self, message.text)
        return ActionReturn.GO


class TranslationAction(Action):
    """Translate to specific language."""

    message: str = Field(description="The text content to be translated.")
    language: str = Field(description="The ISO code or name of the target language.")

    async def pre(self, context: Context) -> ActionReturn:
        """Execute pre process."""
        message = await context.llm.ainvoke(f"Translate `{self.message}` to {self.language}")
        await context.add_usage(self, context.llm.model_name, message.usage_metadata)
        await context.add_response(self, message.text)

        return ActionReturn.GO


class GeneralChatCombination(Action):
    """Casual Generic Chat."""

    class MathProblem(MathProblemAction):
        """Solve the math problem."""

    class Translation(TranslationAction):
        """Translate to specific language."""


class GeneralChatIteration(GeneralChatCombination):
    """Casual Generic Chat."""

    __max_child_iteration__ = 4

    async def fallback(self, context: Context, content: str) -> ActionReturn:
        """Execute fallback."""
        return ActionReturn.BREAK


async def combination() -> None:
    """Chat."""
    context = Context(
        prompts=[
            {
                "role": ChatRole.SYSTEM,
                "content": "",
            },
            {
                "role": ChatRole.USER,
                "content": "4 x 4 and what is `Kamusta` in English?",
            },
        ],
    )
    action, _ = await context.start(GeneralChatCombination)

    print("######################################################")
    print("#                Combination Approach                #")
    print("######################################################")
    print(dumps(context.prompts, indent=4))
    print(dumps(action.serialize(), indent=4))

    general_chat_graph = await graph(GeneralChatCombination)
    print(general_chat_graph.flowchart())


async def iteration() -> None:
    """Chat."""
    context = Context(
        prompts=[
            {
                "role": ChatRole.SYSTEM,
                "content": "",
            },
            {
                "role": ChatRole.USER,
                "content": "4 x 4 and what is `Kamusta` in English?",
            },
        ],
    )
    action, _ = await context.start(GeneralChatIteration)

    print("######################################################")
    print("#                 Iteration Approach                 #")
    print("######################################################")
    print(dumps(context.prompts, indent=4))
    print(dumps(action.serialize(), indent=4))

    general_chat_graph = await graph(GeneralChatIteration)
    print(general_chat_graph.flowchart())


run(combination())
run(iteration())
