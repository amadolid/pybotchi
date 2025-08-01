"""Pybotchi Context."""

from asyncio import get_event_loop, new_event_loop
from collections.abc import Coroutine
from concurrent.futures import Executor
from copy import deepcopy
from functools import cached_property
from typing import Any, Generic

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages.ai import UsageMetadata

from pydantic import BaseModel, Field, PrivateAttr

from typing_extensions import TypeVar

from .action import Action, ActionReturn, T, TAction
from .constants import ChatRole, UNSPECIFIED, Usage
from .llm import LLM

TContext = TypeVar("TContext", bound="Context")
TLLM = TypeVar("TLLM", default=BaseChatModel)


class Context(BaseModel, Generic[TLLM]):
    """Context Handler."""

    prompts: list[dict[str, Any]] = Field(default_factory=list)
    allowed_actions: dict[str, bool] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    integration: dict[str, Any] = Field(default_factory=dict)
    usage: dict[str, int] = Field(default_factory=dict)
    streaming: bool = False
    max_self_loop: int | None = None
    detached: bool = False

    _action_call: dict[str, int] = PrivateAttr(default_factory=dict)

    @cached_property
    def llm(self) -> TLLM:
        """Get base LLM."""
        return LLM.base()

    async def start(
        self, action: type[TAction], /, **kwargs: Any
    ) -> tuple[TAction, ActionReturn]:
        """Start Action."""
        if not self.prompts or self.prompts[0]["role"] != ChatRole.SYSTEM:
            raise RuntimeError("Prompts should not be empty and start with system!")

        self._action_call.clear()

        agent = action(**kwargs)
        return agent, await agent.execute(self)

    def check_self_recursion(self, action: "Action") -> bool:
        """Check self recursion."""
        cls = action.__class__
        name = f"{cls.__module__}.{cls.__name__}"
        if name not in self._action_call:
            self._action_call[name] = 1
        else:
            self._action_call[name] += 1
            max = action.__max_iteration__ or self.max_self_loop
            if max and self._action_call[name] > max:
                return True
        return False

    def add_usage(
        self,
        action: "Action",
        model: BaseChatModel | str,
        usage: UsageMetadata,
        name: str | None = None,
    ) -> None:
        """Add usage."""
        model_name = (
            getattr(model, "model_name", getattr(model, "deployment_name", UNSPECIFIED))
            if isinstance(model, BaseChatModel)
            else model
        )
        action._usage.append(Usage(name=name, model=model_name, usage=usage))

        if model_name not in self.usage:
            self.usage[model_name] = 0

        self.usage[model_name] += usage["total_tokens"]

    async def add_message(
        self, role: ChatRole, content: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Add message."""
        self.prompts.append({"content": content, "role": role})

    async def add_response(
        self,
        action: "Action",
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add tool."""
        tool_call = action._tool_call
        self.prompts.append(
            {
                "content": "",
                "role": ChatRole.ASSISTANT,
                "tool_calls": [tool_call],
            }
        )
        self.prompts.append(
            {"content": content, "role": ChatRole.TOOL, "tool_call_id": tool_call["id"]}
        )

    async def notify(self, message: dict[str, Any]) -> None:
        """Notify Client."""
        pass

    def run_new_event_loop(self, task: Coroutine[Any, Any, T]) -> T:
        """Run concurrent on different thread."""
        loop = new_event_loop()
        try:
            return loop.run_until_complete(task)
        except Exception:
            raise
        finally:
            loop.close()

    async def run_in_thread(
        self, task: Coroutine[Any, Any, T], executor: Executor | None = None
    ) -> T:
        """Run concurrent on different thread."""
        return await get_event_loop().run_in_executor(
            executor, self.run_new_event_loop, task
        )

    async def detach_context(self: TContext) -> TContext:
        """Spawn detached context."""
        return self.__class__(**self.detached_kwargs())

    def detached_kwargs(self) -> dict[str, Any]:
        """Retrieve detached kwargs."""
        return {
            "llm": self.llm,
            "prompts": deepcopy(self.prompts),
            "allowed_actions": deepcopy(self.allowed_actions),
            "metadata": deepcopy(self.metadata),
            "integration": deepcopy(self.integration),
            "streaming": self.streaming,
            "max_self_loop": self.max_self_loop,
            "detached": True,
        }

    async def detached_start(
        self: TContext, action: type["Action"], /, **kwargs: Any
    ) -> tuple[TContext, "Action", ActionReturn]:
        """Start Action."""
        context = await self.detach_context()
        _action, _action_return = await context.start(action, **kwargs)
        return context, _action, _action_return
