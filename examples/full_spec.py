"""Full Spec Action."""

from pybotchi import Action, ActionReturn, Context, DEFAULT_ACTION

from pydantic import Field


# Your Action name should resemble the actual flow.
class GeneralChat(Action):

    # Class doc should describe what it's for
    # This will be used as tool description
    """Casual Generic Chat."""

    ##############################################################
    #                       CLASS VARIABLES                      #
    # ---------------------------------------------------------- #

    # Custom system prompt used in tool selection trigger
    # not specifying will use current system prompt
    __system_prompt__: str | None = None

    # Override current model's temperature
    # this will affect tool selection trigger
    __temperature__: float | None = None

    # This will specify which Action should be the fallback if no applicable child action is detected
    # default: DefaultAction
    __default_tool__: str = DEFAULT_ACTION

    # This will allow only one action on the tool selection trigger
    __first_tool_only__: bool = False

    # This will run the action concurrently using asyncio.TaskGroup
    # Scenario 1:
    #   Selected actions [A1(concurrent), A2(concurrent)]
    #   This will run every action concurrently
    #   This will wait until every concurrent is done even one of it return `End`
    # Scenario 2:
    #   Selected actions [A1(concurrent), A2(non-concurrent), A3(non-concurrent)]
    #   - This will run A1 concurrently
    #   - Continue executing A2 and wait
    #   - If A2 doesn't return `End` continue executing A3 and wait
    #   This will wait until every concurrent is done even one of the action return End
    # Scenario 3:
    #   Selected actions [A1(non-concurrent), A2(non-concurrent), A3(concurrent)]
    #   - This will run A1 and wait
    #   - If A1 doesn't return `End` continue executing A2 and wait
    #   - If A2 doesn't return `End` continue executing A3 concurrently
    #   This will wait until every concurrent is done even one of it return End
    __concurrent__: bool = False

    # --------------------- not inheritable -------------------- #

    # Tagging Action if it's considered as agent
    # This is for future purposes incase we need to support building Custom Agent
    # This attribute is not inheritable and will always default to False
    __agent__: bool = False

    # ---------------------------------------------------------- #
    ##############################################################

    # This is the very first trigger of the action
    # The action hasn't done anything yet, even the tool call.
    async def pre(self, context: Context) -> ActionReturn:
        """Execute pre process."""
        # Default Go(ActionReturn) Instance that doesn't have value
        return ActionReturn.GO

        # Default End(ActionReturn) Instance that doesn't have value
        # This will halt the full operation
        return ActionReturn.END

        # return Go(ActionReturn) Instance with value
        return ActionReturn.go(value="your_return")

        # return End(ActionReturn) Instance with value
        # This will halt the full operation with specified ActionReturn value
        return ActionReturn.end(value="your_return")

    # This is the default fallback if there's no any child actions
    # This is optional and only use if you want to include fallback if you have actions but stil not covering all scenario
    # Prioritize using DefaultAction approach (Declaring child action named DefaultAction with generic assistant description)
    # This will trigger default non streaming invoke. Result will be the content
    async def fallback(self, context: Context, content: str) -> ActionReturn:
        """Execute fallback process."""
        return ActionReturn.GO

    # This process is triggered last per `context execution` if not halted
    # parent_action(pre) -> child_action1 | 2 | 3 | fallback -> parent_action(post)
    # Usually used for consolidating child action results or cleanups
    async def post(
        self, execution: Context, parent: "Action | None" = None
    ) -> ActionReturn:
        """Execute post process."""
        return ActionReturn.GO

    # Child Action 1
    # This should follow General Action Specifications
    # This can have a custom Action parent
    class MathProblem(Action):
        """This Assistant is used when user's inquiry is related to Math Problem."""

        # action's attributes that tool selection trigger can populate
        answer: str = Field(description="Your answer to the math problem")

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            await context.add_response(self, self.answer)
            return ActionReturn.GO

    # Child Action 2
    # This should follow General Action Specifications
    # This can have a custom Action parent
    class Translation(Action):
        """This Assistant is used when user's inquiry is related to Food Recipe."""

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            message = await context.llm.ainvoke(context.prompts)
            context.add_usage(self, context.llm, message.usage_metadata)
            await context.add_response(self, message.text)

            return ActionReturn.GO

    # Continue adding Child Action if needed
