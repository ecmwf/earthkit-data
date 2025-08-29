# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from functools import cached_property

import deprecation
from earthkit.utils.array import array_namespace
from earthkit.utils.array import convert_array

from earthkit.data.core.fieldlist import FieldListCore
from earthkit.data.core.index import Index
from earthkit.data.decorators import detect_out_filename

GRIB_KEYS_NAMES = [
    "class",
    "stream",
    "levtype",
    "type",
    "expver",
    "date",
    "hdate",
    "andate",
    "time",
    "antime",
    "reference",
    "anoffset",
    "verify",
    "fcmonth",
    "fcperiod",
    "leadtime",
    "opttime",
    "origin",
    "domain",
    "method",
    "diagnostic",
    "iteration",
    "number",
    "quantile",
    "levelist",
    "param",
]

LS_KEYS = [
    "name",
    "level",
    "level_type",
    "base_datetime",
    "step",
    "valid_datetime",
    "number",
    "gridType",
]
INDEX_KEYS = list(GRIB_KEYS_NAMES)

DESCRIBE_KEYS = [
    "shortName",
    "typeOfLevel",
    "level",
    "date",
    "time",
    "stepRange",
    "number",
    "paramId",
    "marsClass",
    "marsStream",
    "marsType",
    "experimentVersionNumber",
]


def build_remapping(remapping, patches):
    if remapping is not None or patches is not None:
        from earthkit.data.core.order import build_remapping

        remapping = build_remapping(remapping, patches)
    return None


