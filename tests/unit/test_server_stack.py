"""Tests of the ska_ser_test_equipment.scpi server stack."""

import unittest.mock

import pytest

from ska_ser_scpi import (  # AttributeClient,; ScpiClient,
    AttributeRequest,
    AttributeResponse,
    InterfaceDefinitionType,
    ScpiBytesServer,
    ScpiServer,
)


@pytest.fixture(name="interface_definition")
def interface_definition_fixture() -> InterfaceDefinitionType:
    """
    Return an interface definition for use in testing.

    :returns: an interface definition.
    """
    return {
        "model": "fruit",
        "poll_rate": 0.1,
        "timeout": 0.5,
        "supports_chains": True,
        "attributes": {
            "name": {"field": "NAME", "field_type": "str"},
            "juiciness": {"field": "JUIC", "field_type": "float"},
            "peeled": {"field": "PEEL", "field_type": "bool"},
            "overripe": {"field": "FLAGS", "field_type": "bit", "bit": 0},
            "under-ripe": {"field": "FLAGS", "field_type": "bit", "bit": 1},
            "chilled": {"field": "FLAGS", "field_type": "bit", "bit": 7},
        },
        "sentinel_string": "\r\n",
    }


@pytest.fixture(name="request_bytes")
def request_bytes_fixture() -> bytes:
    """
    Return some request bytes for use in testing.

    :returns: request bytes.
    """
    return b"NAME?;JUIC?;PEEL?;FLAGS?"


@pytest.fixture(name="expected_response_bytes")
def expected_response_bytes_fixture() -> bytes:
    """
    Return the expected response bytes.

    :returns: the expected response bytes.
    """
    return b"orange;98.7;1;130"


@pytest.fixture(name="expected_attribute_request")
def expected_attribute_request_fixture() -> AttributeRequest:
    """
    Return the expected attribute request to the attribute server.

    :returns: the expected attribute request.
    """
    attribute_request = AttributeRequest()
    attribute_request.set_queries(
        "name", "juiciness", "peeled", "overripe", "under-ripe", "chilled"
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
    attribute_response.add_query_response("name", "orange")
    attribute_response.add_query_response("peeled", True)
    attribute_response.add_query_response("overripe", False)
    attribute_response.add_query_response("under-ripe", True)
    attribute_response.add_query_response("chilled", True)

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
