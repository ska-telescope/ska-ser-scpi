"""This module provides an attribute request and response."""
from __future__ import annotations

from collections import Counter
from typing import Any


class AttributeRequest:
    """
    Representation of an attribute request.

    An attribute request specifies

    * the attributes whose values are to be read ("queries")
    * values to be written to attributes ("setops"). These setops allow
      for multiple arguments, so they cover the command invocation case
      as well.
    """

    def __init__(self) -> None:
        """Initialise a new instance."""
        self._queries: dict[str, None] = {}  # using this as a sorted set
        self._setops: list[tuple[str, Any]] = []

    def set_queries(self, *attributes: str) -> None:
        """
        Set the attributes to be queried as part of this request.

        :param attributes: names of the attribute to be queried.
        """
        self._queries.clear()
        for attribute in attributes:
            self._queries[attribute] = None

    def add_setop(self, attribute: str, *args: Any) -> None:
        """
        Add an attribute to be set as part of this request.

        :param attribute: name of the attribute to be set.
        :param args: arguments to the set operation. For an attribute
            write, there will only be one argument. However this method
            also covers the command invocation case, and so allows for
            more than one argument.
        """
        self._setops.append((attribute, args))

    def clear_setops(self) -> None:
        """Clear the setops for this request."""
        self._setops.clear()

    @property
    def queries(self) -> list[str]:
        """
        Return a list of attributes queried in this request.

        :returns: a list of queried attributes.
        """
        return list(self._queries)

    @property
    def setops(self) -> list[tuple[str, Any]]:
        """
        Return the set operations to be performed in this request.

        :returns: a dictionary, keyed by the name of the attribute to be
            written (or commanded), with values being lists of arguments
            to the setop. For writes, this list will only have one
            element, which is the value to be written. For commands,
            the list will be arguments to the command.
        """
        return list(self._setops)

    def copy(self) -> AttributeRequest:
        """
        Return a shallow copy of this attribute request.

        :returns: a shallow copy of this attribute request.
        """
        attribute_request = AttributeRequest()
        attribute_request.set_queries(*self.queries)
        for setop, args in self.setops:
            attribute_request.add_setop(setop, *args)
        return attribute_request

    def __eq__(self, other: object) -> bool:
        """
        Check for equality with another object.

        :param other: the object against which this object is compared
            for equality.

        :returns: whether the objects are equal.
        """
        if not isinstance(other, AttributeRequest):
            return False
        if Counter(self._setops).items() != Counter(other._setops).items():
            return False
        return set(self._queries) == set(other._queries)

    def __lt__(self, other: object) -> bool:
        """
        Check if this object is less than another object.

        When an attribute request is marshalled to a SCPI request, a
        query on a boolean attribute may marshall down to a query on a
        SCPI flag field. This will in turn unmarshall to a query on all
        boolean attributes that contribute to that SCPI flag field.
        Thus, the final attribute request that results from marshalling
        an original attribute request, sending it through a SCPI
        interface, and then unmarshalling it again, may not be exactly
        equal to the original request, but will always *subsume* it.
        This subsumption relationship is implemented here using the
        "rich comparison" operations, so that it can be used in testing.

        :param other: the object against which this object is compared.

        :returns: whether this object is less than the other object.
        """
        if not isinstance(other, AttributeRequest):
            return False
        if not Counter(self._setops).items() < Counter(other._setops).items():
            return False
        return set(self._queries) < set(other._queries)

    def __le__(self, other: object) -> bool:
        """
        Check if this object is less than or equal to another object.

        See :py:meth:`.__lt__` for rationale.

        :param other: the object against which this object is compared.

        :returns: whether this object is less than or equal to the other
            object.
        """
        if not isinstance(other, AttributeRequest):
            return False
        if not Counter(self._setops).items() <= Counter(other._setops).items():
            return False
        return set(self._queries) <= set(other._queries)

    def __gt__(self, other: object) -> bool:
        """
        Check if this object is greater than another object.

        See :py:meth:`.__lt__` for rationale.

        :param other: the object against which this object is compared.

        :returns: whether this object is greater than the other object.
        """
        if not isinstance(other, AttributeRequest):
            return False
        if not Counter(self._setops).items() > Counter(other._setops).items():
            return False
        return set(self._queries) > set(other._queries)

    def __ge__(self, other: object) -> bool:
        """
        Check if this object is greater than or equal to another object.

        See :py:meth:`.__lt__` for rationale.

        :param other: the object against which this object is compared.

        :returns: whether this object is greater than or equal to the
            other object.
        """
        if not isinstance(other, AttributeRequest):
            return False
        if not Counter(self._setops).items() >= Counter(other._setops).items():
            return False
        return set(self._queries) >= set(other._queries)

    def __bool__(self) -> bool:
        """
        Return the boolean value of this object.

        Consistent with other container objects, this method returns
        whether this request is non-empty.

        :returns: whether this request is non-empty.
        """
        return bool(self._queries) or bool(self._setops)

    def __repr__(self) -> str:
        """
        Return a string representation of this object.

        :returns: a string representation of this object.
        """
        return "AttributeRequest with \n" \
               f"\tqueries: {repr(list(self._queries))}" \
               f"\tsetops: {repr(self._setops)}"


class AttributeResponse:
    """
    Representation of an attribute response.

    An attribute response specifies values of attributes that have been
    queried in an attribute request.
    """

    def __init__(self) -> None:
        """Initialise a new instance."""
        self._responses: dict[str, Any] = {}

    def add_query_response(
        self,
        attribute: str,
        value: Any,
    ) -> None:
        """
        Add a response to an attribute value query.

        :param attribute: name of the queried attribute.
        :param value: value of the queried attribute.
        """
        self._responses[attribute] = value

    @property
    def responses(self) -> dict[str, Any]:
        """
        Return responses to queries in an attribute request.

        :returns: a dictionary of attribute values.
        """
        return dict(self._responses)

    def __eq__(self, other: object) -> bool:
        """
        Check for equality with another object.

        :param other: the object against which this object is compared
            for equality.
        :returns: whether the objects are equal.
        """
        if not isinstance(other, AttributeResponse):
            return False
        if self._responses != other._responses:
            return False
        return True

    def __repr__(self) -> str:
        return f"{self._responses}"