class FieldList(Index, FieldListCore):
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
        from earthkit.data.indexing.simple import SimpleFieldList

        return SimpleFieldList([f for f in fields])

    @staticmethod
    def from_numpy(array, metadata):
        return FieldList.from_array(array, metadata)

    @staticmethod
    def from_array(array, metadata):
        from earthkit.data.sources.array_list import from_array

        return from_array(array, metadata)

    @property
    def values(self):
        return self._as_array("values")

    def to_numpy(self, **kwargs):
        return self._as_array("to_numpy", **kwargs)

    def to_array(self, **kwargs):
        return self._as_array("to_array", **kwargs)

    def _as_array(self, accessor, **kwargs):
        """Helper to use pre-allocated target array to store the field values."""

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

    def data(self, keys=("lat", "lon", "value"), flatten=False, dtype=None, index=None):
        _keys = dict(
            lat=self._metadata.geography.latitudes,
            lon=self._metadata.geography.longitudes,
            value=self._values,
        )

        if isinstance(keys, str):
            keys = [keys]

        for k in keys:
            if k not in _keys:
                raise ValueError(f"data: invalid argument: {k}")

        r = {}
        for k in keys:
            # TODO: convert dtype
            v = _keys[k](dtype=dtype)
            if v is None:
                raise ValueError(f"data: {k} not available")
            v = self._reshape(v, flatten)
            if index is not None:
                v = v[index]
            r[k] = v

        # convert latlon to array format
        ll = {k: r[k] for k in r if k != "value"}
        if ll:
            sample = r.get("value", None)
            if sample is None:
                sample = self._values(dtype=dtype)
            for k, v in zip(ll.keys(), convert_array(list(ll.values()), target_array_sample=sample)):
                r[k] = v

        r = list(r.values())
        if len(r) == 1:
            return r[0]
        else:
            return array_namespace(r[0]).stack(r)

    def datetime(self):
        r"""Return the unique, sorted list of dates and times in the fieldlist.

        Returns
        -------
        dict of datatime.datetime
            Dict with items "base_time" and "valid_time".

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "tests/data/t_time_series.grib")
        >>> ds.datetime()
        {'base_time': [datetime.datetime(2020, 12, 21, 12, 0)],
        'valid_time': [
            datetime.datetime(2020, 12, 21, 12, 0),
            datetime.datetime(2020, 12, 21, 15, 0),
            datetime.datetime(2020, 12, 21, 18, 0),
            datetime.datetime(2020, 12, 21, 21, 0),
            datetime.datetime(2020, 12, 23, 12, 0)]}

        """
        base = set()
        valid = set()
        for f in self:
            if v := f.time.base_datetime:
                base.add(v)
            if v := f.time.valid_datetime:
                valid.add(v)
        return {"base_time": sorted(base), "valid_time": sorted(valid)}

    @property
    def geography(self):
        if self._has_shared_geography:
            return self[0].geography
        elif len(self) == 0:
            return None
        else:
            raise ValueError("Fields do not have the same grid geometry")

    def to_latlon(self, index=None, **kwargs):
        if self._has_shared_geography:
            return self[0].to_latlon(**kwargs)
        elif len(self) == 0:
            return dict(lat=None, lon=None)
        else:
            raise ValueError("Fields do not have the same grid geometry")

    def to_points(self, **kwargs):
        if self._has_shared_geography:
            return self[0].to_points(**kwargs)
        elif len(self) == 0:
            return dict(x=None, y=None)
        else:
            raise ValueError("Fields do not have the same grid geometry")

    def bounding_box(self):
        return [f.geography.bounding_box for f in self]

    def projection(self):
        if self._has_shared_geography:
            return self[0].projection()
        elif len(self) == 0:
            return None
        else:
            raise ValueError("Fields do not have the same grid geometry")

    @cached_property
    def _has_shared_geography(self):
        if len(self) > 0:
            grid = self[0].geography.unique_grid_id
            if grid is not None:
                return all(f.geography.unique_grid_id == grid for f in self)
        return False

    def get(self, *keys, remapping=None, patches=None, **kwargs):
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

    def metadata(self, *args, **kwargs):
        result = []
        for s in self:
            result.append(s.metadata(*args, **kwargs))
        return result

    @cached_property
    def _md_indices(self):
        from .indices import FieldListIndices

        return FieldListIndices(self)

    def indices(self, squeeze=False):
        return self._md_indices.indices(squeeze=squeeze)

    def index(self, key):
        return self._md_indices.index(key)

    def _default_ls_keys(self):
        if len(self) > 0:
            return self[0].default_ls_keys
        return []

    def ls(self, n=None, keys=None, extra_keys=None, namespace=None):
        from earthkit.data.utils.summary import ls

        def _proc(keys, n):
            if isinstance(keys, dict):
                keys = list(keys.keys())

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

    def head(self, n=5, **kwargs):
        if n <= 0:
            raise ValueError("head: n must be > 0")
        return self.ls(n=n, **kwargs)

    def tail(self, n=5, **kwargs):
        if n <= 0:
            raise ValueError("n must be > 0")
        return self.ls(n=-n, **kwargs)

    @cached_property
    def _describe_keys(self):
        if len(self) > 0:
            return DESCRIBE_KEYS
        else:
            return []

    def describe(self, *args, **kwargs):
        r"""Generate a summary of the fieldlist."""
        from earthkit.data.utils.summary import format_describe

        def _proc():
            for f in self:
                yield (f._get_fast(self._describe_keys, output=dict))

        return format_describe(_proc(), *args, **kwargs)

    def to_fieldlist(self, array_backend=None, **kwargs):
        # return self.from_fields([f.copy(array_backend=array_backend, **kwargs) for f in self])
        return self.from_fields([f.to_array_based(array_backend=array_backend, **kwargs) for f in self])

    def to_tensor(self, *args, **kwargs):
        from earthkit.data.indexing.tensor import FieldListTensor

        return FieldListTensor.from_fieldlist(self, *args, **kwargs)

    def cube(self, *args, **kwargs):
        from earthkit.data.indexing.cube import FieldCube

        return FieldCube(self, *args, **kwargs)

    @deprecation.deprecated(deprecated_in="0.13.0", removed_in=None, details="Use to_target() instead")
    @detect_out_filename
    def save(self, filename, append=False, **kwargs):
        r"""Write all the fields into a file.

        Parameters
        ----------
        filename: str, optional
            The target file path, if not defined attempts will be made to detect the filename
        append: bool, optional
            When it is true append data to the target file. Otherwise
            the target file be overwritten if already exists. Default is False
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`write`.

        See Also
        --------
        :obj:`write`

        """
        metadata = {}
        bits_per_value = kwargs.pop("bits_per_value", None)
        if bits_per_value is not None:
            metadata = {"bitsPerValue": bits_per_value}

        self.to_target("file", filename, append=append, metadata=metadata, **kwargs)

        # original code
        # flag = "wb" if not append else "ab"
        # with open(filename, flag) as f:
        #     self.write(f, **kwargs)

    @deprecation.deprecated(deprecated_in="0.13.0", removed_in=None, details="Use to_target() instead")
    def write(self, f, **kwargs):
        r"""Write all the fields to a file object.

        Parameters
        ----------
        f: file object
            The target file object.
        **kwargs: dict, optional
            Other keyword arguments passed to the underlying field implementation.

        See Also
        --------
        :obj:`write`

        """
        metadata = {}
        bits_per_value = kwargs.pop("bits_per_value", None)
        if bits_per_value is not None:
            metadata = {"bitsPerValue": bits_per_value}

        self.to_target("file", f, metadata=metadata, **kwargs)

        # original code
        # for s in self:
        #     s.write(f, **kwargs)

    def default_encoder(self):
        if len(self) > 0:
            return self[0].default_encoder()

    def _encode(self, encoder, **kwargs):
        """Double dispatch to the encoder"""
        return encoder._encode_fieldlist(self, **kwargs)

    # def _normalise_sel_input(self, **kwargs):
    #     from .field import Field

    #     return Field._normalise_sel_input(**kwargs)

    @staticmethod
    def normalise_key_values(**kwargs):
        from ..core.field import Field

        return Field.normalise_key_values(**kwargs)
