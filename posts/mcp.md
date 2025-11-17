# As Client

### Prerequisite

- LLM Declaration

```python
from pybotchi import LLM
from langchain_openai import ChatOpenAI

LLM.add(
    base = ChatOpenAI(.....)
)
```

- MCP Server (`MCP-Atlassian`)
  > docker run --rm -p 9000:9000 -i --env-file your-env.env ghcr.io/sooperset/mcp-atlassian:latest --transport streamable-http --port 9000 -vv

### Simple Pybotchi Action

```python
from pybotchi import ActionReturn, MCPAction, MCPConnection

class AtlassianAgent(MCPAction):
    """Atlassian query."""

    __mcp_connections__ = [
        MCPConnection("jira", "http://0.0.0.0:9000/mcp", require_integration=False)
    ]

    async def post(self, context):
        readable_response = await context.llm.ainvoke(context.prompts)
        await context.add_response(self, readable_response.text)
        return ActionReturn.END
```

- `post` is only recommended if mcp tools responses is not in natural language yet.
- You can leverage `post` or `commit_context` for final response generation

### View Graph

```python
from asyncio import run
from pybotchi import graph

print(run(graph(AtlassianAgent)))
```

#### **Result**

```
flowchart TD
mcp.jira.JiraCreateIssueLink[mcp.jira.JiraCreateIssueLink]
mcp.jira.JiraUpdateSprint[mcp.jira.JiraUpdateSprint]
mcp.jira.JiraDownloadAttachments[mcp.jira.JiraDownloadAttachments]
mcp.jira.JiraDeleteIssue[mcp.jira.JiraDeleteIssue]
mcp.jira.JiraGetTransitions[mcp.jira.JiraGetTransitions]
mcp.jira.JiraUpdateIssue[mcp.jira.JiraUpdateIssue]
mcp.jira.JiraSearch[mcp.jira.JiraSearch]
mcp.jira.JiraGetAgileBoards[mcp.jira.JiraGetAgileBoards]
mcp.jira.JiraAddComment[mcp.jira.JiraAddComment]
mcp.jira.JiraGetSprintsFromBoard[mcp.jira.JiraGetSprintsFromBoard]
mcp.jira.JiraGetSprintIssues[mcp.jira.JiraGetSprintIssues]
__main__.AtlassianAgent[__main__.AtlassianAgent]
mcp.jira.JiraLinkToEpic[mcp.jira.JiraLinkToEpic]
mcp.jira.JiraCreateIssue[mcp.jira.JiraCreateIssue]
mcp.jira.JiraBatchCreateIssues[mcp.jira.JiraBatchCreateIssues]
mcp.jira.JiraSearchFields[mcp.jira.JiraSearchFields]
mcp.jira.JiraGetWorklog[mcp.jira.JiraGetWorklog]
mcp.jira.JiraTransitionIssue[mcp.jira.JiraTransitionIssue]
mcp.jira.JiraGetProjectVersions[mcp.jira.JiraGetProjectVersions]
mcp.jira.JiraGetUserProfile[mcp.jira.JiraGetUserProfile]
mcp.jira.JiraGetBoardIssues[mcp.jira.JiraGetBoardIssues]
mcp.jira.JiraGetProjectIssues[mcp.jira.JiraGetProjectIssues]
mcp.jira.JiraAddWorklog[mcp.jira.JiraAddWorklog]
mcp.jira.JiraCreateSprint[mcp.jira.JiraCreateSprint]
mcp.jira.JiraGetLinkTypes[mcp.jira.JiraGetLinkTypes]
mcp.jira.JiraRemoveIssueLink[mcp.jira.JiraRemoveIssueLink]
mcp.jira.JiraGetIssue[mcp.jira.JiraGetIssue]
mcp.jira.JiraBatchGetChangelogs[mcp.jira.JiraBatchGetChangelogs]
__main__.AtlassianAgent --> mcp.jira.JiraCreateIssueLink
__main__.AtlassianAgent --> mcp.jira.JiraGetLinkTypes
__main__.AtlassianAgent --> mcp.jira.JiraDownloadAttachments
__main__.AtlassianAgent --> mcp.jira.JiraAddWorklog
__main__.AtlassianAgent --> mcp.jira.JiraRemoveIssueLink
__main__.AtlassianAgent --> mcp.jira.JiraCreateIssue
__main__.AtlassianAgent --> mcp.jira.JiraLinkToEpic
__main__.AtlassianAgent --> mcp.jira.JiraGetSprintsFromBoard
__main__.AtlassianAgent --> mcp.jira.JiraGetAgileBoards
__main__.AtlassianAgent --> mcp.jira.JiraBatchCreateIssues
__main__.AtlassianAgent --> mcp.jira.JiraSearchFields
__main__.AtlassianAgent --> mcp.jira.JiraGetSprintIssues
__main__.AtlassianAgent --> mcp.jira.JiraSearch
__main__.AtlassianAgent --> mcp.jira.JiraAddComment
__main__.AtlassianAgent --> mcp.jira.JiraDeleteIssue
__main__.AtlassianAgent --> mcp.jira.JiraUpdateIssue
__main__.AtlassianAgent --> mcp.jira.JiraGetProjectVersions
__main__.AtlassianAgent --> mcp.jira.JiraGetBoardIssues
__main__.AtlassianAgent --> mcp.jira.JiraUpdateSprint
__main__.AtlassianAgent --> mcp.jira.JiraBatchGetChangelogs
__main__.AtlassianAgent --> mcp.jira.JiraGetUserProfile
__main__.AtlassianAgent --> mcp.jira.JiraGetWorklog
__main__.AtlassianAgent --> mcp.jira.JiraGetIssue
__main__.AtlassianAgent --> mcp.jira.JiraGetTransitions
__main__.AtlassianAgent --> mcp.jira.JiraTransitionIssue
__main__.AtlassianAgent --> mcp.jira.JiraCreateSprint
__main__.AtlassianAgent --> mcp.jira.JiraGetProjectIssues
```

