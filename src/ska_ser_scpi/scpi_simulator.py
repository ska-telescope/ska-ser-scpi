"""This module provides a simulator framework for a SCPI instrument."""
from ska_ser_devices.client_server import ApplicationServer, SentinelBytesMarshaller

from .attribute_payload import AttributeRequest, AttributeResponse
from .bytes_server import ScpiBytesServer
from .interface_definition import InterfaceDefinitionType, SupportedAttributeType
from .scpi_server import ScpiServer


class ScpiSimulator(ApplicationServer[bytes, bytes]):
    """A simple simulator of hardware that talks SCPI over TCP."""

    def __init__(
        self,
        interface_definition: InterfaceDefinitionType,
        initial_values: dict[str, bool | float | str],
        argument_separator: str = " ",
    ) -> None:
        """
        Initialise a new instance.

        :param interface_definition: definition of the interface to be
            simulated.
        :param initial_values: a dictionary of initial values for the
            simulator to take.
        :param argument_separator: the character which separates the
            SCPI command and the argument.
        """
        self._attribute_values: dict[str, SupportedAttributeType] = {}

        for name, definition in interface_definition["attributes"].items():
            definition_values = list(definition.values())[0]
            if "value" in definition_values:
                self.set_attribute(name, definition_values["value"])

        for name, value in initial_values.items():
            self.set_attribute(name, value)

        scpi_server = ScpiServer(self, interface_definition["attributes"])
        scpi_string_server = ScpiBytesServer(scpi_server, argument_separator)

        marshaller = SentinelBytesMarshaller(
            interface_definition["sentinel_string"].encode()
        )
        super().__init__(
            marshaller.unmarshall,
            marshaller.marshall,
            scpi_string_server.receive_send,
        )

    def receive_send(self, attribute_request: AttributeRequest) -> AttributeResponse:
        """
        Receive an attribute request, handle it, and return a response.

        :param attribute_request: the request to be handled.

        :returns: a response.

        :raises ValueError: if the attribute request contains a setop
            for an attribute with neither arguments nor a defined
            method.
        """
        for attribute_name, attribute_args in attribute_request.setops:
            command_method = getattr(self, attribute_name, None)
            if command_method is None:
                # No special method defined for this, so fall back to an
                # attribute write
                if not attribute_args:
                    raise ValueError(
                        f"{attribute_name} has neither arguments nor a "
                        "defined method."
                    )
                attribute_value = attribute_args[0]  # TODO: Handle >0 error
                self.set_attribute(attribute_name, attribute_value)
            else:
                command_method(*attribute_args)

        attribute_response = AttributeResponse()
        for attribute_name in attribute_request.queries:
            attribute_method = getattr(self, attribute_name, None)
            if attribute_method is None:
                attribute_value = self.get_attribute(attribute_name)
            else:
                attribute_value = attribute_method()

            attribute_response.add_query_response(attribute_name, attribute_value)
        return attribute_response

    def set_attribute(self, name: str, value: SupportedAttributeType) -> None:
        """
        Set the value of a simulator attribute.

        Permitted attributes are the keys of the "attributes" dictionary
        in the interface definition.

        :param name: name of the simulator attribute to be set.
        :param value: new value of the simulator attribute.
        """
        self._attribute_values[name] = value

    def get_attribute(self, name: str) -> SupportedAttributeType:
        """
        Return the value of a simulator attribute.

        Permitted attributes are the keys of the "attributes" dictionary
        in the interface definition.

        :param name: name of the simulator attribute to be returned.

        :returns: the value of the attribute.
        """
        return self._attribute_values[name]
