"""This module provides a SCPI bytes server."""
from __future__ import annotations

from .scpi_payload import ScpiRequest, ScpiResponse
from .scpi_server import ScpiServer


class ScpiBytesServer:  # pylint: disable=too-few-public-methods
    """
    Server receiving/sending SCPI payloads from/to a client.

    Used to receive a SCPI request object, and then send a SCPI response
    object (if required).
    """

    def __init__(
        self,
        scpi_server: ScpiServer,
        argument_separator: str = " ",
        encoding: str = "utf-8",
    ) -> None:
        """
        Initialise a new instance.

        :param scpi_server: the underlying SCPI server to be used.
        :param argument_separator: the character which separates the
            SCPI command and the argument.
        :param encoding: encoding for converting between strings and
            bytes.
        """
        self._scpi_server = scpi_server
        self._argument_separator = argument_separator
        self._encoding = encoding

    def receive_send(self, request_bytes: bytes) -> bytes:
        """
        Receive a bytes request, and send a bytes response.

        :param request_bytes: the bytes received.

        :returns: response bytes.
        """
        scpi_request = self._unmarshall_request(request_bytes)
        scpi_response = self._scpi_server.receive_send(scpi_request)
        response_bytes = self._marshall_response(scpi_response)
        return response_bytes

    def _unmarshall_request(self, request_bytes: bytes) -> ScpiRequest:
        """
        Unmarshall a SCPI request into bytes.

        :param request_bytes: the bytes to be unmarshalled.

        :returns: a SCPI request object.
        """
        scpi_request = ScpiRequest()
        request_str = request_bytes.decode(self._encoding).strip()
        commands = [command.strip() for command in request_str.split(";")]
        for command in commands:
            if command.endswith("?"):
                scpi_request.add_query(command[:-1])
            else:
                scpi_request.add_setop(*command.rsplit(self._argument_separator, 1))
        return scpi_request

    def _marshall_response(self, scpi_response: ScpiResponse) -> bytes:
        """
        Marshall a SCPI response object into a bytestring.

        :param scpi_response: the SCPI response object to be marshalled.

        :returns: a bytestring.
        """
        response_bytes = b";".join(scpi_response.responses.values())
        return response_bytes
