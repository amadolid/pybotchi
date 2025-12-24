from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Event(_message.Message):
    __slots__ = ("name", "data")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    name: str
    data: _struct_pb2.Struct
    def __init__(
        self,
        name: _Optional[str] = ...,
        data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...,
    ) -> None: ...

class ActionListRequest(_message.Message):
    __slots__ = ("group",)
    GROUP_FIELD_NUMBER: _ClassVar[int]
    group: str
    def __init__(self, group: _Optional[str] = ...) -> None: ...

class ActionListResponse(_message.Message):
    __slots__ = ("agent_id", "actions")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    ACTIONS_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    actions: _containers.RepeatedCompositeFieldContainer[ActionSchema]
    def __init__(
        self,
        agent_id: _Optional[str] = ...,
        actions: _Optional[_Iterable[_Union[ActionSchema, _Mapping]]] = ...,
    ) -> None: ...

class ActionSchema(_message.Message):
    __slots__ = ("concurrent", "schema")
    CONCURRENT_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    concurrent: bool
    schema: JSONSchema
    def __init__(
        self,
        concurrent: bool = ...,
        schema: _Optional[_Union[JSONSchema, _Mapping]] = ...,
    ) -> None: ...

class JSONSchema(_message.Message):
    __slots__ = (
        "schema",
        "id",
        "title",
        "description",
        "type",
        "properties",
        "required",
        "additional_properties",
        "items",
        "min_items",
        "max_items",
        "min_length",
        "max_length",
        "pattern",
        "format",
        "minimum",
        "maximum",
        "multiple_of",
        "enum",
        "default_value",
        "definitions",
        "ref",
        "all_of",
        "any_of",
        "one_of",
    )

    class PropertiesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: JSONSchema
        def __init__(
            self,
            key: _Optional[str] = ...,
            value: _Optional[_Union[JSONSchema, _Mapping]] = ...,
        ) -> None: ...

    class DefinitionsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: JSONSchema
        def __init__(
            self,
            key: _Optional[str] = ...,
            value: _Optional[_Union[JSONSchema, _Mapping]] = ...,
        ) -> None: ...

    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    REQUIRED_FIELD_NUMBER: _ClassVar[int]
    ADDITIONAL_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    MIN_ITEMS_FIELD_NUMBER: _ClassVar[int]
    MAX_ITEMS_FIELD_NUMBER: _ClassVar[int]
    MIN_LENGTH_FIELD_NUMBER: _ClassVar[int]
    MAX_LENGTH_FIELD_NUMBER: _ClassVar[int]
    PATTERN_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_FIELD_NUMBER: _ClassVar[int]
    MAXIMUM_FIELD_NUMBER: _ClassVar[int]
    MULTIPLE_OF_FIELD_NUMBER: _ClassVar[int]
    ENUM_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_VALUE_FIELD_NUMBER: _ClassVar[int]
    DEFINITIONS_FIELD_NUMBER: _ClassVar[int]
    REF_FIELD_NUMBER: _ClassVar[int]
    ALL_OF_FIELD_NUMBER: _ClassVar[int]
    ANY_OF_FIELD_NUMBER: _ClassVar[int]
    ONE_OF_FIELD_NUMBER: _ClassVar[int]
    NOT_FIELD_NUMBER: _ClassVar[int]
    schema: str
    id: str
    title: str
    description: str
    type: str
    properties: _containers.MessageMap[str, JSONSchema]
    required: _containers.RepeatedScalarFieldContainer[str]
    additional_properties: bool
    items: JSONSchema
    min_items: int
    max_items: int
    min_length: int
    max_length: int
    pattern: str
    format: str
    minimum: float
    maximum: float
    multiple_of: float
    enum: _containers.RepeatedScalarFieldContainer[str]
    default_value: str
    definitions: _containers.MessageMap[str, JSONSchema]
    ref: str
    all_of: _containers.RepeatedCompositeFieldContainer[JSONSchema]
    any_of: _containers.RepeatedCompositeFieldContainer[JSONSchema]
    one_of: _containers.RepeatedCompositeFieldContainer[JSONSchema]
    def __init__(
        self,
        schema: _Optional[str] = ...,
        id: _Optional[str] = ...,
        title: _Optional[str] = ...,
        description: _Optional[str] = ...,
        type: _Optional[str] = ...,
        properties: _Optional[_Mapping[str, JSONSchema]] = ...,
        required: _Optional[_Iterable[str]] = ...,
        additional_properties: bool = ...,
        items: _Optional[_Union[JSONSchema, _Mapping]] = ...,
        min_items: _Optional[int] = ...,
        max_items: _Optional[int] = ...,
        min_length: _Optional[int] = ...,
        max_length: _Optional[int] = ...,
        pattern: _Optional[str] = ...,
        format: _Optional[str] = ...,
        minimum: _Optional[float] = ...,
        maximum: _Optional[float] = ...,
        multiple_of: _Optional[float] = ...,
        enum: _Optional[_Iterable[str]] = ...,
        default_value: _Optional[str] = ...,
        definitions: _Optional[_Mapping[str, JSONSchema]] = ...,
        ref: _Optional[str] = ...,
        all_of: _Optional[_Iterable[_Union[JSONSchema, _Mapping]]] = ...,
        any_of: _Optional[_Iterable[_Union[JSONSchema, _Mapping]]] = ...,
        one_of: _Optional[_Iterable[_Union[JSONSchema, _Mapping]]] = ...,
        **kwargs
    ) -> None: ...

