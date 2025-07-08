# **Server Structure**

```
server/
│
├── action/                 # Action Abstraction Classes
|   |
│   └── __init__.py
│
├── agents/                 # Custom Agents
|   |
│   ├── __init__.py
|   |
│   ├── base.py             # Custom Contexts used in agents
|   |
│   ├── chat.py             # Generic Chat Agent
|   |
│   ├── code_review.py      # Code Review and PR Review Agents
|   |
│   ├── general_chat.py     # General Chat Agent that support
│   │                       generic chat, navitaire and test-case-generation redirection
|   |
│   ├── navitaire.py        # Navitaire API extraction Agent
|   |
│   ├── redirect.py         # Redirection Agents (Test Case Generation Redirect)
|   |                       ex: use when agent doesn't support current query and inform user
|   |                           to redirect to their respective agent
|   |
│   └── test_case_gen.py    # Test Case Generation Agent
|                           Test Scenario -> Test Case -> Test Case Refinine
|
├── constants/              # Static Values and Classes for global usage
|   |
│   └── __init__.py
|
├── database/               # Database Handler Classes
|   |
│   ├── __init__.py
|   |
│   ├── base.py             # CosmosDB Container Abstraction Class
│   ├── chat.py             # Chat Container Class + custom chat query
│   ├── code.py             # Code Container Class + custom code query
│   └── user.py             # User Container Class + custom user query
|
├── dtos/                   # Data Transfer Object Classes
|   |                       Used for FastAPI's Request validation or Response specification models
|   |                       Should only include data validation flows as much as possible
|   |                       Models are segregrated based on which data they are related to
│   ├── __init__.py
|   |
│   ├── agent.py
│   ├── chat.py
│   ├── code.py
│   ├── common.py
│   ├── file_extractor.py
│   ├── profile.py
│   ├── sso.py
│   ├── test_case_gen.py
│   ├── user.py
│   └── websocket.py
|
├── fixtures/               # Any static/compiled assets that will be used in process
│   ├── sparse_small.pkl/   # used in navitaire
│   └── sparse.pkl/         # used in navitaire
|
├── models/                 # Model entity used for database
|   |
│   ├── __init__.py
|   |
│   ├── base.py             # base model with default id, created_date, updated_date fields
|   |
│   ├── chat.py             # Chat Container Class + custom chat query
|   |
│   ├── code.py             # Code Container Class + custom code query
|   |
│   └── user.py             # User Container Class + custom user query
|
├── prompt/                 # Similar to constant but values are generated in runtime
|   |
│   └── __init__.py
|
├── redis/                  # Redis Handler Classes
|   |
│   ├── __init__.py
|   |
│   ├── base.py             # Redis Abstraction Class
|   |
│   ├── code.py             # Redis connection class with hash "verification"
|   |                       used for verification code (User Verification and Password Reset)
|   |
│   ├── scheduler.py        # Redis connection class with hash "scheduler"
|   |                       used for multi-replicas event handler
|   |
│   └── token.py            # Redis connection class with hash "token"
|                           used for user authentication
|
├── routers/                # API and Websocket Routers
|   |
│   ├── __init__.py         # Routers arrangement setup
|   |
│   ├── agent.py            # Agent building related APIs
|   |
│   ├── base.py             # Router utilities classes
|   |
│   ├── chat.py             # Chat related REST (sample) and websocket (General Chat Agent) router
|   |
│   ├── code_review.py      # Code related REST (PR Review Agent) and websocket (Code Review Agent) router
|   |
│   ├── history.py          # Chat History related REST router
|   |
│   ├── profile.py          # User profile related REST router
|   |
│   ├── sso.py              # Single Sign-On related REST router
|   |
│   ├── test_case_gen.py    # Test Case Generation related REST (upload file) and websocket (Test Case Gen Agents) router
|   |
│   ├── usage.py            # User Token Usage related REST router
|   |
│   └── user.py             # User Management related REST router
|
├── scheduler/              # Background Scheduled Process
|   |
│   ├── __init__.py         # import schedules to activate
|   |
│   ├── base.py             # Scheduler Abstraction Classes
|   |
│   └── chat.py             # Chat related schedule (delete_old_chat_session)
|
├── security/               # Authentication Handler (FastAPI Dependency Injection)
|   |
│   └── __init__.py         # Authencation Abstraciontion (GET_USER_HTTP, GET_USER_WS, GET_USER_ID_WS, GET_NEW_TOKEN)
|
├── services/               # Reusable dedicated services
|   |
│   ├── __init__.py
|   |
│   ├── file_extractor.py   # pdf/docx content extractor and images transciptor
|   |
│   ├── mail.py             # emailer service
|   |
│   ├── navitaire.py        # navitaire search service
|   |
│   ├── openai.py           # Azure OpenAI (LangChain) model builder service
|   |
│   └── tiktoken.py         # token counter service
|
├── sso/                    # Custom SSO Handlers
|   |
│   ├── __init__.py
│   ├── apple.py
│   ├── google.py
│   └── microsoft.py
|
├── static/                 # static assets folder
|
├── utils/                  # Common reusable utility functions
|   |                       should not have internal dependencies as much as possible
|   |
│   └── __init__.py
|
└── websocket/              # Websocket Handler
    |
    └── __init__.py         # Websocket Abstractions Classes
                            includes generic/global websocket used for user/channel/client notifications
```
