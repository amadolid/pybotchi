# **Non-Action Approach**

## **`Prerequisites`**

### **User**

- User are usually retrieve on authentication

#### `via REST auth`

```python
from fastapi import APIRouter
from server.security import BEARER, GET_USER_HTTP

router = APIRouter(prefix="/endpoint")

@router.post("", dependencies=BEARER)
async def chat(user: GET_USER_HTTP) -> dict:
    pass
```

#### `via Websocket auth`

```python
from fastapi import APIRouter
from server.security import BEARER, GET_USER_WS

router = APIRouter(prefix="/endpoint")

@router.websocket("")
async def chat(user: GET_USER_WS) -> dict:
    pass
```

#### `via Container`

```python
from server.database.user import User, UserContainer

async def get_all_users() -> list[User]:
    # do your cosmosdb operation to get your user
    return [user async for user in await UserContainer.read_all_items()]
```

### **Session ID**

- Session ID is generated UUID included on the first chat
- This will be used on succeeding chats

### **Chat History**

```
from server.database.chat import Chat, ChatContainer

async def get_session(
    user: GET_USER_HTTP,
    session_id: str,
    page: int | None = None,
    size: int | None = None,
    sort: Sort = Sort.ASC,
) -> list[Chat]:
    """Get session."""
    return [
        chat
        async for chat in await ChatContainer.find_by_user_id_and_session_id(
            user.id, session_id
        )
    ]
```

## **`Process`**

- Upon gathering those context you may now use your preferred framework
- Requirements are:
  - all chats should be recorded
  - use websocket as much as possible
