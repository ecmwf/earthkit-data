# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import warnings

import deprecation
from earthkit.utils.array import array_namespace as eku_array_namespace

from earthkit.data.core.fieldlist import FieldListCore
from earthkit.data.core.index import Index
from earthkit.data.core.index import MaskIndex
from earthkit.data.core.index import MultiIndex
from earthkit.data.decorators import detect_out_filename
from earthkit.data.decorators import thread_safe_cached_property
from earthkit.data.utils.compute import wrap_maths

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


@wrap_maths
class IndexedFieldList(Index, FieldListCore):
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

        return SimpleFieldList.from_fields(fields)

    @staticmethod
    def from_numpy(array, metadata):
        raise NotImplementedError("IndexedFieldList.from_numpy is not implemented")
        # return FieldList.from_array(array, metadata)

    @staticmethod
    def from_array(array, metadata):
        raise NotImplementedError("IndexedFieldList.from_array is not implemented")

    @property
    def values(self):
        return self._as_array("values")

    def to_numpy(self, **kwargs):
        return self._as_array("to_numpy", empty_array_namespace="numpy", **kwargs)

    def to_array(self, **kwargs):
        ns = kwargs.get("array_namespace", None)
        if ns is None:
            ns = eku_array_namespace(kwargs.get("array_backend", None))

        return self._as_array("to_array", empty_array_namespace=ns, **kwargs)

    def _as_array(self, accessor, empty_array_namespace=None, **kwargs):
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
            xp = eku_array_namespace(vals)
            shape = (n, *vals.shape)
            r = xp.empty(shape, dtype=vals.dtype, device=xp.device(vals))
            r[0] = vals
            for i, f in enumerate(it, start=1):
                r[i] = _vals(f)
        else:
            # create an empty array using the right namespace and dtype
            xp = eku_array_namespace(empty_array_namespace if empty_array_namespace is not None else "numpy")
            r = xp.empty((0,), dtype=kwargs.get("dtype"))

        return r

    def data(self, keys=("lat", "lon", "value"), flatten=False, dtype=None, index=None):
        if isinstance(keys, str):
            keys = [keys]

        if any(k not in ("lat", "lon", "value") for k in keys):
            raise ValueError(f"data: invalid argument: {keys}")

        if self._has_shared_geography:
            if "lat" in keys or "lon" in keys:
                latlon = self[0].to_latlon(flatten=flatten, dtype=dtype, index=index)

            r = []
            for k in keys:
                if k == "lat":
                    r.append(latlon["lat"])
                elif k == "lon":
                    r.append(latlon["lon"])
                elif k == "value":
                    r.extend([f.to_array(flatten=flatten, dtype=dtype, index=index) for f in self])
            return eku_array_namespace(r[0]).stack(r)

        elif len(self) == 0:
            # empty array from the default array namespace
            shape = tuple([0] * len(keys))
            return eku_array_namespace().empty(shape, dtype=dtype)
        else:
            raise ValueError("Fields do not have the same grid geometry")

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
            if v := f.time.base_datetime():
                base.add(v)
            if v := f.time.valid_datetime():
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

    @property
    def latitudes(self):
        if self._has_shared_geography:
            return self[0].geography.latitudes()
        elif len(self) == 0:
            return None
        else:
            raise ValueError("Fields do not have the same grid geometry")

    @property
    def longitudes(self):
        if self._has_shared_geography:
            return self[0].geography.longitudes()
        elif len(self) == 0:
            return None
        else:
            raise ValueError("Fields do not have the same grid geometry")

    def to_latlon(self, index=None, **kwargs):
        if self._has_shared_geography:
            return self[0].to_latlon(index=index, **kwargs)
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
        return [f.geography.bounding_box() for f in self]

    def projection(self):
        if self._has_shared_geography:
            return self[0].geography.projection
        elif len(self) == 0:
            return None
        else:
            raise ValueError("Fields do not have the same grid geometry")

    @thread_safe_cached_property
    def _has_shared_geography(self):
        if len(self) > 0:
            grid = self[0].geography.unique_grid_id()
            if grid is not None:
                return all(f.geography.unique_grid_id() == grid for f in self)
        return False

    def get(
        self,
        keys,
        default=None,
        astype=None,
        raise_on_missing=False,
        output="item_per_field",
        remapping=None,
        patches=None,
    ):
        from earthkit.data.utils.metadata.args import metadata_argument_new

        # _kwargs = kwargs.copy()
        # astype = _kwargs.pop("astype", None)
        keys, astype, default, keys_arg_type = metadata_argument_new(keys, astype=astype, default=default)

        # assert isinstance(keys, (list, tuple))

        remapping = build_remapping(remapping, patches)

        _kwargs = {
            "default": default,
            "raise_on_missing": raise_on_missing,
            "remapping": remapping,
            # "patches": patches,
            "astype": astype,
        }

        if output == "item_per_field":
            return [f._get_fast(keys, output=keys_arg_type, **_kwargs) for f in self]
        elif output == "item_per_key":
            vals = [f._get_fast(keys, output=keys_arg_type, **_kwargs) for f in self]
            if keys_arg_type in (list, tuple):
                return [[x[i] for x in vals] for i in range(len(keys))]
            else:
                assert isinstance(keys, str)
                return vals
        elif output == "dict_per_field":
            return [f._get_fast(keys, output=dict, **_kwargs) for f in self]
        elif output == "dict_per_key":
            vals = [f._get_fast(keys, output=keys_arg_type, **_kwargs) for f in self]
            if keys_arg_type in (list, tuple):
                result = {k: [] for k in keys}
                for i, k in enumerate(keys):
                    result[k] = [x[i] for x in vals]
            else:
                assert isinstance(keys, str)
                result = {keys: vals}
            return result
        else:
            raise ValueError(
                f"get: invalid output={output}. Must be one of 'item_per_field', 'item_per_key', 'dict_per_field', 'dict_per_key'"
            )

    def metadata(self, keys, **kwargs):
        if isinstance(keys, str):
            keys = "metadata." + keys
        else:
            is_tuple = isinstance(keys, tuple)
            keys = ["metadata." + x for x in keys]
            if is_tuple:
                keys = tuple(keys)

        return self.get(keys, **kwargs)

    @thread_safe_cached_property
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

    def ls(self, n=None, keys=None, extra_keys=None, part=None):
        from earthkit.data.utils.summary import ls as summary_ls

        def _proc(keys: list, n: int, part=None):
            num = len(self)
            pos = slice(0, num)
            if n is not None:
                pos = slice(0, min(num, n)) if n > 0 else slice(num - min(num, -n), num)
            pos_range = range(pos.start, pos.stop)

            default = None
            astype = None
            if len(pos_range) > 0:
                default = [None] * len(keys)
                astype = [None] * len(keys)

            if part is not None:
                for i in pos_range:
                    f = self[i]
                    v = {}
                    for ns_val in f._dump_part(part, prefix_keys=True).values():
                        v.update(ns_val)
                    if keys:
                        v.update(f._get_fast(keys, default=default, astype=astype, output=dict))
                    yield (v)
            else:
                for i in pos_range:
                    yield (self[i]._get_fast(keys, default=default, astype=astype, output=dict))

        return summary_ls(_proc, self._default_ls_keys(), n=n, keys=keys, extra_keys=extra_keys, part=part)

    def head(self, n=5, **kwargs):
        if n <= 0:
            raise ValueError("head: n must be > 0")
        return self.ls(n=n, **kwargs)

    def tail(self, n=5, **kwargs):
        if n <= 0:
            raise ValueError("n must be > 0")
        return self.ls(n=-n, **kwargs)

    @thread_safe_cached_property
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

    def to_fieldlist(self, array_backend=None, array_namespace=None, device=None, **kwargs):
        if array_backend is not None:
            warnings.warn(
                "to_fieldlist(): 'array_backend' is deprecated. Use 'array_namespace' instead",
                DeprecationWarning,
            )
            if array_namespace is not None:
                raise ValueError("to_array(): only one of array_backend and array_namespace can be specified")
            array_namespace = array_backend

        return self.from_fields(
            [f.to_array_field(array_namespace=array_namespace, device=device, **kwargs) for f in self]
        )

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

    def unique_values(self, *coords, remapping=None, patches=None, progress_bar=False):
        """Given a list of metadata attributes, such as date, param, levels,
        returns the list of unique values for each attributes
        """
        from collections import defaultdict

        from earthkit.data.core.order import build_remapping

        assert len(coords)
        assert all(isinstance(k, str) for k in coords), coords

        remapping = build_remapping(remapping, patches)
        iterable = self

        if progress_bar:
            from earthkit.data.utils.progbar import progress_bar

            if progress_bar:
                iterable = progress_bar(
                    iterable=self,
                    desc=f"Finding coords in dataset for {coords}",
                )

        vals = defaultdict(dict)
        for f in iterable:
            get = remapping(f.get)
            for k in coords:
                v = get(k, default=None)
                vals[k][v] = True

        vals = {k: tuple(values.keys()) for k, values in vals.items()}

        return vals

    @classmethod
    def new_mask_index(self, *args, **kwargs):
        return MaskFieldList(*args, **kwargs)

    @classmethod
    def merge(cls, sources):
        assert all(isinstance(_, IndexedFieldList) for _ in sources)
        return MultiFieldList(sources)


class MaskFieldList(IndexedFieldList, MaskIndex):
    def __init__(self, *args, **kwargs):
        MaskIndex.__init__(self, *args, **kwargs)


class MultiFieldList(IndexedFieldList, MultiIndex):
    def __init__(self, *args, **kwargs):
        MultiIndex.__init__(self, *args, **kwargs)
