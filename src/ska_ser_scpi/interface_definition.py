"""
This module implements SCPI interface definition handling.

Interfaces definitions are primarily mappings from instrument-
independent attributes like "frequency" to instrument-specific SCPI
fields like "FREQ".
"""
import pkgutil
from typing import TypedDict

import yaml
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


class InterfaceDefinitionFactory:  # pylint: disable=too-few-public-methods
    """Factory that returns a SCPI interface definition for a given model."""

    def __init__(self) -> None:
        """Initialise a new instance."""
        self._interfaces = {
            "AWG5208": "awg/tektronix_awg5208.yaml",
            "SMB100A": "signal_generator/rohde_and_schwarz_smb100a.yaml",
            "TGR2051": "signal_generator/aimtti_tgr2051.yaml",
            "TSG4104A": "signal_generator/tektronix_tsg4104a.yaml",
            "SPECMON26B": "spectrum_analyser/tektronix_specmon26b.yaml",
            "MS2090A": "spectrum_analyser/anritsu_ms2090a.yaml",
            "RSA5103B": "spectrum_analyser/tektronix_rsa5103b.yaml",
        }

    def __call__(self, model: str) -> InterfaceDefinitionType:
        """
        Get an interface definition for the specified model.

        :param model: the name of the model for which an interface
            definition is required.

        :returns: SCPI interface definition for the model.
        """
        file_name = self._interfaces[model]
        interface_definition_data = pkgutil.get_data(
            "ska_ser_test_equipment", file_name
        )
        assert interface_definition_data is not None  # for the type-checker
        interface_definition: InterfaceDefinitionType = yaml.safe_load(
            interface_definition_data
        )
        return interface_definition
