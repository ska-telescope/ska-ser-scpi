"""
This package provides SCPI support.

It is implemented as a three-layer stack:

* The bottom layer works with SCPI byte strings;

* The middle layer works with device-dependent SCPI queries, commands
  and set operations;

* The top layer works with device-independent attribute queries,
  commands and set operations.

The following module diagram shows decomposition and "uses"
relationships. Though it might not appear layered at first glance, it
shows

* a client stack in which each layer uses only its own layer and the
  layer immediately *below*;

* a server stack in which each layer uses only its own layer and the
  layer immediately *above*.

.. image:: scpi.png
"""
__version__ = "0.1.0"


__all__ = [
    "AttributeClient",
    "AttributeRequest",
    "AttributeResponse",
    "AttributeServerProtocol",
    "ScpiBytesClientFactory",
    "ScpiBytesServer",
    "SupportedProtocol",
    "AttributeDefinitionType",
    "InterfaceDefinitionType",
    "ScpiClient",
    "ScpiRequest",
    "ScpiResponse",
    "ScpiServer",
    "SupportedAttributeType",
    "ScpiSimulator",
]

from .attribute_client import AttributeClient
from .attribute_payload import AttributeRequest, AttributeResponse
from .attribute_server import AttributeServerProtocol
from .bytes_client import ScpiBytesClientFactory, SupportedProtocol
from .bytes_server import ScpiBytesServer
from .interface_definition import (
    AttributeDefinitionType,
    InterfaceDefinitionType,
    ReadWriteType,
    SupportedAttributeType,
)
from .scpi_client import ScpiClient
from .scpi_payload import ScpiRequest, ScpiResponse
from .scpi_server import ScpiServer
from .scpi_simulator import ScpiSimulator
