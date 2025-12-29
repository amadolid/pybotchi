"""Pybotchi GRPC Common."""

from enum import StrEnum
from typing import Any, Sequence, TypedDict

from grpc.aio import ClientInterceptor

from .utils import read_cert


class GRPCCompression(StrEnum):
    """GRPC Compression."""

    NoCompression = "NoCompression"
    Deflate = "Deflate"
    Gzip = "Gzip"


class GRPCConfig(TypedDict, total=False):
    """GRPC Config."""

    secure: bool
    url: str
    groups: list[str]
    root_certificates: str | bytes | None
    private_key: str | bytes | None
    certificate_chain: str | bytes | None
    options: list[tuple[str, Any]] | None
    compression: GRPCCompression | None
    metadata: dict[str, Any] | None
    allow_exec: bool


class GRPCConfigLoaded(TypedDict):
    """GRPC Config."""

    url: str
    groups: list[str]
    secure: bool
    root_certificates: bytes | None
    private_key: bytes | None
    certificate_chain: bytes | None
    options: list[tuple[str, Any]] | None
    compression: GRPCCompression | None
    metadata: dict[str, Any] | None
    allow_exec: bool


class GRPCIntegration(TypedDict, total=False):
    """GRPC Integration."""

    config: GRPCConfig
    allowed_actions: dict[str, bool]
    exclude_unset: bool


class GRPCConnection:
    """GRPC Connection configurations."""

    def __init__(
        self,
        name: str,
        url: str = "",
        groups: list[str] | None = None,
        secure: bool = False,
        root_certificates: str | bytes | None = None,
        private_key: str | bytes | None = None,
        certificate_chain: str | bytes | None = None,
        options: list[tuple[str, Any]] | None = None,
        compression: GRPCCompression | None = None,
        interceptors: Sequence[ClientInterceptor] | None = None,
        metadata: dict[str, Any] | None = None,
        allow_exec: bool = False,
        manual_enable: bool = False,
        allowed_actions: dict[str, bool] | None = None,
        exclude_unset: bool = True,
        require_integration: bool = True,
    ) -> None:
        """Build GRPC Connection."""
        self.name = name
        self.url = url
        self.groups = [] if groups is None else groups
        self.secure = secure
        self.root_certificates = root_certificates
        self.private_key = private_key
        self.certificate_chain = certificate_chain
        self.options = options
        self.compression = compression
        self.interceptors = interceptors
        self.metadata = metadata
        self.allow_exec = allow_exec
        self.manual_enable = manual_enable
        self.allowed_actions = {} if allowed_actions is None else allowed_actions
        self.exclude_unset = exclude_unset
        self.require_integration = require_integration

    async def get_config(self, override: GRPCConfig | None) -> GRPCConfigLoaded:
        """Generate config."""
        if override is None:
            return {
                "url": self.url,
                "groups": self.groups,
                "secure": self.secure,
                "root_certificates": (
                    await read_cert(self.root_certificates)
                    if isinstance(self.root_certificates, str)
                    else self.root_certificates
                ),
                "private_key": (
                    await read_cert(self.private_key)
                    if isinstance(self.private_key, str)
                    else self.private_key
                ),
                "certificate_chain": (
                    await read_cert(self.certificate_chain)
                    if isinstance(self.certificate_chain, str)
                    else self.certificate_chain
                ),
                "options": self.options,
                "compression": self.compression,
                "metadata": self.metadata,
                "allow_exec": self.allow_exec,
            }

        url = override.get("url", self.url)
        groups = override.get("groups", self.groups)
        secure = override.get("secure", self.secure)
        root_certificates = override.get("root_certificates", self.root_certificates)
        private_key = override.get("private_key", self.private_key)
        certificate_chain = override.get("certificate_chain", self.certificate_chain)
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

        root_certificates = (
            await read_cert(self.root_certificates)
            if isinstance(self.root_certificates, str)
            else self.root_certificates
        )

        private_key = (
            await read_cert(self.private_key)
            if isinstance(self.private_key, str)
            else self.private_key
        )

        certificate_chain = (
            await read_cert(self.certificate_chain)
            if isinstance(self.certificate_chain, str)
            else self.certificate_chain
        )

        return {
            "url": url,
            "groups": groups,
            "secure": secure,
            "root_certificates": root_certificates,
            "private_key": private_key,
            "certificate_chain": certificate_chain,
            "options": options,
            "compression": compression,
            "metadata": metadata,
            "allow_exec": allow_exec,
        }
