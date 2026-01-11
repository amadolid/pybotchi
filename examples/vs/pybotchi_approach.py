"""Testing."""

from asyncio import run
from datetime import datetime
from os import getenv

from dotenv import load_dotenv

from langchain_openai import AzureChatOpenAI

from pybotchi import Action, ActionReturn, ChatRole, Context, LLM


load_dotenv()

LLM.add(
    base=AzureChatOpenAI(
        api_key=getenv("CHAT_KEY"),  # type: ignore[arg-type]
        azure_endpoint=getenv("CHAT_ENDPOINT"),
        azure_deployment=getenv("CHAT_DEPLOYMENT"),
        model=getenv("CHAT_MODEL"),
        api_version=getenv("CHAT_VERSION"),
        temperature=int(getenv("CHAT_TEMPERATURE", "1")),
        stream_usage=True,
        verbose=True,
    )
)


##############################################################################
#                               FOR APPROACH 0                               #
##############################################################################

print("Starting Approach0...")


# ITERATION ACTION
class Approach0(Action):
    """Casual Generic Chat."""

    __max_child_iteration__ = 5

    async def fallback(self, context: Context, content: str) -> ActionReturn:
        """Execute pre process."""
        await context.add_message(ChatRole.ASSISTANT, content)
        return ActionReturn.END

    class Weather(Action):
        """Call to get the current weather."""

        location: str

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            if self.location.lower() in ["yorkshire"]:
                await context.add_response(self, "It's cold and wet.")
            else:
                await context.add_response(self, "It's warm and sunny.")

            return ActionReturn.GO


async def main() -> None:
    """Test."""
    total = 0.0
    for _i in range(10):
        now = datetime.now().timestamp()
        exec = Context(
            prompts=[
                {"content": "", "role": ChatRole.SYSTEM},
                {"content": "Whats the weather in yorkshire?", "role": ChatRole.USER},
            ],
        )
        await exec.start(Approach0)
        print(exec.prompts[-1]["content"])
        total += datetime.now().timestamp() - now
    print(f"Approach1: {total / 10}")


run(main())

# ----------------------------------------------------------------------------#

##############################################################################
#                               FOR APPROACH 1                               #
##############################################################################

print("Starting Approach1...")


# DIRECT CIRCULAR ACTION
class Approach1(Action):
    """Casual Generic Chat."""

    async def fallback(self, context: Context, content: str) -> ActionReturn:
        """Execute pre process."""
        await context.add_message(ChatRole.ASSISTANT, content)
        return ActionReturn.END

    class Weather(Action):
        """Call to get the current weather."""

        location: str

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            if self.location.lower() in ["yorkshire"]:
                await context.add_response(self, "It's cold and wet.")
            else:
                await context.add_response(self, "It's warm and sunny.")

            return ActionReturn.GO


# Add action on Weather pointed to Approach1
Approach1.Weather.add_child(Approach1, "DefaultAction")


async def main() -> None:  # type: ignore[no-redef]
    """Test."""
    total = 0.0
    for _i in range(10):
        now = datetime.now().timestamp()
        exec = Context(
            prompts=[
                {"content": "", "role": ChatRole.SYSTEM},
                {"content": "Whats the weather in yorkshire?", "role": ChatRole.USER},
            ],
        )
        await exec.start(Approach1)
        print(exec.prompts[-1]["content"])
        total += datetime.now().timestamp() - now
    print(f"Approach1: {total / 10}")


run(main())

# ----------------------------------------------------------------------------#

##############################################################################
#                               FOR APPROACH 2                               #
##############################################################################

print("Starting Approach2...")


# INDIRECT CIRCULAR ACTION
class Approach2(Action):
    """Casual Generic Chat."""

    async def fallback(self, context: Context, content: str) -> ActionReturn:
        """Execute pre process."""
        await context.add_message(ChatRole.ASSISTANT, content)
        return ActionReturn.END

    class Weather(Action):
        """Call to get the current weather."""

        location: str

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            if self.location.lower() in ["yorkshire"]:
                await context.add_response(self, "It's cold and wet.")
            else:
                await context.add_response(self, "It's warm and sunny.")

            # Indirect Trigger
            result = await Approach2().execute(context, self)  # type: ignore[call-arg]
            return result


async def main() -> None:  # type: ignore[no-redef]
    """Test."""
    total = 0.0
    for _i in range(10):
        now = datetime.now().timestamp()
        exec = Context(
            prompts=[
                {"content": "", "role": ChatRole.SYSTEM},
                {"content": "Whats the weather in yorkshire?", "role": ChatRole.USER},
            ],
        )
        await exec.start(Approach2)
        print(exec.prompts[-1]["content"])
        total += datetime.now().timestamp() - now
    print(f"Approach2: {total / 10}")


run(main())

# ----------------------------------------------------------------------------#


##############################################################################
#            FOR APPROACH 3 (slightly SLOWER but has more control)           #
##############################################################################

print("Starting Approach3...")


# INDIRECT CIRCULAR ACTION
class Approach3(Action):
    """Casual Generic Chat."""

    class DefaultAction(Action):
        """Default Assistant if no other applicable tool."""

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            # any other process here
            # streaming, binding, with config
            message = await context.llm.ainvoke(context.prompts)
            await context.add_message(ChatRole.ASSISTANT, message.text)

            return ActionReturn.END

    class Weather(Action):
        """Call to get the current weather."""

        location: str

        async def pre(self, context: Context) -> ActionReturn:
            """Execute pre process."""
            if self.location.lower() in ["yorkshire"]:
                await context.add_response(self, "It's cold and wet.")
            else:
                await context.add_response(self, "It's warm and sunny.")

            # OR Indirect Trigger
            # action, result = await Approach3().execute(context, self)
            return ActionReturn.GO


Approach3.Weather.add_child(Approach3, "DefaultAction")


async def main() -> None:  # type: ignore[no-redef]
    """Test."""
    total = 0.0
    for _i in range(10):
        now = datetime.now().timestamp()
        exec = Context(
            prompts=[
                {"content": "", "role": ChatRole.SYSTEM},
                {"content": "Whats the weather in yorkshire?", "role": ChatRole.USER},
            ],
        )
        await exec.start(Approach3)
        print(exec.prompts[-1]["content"])
        total += datetime.now().timestamp() - now
    print(f"Approach3: {total / 10}")


run(main())

# ----------------------------------------------------------------------------#
