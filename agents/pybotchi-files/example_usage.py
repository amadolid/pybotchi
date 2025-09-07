"""PyBotchi Testing."""

from os import getenv

from dotenv import load_dotenv

from fastapi import FastAPI, File, UploadFile

from langchain_openai import AzureChatOpenAI

from pybotchi import Context, LLM

from pybotchi_files import ManageFiles

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

LLM.add(base=llm, vision=llm)

app = FastAPI()


@app.post("/test")
async def test(
    query: str,
    files: list[UploadFile],
    ignored_images: list[UploadFile] = File(default_factory=list),
) -> str:
    """Test Agent."""
    context = Context(
        prompts=[
            {
                "role": "system",
                "content": "".strip(),
            },
            {
                "role": "user",
                "content": query,
            },
        ],
        metadata={
            "uploads": files,
            "ignored_images": ignored_images,
        },
    )
    await context.start(ManageFiles)
    return context.prompts[-1]["content"]
