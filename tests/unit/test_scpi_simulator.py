"""
This module tests the SPCI-over-TCP simulator.

It is also intended to stress-test the marshalling / unmarshalling
functionality.
"""

import random
import threading
from contextlib import contextmanager
from typing import Any, Iterator

import pytest
from ska_ser_devices.client_server import TcpServer

from ska_ser_scpi.attribute_client import AttributeClient
from ska_ser_scpi.attribute_payload import AttributeRequest
from ska_ser_scpi.bytes_client import ScpiBytesClientFactory
from ska_ser_scpi.interface_definition import (
    AttributeDefinitionType,
    InterfaceDefinitionType,
    SupportedAttributeType,
    expand_read_write_command,
)
from ska_ser_scpi.scpi_client import ScpiClient
from ska_ser_scpi.scpi_simulator import ScpiSimulator


@pytest.fixture(name="interface_definition")
def interface_definition_fixture() -> InterfaceDefinitionType:
    """
    Return an interface definition for use in testing.

    :returns: an interface definition.
    """
    size = 500

    definition: dict[str, dict[str, AttributeDefinitionType]] = {}
    for i in range(1, size + 1):
        definition[f"float{i}"] = {
            "read_write": {"field": f"FLT{i}", "field_type": "float"}
        }
        definition[f"string{i}"] = {
            "read_write": {"field": f"STR{i}", "field_type": "str"}
        }
        definition[f"boolean{i}"] = {
            "read_write": {"field": f"BOOL{i}", "field_type": "bool"}
        }
        definition[f"bit{i}"] = {
            "read_write": {
                "field": f"FLGS{1+(i-1)//100}",
                "field_type": "bit",
                "bit": (i - 1) % 100,
            }
        }
    interface_definition: InterfaceDefinitionType = {
        "model": "TEST",
        "supports_chains": True,
        "poll_rate": 0.1,
        "timeout": 0.5,
        "attributes": definition,
        "sentinel_string": "\r\n",
        "return_response": False,
    }

    interface_definition = expand_read_write_command(interface_definition)
    return interface_definition


@pytest.fixture(name="initial_values")
def initial_values_fixture() -> dict[str, SupportedAttributeType]:
    """
    Return the simulator's initial values.

    :returns: the simulator's initial values.
    """
    size = 500

    values: dict[str, SupportedAttributeType] = {}
    for i in range(1, size + 1):
        values[f"float{i}"] = float(i)
        values[f"string{i}"] = str(i)
        values[f"boolean{i}"] = i % 2 == 0
        values[f"bit{i}"] = i % 2 == 0
    return values


@pytest.fixture(name="simulator")
def simulator_fixture(
    interface_definition: InterfaceDefinitionType,
    initial_values: dict[str, Any],
) -> ScpiSimulator:
    """
    Return a simulator for use in testing.

    :param interface_definition: definition of the simulator's SCPI
        interface.
    :param initial_values: dictionary of initial values that the
        simulator should be initialised to take.

    :returns: a SCPI-over-TCP simulator.
    """
    return ScpiSimulator(interface_definition, initial_values)


@pytest.fixture(name="simulator_server")
def simulator_server_fixture(
    simulator: ScpiSimulator,
) -> Iterator[TcpServer]:
    """
    Return a simulator server for use in testing.

    :param simulator: the backend simulator to be fronted by the server.

    :yields: a simulator server.
    """

    @contextmanager
    def simulator_server_context() -> Iterator[TcpServer]:
        server = TcpServer("localhost", 0, simulator)

        with server:
            server_thread = threading.Thread(
                name="Simulator thread", target=server.serve_forever
            )
            server_thread.daemon = True
            server_thread.start()
            yield server
            server.shutdown()

    with simulator_server_context() as server:
        yield server


@pytest.fixture(name="attribute_client")
def attribute_client_fixture(
    simulator_server: TcpServer,
    interface_definition: InterfaceDefinitionType,
) -> AttributeClient:
    """
    Return an attribute client that sends to/receives from the simulator.

    :param simulator_server: the simulator server that this attribute
        client will send attribute requests to,
        and receive attribute responses from.
    :param interface_definition: definition of the simulator interface.

    :returns: an attribute client.
    """
    host, port = simulator_server.server_address
    bytes_client = ScpiBytesClientFactory().create_client("tcp", host, port, 3.0)
    scpi_client = ScpiClient(
        bytes_client, return_response=interface_definition["return_response"]
    )
    attribute_client = AttributeClient(scpi_client, interface_definition["attributes"])
    return attribute_client


@pytest.fixture(name="attribute_selection")
def attribute_selection_fixture(
    interface_definition: InterfaceDefinitionType,
) -> list[str]:
    """
    Return a list of attributes selected to be queried.

    :param interface_definition: interface definition of the simulator.

    :returns: a list of attributes selected to be queried.
    """
    keys = list(interface_definition["attributes"])
    sample = random.sample(keys, len(keys) // 2)
    random.shuffle(sample)
    return sample


@pytest.fixture(name="expected_values")
def expected_values_fixture(
    initial_values: dict[str, SupportedAttributeType],
    attribute_selection: list[str],
) -> dict[str, Any]:
    """
    Return the expected values for the selected attributes.

    :param initial_values: initial values of the simulator.
    :param attribute_selection: the attributes selected to be queried.

    :returns: a dictionary of expected attribute values.
    """
    expected: dict[str, Any] = {}
    for key in attribute_selection:
        if key.startswith("float"):
            expected[key] = pytest.approx(initial_values[key])
        else:
            expected[key] = initial_values[key]
    return expected


def test_simulator_queries(
    attribute_client: AttributeClient,
    expected_values: dict[str, SupportedAttributeType],
) -> None:
    """
    Test that we can query simulator attributes.

    This is intended primarily as a stress-test for the marshalling and
    unmarshalling code. We construct a query that requests half the
    simulator's attributes, in any order, and we expect to get the
    correct results back.

    :param attribute_client: client for attribute requests and
        responses.
    :param expected_values: dictionary of expected simulator values.
    """
    attribute_request = AttributeRequest()

    attribute_request.set_queries(*expected_values.keys())

    attribute_response = attribute_client.send_receive(attribute_request)

    for key, value in expected_values.items():
        assert attribute_response.responses[key] == value, (
            f"Expected key {key} to have value {value}, but it has value "
            f"{attribute_response.responses[key]}."
        )
