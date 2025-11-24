"""Pybotchi GRPC Common."""

from enum import StrEnum
from typing import Any, Sequence, TypedDict

from grpc import Compression
from grpc._typing import ChannelArgumentType
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


class GRPCIntegration(TypedDict, total=False):
    """GRPC Integration."""

    config: GRPCConfig
    allowed_tools: set[str]
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
    ) -> None:
        """Build GRPC Connection."""
        self.name = name
        self.url = url
        self.group = group
        self.options = options
        self.compression = compression
        self.interceptors = interceptors
        self.metadata = metadata

    def get_config(self, override: GRPCConfig | None) -> GRPCConfig:
        """Generate config."""
        if override is None:
            return {
                "url": self.url,
                "group": self.group,
                "options": self.options,
                "compression": self.compression,
                "metadata": self.metadata,
            }

        url = override.get("url", self.url)
        group = override.get("group", self.group)
        options = override.get("options", self.options)
        compression = (
            Compression[comp]
            if (comp := override.get("compression"))
            else self.compression
        )

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
        }
