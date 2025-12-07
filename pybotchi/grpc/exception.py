"""Pybotchi GRPC Exception."""


class GRPCRemoteError(Exception):
    """GRPC Remote Exception."""

    def __init__(
        self, cls: str, alias: str, type: str, message: str, tracebacks: list[str]
    ) -> None:
        """Initialize Error."""
        self.cls = cls
        self.alias = alias
        self.type = type
        self.message = message
        self.tracebacks = tracebacks

        super().__init__(cls, alias, type, message, tracebacks)

    def __str__(self) -> str:
        """Return formatted error message."""
        return f"{self.cls}[{self.alias}] {self.type}: {self.message}\n\n{'\n'.join(self.tracebacks)}"
