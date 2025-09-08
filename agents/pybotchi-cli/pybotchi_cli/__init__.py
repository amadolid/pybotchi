"""PyBotchi Agents related to cli commands."""

from subprocess import run

from pybotchi import Action, ActionReturn, Context
from pybotchi.utils import apply_placeholders

from pydantic import Field


class ExecuteBashCommandAction(Action):
    """Executes Bash commands in a CLI environment."""

    script: str = Field(
        description="""
A multi-line script that includes comprehensive logging before and after each process.
Logs should clearly display the inputs and outputs of every manipulation step.
If the script contains a large loop (e.g., 100 iterations or more), avoid placing logs inside the loop to prevent excessive output.
""".strip()
    )

    confirmation_message: str = Field(
        description="""
A template message displayed to the user for approval before running the script. Must include the ${script} placeholder, which will be replaced with the actual script content at runtime. Example:
"Here's the script I will run:\n```\n${script}\n```\n\nIf you want to proceed, please reply with "I know what I am doing" exactly:"`
Leave this field empty if no confirmation is required. Use this to warn about potential security concerns, any modifications or to request user verification.
""".strip()
    )

    ####################################################################################################
    #                                             EXECUTION                                            #
    ####################################################################################################

    async def pre(self, context: Context) -> ActionReturn:
        """Execute pre process.

        You may override this to meet your requirements.
        """
        if not await self.confirm_human(context):
            await context.add_response(self, "Cancelled!")
            return ActionReturn.GO

        result = run(self.script, shell=True, capture_output=True)

        await context.add_response(self, (result.stdout or result.stderr).decode())

        return ActionReturn.GO

    ####################################################################################################
    #                                             UTILITIES                                            #
    ####################################################################################################

    async def confirm_human(self, context: Context) -> bool:
        """Ask human for confirmation.

        You may override this to meet your requirements.
        You may use websocket or any approach that can ask user before proceeding.
        """
        if self.confirmation_message:
            response = input(
                f"{apply_placeholders(self.confirmation_message, script=self.script)}\n"
            )
            return response.lower() == "i know what i am doing"
        return True
