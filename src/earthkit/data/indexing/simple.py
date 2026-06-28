# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import abstractmethod

from earthkit.data.core.field import Field
from earthkit.data.data.fieldlist import FieldListData

from .indexed import IndexFieldListBase


class SimpleFieldListBase(IndexFieldListBase):
    """Base class for a SimpleFieldList implementation containing a list of fields.

    Subclasses must implement the ``_fields`` property that should return a list of fields.
    The rest of the methods are implemented in terms of this property.

    For a concrete implementation of this class,
    see :py:class:`~earthkit.data.indexing.simple.SimpleFieldList`.
    """

    @property
    @abstractmethod
    def _fields(self):
        pass

    def _getitem(self, n):
        if isinstance(n, int):
            return self._fields[n]

    def __len__(self):
        return len(self._fields)

    def mutate_source(self):
        return self

    def __getstate__(self) -> dict:
        ret = {}
        # print("SimpleFieldList Getstate")
        ret["_fields"] = self._fields
        return ret

    def __setstate__(self, state: dict):
        # print("SimpleFieldList Setstate")
        self._fields = state.pop("_fields")

    def _default_encoder(self):
        if len(self) > 0:
            return self[0]._default_encoder()

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        assert len(args) == 2
        fs = args[0]
        indices = list(args[1])
        return cls.from_fields([fs._fields[i] for i in indices])

    @classmethod
    def merge(cls, sources):
        for s in sources:
            if not isinstance(s, SimpleFieldListBase):
                raise ValueError("SimpleFieldList can only be merged to another SimpleFieldLists")

        if not all(isinstance(_, SimpleFieldListBase) for _ in sources):
            raise ValueError("SimpleFieldList can only be merged to another SimpleFieldLists")

        from itertools import chain

        return cls.from_fields(list(chain(*[f for f in sources])))

    def to_data_object(self):
        return FieldListData(self)


class SimpleFieldList(SimpleFieldListBase):
    """A simple FieldList implementation containing a list of fields.

    This is a top level earthkit-data object and can be directly imported from ``earthkit.data``.

    It can be created with the top level factory function
    :py:func:`~earthkit.data.core.fieldlist.create_fieldlist` or by
    the static method :py:meth:`~earthkit.data.core.fieldlist.FieldList.from_fields` that is
    available for all :class:`~earthkit.data.core.fieldlist.FieldList` implementations.

    Parameters
    ----------
    fields: iterable, :class:`~earthkit.data.core.field.Field`, None
        Iterable of :class:`~earthkit.data.core.field.Field` objects.

    Examples
    --------
    A SimpleFieldList can be created from a list of fields:

    >>> import earthkit.data as ekd
    >>> fl = ekd.SimpleFieldList(list_of_fields)

    It can also be created by the top level factory function
    :py:func:`~earthkit.data.core.fieldlist.create_fieldlist`:

    >>> import earthkit.data as ekd
    >>> fl = ekd.create_fieldlist(list_of_fields)

    or with the :py:meth:`~earthkit.data.core.fieldlist.FieldList.from_fields` static method that
    is available for all :class:`~earthkit.data.core.fieldlist.FieldList` implementations:

    >>> import earthkit.data as ekd
    >>> fl = ekd.FieldList.from_fields(list_of_fields)
    >>> fl = ekd.SimpleFieldList.from_fields(list_of_fields)
    >>> fl = fl_other.from_fields(list_of_fields)

    """

    def __init__(self, fields=None):
        if isinstance(fields, Field):
            fields = [fields]

        self.__fields = fields if fields is not None else []

    @property
    def _fields(self):
        return self.__fields

    def __getstate__(self) -> dict:
        ret = {}
        ret["_fields"] = self._fields
        return ret

    def __setstate__(self, state: dict):
        fields = state.pop("_fields")
        self.__init__(fields)

    def __repr__(self):
        return f"SimpleFieldList, {len(self)} fields"
