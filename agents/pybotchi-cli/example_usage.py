"""PyBotchi Testing."""

from asyncio import run
from os import getenv
from sys import argv

from dotenv import load_dotenv

from langchain_openai import AzureChatOpenAI

from pybotchi import Action, ActionReturn, Context, LLM

from pybotchi_cli import ExecuteBashCommandAction

load_dotenv()

llm = AzureChatOpenAI(
    api_key=getenv("CHAT_KEY"),  # type: ignore[arg-type]
    azure_endpoint=getenv("CHAT_ENDPOINT"),
    azure_deployment=getenv("CHAT_DEPLOYMENT"),
    model=getenv("CHAT_MODEL"),
    api_version=getenv("CHAT_VERSION"),
    temperature=int(getenv("CHAT_TEMPERATURE", "1")),
    stream_usage=True,
)

LLM.add(base=llm)


####################################################################################################
#                                            BASE AGENT                                            #
####################################################################################################


class DevOpsCommand(Action):
    """DevOps Command."""

    async def fallback(self, context: Context, content: str) -> ActionReturn:
        """Execute fallback process."""
        await context.add_response(self, content)
        return ActionReturn.GO

    class ExecuteBashCommand(ExecuteBashCommandAction):
        """Executes Bash commands in a CLI environment."""


async def test() -> None:
    """Test Agent."""
    context = Context(
        prompts=[
            {
                "role": "system",
                "content": """
You are an expert DevOps engineer whose sole job is to detect the intent of the user's query.
Your capabilities are strictly limited to:
1. `ExecuteBashCommand` - for executing bash commands.

If the user asks you to perform any other task outside of executing bash commands, you must say it's unsupported.
  e.g. "I don't support it. All I can do is execute bash commands."

If the user does not specify any clear request, you may ask how you can be helpful.
  e.g. "Please let me know how I can help. I can execute bash commands."
""".strip(),
            },
            {
                "role": "user",
                "content": argv[-1],
            },
        ]
    )
    await context.start(DevOpsCommand)
    print(context.prompts[-1]["content"])


run(test())
