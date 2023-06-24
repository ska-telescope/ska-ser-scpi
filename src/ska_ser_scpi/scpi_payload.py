"""This module provides a SCPI request and response."""
from __future__ import annotations

import logging

class ScpiRequest:
    """
    Representation of an attribute request.

    A SCPI request specifies:

    * SCPI fields whose values are to be read ("queries")
    * string values to be written to fields ("setops"). These setops
      allow for multiple arguments, so they cover the command invocation
      case as well.
    """

    def __init__(self) -> None:
        """Initialise a new instance."""
        # We'll use this dict as a sorted set
        self._queries: dict[str, None] = {}
        self._setops: list[tuple[str, list[str]]] = []

    def add_query(self, field: str) -> None:
        """
        Add a field to be queried as part of this request.

        :param field: name of the field to be queried.
        """
        logging.debug("Add SCPI request field: %s", field)
        self._queries[field] = None

    def add_setop(self, field: str, *args: str, replace: bool = False) -> None:
        """
        Add a field to be set as part of this request.

        :param field: name of the field to be set.
        :param args: arguments to the set operation. For a field write,
            there will only be one argument. However this method also
            covers the command invocation case, and so allows for more
            than one argument.
        :param replace: whether to replace any existing setop with the
            same field name.
        """
        if replace:
            logging.debug("Replace SCPI field '%s' in request : %s", field, args)
            # pylint: disable-next=consider-using-enumerate
            for i in range(len(self._setops)):
                (this_field, _) = self._setops[i]
                if field == this_field:
                    self._setops[i] = (field, list(args))
                    break
            else:
                self._setops.append((field, list(args)))
        else:
            logging.debug("Add SCPI field '%s' to request : %s", field, args)
            self._setops.append((field, list(args)))
        logging.info("Field %s has %d operations %s",
                     field, len(self._setops), self._setops)

    @property
    def queries(self) -> list[str]:
        """
        Return a list of SCPI fields to be queried in this SCPI request.

        :returns: list of SCPI fields.
        """
        return list(self._queries)

    @property
    def setops(self) -> list[tuple[str, list[str]]]:
        """
        Return a set operations to be performed in this SCPI request.

        :returns: a dictionary, keyed by the name of the SCPI field to be
            written (or commanded), with values being lists of string
            arguments to the setop. For writes, this list will only have
            one element, which is the value to be written. For commands,
            the list will be arguments to the command.
        """
        return list(self._setops)

    def __eq__(self, other: object) -> bool:
        """
        Check for equality with another object.

        :param other: the object against which this object is compared
            for equality.

        :returns: whether the objects are equal.
        """
        if not isinstance(other, ScpiRequest):
            return False
        if self._queries != other._queries:
            return False
        if self._setops != other._setops:
            return False
        return True

    def __repr__(self):
        return f"{self._setops}"


class ScpiResponse:
    """
    Representation of an SCPI field query response.

    A SCPI response specifies values of SCPI fields that have been
    queried in an attribute request.
    """

    def __init__(self) -> None:
        """Initialise a new instance."""
        self._responses: dict[str, str] = {}

    def add_query_response(self, field: str, value: str) -> None:
        """
        Add a response to a SCPI field value query.

        :param field: name of the queried SCPI field.
        :param value: value of the queried SCPI field.
        """
        logging.debug("Add SCPI query response field: %s (value %s)", field, value)
        self._responses[field] = value

    @property
    def responses(self) -> dict[str, str]:
        """
        Return responses to queries in a SCPI request.

        :returns: a dictionary, keyed by the SCPI field, with a single
            string value for each key, representing the value of that
            field.
        """
        return dict(self._responses)

    def __eq__(self, other: object) -> bool:
        """
        Check for equality with another object.

        :param other: the object against which this object is compared
            for equality.
        :returns: whether the objects are equal.
        """
        if not isinstance(other, ScpiResponse):
            return False
        if self._responses != other._responses:
            return False
        return True

    def __repr__(self):
        return f"{self._responses}"
