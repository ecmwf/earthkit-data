# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from functools import cached_property

from earthkit.utils.array import array_namespace

from earthkit.data.core.index import Index
from earthkit.data.sources import Source


def build_remapping(remapping, patches):
    if remapping is not None or patches is not None:
        from earthkit.data.core.order import build_remapping

        remapping = build_remapping(remapping, patches)
    return None


class FieldList(Index):
    @property
    def values(self):
        r"""array-like: Get all the fields' values as a 2D array. It is formed as the array of
        :obj:`GribField.values <data.readers.grib.codes.GribField.values>` per field.

        See Also
        --------
        to_array

        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> for f in ds:
        ...     print(f.values.shape)
        ...
        (209,)
        (209,)
        >>> v = ds.values
        >>> v.shape
        (2, 209)
        >>> v[0][:3]
        array([262.78027344, 267.44726562, 268.61230469])

        """
        return self._as_array("values")

    def to_numpy(self, **kwargs):
        r"""Return all the fields' values as an ndarray. It is formed as the array of the
        :obj:`data.core.fieldlist.Field.to_numpy` values per field.

        Parameters
        ----------
        **kwargs: dict, optional
            Keyword arguments passed to :obj:`data.core.fieldlist.Field.to_numpy`

        Returns
        -------
        ndarray
            Array containing the field values.

        See Also
        --------
        to_array
        values
        """
        return self._as_array("to_numpy", **kwargs)

    def to_array(self, **kwargs):
        r"""Return all the fields' values as an array. It is formed as the array of the
        :obj:`data.core.fieldlist.Field.to_array` values per field.

        Parameters
        ----------
        **kwargs: dict, optional
            Keyword arguments passed to :obj:`data.core.fieldlist.Field.to_array`

        Returns
        -------
        array-like
            Array containing the field values.

        See Also
        --------
        values
        to_numpy
        """
        return self._as_array("to_array", **kwargs)

    def _as_array(self, accessor, **kwargs):
        """Use pre-allocated target array to store the field values."""

        def _vals(f):
            return getattr(f, accessor)(**kwargs) if not is_property else getattr(f, accessor)

        n = len(self)
        if n > 0:
            it = iter(self)
            first = next(it)
            is_property = not callable(getattr(first, accessor, None))
            vals = _vals(first)
            first = None
            ns = array_namespace(vals)
            shape = (n, *vals.shape)
            r = ns.empty(shape, dtype=vals.dtype)
            r[0] = vals
            for i, f in enumerate(it, start=1):
                r[i] = _vals(f)
            return r

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
                    v = f.get(namespace=ns)
                    if len(keys) > 0:
                        v.update(f._get_fast(keys, output=dict))
                    yield (v)
            else:
                for i in pos_range:
                    yield (self[i]._get_fast(keys, output=dict))

        _keys = self._default_ls_keys() if namespace is None else dict(namespace=namespace)
        return ls(_proc, _keys, n=n, keys=keys, extra_keys=extra_keys)

    def _default_ls_keys(self):
        if len(self) > 0:
            return self[0].default_ls_keys
        return []

    def get(self, *keys, remapping=None, patches=None, **kwargs):
        r"""Return the metadata values for each field.

        Parameters
        ----------
        *args: tuple
            Positional arguments defining the metadata keys. Passed to
            :obj:`GribField.metadata() <data.readers.grib.codes.GribField.metadata>`
        **kwargs: dict, optional
            Keyword arguments passed to
            :obj:`GribField.metadata() <data.readers.grib.codes.GribField.metadata>`

        Returns
        -------
        list
            List with one item per :obj:`GribField <data.readers.grib.codes.GribField>`

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> ds.metadata("param")
        ['2t', 'msl']
        >>> ds.metadata("param", "units")
        [('2t', 'K'), ('msl', 'Pa')]
        >>> ds.metadata(["param", "units"])
        [['2t', 'K'], ['msl', 'Pa']]

        """
        from earthkit.data.utils.metadata.args import metadata_argument_new

        _kwargs = kwargs.copy()
        astype = _kwargs.pop("astype", None)
        keys, astype, key_arg_type = metadata_argument_new(*keys, astype=astype)

        remapping = build_remapping(remapping, patches)

        return [
            f._get_fast(keys, output=key_arg_type, astype=astype, remapping=remapping, **_kwargs)
            for f in self
        ]

    def get_as_dict(self, *args, group=False, remapping=None, patches=None, **kwargs):
        r"""Return the metadata values for each field.

        Parameters
        ----------
        *args: tuple
            Positional arguments defining the metadata keys. Passed to
            :obj:`GribField.metadata() <data.readers.grib.codes.GribField.metadata>`
        **kwargs: dict, optional
            Keyword arguments passed to
            :obj:`GribField.metadata() <data.readers.grib.codes.GribField.metadata>`

        Returns
        -------
        list
            List with one item per :obj:`GribField <data.readers.grib.codes.GribField>`

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> ds.metadata("param")
        ['2t', 'msl']
        >>> ds.metadata("param", "units")
        [('2t', 'K'), ('msl', 'Pa')]
        >>> ds.metadata(["param", "units"])
        [['2t', 'K'], ['msl', 'Pa']]

        """
        from earthkit.data.utils.metadata.args import metadata_argument_new

        _kwargs = kwargs.copy()
        astype = _kwargs.pop("astype", None)
        keys, astype, _ = metadata_argument_new(*args, astype=astype)

        remapping = build_remapping(remapping, patches)

        if group:
            result = {k: [] for k in keys}
            vals = []
            for f in self:
                vals.append(f._get_fast_list(keys[0], remapping=remapping, **_kwargs))

            for i, k in enumerate(keys):
                result[k] = vals[:][i]

            return result
        else:
            result = []
            for f in self:
                result.append(f._get_fast_dict(keys, astype=astype, remapping=remapping, **_kwargs))
            return result

    @property
    def geography(self):
        if self._has_shared_geography:
            return self[0].geography
        elif len(self) == 0:
            return None
        else:
            raise ValueError("Fields do not have the same grid geometry")

    def to_latlon(self, index=None, **kwargs):
        r"""Return the latitudes/longitudes shared by all the fields.

        Parameters
        ----------
        index: array indexing object, optional
            The index of the latitudes/longitudes to be extracted. When it is None
            all the values are extracted.
        **kwargs: dict, optional
            Keyword arguments passed to
            :meth:`Field.to_latlon() <data.core.fieldlist.Field.to_latlon>`

        Returns
        -------
        dict
            Dictionary with items "lat" and "lon", containing the arrays of the latitudes and
            longitudes, respectively.

        Raises
        ------
        ValueError
            When not all the fields have the same grid geometry

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> for f in ds:
        ...     print(f.shape)
        ...
        (11, 19)
        (11, 19)
        >>> r = ds.to_latlon()
        >>> for k, v in r.items():
        ...     print(f"{k}: shape={v.shape}")
        ...
        lat: shape=(11, 19)
        lon: shape=(11, 19)
        >>> r["lon"][:2]
        array([[-27., -23., -19., -15., -11.,  -7.,  -3.,   1.,   5.,   9.,  13.,
         17.,  21.,  25.,  29.,  33.,  37.,  41.,  45.],
        [-27., -23., -19., -15., -11.,  -7.,  -3.,   1.,   5.,   9.,  13.,
         17.,  21.,  25.,  29.,  33.,  37.,  41.,  45.]])

        """
        if self._has_shared_geography:
            return self[0].to_latlon(**kwargs)
        elif len(self) == 0:
            return dict(lat=None, lon=None)
        else:
            raise ValueError("Fields do not have the same grid geometry")

    @property
    def bounding_box(self):
        r"""List of :obj:`BoundingBox <data.utils.bbox.BoundingBox>`: Return the bounding box for each field."""
        return [f.geography.bounding_box for f in self]

    @cached_property
    def _has_shared_geography(self):
        if len(self) > 0:
            grid = self[0].geography.unique_grid_id
            if grid is not None:
                return all(f.geography.unique_grid_id == grid for f in self)
        return False

    def to_fieldlist(self, array_backend=None, **kwargs):
        r"""Convert to a new :class:`FieldList`.

        Parameters
        ----------
        array_backend: str, module, :obj:`ArrayBackend`
            Specifies the array backend for the generated :class:`FieldList`. The array
            type must be supported by :class:`ArrayBackend`.

        **kwargs: dict, optional
            ``kwargs`` are passed to :obj:`to_array` to
            extract the field values the resulting object will store.

        Returns
        -------
        :class:`SimpleFieldList`
            - a new fieldlist containing :class`ArrayField` fields

        Examples
        --------
        The following example will convert a fieldlist read from a file into a
        :class:`SimpleFieldList` storing single precision field values.

        >>> import numpy as np
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/tuv_pl.grib")
        >>> ds.path
        'docs/examples/tuv_pl.grib'
        >>> r = ds.to_fieldlist(array_backend="numpy", dtype=np.float32)
        >>> r
        SimpleFieldList(fields=18)
        >>> hasattr(r, "path")
        False
        >>> r.to_numpy().dtype
        dtype('float32')

        """
        # return self.from_fields([f.copy(array_backend=array_backend, **kwargs) for f in self])
        return self.from_fields([f.to_array_based(array_backend=array_backend, **kwargs) for f in self])

    def normalise_selection(self, **kwargs):
        from .field import Field

        return Field.normalise_selection(**kwargs)

    def to_tensor(self, *args, **kwargs):
        from earthkit.data.indexing.tensor import FieldListTensor

        return FieldListTensor.from_fieldlist(self, *args, **kwargs)

    def cube(self, *args, **kwargs):
        from earthkit.data.indexing.cube import FieldCube

        return FieldCube(self, *args, **kwargs)

    def default_encoder(self):
        if len(self) > 0:
            return self[0].default_encoder()

    def _encode(self, encoder, **kwargs):
        """Double dispatch to the encoder"""
        return encoder._encode_fieldlist(self, **kwargs)


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

    def to_pandas(self, *args, **kwargs):
        # TODO make it generic
        if len(self) > 0:
            if self[0].default_encoder() == "grib":
                from earthkit.data.readers.grib.pandas import PandasMixIn

                class _C(PandasMixIn, SimpleFieldList):
                    pass

                return _C(self.fields).to_pandas(*args, **kwargs)
        else:
            import pandas as pd

            return pd.DataFrame()

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
        print("StreamFieldList.batched", type(self._source))
        return self._source.batched(n)

    def group_by(self, *keys, **kwargs):
        return self._source.group_by(*keys)

    def __getstate__(self):
        raise NotImplementedError("StreamFieldList cannot be pickled")

    # def to_xarray(self, **kwargs):
    #     from earthkit.data.core.fieldlist import FieldList

    #     fields = [f for f in self]
    #     return FieldList.from_fields(fields).to_xarray(**kwargs)

    @classmethod
    def merge(cls, sources):
        from earthkit.data.sources.stream import MultiStreamSource

        assert all(isinstance(s, StreamFieldList) for s in sources), sources
        assert len(sources) > 1
        return MultiStreamSource.merge(sources)

    def default_encoder(self):
        return None
