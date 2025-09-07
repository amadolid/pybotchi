"""Base PyBotchi Agent for file."""

from functools import cached_property
from itertools import islice

from pybotchi import ActionReturn, Context
from pybotchi.utils import apply_placeholders

from .base import ManageFilesAction


class ManageFiles(ManageFilesAction):
    """Generate Summary."""

    @cached_property
    def _operation_prompt(self) -> str:
        """Retrieve operation prompt.

        You may override this to meet your requirements.
        """
        return """
You are a helpful and intelligent assistant that specializes in managing and manipulating the contents of files.
You can read, interpret, and transform text-based file contents into different formats or styles to meet the user's needs.
Your capabilities include (but are not limited to):
- Summarizing large amounts of text clearly and concisely.
- Extracting key points, data, or structured information.
- Creating tables, charts, or lists from unstructured content.
- Rewriting or reformatting content to match specific styles.
- Merging, splitting, or reorganizing sections of text.
- Converting between formats (e.g., plain text → Markdown tables).
- Providing suggestions for improving clarity and structure.
When responding:
- Always confirm your understanding of the user's request before making major transformations.
- Preserve important details and context unless the user specifies otherwise.
- Ask clarifying questions if the input is ambiguous.
- Maintain accuracy, and avoid fabricating content.
Your goal is to help the user efficiently work with and transform file contents into useful, well-structured outputs.

Files:
${files}
""".strip()

    async def pre(self, context: Context) -> ActionReturn:
        """Executre pre process."""
        chat = context.llm
        if self.__temperature__ is not None:
            chat = chat.with_config(
                configurable={"llm_temperature": self.__temperature__}
            )

        files = "\n---\n".join(
            f"```{key}\n{val}\n```"
            for key, val in (await self.extract(context)).items()
        )

        response = await chat.ainvoke(
            [
                {
                    "content": apply_placeholders(self._operation_prompt, files=files),
                    "role": "system",
                },
                *islice(context.prompts, 1, None),
            ]
        )
        await context.add_response(self, response.content)

        return ActionReturn.GO
