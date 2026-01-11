"""PyBotchi Testing."""

from functools import cached_property
from os import getenv

from dotenv import load_dotenv

from fastapi import FastAPI, File, UploadFile

from langchain_openai import AzureChatOpenAI

from pybotchi import Action, ActionReturn, Context, LLM

from pybotchi_files import ManipulateFilesContent

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

####################################################################################################
#                                            BASE AGENT                                            #
####################################################################################################


@app.post("/test")
async def test(
    query: str,
    files: list[UploadFile],
    ignored_images: list[UploadFile] = File(default_factory=list),  # noqa: B008
) -> str:
    """Test Agent."""
    context = Context(
        prompts=[
            {
                "role": "system",
                "content": "",
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
    await context.start(ManipulateFilesContent)
    return context.prompts[-1]["content"]


####################################################################################################
#                                          OVERRIDEN AGENT                                         #
####################################################################################################


class ManipulateContent(Action):
    """Manipulate Content."""

    async def fallback(self, context: Context, content: str) -> ActionReturn:
        """Execute fallback process."""
        await context.add_response(self, content)
        return ActionReturn.GO

    class Summarize(ManipulateFilesContent):
        """Summarize Content."""

        @cached_property
        def _operation_prompt(self) -> str:
            """Retrieve operation prompt.

            You may override this to meet your requirements.
            """
            return """
Summarize the provided content into the shortest possible form while preserving only the essential meaning."

**Rules:**
1. **Length:** Maximum 1-2 sentences or 20 words.
2. **Clarity:** Use plain, direct language.
3. **Focus:** Keep only the main idea; remove examples, details, and filler.
4. **Neutrality:** No personal opinions or interpretations.
5. **Accuracy:** Do not add information not found in the original content.

Files:
${files}
""".strip()

    class GenerateTitle(ManipulateFilesContent):
        """Generate Title Content."""

        @cached_property
        def _operation_prompt(self) -> str:
            """Retrieve operation prompt.

            You may override this to meet your requirements.
            """
            return """
Generate a short, clear, and relevant title for the provided content."

**Rules:**
1. **Length:** Maximum 5-8 words.
2. **Clarity:** Use simple, direct language that reflects the core topic.
3. **Relevance:** Title must accurately represent the main subject.
4. **Neutrality:** Avoid bias, sensationalism, or personal opinions.
5. **Creativity:** Prefer engaging but professional wording.

Files:
${files}
""".strip()


@app.post("/test2")
async def test2(
    query: str,
    files: list[UploadFile],
    ignored_images: list[UploadFile] = File(default_factory=list),  # noqa: B008
) -> str:
    """Test Agent."""
    context = Context(
        prompts=[
            {
                "role": "system",
                "content": """
You are an expert copywriter whose sole job is to detect the intent of the user's query.

Your capabilities are strictly limited to:
1. `Summarize` - for summarization.
2. `GenerateTitle` - for title generation.

If the user asks you to perform any other task outside of summarizing or generating a title, you may say it's unsupported.
  e.g. "I don't support it. All I can do is summarizing and generating titles."

If the user does not specify any clear request, you may ask how you can be helpful.
  e.g. "Please let me know how I can help. I can do summarizing and generating titles."
""".strip(),
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
    await context.start(ManipulateContent)
    return context.prompts[-1]["content"]
