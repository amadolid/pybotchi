from .action import GRPCRemoteAction as GRPCRemoteAction
from .utils import read_cert as read_cert
from _typeshed import Incomplete
from enum import StrEnum
from grpc.aio import ClientInterceptor as ClientInterceptor
from typing import Any, Sequence, TypedDict

class GRPCCompression(StrEnum):
    NoCompression = 'NoCompression'
    Deflate = 'Deflate'
    Gzip = 'Gzip'

class GRPCConfig(TypedDict, total=False):
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
    config: GRPCConfig
    allowed_actions: dict[str, bool]
    exclude_unset: bool

class GRPCConnection:
    name: Incomplete
    url: Incomplete
    groups: Incomplete
    secure: Incomplete
    root_certificates: Incomplete
    private_key: Incomplete
    certificate_chain: Incomplete
    options: Incomplete
    compression: Incomplete
    interceptors: Incomplete
    metadata: Incomplete
    allow_exec: Incomplete
    manual_enable: Incomplete
    allowed_actions: Incomplete
    remote_action_class: Incomplete
    exclude_unset: Incomplete
    require_integration: Incomplete
    def __init__(self, name: str, url: str = '', groups: list[str] | None = None, secure: bool = False, root_certificates: str | bytes | None = None, private_key: str | bytes | None = None, certificate_chain: str | bytes | None = None, options: list[tuple[str, Any]] | None = None, compression: GRPCCompression | None = None, interceptors: Sequence[ClientInterceptor] | None = None, metadata: dict[str, Any] | None = None, allow_exec: bool = False, manual_enable: bool = False, allowed_actions: dict[str, bool] | None = None, remote_action_class: type['GRPCRemoteAction'] | None = None, exclude_unset: bool = True, require_integration: bool = True) -> None: ...
    async def get_config(self, override: GRPCConfig | None) -> GRPCConfigLoaded: ...
