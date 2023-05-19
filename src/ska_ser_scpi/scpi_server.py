"""This module provides a SCPI server."""
from __future__ import annotations

from typing import TypedDict

from typing_extensions import NotRequired

from .attribute_payload import AttributeRequest, AttributeResponse
from .attribute_server import AttributeServerProtocol
from .interface_definition import AttributeDefinitionType, ReadWriteType
from .scpi_payload import ScpiRequest, ScpiResponse


class _FieldDefinitionType(TypedDict):
    # TODO: Tighten this up.
    # field_type not always required?
    # "attributes" required iff field_type == "bits",
    # "attribute" not allowed if field_type == "bits"
    field_type: NotRequired[str]
    attribute: NotRequired[str]
    attributes: NotRequired[dict[int, str]]


class ScpiServer:  # pylint: disable=too-few-public-methods
    """
    Service for receiving/sending SCPI payloads from/to a client.

    Used to receive a SCPI request object, and respond with a SCPI
    response object.
    """

    def __init__(
        self,
        attribute_server: AttributeServerProtocol,
        attribute_definitions: dict[str, AttributeDefinitionType],
    ) -> None:
        """
        Initialise a new instance.

        :param attribute_server: the underlying attribute server to be
            used.
        :param attribute_definitions: definitions of the attributes that
            the SCPI interface supports.
        """
        self._attribute_server = attribute_server

        self._attribute_map = attribute_definitions

        self._field_map: dict[str, ReadWriteType, _FieldDefinitionType] = {}
        for attribute, definition in self._attribute_map.items():
            for method in list(definition.keys()):
                field = definition[method]["field"]
                if "field_type" in definition[method]:
                    attribute_type = definition[method]["field_type"]
                    if attribute_type == "bit":
                        bit = definition[method]["bit"]
                        if field not in self._field_map:
                            self._field_map[field] = {
                                f"{method}": {
                                    "field_type": "bits",
                                    "attributes": {},
                                }
                            }
                        self._field_map[field][method]["attributes"][bit] = attribute
                    else:
                        if field not in self._field_map:
                            self._field_map[field] = {}
                        self._field_map[field].update(
                            {
                                f"{method}": {
                                    "field_type": attribute_type,
                                    "attribute": attribute,
                                }
                            }
                        )
                else:
                    self._field_map[field] = {f"{method}": {"attribute": attribute}}

    def receive_send(self, scpi_request: ScpiRequest) -> ScpiResponse:
        """
        Send a SCPI request, and receive a SCPI response.

        :param scpi_request: details of the SCPI request to be sent.

        :returns: details of the SCPI response.
        """
        attribute_request = self._unmarshall_request(scpi_request)
        attribute_response = self._attribute_server.receive_send(attribute_request)
        scpi_response = self._marshall_response(attribute_response)
        return scpi_response

    def _unmarshall_request(
        self,
        scpi_request: ScpiRequest,
    ) -> AttributeRequest:
        """
        Unmarshall a SCPI request into an attribute request.

        :param scpi_request: the SCPI request object to be unmarshalled.

        :returns: an attribute request object.

        :raises ValueError: if an unsupported attribute type is
            encountered.
        """
        attribute_request = AttributeRequest()

        queries: list[str] = []
        for field in scpi_request.queries:
            definition = self._field_map[field]
            if definition["read"]["field_type"] == "bits":
                queries.extend(definition["read"]["attributes"].values())
            else:
                queries.append(definition["read"]["attribute"])
        attribute_request.set_queries(*queries)

        for field, args in scpi_request.setops:
            definition = self._field_map[field]
            field_type = definition["write"].get("field_type", None)
            if field_type == "bits":
                value = int(args[0])  # TODO: Handle >1 args error case
                for bit, attribute in definition["write"]["attributes"].items():
                    mask = 1 << bit
                    attribute_value = bool(value & mask)
                    attribute_request.add_setop(attribute, attribute_value)
            else:
                attribute = definition["write"]["attribute"]
                if field_type is None:  # command with no args
                    attribute_request.add_setop(attribute)
                elif field_type == "bool":
                    bool_args = [arg == "1" for arg in args]
                    attribute_request.add_setop(attribute, *bool_args)
                elif field_type == "float":
                    float_args = [float(arg) for arg in args]
                    attribute_request.add_setop(attribute, *float_args)
                elif field_type == "str":
                    attribute_request.add_setop(attribute, *args)
                else:
                    raise ValueError(
                        f"Cannot unmarshall SCPI field {field} to "
                        f"attribute type {field_type}."
                    )

        return attribute_request

    def _marshall_response(self, attribute_response: AttributeResponse) -> ScpiResponse:
        """
        Marshall an attribute response down into a SCPI response.

        :param attribute_response: the attribute response object to be
            marshalled.

        :returns: a SCPI response object.
        """
        scpi_response = ScpiResponse()

        for attribute in attribute_response.responses:
            definition = list(self._attribute_map[attribute].values())[0]
            attribute_type = definition["field_type"]
            field = definition["field"]
            attribute_value = attribute_response.responses[attribute]

            if attribute_type == "bit":
                field_value = scpi_response.responses.get(field, "0")
                if attribute_value:
                    bit = definition["bit"]
                    bitmask = 1 << bit
                    field_value = str(int(field_value) | bitmask)
                scpi_response.add_query_response(field, field_value)
            elif attribute_type == "bool":
                scpi_response.add_query_response(field, "1" if attribute_value else "0")
            else:
                scpi_response.add_query_response(field, str(attribute_value))

        return scpi_response
