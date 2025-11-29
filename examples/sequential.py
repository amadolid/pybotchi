"""User APIs."""

from asyncio import run
from json import dumps

from prerequisite import Action, ActionReturn, ChatRole, Context, graph

from pydantic import Field


class AnswerMathProlemAction(Action):
    """Answer math problem."""

    answer: str = Field(description="The answer to the math problem")

    async def pre(self, context: Context) -> ActionReturn:
        """Execute pre process."""
        await context.add_response(self, self.answer)
        return ActionReturn.GO


class TranslateAction(Action):
    """Translate query to requested language."""

    translation: str = Field(description="The translation of the query")

    async def pre(self, context: Context) -> ActionReturn:
        """Execute pre process."""
        await context.add_response(self, self.translation)
        return ActionReturn.GO


class GeneralChatCombination(Action):
    """Casual Generic Chat."""

    class AnswerMathProlem(AnswerMathProlemAction):
        """Solve math problem."""

    class Translate(TranslateAction):
        """Translate query to requested language."""


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
