"""This module provides a SCPI client."""
from __future__ import annotations

import logging
import re
import socket
from typing import Final

from ska_ser_devices.client_server.application import ApplicationClient

from .scpi_payload import ScpiRequest, ScpiResponse

logger = logging.getLogger(__name__)


class ScpiClient:  # pylint: disable=too-few-public-methods
    """
    Client for sending/receiving SCPI payloads to/from a server.

    Used to transmit a SCPI request object, and then receive a SCPI
    response object.
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        bytes_client: ApplicationClient[bytes, bytes],
        chain: bool = True,
        argument_separator: str = " ",
        return_response: bool = False,
        encoding: str = "utf-8",
        timeout_retries: int = 2,
    ) -> None:
        """
        Initialise a new instance.

        :param bytes_client: the underlying bytes client to be
            used.
        :param chain: whether this client should chain SCPI commands.
        :param argument_separator: the character which separates the
            SCPI command and the argument.
        :param return_response: whether this device returns a package
            in response to a sent SCPI command.
        :param encoding: the encoding to use when converting strings to
            bytes and vice versa.
        :param timeout_retries: number of times to retry communications
            in the case of socket timeouts. (The number of connection
            attempts is one more than the number of retries i.e. if we
            set the number of retries to 0, then we try only once.)
        """
        self._bytes_client = bytes_client
        self._chain = chain
        self._argument_separator = argument_separator
        self._return_response: bool = return_response
        self._encoding: Final = encoding
        self._timeout_retries: int = timeout_retries

        # Responses are fields separated by semicolons, but we can't
        # just split on semicolons, because the system errors field is
        # a comma-separate list of error code, error string pairs, and
        # the error string always contains semicolons. Even csv doesn't
        # help us here!
        self._response_regex = re.compile(r'(?:[^;"]|"[^"]+?")+')

    def send_receive(self, scpi_request: ScpiRequest) -> ScpiResponse:
        """
        Send a SCPI request, and receive a SCPI response.

        :param scpi_request: details of the SCPI request to be sent.

        :raises socket.timeout: if we timeout waiting for some data to
            be received on the socket.

        :returns: details of the SCPI response.
        """
        response_fields = scpi_request.queries
        (setops, queries) = self._marshall_request(scpi_request)

        for request_bytes in setops:
            self._bytes_client(
                request_bytes, expect_response=self._return_response
            )  # type:ignore[call-overload]

        responses = []
        for request_bytes in queries:
            # TODO: Socket timeouts against the instrument are fairly common,
            # even though the timeout is set fairly high. This retry loop
            # provides some insurance. We need to understand this better.
            for connection_attempt in range(1, self._timeout_retries + 2):
                try:
                    response_bytes = self._bytes_client(request_bytes)
                except socket.timeout:
                    if connection_attempt > self._timeout_retries:
                        raise
                else:
                    responses.append(response_bytes)
                    break

        scpi_response = self._unmarshall_response(responses, response_fields)
        return scpi_response

    def _marshall_request(
        self, scpi_request: ScpiRequest
    ) -> tuple[list[bytes], list[bytes]]:
        """
        Marshall a SCPI request object into a list of byte strings.

        :param scpi_request: the SCPI request object to be marshalled.

        :returns: a tuple consisting of a list of setop byte strings and
            a list of query byte strings.
        """
        setops = []
        if scpi_request.setops:
            for setop, args in scpi_request.setops:
                setop_str = self._argument_separator.join([setop, *args])
                setops.append(setop_str.encode(self._encoding))
            if self._chain:
                setops = [b";".join(setops)]

        queries = []
        if scpi_request.queries:
            for query in scpi_request.queries:
                # TODO add question mark here?
                query_str = f"{query}?"
                logger.info("Add query %s", query_str)
                queries.append(query_str.encode(self._encoding))
            if self._chain:
                queries = [b";".join(queries)]

        return (setops, queries)

    def _unmarshall_response(
        self,
        responses: list[bytes],
        fields: list[str],
    ) -> ScpiResponse:
        """
        Unmarshall a list of byte strings into a SCPI response.

        :param responses: list of byte strings.
        :param fields: list of fields contained in the byte strings.

        :returns: a SCPI response object.

        :raises ValueError: if the list of response byte strings
            contains more SCPI field values than the provided list of
            fields.
        """
        scpi_response = ScpiResponse()
        values: list[str] = []
        for response_bytes in responses:
            response_str = response_bytes.decode(self._encoding).strip()
            if response_str:
                logger.info("Add response %s", response_str)
                values.extend(self._response_regex.findall(response_str))

        if len(values) != len(fields):
            raise ValueError(
                f"Mismatch: unpacked {len(values)} value(s): {values} but "
                f"{len(fields)} field(s) were provided: {fields}."
            )
        for field, value in zip(fields, values):
            scpi_response.add_query_response(field, value)

        return scpi_response
