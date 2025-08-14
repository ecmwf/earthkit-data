# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.core.index import Index
from earthkit.data.sources import Source


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

    def ls(self, n=None, keys=None, extra_keys=None, namespace=None):
        r"""Generate a list like summary using a set of metadata keys.

        Parameters
        ----------
        n: int, None
            The number of :obj:`Field`\ s to be
            listed. None means all the messages, ``n > 0`` means fields from the front, while
            ``n < 0`` means fields from the back of the fieldlist.
        keys: list of str, dict, None
            Metadata keys. If it is None the following default set of keys will be used:  "centre",
            "shortName", "typeOfLevel", "level", "dataDate", "dataTime", "stepRange", "dataType",
            "number", "gridType". To specify a column title for each key in the output use a dict.
        extra_keys: list of str, dict, None
            List of additional keys to ``keys``. To specify a column title for each key in the output
            use a dict.
        namespace: str, None
            The namespace to choose the ``keys`` from. When it is set ``keys`` and
            ``extra_keys`` are omitted.

        Returns
        -------
        Pandas DataFrame
            DataFrame with one row per :obj:`Field`.

        See Also
        --------
        head
        tail

        """
        from earthkit.data.utils.summary import ls

        def _proc(keys, n):
            num = len(self)
            pos = slice(0, num)
            if n is not None:
                pos = slice(0, min(num, n)) if n > 0 else slice(num - min(num, -n), num)
            pos_range = range(pos.start, pos.stop)

            if "namespace" in keys:
                ns = keys.pop("namespace", None)
                for i in pos_range:
                    f = self[i]
                    v = f.metadata(namespace=ns)
                    if len(keys) > 0:
                        v.update(f._attributes(keys))
                    yield (v)
            else:
                for i in pos_range:
                    yield (self[i]._attributes(keys))

        _keys = self._default_ls_keys() if namespace is None else dict(namespace=namespace)
        return ls(_proc, _keys, n=n, keys=keys, extra_keys=extra_keys)

    def _default_ls_keys(self):
        if len(self) > 0:
            return self[0]._kwargs.get("ls_keys", None)
        return []


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

    def mutate_source(self):
        return self

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


class StreamFieldList(FieldList, Source):
    def __init__(self, source, **kwargs):
        FieldList.__init__(self, **kwargs)
        self._source = source

    def mutate(self):
        return self

    def __iter__(self):
        return iter(self._source)

    def batched(self, n):
        return self._source.batched(n)

    def group_by(self, *keys, **kwargs):
        return self._source.group_by(*keys)

    def __getstate__(self):
        raise NotImplementedError("StreamFieldList cannot be pickled")

    # def to_xarray(self, **kwargs):
    #     from earthkit.data.core.fieldlist import FieldList

    #     fields = [f for f in self]
    #     return FieldList.from_fields(fields).to_xarray(**kwargs)

    # @classmethod
    # def merge(cls, sources):
    #     assert all(isinstance(s, StreamFieldList) for s in sources), sources
    #     assert len(sources) > 1
    #     return MultiStreamSource.merge(sources)

    def default_encoder(self):
        return None
