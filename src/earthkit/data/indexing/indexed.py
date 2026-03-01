# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from collections import defaultdict

from earthkit.utils.array import array_namespace as eku_array_namespace
from earthkit.utils.decorators import thread_safe_cached_property

from earthkit.data.core.fieldlist import FieldList
from earthkit.data.core.index import Index
from earthkit.data.core.index import MaskIndex
from earthkit.data.core.index import MultiIndex
from earthkit.data.core.order import build_remapping
from earthkit.data.utils.compute import wrap_maths


@wrap_maths
class IndexFieldListBase(Index, FieldList):
    # @staticmethod
    # def from_fields(fields):
    #     r"""Create a :class:`SimpleFieldList`.

    #     Parameters
    #     ----------
    #     fields: iterable
    #         Iterable of :obj:`Field` objects.

    #     Returns
    #     -------
    #     :class:`SimpleFieldList`

    #     """
    #     from earthkit.data.indexing.simple import SimpleFieldList

    #     return SimpleFieldList.from_fields(fields)

    @property
    def values(self):
        return self._as_array("values")

    def to_numpy(self, **kwargs):
        return self._as_array("to_numpy", empty_array_namespace="numpy", **kwargs)

    def to_array(self, **kwargs):
        ns = kwargs.get("array_namespace", None)
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
                lat, lon = self[0].geography.latlons(flatten=flatten, dtype=dtype)
                if index is not None:
                    lat = lat[index]
                    lon = lon[index]

            r = []
            for k in keys:
                if k == "lat":
                    r.append(lat)
                elif k == "lon":
                    r.append(lon)
                elif k == "value":
                    r.extend([f.to_array(flatten=flatten, dtype=dtype, index=index) for f in self])
            return eku_array_namespace(r[0]).stack(r)

        elif len(self) == 0:
            # empty array from the default array namespace
            shape = tuple([0] * len(keys))
            return eku_array_namespace().empty(shape, dtype=dtype)
        else:
            raise ValueError("Fields do not have the same grid geometry")

    @property
    def geography(self):
        if self._has_shared_geography:
            return self[0].geography
        elif len(self) == 0:
            raise ValueError("Cannot determine geography of an empty FieldList")
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
        output="auto",
        group_by_key=False,
        flatten_dict=False,
        remapping=None,
        patch=None,
    ):
        from earthkit.data.utils.args import metadata_argument_new

        keys, astype, default, keys_arg_type = metadata_argument_new(keys, astype=astype, default=default)

        if output == "auto":
            if keys_arg_type is not None:
                output = keys_arg_type
        elif output in [list, "list"]:
            output = list
        elif output in [tuple, "tuple"]:
            output = tuple
        elif output in [dict, "dict"]:
            output = dict
        else:
            raise ValueError(f"Invalid output: {output}")

        remapping = build_remapping(remapping, patch, forced_build=False)

        _kwargs = {
            "default": default,
            "raise_on_missing": raise_on_missing,
            "remapping": remapping,
            "flatten_dict": flatten_dict,
            # "patch": patch,
            "astype": astype,
        }

        if not group_by_key or output == "auto":
            return [f._get_fast(keys, output=output, **_kwargs) for f in self]
        else:
            if output is dict:
                result = defaultdict(list)
                for f in self:
                    r = f._get_fast(keys, output=dict, **_kwargs)
                    for k, v in r.items():
                        result[k].append(v)
                return dict(result)
            else:
                vals = [f._get_fast(keys, output=list, **_kwargs) for f in self]
                return [[x[i] for x in vals] for i in range(len(keys))]

    def metadata(self, keys, **kwargs):
        if isinstance(keys, str):
            keys = "metadata." + keys
        else:
            is_tuple = isinstance(keys, tuple)
            keys = ["metadata." + x for x in keys]
            if is_tuple:
                keys = tuple(keys)

        return self.get(keys, raise_on_missing=True, **kwargs)

    def _default_ls_keys(self):
        if len(self) > 0:
            return self[0].default_ls_keys
        return []

    def ls(self, n=None, keys="default", extra_keys=None, collections=None):
        from earthkit.data.utils.summary import ls as summary_ls

        def _proc(n: int, keys: str | list | tuple = None, collections: str | list | tuple = None):
            num = len(self)
            pos = slice(0, num)

            if n is not None:
                pos = slice(0, min(num, n)) if n > 0 else slice(num - min(num, -n), num)
            pos_range = range(pos.start, pos.stop)

            default = None
            astype = None
            if keys and len(pos_range) > 0:
                default = [None] * len(keys)
                astype = [None] * len(keys)

            for i in pos_range:
                r = self[i]._get_fast(
                    keys=keys,
                    default=default,
                    astype=astype,
                    collections=collections,
                    output=dict,
                    flatten_dict=True,
                )
                yield r

            # if component is not None:
            #     for i in pos_range:
            #         f = self[i]
            #         v = {}
            #         for ns_val in f._dump_component(component, prefix_keys=True, filter=filter).values():
            #             v.update(ns_val)
            #         if keys:
            #             v.update(f._get_fast(keys, default=default, astype=astype, output=dict))
            #         yield (v)
            # else:
            #     for i in pos_range:
            #         yield (self[i]._get_fast(keys, default=default, astype=astype, output=dict))

        if keys == "default":
            keys = self._default_ls_keys()

        return summary_ls(_proc, n=n, keys=keys, extra_keys=extra_keys, collections=collections)

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
        # if len(self) > 0:
        #     return DESCRIBE_KEYS
        # else:
        #     return []
        return []

    def describe(self, *args, **kwargs):
        r"""Generate a summary of the fieldlist."""
        from earthkit.data.utils.summary import format_describe

        def _proc():
            for f in self:
                # PW: TODO: `default` and `astype` kwargs of `f._get_fast()` might need to be aligned with `keys`
                yield (f._get_fast(self._describe_keys, output=dict))

        return format_describe(_proc(), *args, **kwargs)

    def to_fieldlist(self, array_namespace=None, device=None, **kwargs):
        return self.from_fields(
            [f.to_array_field(array_namespace=array_namespace, device=device, **kwargs) for f in self]
        )

    def to_tensor(self, *args, **kwargs):
        from earthkit.data.indexing.tensor import FieldListTensor

        return FieldListTensor.from_fieldlist(self, *args, **kwargs)

    def to_cube(self, *args, **kwargs):
        from earthkit.data.indexing.cube import FieldCube

        return FieldCube(self, *args, **kwargs)

    def _encode(self, encoder, **kwargs):
        """Double dispatch to the encoder"""
        return encoder._encode_fieldlist(self, **kwargs)

    # def _normalise_sel_input(self, **kwargs):
    #     from .field import Field

    #     return Field._normalise_sel_input(**kwargs)

    @staticmethod
    def _normalise_key_values(**kwargs):
        from ..core.field import Field

        return Field._normalise_key_values(**kwargs)

    # def unique_values(self, *coords, remapping=None, patch=None, progress_bar=False):
    #     """Given a list of metadata attributes, such as date, param, levels,
    #     returns the list of unique values for each attributes
    #     """
    #     from collections import defaultdict

    #     from earthkit.data.core.order import build_remapping

    #     assert len(coords)
    #     assert all(isinstance(k, str) for k in coords), coords

    #     remapping = build_remapping(remapping, patch)
    #     iterable = self

    #     if progress_bar:
    #         from earthkit.data.utils.progbar import progress_bar

    #         if progress_bar:
    #             iterable = progress_bar(
    #                 iterable=self,
    #                 desc=f"Finding coords in dataset for {coords}",
    #             )

    #     vals = defaultdict(dict)
    #     for f in iterable:
    #         get = remapping(f.get)
    #         for k in coords:
    #             v = get(k, default=None)
    #             vals[k][v] = True

    #     vals = {k: tuple(values.keys()) for k, values in vals.items()}

    #     return vals

    def _unary_op(self, oper):
        from earthkit.data.utils.compute import get_method

        method = "loop"
        return get_method(method).unary_op(oper, self)

    def _binary_op(self, oper, y):
        from earthkit.data.utils.compute import get_method

        method = "loop"
        r = get_method(method).binary_op(oper, self, y)
        return r

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        return MaskFieldList(*args, **kwargs)

    @classmethod
    def merge(cls, sources):
        assert all(isinstance(_, IndexFieldListBase) for _ in sources)
        return MultiFieldList(sources)


class MaskFieldList(IndexFieldListBase, MaskIndex):
    def __init__(self, *args, **kwargs):
        MaskIndex.__init__(self, *args, **kwargs)


class MultiFieldList(IndexFieldListBase, MultiIndex):
    def __init__(self, *args, **kwargs):
        MultiIndex.__init__(self, *args, **kwargs)
