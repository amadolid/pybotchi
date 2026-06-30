class GRPCRemoteError(Exception):
    cls: str
    alias: str
    type: str
    message: str
    tracebacks: list[str]
    def __init__(self, cls: str, alias: str, type: str, message: str, tracebacks: list[str]) -> None: ...
    def __str__(self) -> str: ...
