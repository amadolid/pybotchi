"""Interactive Action."""

from os import getenv
from typing import Any, ClassVar

from dotenv import load_dotenv

from fastapi import FastAPI, WebSocket

from langchain_openai import AzureChatOpenAI

from pybotchi import Action, ChatRole, Context as BaseContext, LLM

from pydantic import ConfigDict, Field

from uvicorn import run

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
    )
)

Context = BaseContext[AzureChatOpenAI]


class InteractiveContext(Context):
    """InteractiveContext Handler."""

    websocket: WebSocket

    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    async def notify(self, message: dict[str, Any]) -> None:
        """Notify Client."""
        await self.websocket.send_json(message)

    async def wait_for_input(self, message: dict[str, Any]) -> str:
        """Wait for client input."""
        await self.websocket.send_json(message)
        # reply_json = await self.websocket.receive_json()
        reply_message = await self.websocket.receive_text()
        return reply_message


class GeneralChat(Action):
    """Casual Generic Chat."""

    class MathProblem(Action):
        """This Assistant is used when user's inquiry is related to Math Problem."""

        answer: int = Field(description="Your answer to the math problem")

        async def pre(self, context: InteractiveContext) -> None:
            """Execute pre process."""
            ######################################################
            #     Wait for client response before continuing     #
            ######################################################
            reply = await context.wait_for_input({"message": "before I answer that give me your answer?"})

            if int(reply.strip()) != self.answer:
                message = f"You're Wrong! Answer is {self.answer}"
            else:
                message = "You're Correct!"

            await context.add_message(ChatRole.ASSISTANT, message)

            ######################################################
            #                    notify client                   #
            ######################################################

            await context.notify({"message": message})


app = FastAPI()


@app.websocket("/test")
async def testing(websocket: WebSocket) -> None:
    """Test."""
    await websocket.accept()
    context = InteractiveContext(
        prompts=[
            {
                "role": ChatRole.SYSTEM,
                "content": "",
            }
        ],
        websocket=websocket,
    )
    await context.notify({"message": "Ask me mathematical equation"})

    while True:
        context.prompts.append(
            {
                "role": ChatRole.USER,
                "content": await websocket.receive_text(),
            }
        )
        await context.start(GeneralChat)


if __name__ == "__main__":
    run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
