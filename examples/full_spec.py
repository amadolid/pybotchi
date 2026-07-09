"""Full Spec Action."""

from collections.abc import Generator
from typing import Any

from pydantic import Field

from pybotchi import Action, ActionResult, ActionReturn, Context, DEFAULT_ACTION, Groups


# Action name should describe the flow it represents.
class GeneralChat(Action):
    """Casual Generic Chat.

    The class docstring becomes the tool description shown to the LLM during child selection.
    Keep it concise and behaviorally accurate.
    """

    ##############################################################
    #                       CLASS VARIABLES                      #
    # ---------------------------------------------------------- #

    # Whether this action is included in the parent's tool selection.
    # Set False to hide it entirely by default; can be toggled per-request via context.allowed_actions.
    __enabled__: bool = True

    # System prompt used during this action's child selection trigger.
    # When None, the active conversation system prompt is used instead.
    __system_prompt__: str | None = None

    # Fully overrides the child-selection prompt template.
    # Supports placeholders: ${tool_choice}, ${default}, ${system}, ${addons}.
    # When None, falls back to DEFAULT_TOOL_CALL_PROMPT (configurable via env var).
    __tool_call_prompt__: str | None = None

    # Fully overrides the finalization prompt used when __max_iteration__ is exhausted.
    # Supports ${system}. When None, falls back to DEFAULT_MAX_ITERATION_PROMPT.
    __max_iteration_prompt__: str | None = None

    # LLM temperature override applied during child selection for this action.
    # When None, the model's configured default is used.
    __temperature__: float | None = None

    # Sliding window: only the last N prompts are sent to the LLM during child selection.
    # Keeps token costs predictable in long iteration loops. None means no limit.
    __max_child_selection_prompts__: int | None = None

    # Name of the child action suggested to the LLM as the default choice in the prompt.
    # The LLM can still pick any other child; this only biases selection.
    # Defaults to DEFAULT_ACTION ("DefaultAction"), configurable via env var.
    __default_tool__: str = DEFAULT_ACTION

    # When True, only the first tool call from the LLM response is executed per iteration,
    # even if the model suggests multiple tools. Pair with __max_iteration__ for step-by-step loops.
    __first_tool_only__: bool = False

    # When True, this action runs inside an asyncio.TaskGroup alongside other concurrent siblings.
    # Set on the CHILD action, not the parent.
    #
    # Scenario 1 — All selected actions are concurrent:
    #   [A1(concurrent), A2(concurrent)]
    #   Both run in parallel. Wait for all to complete.
    #
    # Scenario 2 — Mixed: concurrent first, sequential after:
    #   [A1(concurrent), A2(sequential), A3(sequential)]
    #   A1 starts in the background. A2 runs inline and is awaited. A3 runs inline after A2.
    #   Wait for A1's background task to finish last.
    #
    # Scenario 3 — Mixed: sequential first, concurrent last:
    #   [A1(sequential), A2(sequential), A3(concurrent)]
    #   A1 runs and is awaited. A2 runs and is awaited. A3 starts concurrently.
    #   Wait for A3's background task to finish.
    #
    # The loop exits early only if an action returns BREAK or STOP; END does not stop siblings.
    __concurrent__: bool = False

    # Maximum number of child selection iterations per turn.
    # When set, the action loops its child execution up to this many times.
    # On exhaustion, on_max_iteration() is called to synthesize a final response.
    # Use ActionReturn.BREAK from any hook to exit the loop early.
    __max_iteration__: int | None = None

    # Per-action self-call cap within a single turn.
    # Tracks how many times this specific action class has been invoked.
    # When exceeded, ActionReturn.STOP is returned automatically.
    # Falls back to context.max_self_recursion when None.
    __max_self_recursion__: int | None = None

    # --------------------- not inheritable -------------------- #

    # Marks this class as a top-level agent for the all_agents() generator.
    # Does not change runtime behavior. Always resets to False in subclasses.
    __agent__: bool = False

    # Human-friendly name used in notify() events and as the MCP tool title.
    # Defaults to the class name. Override to display a readable label without renaming the class.
    __display_name__: str

    # Registers this action into gRPC/MCP/a2a integration groups.
    # Use a set[str] to apply to all valid group types, or a Groups dict to target specific ones.
    __groups__: Groups | set[str] | None

    # ---------------------------------------------------------- #
    ##############################################################

    # Called first, before child selection or any tool calls.
    # Use for guardrails, data gathering (RAG), preprocessing, or logging.
    async def pre(self, context: Context) -> ActionResult:
        """Execute pre process."""
        # None (or omit return) — continue normally; nothing is interrupted.
        return None

        # END — stop only this action's remaining lifecycle (post won't run).
        # Siblings at the same level continue unaffected.
        return ActionReturn.END

        # BREAK — stop this action AND break the nearest ancestor's __max_iteration__ loop.
        # Also stops subsequent siblings in sequential execution at the parent level.
        return ActionReturn.BREAK

        # STOP — stop the entire agent immediately, propagating through all ancestors.
        return ActionReturn.STOP

        # stop(value=...) — same as STOP but carries a return value accessible after context.start().
        return ActionReturn.stop(value="any_value_with_any_type")

    # Called when no child action is selected by the LLM, or when the action has no children
    # (in which case the LLM is invoked first and the plain-text result is passed here).
    # Optional — only define this if you need to handle the no-tool-call case explicitly.
    # Prefer the DefaultAction pattern over fallback when you have child actions.
    async def fallback(self, context: Context, content: str) -> ActionResult:
        """Execute fallback process."""

    # Called after all child actions complete (and after the iteration loop exits).
    # Use for consolidating results, data persistence, cleanup, or final LLM summarization.
    # Only runs if the lifecycle was not halted by END, BREAK, or STOP before reaching it.
    async def post(self, context: Context) -> ActionResult:
        """Execute post process."""

    # Called when a child action fails to initialize from the LLM's tool call arguments
    # (e.g. a Pydantic validation error due to wrong argument types).
    # Return a correction string to feed back to the LLM so it can retry on the next iteration.
    # Return None to skip the failed action and continue the loop.
    async def on_child_init_error(
        self,
        context: Context,
        next_actions: list["Action"],
        child_cls: type[Action],
        child_args: dict[str, Any],
        exception: Exception,
    ) -> str | None:
        """Execute on child init error process."""

    # Called when any unhandled exception propagates through execute().
    # unwrapped_exceptions is a generator of leaf exceptions from unwrap_exceptions(),
    # useful for inspecting ExceptionGroup members individually.
    # Return an ActionResult to recover, or re-raise to propagate the error upward.
    async def on_error(
        self,
        context: Context,
        exception: Exception,
        unwrapped_exceptions: Generator[Exception, None, None],
    ) -> ActionResult:
        """Execute on error process."""

    class MathProblem(Action):
        """This Assistant is used when user's inquiry is related to Math Problem."""

        # Fields declared here are populated by the LLM during child selection (tool call arguments).
        answer: str = Field(description="Your answer to the math problem")

        async def pre(self, context: Context) -> None:
            """Execute pre process."""
            await context.add_response(self, self.answer)

    class Translation(Action):
        """This Assistant is used when user's inquiry is related to Translation."""

        async def pre(self, context: Context) -> None:
            """Execute pre process."""
            message = await context.llm.ainvoke(context.prompts)
            await context.add_usage(self, context.llm.model, message.usage_metadata)
            await context.add_response(self, message.text)

    # Continue adding child actions as inner classes following the same pattern.
