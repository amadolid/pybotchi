"""Pybotchi Action."""

from __future__ import annotations

from asyncio import TaskGroup
from collections import OrderedDict
from inspect import getmembers
from itertools import islice
from os import getenv
from typing import Any, TYPE_CHECKING, TypeAlias, TypeVar
from uuid import uuid4

from mcp.server.fastmcp import FastMCP

from openai.types.chat.chat_completion_message_tool_call_param import (
    ChatCompletionMessageToolCallParam,
)

from pydantic import BaseModel, PrivateAttr

from .constants import ActionEntry, ActionReturn, UsageData
from .utils import apply_placeholders

if TYPE_CHECKING:
    from .context import Context

try:
    from uuid6 import uuid7  # type: ignore[import-not-found]

    gen_uuid = uuid7
except Exception:
    gen_uuid = uuid4


DEFAULT_ACTION = getenv("DEFAULT_ACTION", "DefaultAction")
DEFAULT_TOOL_CALL_PROMPT = getenv(
    "DEFAULT_TOOL_CALL_PROMPT",
    """
You are an AI assistant expert in function calling.
Your primary responsibility is to select and invoke the most suitable function(s) to accurately fulfill the user's request, following the guidelines below.

# `tool_choice` is set to "${tool_choice}"

# Function Calling Guidelines:
- You may call one or more functions as needed, including repeated calls to the same function, to ensure the user's request is fully addressed.
- Always invoke functions in a logical and sequential order to ensure comprehensive and accurate responses.
- If `${default}` function is provided and `Initial Task` doesn't have rules over it, prioritize invoking it whenever no other relevant or suitable function is available.
- If `tool_choice` is set to `auto` and no suitable function can be identified, respond directly to the user based on the provided `Initial Task`.

# Initial Task:
${system}

${addons}
""".strip(),
)

TAction = TypeVar("TAction", bound="Action")
T = TypeVar("T")

ChildActions: TypeAlias = OrderedDict[str, type["Action"]]


