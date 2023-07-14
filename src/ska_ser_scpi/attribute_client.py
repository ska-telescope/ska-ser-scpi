"""This module provides an attribute client."""
from typing import TypedDict
import re
import numpy as np
from typing_extensions import NotRequired

from .attribute_payload import AttributeRequest, AttributeResponse
from .interface_definition import AttributeDefinitionType, SupportedAttributeType
from .scpi_client import ScpiClient
from .scpi_payload import ScpiRequest, ScpiResponse


class _FieldDefinitionType(TypedDict):
    # TODO: Tighten this up.
    # field_type not always required?
    # "attributes" required iff field_type == "bits",
    # "attribute" not allowed if field_type == "bits"
    field_type: NotRequired[str]
    block_data_type: NotRequired[str]
    attribute: NotRequired[str]
    attributes: NotRequired[dict[int, str]]


class AttributeClient:  # pylint: disable=too-few-public-methods
    """
    Client interface for attribute payloads.

    Used to transmit an attribute request, and then receive an attribute
    response.
    """

    def __init__(
        self,
        scpi_client: ScpiClient,
        attribute_definitions: dict[str, dict[str, AttributeDefinitionType]],
    ) -> None:
        """
        Initialise a new instance.

        :param scpi_client: The underlying SCPI client interface.
        :param attribute_definitions: definitions of the attributes that
            the SCPI interface supports.
        """
        self._scpi_client = scpi_client

        self._attribute_map = attribute_definitions

        self._field_map: dict[str, dict[str, _FieldDefinitionType]] = {}
        for attribute, definition in self._attribute_map.items():
            for method in list(definition.keys()):
                field = definition[method]["field"]
                if field not in self._field_map:
                    self._field_map[field] = {}
                if "field_type" in definition[method]:
                    attribute_type = definition[method]["field_type"]
                    if attribute_type == "bit" or attribute_type == "packet_item":
                        idx = definition[method][attribute_type]
                        if method not in self._field_map[field]:
                            self._field_map[field][method] = {
                                "field_type": attribute_type,
                                "attributes": {},
                            }
                        self._field_map[field][method]["attributes"].update(
                            {idx: attribute}
                        )
                    else:
                        field_info: _FieldDefinitionType = {
                            "field_type": attribute_type,
                            "attribute": attribute,
                        }
                        if attribute_type == "arbitrary_block":
                            field_info["block_data_type"] = definition[method][
                                "block_data_type"
                            ]
                        self._field_map[field][method] = field_info
                else:
                    self._field_map[field] = {method: {"attribute": attribute}}

    def send_receive(self, attribute_request: AttributeRequest) -> AttributeResponse:
        """
        Send an attribute request, and receive an attribute response.

        :param attribute_request: details of the attribute request to be
            sent.

        :returns: details of the attribute response.
        """
        scpi_request = self._marshall_request(attribute_request)
        scpi_response = self._scpi_client.send_receive(scpi_request)
        attribute_response = self._unmarshall_response(scpi_response)
        return attribute_response

    def _marshall_request(self, attribute_request: AttributeRequest) -> ScpiRequest:
        """
        Marshall an attribute request down into a SCPI request.

        :param attribute_request: the attribute request object to be
            marshalled.

        :returns: a SCPI request object.
        """
        scpi_request = ScpiRequest()

        for attribute in attribute_request.queries:
            field = self._attribute_map[attribute]["read"]["field"]
            scpi_request.add_query(field)

        for attribute, args in attribute_request.setops:
            definition = self._attribute_map[attribute]
            field = definition["write"]["field"]
            field_type = definition["write"].get("field_type", None)
            if field_type is None:
                scpi_request.add_setop(field)  # command with no args
            elif field_type == "bit":
                bit = definition["write"]["bit"]
                for this_field, these_args in scpi_request.setops:
                    if field == this_field:
                        current_flag = int(these_args[0])
                        break
                else:
                    current_flag = 0
                mask = 1 << bit
                if args[0]:  # TODO: handle >1 args error case
                    scpi_request.add_setop(
                        field, str(int(mask | current_flag)), replace=True
                    )
                else:
                    scpi_request.add_setop(field, str(int(~mask & current_flag)))
            else:
                if field_type == "bool":
                    str_args = ["1" if arg else "0" for arg in args]
                else:
                    str_args = [str(arg) for arg in args]
                scpi_request.add_setop(field, *str_args)

        return scpi_request

    def _unmarshall_response(
        self,
        scpi_response: ScpiResponse,
    ) -> AttributeResponse:
        """
        Unmarshall a SCPI response into an attribute response.

        :param scpi_response: the SCPI response object to be
            unmarshalled.

        :raises ValueError: if response data is invalid

        :returns: an attribute response object.
        """
        attribute_response = AttributeResponse()

        for field, field_value in scpi_response.responses.items():
            definition = list(self._field_map[field].values())[0]
            field_type = definition["field_type"]
            value: SupportedAttributeType  # for the type checker
            if field_type == "bit":
                for bit, attribute in definition["attributes"].items():
                    mask = 1 << bit
                    value = bool(int(field_value) & mask)
                    attribute_response.add_query_response(attribute, value)
            elif field_type == "packet_item":
                packet = re.split(" ", field_value.decode("utf-8"))
                for idx, attribute in definition["attributes"].items():
                    value = float(packet[idx])
                    attribute_response.add_query_response(attribute, value)
            else:
                attribute = definition["attribute"]
                if field_type == "bool":
                    value = field_value == b"1"
                elif field_type == "float":
                    value = float(field_value)
                elif field_type == "int":
                    value = int(field_value)
                elif field_type == "packet_index":
                    value = field_value
                elif field_type == "arbitrary_block":
                    if not field_value.startswith(b"#"):
                        raise ValueError(
                            f"Malformed value for arbitrary_block field {field} "
                            f"does not start with '#'"
                        )
                    # an index into bytes returns an int, not bytes, so we must slice
                    len_head = 2 + int(field_value[1:2])
                    len_data = int(field_value[2:len_head])
                    data_bytes = field_value[len_head:]
                    if len(data_bytes) != len_data:
                        raise ValueError(
                            f"Received {len(data_bytes)} bytes, "
                            f"expected {len_data} for arbitrary_block field {field}"
                        )
                    dtype = getattr(np, definition["block_data_type"])
                    # Return a list because attribute values are used in equality
                    # comparisons for if conditions in various places. np.ndarray
                    # breaks that by overriding == to return an element-wise array
                    # which raises ValueError when coerced to bool.
                    value = list(np.frombuffer(data_bytes, dtype=dtype))
                else:
                    value = field_value.decode("utf-8")
                attribute_response.add_query_response(attribute, value)

        return attribute_response
