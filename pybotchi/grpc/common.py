"""Pybotchi GRPC Common."""

from enum import StrEnum
from typing import Any, Sequence, TypedDict

from grpc.aio import ClientInterceptor


class GRPCCompression(StrEnum):
    """GRPC Compression."""

    NoCompression = "NoCompression"
    Deflate = "Deflate"
    Gzip = "Gzip"


class GRPCConfig(TypedDict, total=False):
    """GRPC Config."""

    url: str
    group: str
    options: list[tuple[str, Any]] | None
    compression: GRPCCompression | None
    metadata: dict[str, Any] | None
    allow_exec: bool


class GRPCIntegration(TypedDict, total=False):
    """GRPC Integration."""

    config: GRPCConfig
    allowed_actions: list[str]
    exclude_unset: bool


class GRPCConnection:
    """GRPC Connection configurations."""

    def __init__(
        self,
        name: str,
        url: str = "",
        group: str = "",
        options: list[tuple[str, Any]] | None = None,
        compression: GRPCCompression | None = None,
        interceptors: Sequence[ClientInterceptor] | None = None,
        metadata: dict[str, Any] | None = None,
        allow_exec: bool = False,
        allowed_actions: set[str] | None = None,
        exclude_unset: bool = True,
        require_integration: bool = True,
    ) -> None:
        """Build GRPC Connection."""
        self.name = name
        self.url = url
        self.group = group
        self.options = options
        self.compression = compression
        self.interceptors = interceptors
        self.metadata = metadata
        self.allow_exec = allow_exec
        self.allowed_actions = (
            set[str]() if allowed_actions is None else allowed_actions
        )
        self.exclude_unset = exclude_unset
        self.require_integration = require_integration

    def get_config(self, override: GRPCConfig | None) -> GRPCConfig:
        """Generate config."""
        if override is None:
            return {
                "url": self.url,
                "group": self.group,
                "options": self.options,
                "compression": self.compression,
                "metadata": self.metadata,
                "allow_exec": self.allow_exec,
            }

        url = override.get("url", self.url)
        group = override.get("group", self.group)
        options = override.get("options", self.options)
        compression = override.get("compression", self.compression)
        allow_exec = override.get("allow_exec", self.allow_exec)

        metadata: dict[str, str] | None
        if _metadata := override.get("metadata"):
            if self.metadata is None:
                metadata = _metadata
            else:
                metadata = self.metadata | _metadata
        else:
            metadata = self.metadata

        return {
            "url": url,
            "group": group,
            "options": options,
            "compression": compression,
            "metadata": metadata,
            "allow_exec": allow_exec,
        }