class Action(BaseModel):
    """Base Agent Action."""

    __mcp_servers__: dict[str, FastMCP] = {}

    ##############################################################
    #                       CLASS VARIABLES                      #
    ##############################################################

    __enabled__: bool = True
    __system_prompt__: str | None = None
    __tool_call_prompt__: str | None = None
    __temperature__: float | None = None
    __max_tool_prompts__: int | None = None
    __default_tool__ = DEFAULT_ACTION
    __first_tool_only__ = False
    __concurrent__ = False
    __mcp_hosts__: list[str] | None = None

    __has_pre__: bool
    __has_fallback__: bool
    __has_on_error__: bool
    __has_post__: bool
    __detached__: bool

    __max_iteration__: int | None = None
    __max_child_iteration__: int | None = None
    __child_actions__: ChildActions
    __mcp_tool_actions__: ChildActions

    # --------------------- not inheritable -------------------- #

    __agent__: bool = False
    __display_name__: str
    __mcp_groups__: list[str] | None
    __to_commit__: bool = True

    # ---------------------------------------------------------- #

    ##############################################################
    #                     INSTANCE VARIABLES                     #
    ##############################################################

    _usage: list[UsageData] = PrivateAttr(default_factory=list)
    _actions: list["Action"] = PrivateAttr(default_factory=list)
    _parent: Action | None = PrivateAttr(None)

    # ---------------------------------------------------------- #

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """Override __pydantic_init_subclass__."""
        src = cls.__dict__
        cls.__agent__ = src.get("__agent__", False)
        cls.__display_name__ = src.get("__display_name__", cls.__name__)
        cls.__has_pre__ = cls.pre is not Action.pre
        cls.__has_fallback__ = cls.fallback is not Action.fallback
        cls.__has_on_error__ = cls.on_error is not Action.on_error
        cls.__has_post__ = cls.post is not Action.post
        cls.__detached__ = src.get(
            "__detached__", cls.commit_context is not Action.commit_context
        )
        cls.__mcp_groups__ = src.get("__mcp_groups__")
        cls.__to_commit__ = src.get("__to_commit__", True)

        cls.__mcp_tool_actions__ = OrderedDict()
        cls.__child_actions__ = OrderedDict()
        for _, attr in getmembers(cls):
            if isinstance(attr, type):
                if getattr(attr, "__mcp_tool__", False):
                    cls.__mcp_tool_actions__[attr.__name__] = attr
                elif issubclass(attr, Action):
                    cls.__child_actions__[attr.__name__] = attr

    async def get_child_actions(self, context: Context) -> ChildActions:
        """Retrieve child Actions."""
        return OrderedDict(
            item
            for item in self.__child_actions__.items()
            if context.allowed_actions.get(item[0], item[1].__enabled__)
        )

    @property
    def _tool_call(self) -> ChatCompletionMessageToolCallParam:
        """Override post init."""
        tool_id = f"call_{gen_uuid().hex}"
        return {
            "id": tool_id,
            "function": {
                "name": self.__class__.__name__,
                "arguments": self.model_dump_json(),
            },
            "type": "function",
        }

    async def execute(
        self, context: Context, parent: Action | None = None
    ) -> ActionReturn:
        """Execute main process."""
        self._parent = parent
        parent_context = context
        try:
            if self.__detached__:
                context = await context.detach_context()

            if context.check_self_recursion(self):
                return ActionReturn.END

            if self.__has_pre__ and (result := await self.pre(context)).is_break:
                return result

            if self.__max_child_iteration__:
                iteration = 0
                while iteration <= self.__max_child_iteration__:
                    if (result := await self.execution(context)).is_break:
                        break
                    iteration += 1
                if result.is_end:
                    return result
            elif (result := await self.execution(context)).is_break:
                return result

            if self.__has_post__ and (result := await self.post(context)).is_break:
                return result

            return ActionReturn.GO
        except Exception as exception:
            if not self.__has_on_error__:
                self.__to_commit__ = False
                raise exception
            elif (result := await self.on_error(context, exception)).is_break:
                return result
            return ActionReturn.GO
        finally:
            if self.__to_commit__ and self.__detached__:
                await self.commit_context(parent_context, context)

    async def pre(self, context: Context) -> ActionReturn:
        """Execute pre process."""
        return ActionReturn.GO

    async def fallback(self, context: Context, content: str) -> ActionReturn:
        """Execute fallback process."""
        return ActionReturn.GO

    async def on_error(self, context: Context, exception: Exception) -> ActionReturn:
        """Execute on error process."""
        return ActionReturn.GO

    def child_selection_prompt(self, context: Context, tool_choice: str) -> str:
        """Get child selection prompt."""
        return apply_placeholders(
            self.__tool_call_prompt__ or DEFAULT_TOOL_CALL_PROMPT,
            tool_choice=tool_choice,
            default=self.__default_tool__,
            system=self.__system_prompt__
            or context.prompts[0]["content"]
            or "Not defined",
        )

    async def child_selection(
        self,
        context: Context,
        child_actions: ChildActions | None = None,
    ) -> tuple[list["Action"], str]:
        """Execute tool selection process."""
        tool_choice = "auto" if self.__has_fallback__ else "required"

        if child_actions is None:
            child_actions = await self.get_child_actions(context)
        llm = context.llm.bind_tools([*child_actions.values()], tool_choice=tool_choice)
        if self.__temperature__ is not None:
            llm = llm.with_config(
                configurable={"llm_temperature": self.__temperature__}
            )

        max = len(context.prompts)
        if self.__max_tool_prompts__:
            min = max - self.__max_tool_prompts__
            min = 1 if min < 1 else min
        else:
            min = 1

        message = await llm.ainvoke(
            [
                {
                    "content": self.child_selection_prompt(context, tool_choice),
                    "role": "system",
                },
                *islice(context.prompts, min, max),
            ]
        )
        context.add_usage(
            self,
            context.llm,
            message.usage_metadata,  # type: ignore[attr-defined]
            "$tool",
        )

        next_actions = [
            child_actions[call["name"]](**call["args"]) for call in message.tool_calls  # type: ignore[attr-defined]
        ]

        return next_actions, message.text()

    async def execution(self, context: Context) -> ActionReturn:
        """Execute core process."""
        child_actions = await self.get_child_actions(context)
        if (
            len(child_actions) == 1
            and not (action := next(iter(child_actions.values()))).model_fields
            and not self.__has_fallback__
        ):
            self._actions.append(next_action := action())  # type: ignore[call-arg]
            if (result := await next_action.execute(context, self)).is_break:
                return result
        elif child_actions:
            await context.notify(
                {
                    "event": "tool",
                    "type": "selection",
                    "status": "started",
                    "data": [n.__display_name__ for n in child_actions.values()],
                }
            )

            next_actions, content = await self.child_selection(context, child_actions)

            await context.notify(
                {
                    "event": "tool",
                    "type": "selection",
                    "status": "completed",
                    "data": [
                        {"action": n.__display_name__, "args": n.model_dump()}
                        for n in next_actions
                    ],
                }
            )

            if next_actions:
                if (
                    result := await (
                        self.concurrent_children_execution
                        if any(True for na in next_actions if na.__concurrent__)
                        else self.sequential_children_execution
                    )(context, next_actions)
                ).is_break:
                    return result
            elif (
                self.__has_fallback__
                and (result := await self.fallback(context, content)).is_break
            ):
                return result
        elif self.__has_fallback__:
            llm = (
                context.llm.with_config(
                    configurable={"llm_temperature": self.__temperature__}
                )
                if self.__temperature__ is not None
                else context.llm
            )

            await context.notify(
                {
                    "event": "tool",
                    "type": "fallback",
                    "status": "started",
                    "data": self.__display_name__,
                }
            )

            message = await llm.ainvoke(context.prompts)

            context.add_usage(
                self,
                context.llm,
                message.usage_metadata,  # type: ignore[attr-defined]
                "$fallback",
            )

            await context.notify(
                {
                    "event": "tool",
                    "type": "fallback",
                    "status": "completed",
                    "data": self.__display_name__,
                }
            )

            if (result := await self.fallback(context, message.text())).is_break:  # type: ignore[arg-type]
                return result

        return ActionReturn.GO

    async def concurrent_children_execution(
        self, context: Context, next_actions: list[Action]
    ) -> ActionReturn:
        """Run children execution with concurrent."""
        async with TaskGroup() as tg:
            for next_action in (
                islice(next_actions, 1) if self.__first_tool_only__ else next_actions
            ):
                self._actions.append(next_action)
                if next_action.__concurrent__:
                    tg.create_task(next_action.execute(context, self))
                elif (result := await next_action.execute(context, self)).is_break:
                    return result

        return ActionReturn.GO

    async def sequential_children_execution(
        self, context: Context, next_actions: list[Action]
    ) -> ActionReturn:
        """Run children execution sequentially."""
        for next_action in (
            islice(next_actions, 1) if self.__first_tool_only__ else next_actions
        ):
            self._actions.append(next_action)
            if (result := await next_action.execute(context, self)).is_break:
                return result

        return ActionReturn.GO

    async def post(self, context: Context) -> ActionReturn:
        """Execute post process."""
        return ActionReturn.GO

    async def commit_context(self, parent: Context, child: Context) -> None:
        """Execute commit context if it's detached."""
        usage = parent.usage
        for model, token in child.usage.items():
            if model not in usage:
                usage[model] = token
            else:
                usage[model] += token

    def serialize(self) -> ActionEntry:
        """Serialize Action."""
        return {
            "name": self.__class__.__name__,
            "args": self.model_dump(),
            "usages": self._usage,
            "actions": [a.serialize() for a in self._actions],
        }

    ####################################################################################################
    #                                           ACTION TOOLS                                           #
    # ------------------------------------------------------------------------------------------------ #

    @classmethod
    def add_child(
        cls,
        action: type["Action"],
        name: str | None = None,
        override: bool = False,
        extended: bool = True,
    ) -> None:
        """Add child action."""
        name = name or action.__name__
        if not override and hasattr(cls, name):
            raise ValueError(f"Attribute {name} already exists!")

        if not issubclass(action, Action):
            raise ValueError(f"{action.__name__} is not a valid action!")

        if extended:
            action = type(name, (action,), {"__module__": action.__module__})

        if getattr(action, "__mcp_tool__", False):
            cls.__mcp_tool_actions__[name] = action
        else:
            cls.__child_actions__[name] = action
        setattr(cls, name, action)

    @classmethod
    def add_grand_child(
        cls,
        action: type["Action"],
        name: str | None = None,
        override: bool = False,
        extended: bool = True,
    ) -> None:
        """Add child action."""
        for ccls in cls.__child_actions__.values():
            ccls.add_child(action, name, override, extended)
