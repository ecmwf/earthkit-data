# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.core.index import Index


class FieldList(Index):
    @staticmethod
    def from_fields(fields):
        r"""Create a :class:`SimpleFieldList`.

        Parameters
        ----------
        fields: iterable
            Iterable of :obj:`Field` objects.

        Returns
        -------
        :class:`SimpleFieldList`

        """
        return SimpleFieldList([f for f in fields])


class SimpleFieldList(FieldList):
    def __init__(self, fields=None):
        r"""Initialize a FieldList object."""
        self._fields = fields

    @property
    def fields(self):
        """Return the fields in the list."""
        return self._fields

    def append(self, field):
        self.fields.append(field)

    def _getitem(self, n):
        if isinstance(n, int):
            return self.fields[n]

    def __len__(self):
        return len(self.fields)

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        assert len(args) == 2
        fs = args[0]
        indices = list(args[1])
        return cls.from_fields([fs.fields[i] for i in indices])

    @classmethod
    def merge(cls, sources):
        if not all(isinstance(_, SimpleFieldList) for _ in sources):
            raise ValueError("SimpleFieldList can only be merged to another SimpleFieldLists")

        from itertools import chain

        return cls.from_fields(list(chain(*[f for f in sources])))
