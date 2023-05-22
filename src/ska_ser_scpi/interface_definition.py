"""
This module implements SCPI interface definition handling.

Interfaces definitions are primarily mappings from instrument-
independent attributes like "frequency" to instrument-specific SCPI
fields like "FREQ".
"""
from typing import TypedDict

from typing_extensions import NotRequired

SupportedAttributeType = bool | float | str


class ReadWriteType(TypedDict):
    """Type specification for SCPI command read/write access levels."""

    read: NotRequired[str]
    write: NotRequired[str]
    read_write: NotRequired[str]


class AttributeDefinitionType(TypedDict):
    """Type specification for an attribute definition dictionary."""

    field: str
    field_type: str
    min_value: NotRequired[float]
    max_value: NotRequired[float]
    absolute_resolution: NotRequired[float]
    bit: NotRequired[int]
    value: NotRequired[SupportedAttributeType]


InterfaceDefinitionType = TypedDict(
    "InterfaceDefinitionType",
    {
        "model": str,
        "supports_chains": bool,
        "poll_rate": float,
        "timeout": float,
        "attributes": dict[str, AttributeDefinitionType],
        "sentinel_string": str,
    },
)


def expand_read_write(
    interface_definition: InterfaceDefinitionType,
) -> InterfaceDefinitionType:
    """Processing of read_write SCPI commands in the interface definition"""
    for attribute, definition in interface_definition["attributes"].items():
        if "read_write" in definition:
            exploded_attribute = {
                "read": interface_definition["attributes"][attribute]["read_write"],
                "write": interface_definition["attributes"][attribute]["read_write"],
            }
            interface_definition["attributes"][attribute] = exploded_attribute
    return interface_definition
