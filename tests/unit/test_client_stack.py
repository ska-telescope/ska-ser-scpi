"""Tests of the ska_ser_test_equipment.scpi client stack."""

import unittest.mock

import pytest

from ska_ser_scpi import (
    AttributeClient,
    AttributeRequest,
    AttributeResponse,
    InterfaceDefinitionType,
    ScpiClient,
    expand_read_write,
)


@pytest.fixture(name="interface_definition")
def interface_definition_fixture() -> InterfaceDefinitionType:
    """
    Return an interface definition for use in testing.

    :returns: an interface definition.
    """
    interface_definition = {
        "model": "fruit",
        "poll_rate": 0.1,
        "timeout": 0.5,
        "supports_chains": True,
        "attributes": {
            "name": {"read": {"field": "NAME", "field_type": "str"}},
            "juiciness": {"read_write": {"field": "JUIC", "field_type": "float"}},
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
        },
        "sentinel_string": "\r\n",
    }

    interface_definition = expand_read_write(interface_definition)
    return interface_definition


@pytest.fixture(name="attribute_request")
def attribute_request_fixture() -> AttributeRequest:
    """
    Return an attribute request object for use in testing.

    :returns: an attribute request object.
    """
    attribute_request = AttributeRequest()
    attribute_request.set_queries(
        "name", "juiciness", "peeled", "overripe", "under-ripe"
    )
    attribute_request.add_setop("peeled", True)
    attribute_request.add_setop("chilled", True)
    return attribute_request


@pytest.fixture(name="expected_attribute_response")
def expected_attribute_response_fixture() -> AttributeResponse:
    """
    Return the expected attribute response object, for use in testing.

    :returns: an attribute response object.
    """
    attribute_response = AttributeResponse()
    attribute_response.add_query_response("name", "orange")
    attribute_response.add_query_response("juiciness", 98.7)
    attribute_response.add_query_response("peeled", True)
    attribute_response.add_query_response("overripe", False)
    attribute_response.add_query_response("under-ripe", True)
    attribute_response.add_query_response("chilled", True)
    return attribute_response


@pytest.fixture(name="expected_bytes_call")
def expected_bytes_call_fixture() -> bytes:
    """
    Return the expected bytes call to the bytes client.

    :returns: the expected bytes call.
    """
    return b"NAME?;JUIC?;PEEL?;FLAGS?"


@pytest.fixture(name="mock_bytes_client")
def mock_bytes_client_fixture() -> unittest.mock.Mock:
    """
    Return a mock bytes client to sit at the bottom of the client stack.

    :returns: a mock attribute server.
    """
    mock_bytes_client = unittest.mock.Mock()
    mock_bytes_client.return_value = b"orange;98.7;1;130"
    return mock_bytes_client


@pytest.fixture(name="attribute_client")
def attribute_client_fixture(
    mock_bytes_client: unittest.mock.Mock,
    interface_definition: InterfaceDefinitionType,
) -> AttributeClient:
    """
    Return the attribute client at the top of the stack.

    :param mock_bytes_client: a mock SCPI bytes client to sit at the
        bottom of the stack.
    :param interface_definition: definition of the attribute, including
        its mapping to SCPI field.

    :returns: an attribute client.
    """
    scpi_client = ScpiClient(
        mock_bytes_client, chain=interface_definition["supports_chains"]
    )
    return AttributeClient(scpi_client, interface_definition["attributes"])


def test_client_stack(
    attribute_client: AttributeClient,
    mock_bytes_client: unittest.mock.Mock,
    attribute_request: AttributeRequest,
    expected_bytes_call: bytes,
    expected_attribute_response: AttributeResponse,
) -> None:
    """
    Test flow of SCPI commands on the client side.

    The client stack receives a device-independent attribute request,
    marshalls that down to a device-dependent ScpiRequest, then
    unmarshalls that into a string of bytes.

    A string of bytes is constructed in response to the request bytes.
    This is ummarshalled into to a device-dependent SCPI response, which
    is unmarshalled into a device-independent attribute response.

    :param attribute_client: the attribute client at the top of the
        stack.
    :param mock_bytes_client: a mock SCPI bytes client to sit at the
        bottom of the stack.
    :param attribute_request: an attribute request to be sent to the
        client.
    :param expected_bytes_call: the bytes that we expect the attribute
        request to be marshalled down to.
    :param expected_attribute_response: the attribute response that we
        expect the attribute client to receive in response to the
        attribute request.
    """
    attribute_response = attribute_client.send_receive(attribute_request)
    assert attribute_response == expected_attribute_response
    mock_bytes_client.assert_called_with(expected_bytes_call)
