"""
This module implements SCPI interface definition handling.

Interfaces definitions are primarily mappings from instrument-
independent attributes like "frequency" to instrument-specific SCPI
fields like "FREQ".
"""
from typing import Any, TypedDict

import numpy as np
from typing_extensions import NotRequired

SupportedScalarType = bool | float | int | str | np.number[Any]
SupportedAttributeType = SupportedScalarType | list[SupportedScalarType]


class AttributeDefinitionType(TypedDict):
    """Type specification for an attribute definition dictionary."""

    field: str
    field_type: str
    block_data_type: NotRequired[str]
    max_dim_x: NotRequired[int]
    min_value: NotRequired[float]
    max_value: NotRequired[float]
    absolute_resolution: NotRequired[float]
    bit: NotRequired[int]
    packet_item: NotRequired[int]
    value: NotRequired[SupportedAttributeType]


InterfaceDefinitionType = TypedDict(
    "InterfaceDefinitionType",
    {
        "model": str,
        "supports_chains": bool,
        "poll_rate": float,
        "timeout": float,
        "attributes": dict[str, dict[str, AttributeDefinitionType]],
        "sentinel_string": str,
        "argument_separator": str,
        "return_response": bool,
    },
)


def expand_read_write_command(
    interface_definition: InterfaceDefinitionType,
) -> InterfaceDefinitionType:
    """
    Process read_write SCPI commands in the interface definition.

    :param interface_definition: the original interface_definition dictionary

    :returns: the updated interface definition which has expanded "read_write" commands
        into separate "read" and "write" commands.
    """
    for attribute, definition in interface_definition["attributes"].items():
        if "read_write" in definition:
            expanded_attribute = {
                "read": interface_definition["attributes"][attribute]["read_write"],
                "write": interface_definition["attributes"][attribute]["read_write"],
            }
            interface_definition["attributes"][attribute] = expanded_attribute
    return interface_definition
