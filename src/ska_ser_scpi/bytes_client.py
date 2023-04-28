"""This module provides a protocol for SCPI bytes clients."""
from __future__ import annotations

from typing import Literal

from ska_ser_devices.client_server import (
    ApplicationClient,
    SentinelBytesMarshaller,
    TcpClient,
    TelnetClient,
)

SupportedProtocol = Literal["tcp", "telnet"]


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
    ) -> ApplicationClient[bytes, bytes]:
        """
        Create and return a client for a given protocol and address.

        :param protocol: name of a supported protocol.
        :param host: host name or IP address.
        :param port: port on which the device is listening.
        :param timeout: how long to wait during blocking operations.
        :param sentinel_string: sentinel string indicating the end of a
            payload.

        :returns: a client that can use the given protocol and address to
            send/receive bytes to/from a server.
        """
        bytes_client = self._clients[protocol](str(host), port, timeout)
        marshaller = SentinelBytesMarshaller(sentinel_string.encode())

        return ApplicationClient[bytes, bytes](
            bytes_client, marshaller.marshall, marshaller.unmarshall
        )
