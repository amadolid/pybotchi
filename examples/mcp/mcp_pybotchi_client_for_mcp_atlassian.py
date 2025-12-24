"""User APIs."""

from asyncio import run
from json import dumps

from mcp_prerequisite import (
    Action,
    ActionReturn,
    ChatRole,
    MCPAction,
    MCPConnection,
    MCPContext,
    MCPIntegration,
    MCPToolAction,
    graph,
)


class GeneralChat(MCPAction):
    """Casual Generic Chat."""

    # https://github.com/sooperset/mcp-atlassian
    __mcp_connections__ = [MCPConnection("jira", "SSE", "http://localhost:9000/sse")]
    __max_child_iteration__ = 5
    # __detached__ = True

    async def pre_mcp(self, context: MCPContext) -> ActionReturn:
        """Execute pre mcp execution."""
        print("Trigger anything here before mcp client connection")
        print("Build context.integrations['jira']['config']")
        print("Refresh tokens")
        print("etc ...")
        return ActionReturn.GO

    class JiraSearch(MCPToolAction):  # noqa: D106
        async def pre(self, context: MCPContext) -> ActionReturn:
            """Execute pre execution."""
            print("#####################################")
            return await super().pre(context)

    class FinalResponse(Action):
        """Finalize Response."""

        async def pre(self, context: MCPContext) -> ActionReturn:
            """Test."""
            message = await context.llm.ainvoke(context.prompts)
            await context.add_usage(
                self, context.llm.model_name, message.usage_metadata
            )

            await context.add_response(self, message.text)

            return ActionReturn.BREAK

    class IgnoredAction(Action):
        """Ignored Action."""

    async def commit_context(self, parent: MCPContext, child: MCPContext) -> None:
        """Execute commit context if it's detached."""
        await super().commit_context(parent, child)
        await parent.add_response(self, child.prompts[-1]["content"])


async def test() -> None:
    """Chat."""
    integrations: dict[str, MCPIntegration] = {
        "jira": {
            # ----------------------------------------- #
            # OVERRIDE BASE CONNECTION
            # ----------------------------------------- #
            # "mode": "SHTTP",
            # "config": {
            #     "url": "http://localhost:9000/mcp",
            # },
            # ----------------------------------------- #
            "allowed_tools": {
                "JiraSearchFields": False,
                "JiraCreateSprint": False,
                "JiraGetAllProjects": False,
                "JiraCreateVersion": False,
                "JiraLinkToEpic": False,
                "JiraGetWorklog": False,
                "JiraDeleteIssue": False,
                "JiraAddComment": False,
                "JiraUpdateSprint": False,
                "JiraCreateRemoteIssueLink": False,
                "JiraGetProjectIssues": False,
                "JiraBatchCreateIssues": False,
                "JiraAddWorklog": False,
                "JiraGetSprintsFromBoard": False,
                "JiraCreateIssue": False,
                "JiraGetAgileBoards": False,
                "JiraRemoveIssueLink": False,
                "JiraGetTransitions": False,
                "JiraGetUserProfile": False,
                "JiraGetLinkTypes": False,
                "JiraBatchGetChangelogs": False,
                "JiraGetProjectVersions": False,
                "JiraTransitionIssue": False,
                "JiraUpdateIssue": False,
                "JiraGetSprintIssues": False,
                "JiraBatchCreateVersions": False,
                "JiraDownloadAttachments": False,
                "JiraCreateIssueLink": False,
                "JiraGetBoardIssues": False,
            },
        }
    }
    context = MCPContext(
        prompts=[
            {
                "role": ChatRole.SYSTEM,
                "content": (
                    "Use Jira Tool until user's request is addressed. Use FinalResponse"
                    " tool to make the response more human readable."
                ),
            },
            {
                "role": ChatRole.USER,
                "content": "give me one inprogress ticket currently assigned to me?",
            },
        ],
        allowed_actions={"IgnoredAction": True},
        integrations=integrations,
    )
    action, result = await context.start(GeneralChat)
    print(dumps(context.prompts, indent=4))
    print(dumps(action.serialize(), indent=4))

    general_chat_graph = await graph(
        GeneralChat, {"IgnoredAction": False}, integrations
    )
    print(general_chat_graph.flowchart())


run(test())
