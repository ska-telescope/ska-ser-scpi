"""Tests of the ska_ser_test_equipment.scpi server stack."""

import unittest.mock

import pytest

from ska_ser_scpi import (  # AttributeClient,; ScpiClient,
    AttributeRequest,
    AttributeResponse,
    InterfaceDefinitionType,
    ScpiBytesServer,
    ScpiServer,
    expand_read_write_command,
)


@pytest.fixture(name="interface_definition")
def interface_definition_fixture() -> InterfaceDefinitionType:
    """
    Return an interface definition for use in testing.

    :returns: an interface definition.
    """
    interface_definition: InterfaceDefinitionType = {
        "model": "fruit",
        "poll_rate": 0.1,
        "timeout": 0.5,
        "supports_chains": True,
        "attributes": {
            "name": {"read": {"field": "NAME", "field_type": "str"}},
            "juiciness": {"read_write": {"field": "JUIC", "field_type": "float"}},
            "rotten": {"read_write": {"field": "ROTT", "field_type": "int"}},
            "peeled": {"read_write": {"field": "PEEL", "field_type": "bool"}},
            "overripe": {
                "read_write": {"field": "FLAGS", "field_type": "bit", "bit": 0}
            },
            "under-ripe": {
                "read_write": {"field": "FLAGS", "field_type": "bit", "bit": 1}
            },
            "chilled": {
                "read_write": {"field": "FLAGS", "field_type": "bit", "bit": 7}
            },
            "boiled": {
                "read": {
                    "field": "PROCESS",
                    "field_type": "packet_item",
                    "packet_item": 0,
                },
                "write": {"field": "BOIL", "field_type": "float"},
            },
            "fried": {
                "read": {
                    "field": "PROCESS",
                    "field_type": "packet_item",
                    "packet_item": 1,
                },
                "write": {"field": "FRY", "field_type": "float"},
            },
            "dried": {
                "read": {
                    "field": "PROCESS",
                    "field_type": "packet_item",
                    "packet_item": 2,
                },
                "write": {"field": "DRY", "field_type": "float"},
            },
            "fermented": {
                "read": {
                    "field": "PROCESS",
                    "field_type": "packet_item",
                    "packet_item": 3,
                },
                "write": {"field": "FERMENT", "field_type": "float"},
            },
        },
        "sentinel_string": "\r\n",
        "argument_separator": " ",
        "return_response": True,
    }

    interface_definition = expand_read_write_command(interface_definition)
    return interface_definition


@pytest.fixture(name="request_bytes")
def request_bytes_fixture() -> bytes:
    """
    Return some request bytes for use in testing.

    :returns: request bytes.
    """
    return b"NAME?;JUIC?;ROTT?;PEEL?;FLAGS?;PROCESS?"


@pytest.fixture(name="expected_response_bytes")
def expected_response_bytes_fixture() -> bytes:
    """
    Return the expected response bytes.

    :returns: the expected response bytes.
    """
    return b"orange;98.7;30;1;130;0.1 0.2 0.3 0.4"


@pytest.fixture(name="expected_attribute_request")
def expected_attribute_request_fixture() -> AttributeRequest:
    """
    Return the expected attribute request to the attribute server.

    :returns: the expected attribute request.
    """
    attribute_request = AttributeRequest()
    attribute_request.set_queries(
        "name",
        "juiciness",
        "rotten",
        "peeled",
        "overripe",
        "under-ripe",
        "chilled",
        "boiled",
        "fried",
        "dried",
        "fermented",
    )
    return attribute_request


@pytest.fixture(name="mock_attribute_server")
def mock_attribute_server_fixture() -> unittest.mock.Mock:
    """
    Return a mock attribute server to sit at the bottom of the server stack.

    :returns: a mock attribute server.
    """
    attribute_response = AttributeResponse()
    attribute_response.add_query_response("name", "orange")
    attribute_response.add_query_response("juiciness", 98.7)
    attribute_response.add_query_response("rotten", 30)
    attribute_response.add_query_response("peeled", True)
    attribute_response.add_query_response("overripe", False)
    attribute_response.add_query_response("under-ripe", True)
    attribute_response.add_query_response("chilled", True)
    attribute_response.add_query_response("boiled", 0.1)
    attribute_response.add_query_response("fried", 0.2)
    attribute_response.add_query_response("dried", 0.3)
    attribute_response.add_query_response("fermented", 0.4)

    mock_bytes_client = unittest.mock.Mock()
    mock_bytes_client.receive_send.return_value = attribute_response
    return mock_bytes_client


@pytest.fixture(name="bytes_server")
def bytes_server_fixture(
    mock_attribute_server: unittest.mock.Mock,
    interface_definition: InterfaceDefinitionType,
) -> ScpiBytesServer:
    """
    Return the SCPI bytes server under test.

    :param mock_attribute_server: a mock attribute server that sits at
        the bottom of the server stack.
    :param interface_definition: definition of the attribute, including
        its mapping to SCPI field.

    :returns: a SCPI bytes server.
    """
    scpi_server = ScpiServer(mock_attribute_server, interface_definition["attributes"])
    return ScpiBytesServer(scpi_server)


def test_server_stack(
    bytes_server: ScpiBytesServer,
    mock_attribute_server: unittest.mock.Mock,
    request_bytes: bytes,
    expected_attribute_request: AttributeRequest,
    expected_response_bytes: bytes,
) -> None:
    """
    Test flow of SCPI commands on the server side.

    The server stack receives bytes, unmarshalls it into a
    device-dependent ScpiRequest, then unmarshalls that into a
    device-independent AttributeRequest.

    A device-independent AttributeResponse is created. This is
    marshalled down to a device-dependent ScpiResponse, which is
    marshalled down to bytes to be sent in response to the original
    request bytes.

    :param bytes_server: the SCPI bytes server that receives the
        initial request bytes.
    :param mock_attribute_server: a mock attribute server that sets at
        the bottom of the server stack.
    :param request_bytes: the bytes to be sent to the bytes server.
    :param expected_attribute_request: the attribute request that we
        expect to see the request bytes marshalled to.
    :param expected_response_bytes: the response bytes that we expect
        to be sent in response to the request.
    """
    response_bytes = bytes_server.receive_send(request_bytes)
    assert response_bytes == expected_response_bytes
    mock_attribute_server.receive_send.assert_called_once_with(
        expected_attribute_request
    )
