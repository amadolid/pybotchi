"""Sequential Action."""

from asyncio import run
from json import dumps
from typing import Any, ClassVar

from prerequisite import Action, ActionReturn, ChatRole, Context, graph, uuid

from pydantic import BaseModel, Field


class MathProblemAction(Action):
    """Solve the math problem."""

    equation: str = Field(description="The mathematical equation to solve (e.g., '2x + 5')")

    async def pre(self, context: Context) -> ActionReturn:
        """Execute pre process."""
        message = await context.llm.ainvoke(f"Solve `{self.equation}`")
        await context.add_usage(self, context.llm.model, message.usage_metadata)
        await context.add_response(self, message.text)
        return ActionReturn.GO


class TranslationAction(Action):
    """Translate to specific language."""

    message: str = Field(description="The text content to be translated.")
    language: str = Field(description="The ISO code or name of the target language.")

    async def pre(self, context: Context) -> ActionReturn:
        """Execute pre process."""
        message = await context.llm.ainvoke(f"Translate `{self.message}` to {self.language}")
        await context.add_usage(self, context.llm.model, message.usage_metadata)
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

    __max_child_iteration__ = 10
    __first_tool_only__ = True

    async def fallback(self, context: Context, content: str) -> ActionReturn:
        """Execute fallback."""
        return ActionReturn.BREAK


class GeneralChatIterationExceedLimit(Action):
    """Casual Generic Chat."""

    __max_child_iteration__ = 4
    __first_tool_only__ = True

    class Print(Action):
        """Print Number."""

        number: int

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            await context.add_response(self, str(self.number))
            return ActionReturn.GO


class GeneralChatWithCorrection(Action):
    """Casual Generic Chat."""

    __max_child_iteration__ = 4
    __first_tool_only__ = True

    class Print(Action):
        """Print Number."""

        number: int

        failed_once: ClassVar[bool] = False

        @classmethod
        async def _as_tool(cls, context: Context) -> dict[str, Any] | type[BaseModel]:
            """Convert Action to tool."""
            if not cls.failed_once:
                print("###################################################")
                print("#         FORCING FIRST TOOL CALL TO FAIL         #")
                print("###################################################")
                cls.failed_once = True
                schema = cls.model_json_schema()

                schema["properties"]["number"] = {
                    "description": "Word number: one, two, ...",
                    "title": "number",
                    "type": "string",
                }
                schema["additionalProperties"] = False
                return {
                    "type": "function",
                    "function": {
                        "name": schema.pop("title"),
                        "description": schema.pop("description", ""),
                        "strict": True,
                        "parameters": schema,
                    },
                }
            return cls

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            await context.add_response(self, str(self.number))
            return ActionReturn.GO

    async def on_child_init_error(
        self,
        context: Context,
        next_actions: list[Action],
        child_cls: type[Action],
        child_args: dict[str, Any],
        exception: Exception,
    ) -> str | None:
        """Execute on child init error process."""
        # All of this are optional

        # This is not necessary but good for monitoring
        self._actions.append(
            {
                "name": child_cls.__name__,
                "args": child_args,
                "usages": [],
                "actions": [],
            }
        )

        # This one can be critical to retain proper history
        await context.add_response(
            {
                "id": f"call_{uuid().hex}",
                "function": {
                    "name": child_cls.__name__,
                    "arguments": dumps(child_args),
                },
                "type": "function",
            },
            str(exception),
        )

        # Other approach #1
        # You may just add assistant error
        # await context.add_message(ChatRole.ASSISTANT, str(exception))

        # Other approach #2
        # construct the
        # child = child_cls.model_construct(**child_args)
        # self._actions.append(child)
        # await context.add_response(child, str(exception))

        return None


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
    print("# --------- Final Responses (Combination)  --------- #")
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
    print("# ----------- Final Responses (Iteration) ---------- #")
    print(context.prompts[-3]["content"])
    print(context.prompts[-1]["content"])
    print("# -------------------------------------------------- #")

    general_chat_graph = await graph(GeneralChatIteration)
    print(general_chat_graph.flowchart())


async def iteration_exceed_limit() -> None:
    """Chat."""
    context = Context(
        prompts=[
            {
                "role": ChatRole.SYSTEM,
                "content": "",
            },
            {
                "role": ChatRole.USER,
                "content": "Print from 1 to 10",
            },
        ],
    )
    action, _ = await context.start(GeneralChatIterationExceedLimit)

    print("######################################################")
    print("#    Sequential Approach (Iteration exceed limit)    #")
    print("######################################################")
    print(dumps(context.prompts, indent=4))
    print(dumps(action.serialize(), indent=4))
    print("# ----- Final Response (Iteration exceed limit) ---- #")
    print(context.prompts[-1]["content"])
    print("# -------------------------------------------------- #")

    general_chat_graph = await graph(GeneralChatIterationExceedLimit)
    print(general_chat_graph.flowchart())


async def iteration_with_correction() -> None:
    """Chat."""
    context = Context(
        prompts=[
            {
                "role": ChatRole.SYSTEM,
                "content": "",
            },
            {
                "role": ChatRole.USER,
                "content": "Print from 1 to 10",
            },
        ],
    )
    action, _ = await context.start(GeneralChatWithCorrection)

    print("######################################################")
    print("#   Sequential Approach (Iteration with correction)  #")
    print("######################################################")
    print(dumps(context.prompts, indent=4))
    print(dumps(action.serialize(), indent=4))
    print("# --- Final Response (Iteration with correction) --- #")
    print(context.prompts[-1]["content"])
    print("# -------------------------------------------------- #")

    general_chat_graph = await graph(GeneralChatWithCorrection)
    print(general_chat_graph.flowchart())


run(combination())
run(iteration())
run(iteration_exceed_limit())
run(iteration_with_correction())
