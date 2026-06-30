"""Pybotchi GRPC Exception."""


class GRPCRemoteError(Exception):
    """GRPC Remote Exception."""

    def __init__(self, cls: str, alias: str, type: str, message: str, tracebacks: list[str]) -> None:
        """Initialize Error."""
        self.cls: str = cls
        self.alias: str = alias
        self.type: str = type
        self.message: str = message
        self.tracebacks: list[str] = tracebacks

        super().__init__(cls, alias, type, message, tracebacks)

    def __str__(self) -> str:
        """Return formatted error message."""
        return f"{self.cls}[{self.alias}] {self.type}: {self.message}\n\n{'\n'.join(self.tracebacks)}"
