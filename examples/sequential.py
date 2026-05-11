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

    async def fallback(self, context: Context, content: str) -> ActionReturn:
        """Execute fallback."""
        return ActionReturn.BREAK


class GeneralChatIterationWithLimit(Action):
    """Casual Generic Chat."""

    __max_child_iteration__ = 4
    __first_tool_only__ = True

    class Shout(Action):
        """Shout Number."""

        count: int

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            await context.add_response(self, str(self.count))
            return ActionReturn.GO


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
    print("#          Sequential Approach (Combination)         #")
    print("######################################################")
    print(dumps(context.prompts, indent=4))
    print(dumps(action.serialize(), indent=4))
    print("# ----------------- Final Responses ---------------- #")
    print(context.prompts[-3]["content"])
    print(context.prompts[-1]["content"])
    print("# -------------------------------------------------- #")

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
    print("#           Sequential Approach (Iteration)          #")
    print("######################################################")
    print(dumps(context.prompts, indent=4))
    print(dumps(action.serialize(), indent=4))
    print("# ----------------- Final Responses ---------------- #")
    print(context.prompts[-3]["content"])
    print(context.prompts[-1]["content"])
    print("# -------------------------------------------------- #")

    general_chat_graph = await graph(GeneralChatIteration)
    print(general_chat_graph.flowchart())


async def iteration_with_limit() -> None:
    """Chat."""
    context = Context(
        prompts=[
            {
                "role": ChatRole.SYSTEM,
                "content": "",
            },
            {
                "role": ChatRole.USER,
                "content": "Shout from 1 to 10",
            },
        ],
    )
    action, _ = await context.start(GeneralChatIterationWithLimit)

    print("######################################################")
    print("#     Sequential Approach (Iteration with limit)     #")
    print("######################################################")
    print(dumps(context.prompts, indent=4))
    print(dumps(action.serialize(), indent=4))
    print("# ----------------- Final Response ----------------- #")
    print(context.prompts[-1]["content"])
    print("# -------------------------------------------------- #")

    general_chat_graph = await graph(GeneralChatIterationWithLimit)
    print(general_chat_graph.flowchart())


run(combination())
run(iteration())
run(iteration_with_limit())
