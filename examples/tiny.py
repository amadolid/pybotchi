"""Full Spec Action."""

from pybotchi import Action, ActionReturn, ChatRole, Context


################################################################################
#                                     MINI                                     #
################################################################################


class Mini(Action):
    """This Assistant is for replying to greetings."""

    # This is the default fallback if there's no any child actions
    # This is optional and only use if you want to include fallback if you have actions but stil not covering all scenario
    # Prioritize using DefaultAction approach (Declaring child action named DefaultAction with generic assistant description)
    # This will trigger default non streaming invoke. Result will be the content
    async def fallback(self, context: Context, content: str) -> ActionReturn:
        """Execute fallback process."""
        # ASSISTANT CHAT
        # only use for additional chat of user/assistant
        await context.add_message(ChatRole.ASSISTANT, content)

        # TOOL CHAT
        # Recommended to retain tool trigger context and avoid retriggering
        await context.add_response(self, content)

        return ActionReturn.END


################################################################################
#                                     NANO                                     #
################################################################################


class Nano(Action):
    """This Assistant is for replying to greetings."""

    # This is the very first trigger of the action
    # The action hasn't done anything yet, even the tool call.
    async def pre(self, context: Context) -> ActionReturn:
        """Execute nano process."""
        # ASSISTANT CHAT
        # only use for additional chat of user/assistant
        await context.add_message(ChatRole.ASSISTANT, "Hello")

        # TOOL CHAT
        # Recommended to retain tool trigger context and avoid retriggering
        await context.add_response(self, "Hello")

        return ActionReturn.END
