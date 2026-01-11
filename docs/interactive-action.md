# **`Interactive Action`**

## **Action Implementation**

```python
from pydantic import Field

from server.action import Action, ActionReturn
from server.agents.base import InteractiveContext
from server.constants import ChatRole

class GeneralChat(Action):
    """Casual Generic Chat."""

    class MathProblem(Action):
        """This Assistant is used when user's inquiry is related to Math Problem."""

        answer: int = Field(description="Your answer to the math problem")

        async def pre(self, context: InteractiveContext) -> ActionReturn:
            """Execute pre process."""
            ######################################################
            #     Wait for client response before continuing     #
            ######################################################
            event = await context.wait_for_input(
                {"message": "before I answer that give me your answer?"}
            )

            if int(event.message.strip()) != self.answer:
                message = f"You're Wrong! Answer is {self.answer}"
            else:
                message = "You're Correct!"

            await context.add_message(ChatRole.ASSISTANT, message)

            ######################################################
            #                    notify client                   #
            ######################################################

            await context.notify({"message": message})
            return ActionReturn.GO
```

## Router Implementation

```python
from fastapi import APIRouter

from server.agents.base import InteractiveExecution
from server.constants import ChatRole
from server.routers.base import WSRouter

router = WSRouter("/testing")


@router.agent("/interactive")
async def interactive_chat(context: InteractiveContext) -> None:
    """Interactive chat."""
    action, result = await context.start(GeneralChat) # import GeneralChat

    await context.notify({"event": "context", "data": context.serialize([action])})
```

## **Connection**

> **WS** /base/testing/interactive\
> **\- `/base` is from bcsai assist base path and may change anytime**
>
> **Headers**:\
> \- Authorization: Bearer **{user_token}**
>
> **Query Params**:\
> \- message **(required)** - initial message\
> \- session_id **(optional)** - will auto generate if not specified\

#### **Initial Connection**

> **WS** /base/testing/interactive?message=4x4

#### **Inbound Event**

##### **This is only based on current example. The response is dynamic and could be anything.**

```python
{
	"message": "before I answer that give me your answer?"
}
```

#### **Outbound Event**

```python
{
    "type": "chat",
	"message": "16",
    "metadata": None # optional
}
```

#### **Inbound Event**

##### **This is only based on current example. The response is dynamic and could be anything.**

```python
{
	"message": "You're Correct!"
}
```

## **Example Implementations**

- [Interactive Agent](../examples/interactive_action.py)