### Execute

```python
from asyncio import run
from pybotchi import Context

async def test() -> None:
    """Chat."""
    context = Context(
        prompts=[
            {
                "role": "system",
                "content": "Use Jira Tool/s until user's request is addressed",
            },
            {
                "role": "user",
                "content": "give me one inprogress ticket currently assigned to me?",
            },
        ]
    )
    await context.start(AtlassianAgent)
    print(context.prompts[-1]["content"])


run(test())
```

#### **Result**

```
Here is one "In Progress" ticket currently assigned to you:

- Ticket Key: BAAI-244
- Summary: [FOR TESTING ONLY]: Title 1
- Description: Description 1
- Issue Type: Task
- Status: In Progress
- Priority: Medium
- Created: 2025-08-11
- Updated: 2025-08-11
```

## Override Tools (JiraSearch)

```
from pybotchi import ActionReturn, MCPAction, MCPConnection, MCPToolAction

class AtlassianAgent(MCPAction):
    """Atlassian query."""

    __mcp_connections__ = [
        MCPConnection("jira", "http://0.0.0.0:9000/mcp", require_integration=False)
    ]

    async def post(self, context):
        readable_response = await context.llm.ainvoke(context.prompts)
        await context.add_response(self, readable_response.text)
        return ActionReturn.END

    class JiraSearch(MCPToolAction):
        async def pre(self, context):
            print("You can do anything here or even call `super().pre`")
            return await super().pre(context)
```

### View Overridden Graph

```
flowchart TD
... same list ...
mcp.jira.patched.JiraGetIssue[mcp.jira.patched.JiraGetIssue]
... same list ...
__main__.AtlassianAgent --> mcp.jira.patched.JiraGetIssue
... same list ...
```

#### **Updated Result**

```
You can do anything here or even call `super().pre`
Here is one "In Progress" ticket currently assigned to you:

- Ticket Key: BAAI-244
- Summary: [FOR TESTING ONLY]: Title 1
- Description: Description 1
- Issue Type: Task
- Status: In Progress
- Priority: Medium
- Created: 2025-08-11
- Last Updated: 2025-08-11
- Reporter: Alexie Madolid

If you need details from another ticket or more information, let me know!
```

# As Server

#### **server.py**

```python
from contextlib import AsyncExitStack, asynccontextmanager
from fastapi import FastAPI
from pybotchi import Action, ActionReturn, start_mcp_servers

class TranslateToEnglish(Action):
    """Translate sentence to english."""

    __groups__ = {"mcp": {"your_endpoint1", "your_endpoint2"}}

    sentence: str

    async def pre(self, context):
        message = await context.llm.ainvoke(
            f"Translate this to english: {self.sentence}"
        )
        await context.add_response(self, message.text)
        return ActionReturn.GO

class TranslateToFilipino(Action):
    """Translate sentence to filipino."""

    __groups__ = {"mcp": {"your_endpoint2"}}

    sentence: str

    async def pre(self, context):
        message = await context.llm.ainvoke(
            f"Translate this to Filipino: {self.sentence}"
        )
        await context.add_response(self, message.text)
        return ActionReturn.GO

@asynccontextmanager
async def lifespan(app):
    """Override life cycle."""
    async with AsyncExitStack() as stack:
        await mount_mcp_groups(app, stack)
        yield


app = FastAPI(lifespan=lifespan)
```

#### **client.py**

```bash
from asyncio import run

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main(endpoint: int):
    async with streamablehttp_client(
        f"http://localhost:8000/your_endpoint{endpoint}/mcp",
    ) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            response = await session.call_tool(
                "TranslateToEnglish",
                arguments={
                    "sentence": "Kamusta?",
                },
            )
            print(f"Available tools: {[tool.name for tool in tools.tools]}")
            print(response.content[0].text)


run(main(1))
run(main(2))
```

#### **Result**

```
Available tools: ['TranslateToEnglish']
"Kamusta?" in English is "How are you?"
Available tools: ['TranslateToFilipino', 'TranslateToEnglish']
"Kamusta?" translates to "How are you?" in English.
```
