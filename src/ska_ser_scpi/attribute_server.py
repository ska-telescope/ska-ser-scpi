"""
This module defines the interface of an attribute server.

An attribute server is the final layer of a SCPI simulator. The server
receives a byte request, which it unmarshalls to a SCPI request, which
it then unmarshall to an attribute request. The job of an attribute
server is to handle the attribute request, and produce an attribute
response. The attribute response is then marshalled down to a SCPI
response, which is finally marshalled down to a byte-string, which is
sent as a response to the original byte request.
"""
from typing import Protocol

from .attribute_payload import AttributeRequest, AttributeResponse


# pylint: disable-next=too-few-public-methods
class AttributeServerProtocol(Protocol):
    """Structural subtyping protocol for an attribute server."""

    def receive_send(self, attribute_request: AttributeRequest) -> AttributeResponse:
        """
        Handle an attribute request and send a response.

        :param attribute_request: the request info.

        :returns: an attribute response.
        """  # noqa: DAR202
