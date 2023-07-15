"""This module provides a SCPI server."""
from __future__ import annotations

import logging
from typing import TypedDict

from typing_extensions import NotRequired

from .attribute_payload import AttributeRequest, AttributeResponse
from .attribute_server import AttributeServerProtocol
from .interface_definition import AttributeDefinitionType
from .scpi_payload import ScpiRequest, ScpiResponse

logger = logging.getLogger(__name__)


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
        attribute_definitions: dict[str, dict[str, AttributeDefinitionType]],
    ) -> None:
        """
        Initialise a new instance.

        :param attribute_server: the underlying attribute server to be used.
        :param attribute_definitions: attributes that SCPI interface supports.
        """
        self._attribute_server = attribute_server

        self._attribute_map = attribute_definitions

        self._field_map: dict[str, dict[str, _FieldDefinitionType]] = {}
        logger.debug("Process SCPI attribute map %s", self._attribute_map)
        for attribute, definition in self._attribute_map.items():
            logger.debug("Process SCPI attribute %s", attribute)
            logger.debug("Process SCPI definition %s", definition)
            # for method in list(definition.keys()):
            for method, definition_method in definition.items():
                logger.debug("Process SCPI method %s", method)
                # definition_method = dict(definition[method])
                field = definition_method["field"]
                if field not in self._field_map:
                    logger.info("Add field %s", field)
                    self._field_map[field] = {}
                if "field_type" in definition_method:
                    attribute_type = definition_method["field_type"]
                    if attribute_type == "bit":
                        bit = definition_method["bit"]
                        if method not in self._field_map[field]:
                            self._field_map[field][method] = {
                                "field_type": "bits",
                                "attributes": {},
                            }
                        self._field_map[field][method]["attributes"].update(
                            {bit: attribute}
                        )
                    else:
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
        for field in self._field_map:
            logger.info("Defined field %s [%s]", field, self._field_map[field])

    def receive_send(self, scpi_request: ScpiRequest) -> ScpiResponse:
        """
        Send a SCPI request, and receive a SCPI response.

        :param scpi_request: details of the SCPI request to be sent.
        :returns: details of the SCPI response.
        """
        logger.info("SCPI receive %s", scpi_request)
        attribute_request = self._unmarshall_request(scpi_request)
        try:
            attribute_response = self._attribute_server.receive_send(attribute_request)
        except ValueError as a_err:
            logger.error("Could not receive/send : %s", str(a_err))
            return None
        scpi_response = self._marshall_response(attribute_response)
        logger.info("SCPI response: %s", attribute_response)
        return scpi_response

    # pylint: disable-next=too-many-locals, too-many-branches
    def _unmarshall_request(  # noqa: C901
        self,
        scpi_request: ScpiRequest,
    ) -> AttributeRequest:
        """
        Unmarshall a SCPI request into an attribute request.

        :param scpi_request: the SCPI request object to be unmarshalled.
        :returns: an attribute request object.
        :raises ValueError: if an unsupported attribute type is encountered.
        """
        attribute_request = AttributeRequest()

        queries: list[str] = []
        for field in scpi_request.queries:
            try:
                definition = self._field_map[field]
            except KeyError:
                logger.warning("Could not read definition for field '%s'",
                                field)
                continue
            if definition["read"]["field_type"] == "bits":
                queries.extend(definition["read"]["attributes"].values())
            else:
                queries.append(definition["read"]["attribute"])
        logger.debug("Loaded %d queries : %s", len(queries), queries)
        attribute_request.set_queries(*queries)

        for field, args in scpi_request.setops:
            # if field not in self._field_map:
            #     logger.warning("Field '%s' not found", field)
            #     args = field.split(':')[-1]
            #     field = ':'.join(field.split(':')[:-1])
            # if field not in self._field_map:
            #     args = field.split(':')[-1]
            #     logger.warning("Field '%s' not found", field)
            #     field = ':'.join(field.split(':')[:-1])
            logger.debug("Field %s args: %s", field, args)
            # if field not in self._field_map:
            #     logger.warning("No definition for field '%s'", field)
            try:
                definition = self._field_map[field]
            except KeyError:
                logger.error("No definition for field '%s'", field)
                field = field.split(':')[:-1]
                continue
            try:
                field_type = definition["write"].get("field_type", None)
            except KeyError:
                logger.error("No definition for field type 'write'")
                continue
            if field_type == "bits":
                # TODO: Handle >1 args error case
                value = int(args[0])
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
                elif field_type == "int":
                    int_args = [int(arg) for arg in args]
                    attribute_request.add_setop(attribute, *int_args)
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

        :param attribute_response: attribute response object to be marshalled.
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
                scpi_response.add_query_response(
                    field,
                    "1" if attribute_value else "0"
                )
            else:
                scpi_response.add_query_response(field, str(attribute_value))

        return scpi_response
