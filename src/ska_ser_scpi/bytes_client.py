"""This module provides a protocol for SCPI bytes clients."""
from __future__ import annotations

import logging
import re
from typing import Iterator, Literal

from ska_ser_devices.client_server import (
    ApplicationClient,
    SentinelBytesMarshaller,
    TcpClient,
    TelnetClient,
)

SupportedProtocol = Literal["tcp", "telnet"]


class _JimmiedSentinelBytesMarshaller(SentinelBytesMarshaller):
    def unmarshall(self, bytes_iterator: Iterator[bytes]) -> bytes:
        """
        Unmarshall bytes with awareness of IEEE 488.2 arbitrary blocks.

        These blocks start with a length header, and then contain arbitrary
        byte data, as the name suggests. That means that the blocks can
        contain our sentinel string, and be split in half when they shouldn't
        be! We need to watch for the beginning of these blocks, and then
        keep reading from the stream, ignoring the sentinel, until we have
        as much data as we expect.

        Note this will only work when chaining is disabled, because we only
        look for the arbitrary block header at the start of each chunk.

        :param bytes_iterator: an iterator of bytestrings received
            by the server

        :raises ValueError: when an arbitrary-block-looking payload
            is received that is longer than its header indicates

        :return: the application-layer bytestring, minus the terminator.
        """
        payload = next(bytes_iterator)
        if re.match(rb"^#\d\d+", payload):
            len_head = 2 + int(payload[1:2])
            len_data = int(payload[2:len_head])
            len_expected = len_head + len_data + len(self._sentinel)
            while len(payload) < len_expected or not payload.endswith(self._sentinel):
                payload = payload + next(bytes_iterator)
            if len(payload) > len_expected:
                len_received = len(payload) - len_head - len(self._sentinel)
                raise ValueError(
                    "Malformed IEEE 488.2 Definite Length Arbitrary Block Data: "
                    f"received {len_received} bytes but header stated {len_data} bytes"
                )
        else:
            while not payload.endswith(self._sentinel):
                payload = payload + next(bytes_iterator)
        return payload.removesuffix(self._sentinel)


# pylint: disable-next=too-few-public-methods
class ScpiBytesClientFactory:
    """Factory for clients that send/receive bytes to/from servers."""

    def __init__(self) -> None:
        """Initialise a new instance."""
        self._clients: dict[SupportedProtocol, type[TcpClient] | type[TelnetClient]] = {
            "tcp": TcpClient,
            "telnet": TelnetClient,
        }

    # pylint: disable=too-many-arguments
    def create_client(
        self,
        protocol: SupportedProtocol,
        host: str | bytes | bytearray,
        port: int,
        timeout: float,
        sentinel_string: str = "\r\n",
        logger: logging.Logger | None = None,
    ) -> ApplicationClient[bytes, bytes]:
        """
        Create and return a client for a given protocol and address.

        :param protocol: name of a supported protocol.
        :param host: host name or IP address.
        :param port: port on which the device is listening.
        :param timeout: how long to wait during blocking operations.
        :param sentinel_string: sentinel string indicating the end of a
            payload.
        :param logger: a python standard logger

        :returns: a client that can use the given protocol and address to
            send/receive bytes to/from a server.
        """
        bytes_client = self._clients[protocol](str(host), port, timeout, logger=logger)
        marshaller = _JimmiedSentinelBytesMarshaller(
            sentinel_string.encode(), logger=logger
        )

        return ApplicationClient[bytes, bytes](
            bytes_client, marshaller.marshall, marshaller.unmarshall
        )