class TraverseRequest(_message.Message):
    __slots__ = (
        "nodes",
        "alias",
        "group",
        "name",
        "allowed_actions",
        "integrations",
        "bypass",
    )

    class AllowedActionsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: bool
        def __init__(self, key: _Optional[str] = ..., value: bool = ...) -> None: ...

    NODES_FIELD_NUMBER: _ClassVar[int]
    ALIAS_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_ACTIONS_FIELD_NUMBER: _ClassVar[int]
    INTEGRATIONS_FIELD_NUMBER: _ClassVar[int]
    BYPASS_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[Node]
    alias: str
    group: str
    name: str
    allowed_actions: _containers.ScalarMap[str, bool]
    integrations: _struct_pb2.Struct
    bypass: bool
    def __init__(
        self,
        nodes: _Optional[_Iterable[_Union[Node, _Mapping]]] = ...,
        alias: _Optional[str] = ...,
        group: _Optional[str] = ...,
        name: _Optional[str] = ...,
        allowed_actions: _Optional[_Mapping[str, bool]] = ...,
        integrations: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...,
        bypass: bool = ...,
    ) -> None: ...

class TraverseGraph(_message.Message):
    __slots__ = ("origin", "nodes", "edges")
    ORIGIN_FIELD_NUMBER: _ClassVar[int]
    NODES_FIELD_NUMBER: _ClassVar[int]
    EDGES_FIELD_NUMBER: _ClassVar[int]
    origin: str
    nodes: _containers.RepeatedCompositeFieldContainer[Node]
    edges: _containers.RepeatedCompositeFieldContainer[Edge]
    def __init__(
        self,
        origin: _Optional[str] = ...,
        nodes: _Optional[_Iterable[_Union[Node, _Mapping]]] = ...,
        edges: _Optional[_Iterable[_Union[Edge, _Mapping]]] = ...,
    ) -> None: ...

class Node(_message.Message):
    __slots__ = ("id", "name")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    def __init__(
        self, id: _Optional[str] = ..., name: _Optional[str] = ...
    ) -> None: ...

class Edge(_message.Message):
    __slots__ = ("source", "target", "concurrent", "name")
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    TARGET_FIELD_NUMBER: _ClassVar[int]
    CONCURRENT_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    source: str
    target: str
    concurrent: bool
    name: str
    def __init__(
        self,
        source: _Optional[str] = ...,
        target: _Optional[str] = ...,
        concurrent: bool = ...,
        name: _Optional[str] = ...,
    ) -> None: ...
