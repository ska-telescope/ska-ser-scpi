"""
This module implements SCPI interface definition handling.

Interfaces definitions are primarily mappings from instrument-
independent attributes like "frequency" to instrument-specific SCPI
fields like "FREQ".
"""
from typing import TypedDict

from typing_extensions import NotRequired

SupportedAttributeType = bool | float | str


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
