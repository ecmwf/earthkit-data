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
from earthkit.data.core.index import Index, MaskIndex, MultiIndex
from earthkit.data.core.order import build_remapping
from earthkit.data.utils.compute import wrap_maths

from .pandas import PandasMixIn
from .xarray import XarrayMixIn


class IndexForFieldList(Index):
    """Provide fieldlist specific documentation for the Index interface.

    This is the same class as :py:class:`~earthkit.data.core.index.Index`, but with
    the docstrings of some of the methods overridden to provide fieldlist
    specific documentation.

    """

    def unique(
        self,
        *args,
        sort=False,
        drop_none=True,
        squeeze=False,
        unwrap_single=False,
        remapping=None,
        patch=None,
        cache=True,
        progress_bar=False,
    ) -> dict | tuple:
        """Return the unique values for a given set of metadata keys.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the metadata keys to collect unique values for.
        sort: bool, optional
            Whether to sort the collected unique values. Default is False.
        drop_none: bool, optional
            Whether to drop None values from the collected unique values. Default is True.
        squeeze: bool, optional
            When True only returns the metadata keys that have more than one values. Default is False.
        unwrap_single: bool, optional
            When True and only one metadata key is specified, the unique values are returned as a tuple instead
            of a dict. Default is False.
        remapping: dict, optional
            A dictionary for remapping keys or values during collection. Default is None.
        patch: dict, optional
            A dictionary for patching key values during collection. Default is None.
        cache: bool, optional
            Whether to use an a cache attached to the fieldlist for previously collected unique values.
            Default is True.
        progress_bar: bool, optional
            Whether to display a progress bar during collection. Default is False.

        Returns
        -------
        dict
            A dictionary containing the unique values for the specified metadata keys.

        """
        return super().unique(
            *args,
            sort=sort,
            drop_none=drop_none,
            squeeze=squeeze,
            unwrap_single=unwrap_single,
            remapping=remapping,
            patch=patch,
            cache=cache,
            progress_bar=progress_bar,
        )

    def sel(self, *args, remapping=None, **kwargs) -> "FieldList":
        """Select the fields matching the given metadata conditions.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the filter conditions as a dict.
            Both single or multiple keys are allowed to use. When multiple filter conditions
            are specified, they are combined with a logical AND operator. Each metadata key in
            the filter conditions can specify the following type of filter values:

            - single value::

                fl.sel({parameter.variable: "t"})

            - list of values::

                fl.sel({parameter.variable: ["u", "v"]})

            - slice of values (defines a closed interval, so treated as inclusive of both the start
            and stop values, unlike normal Python indexing). The following example filters the fields
            with "vertical.level" between 300 and 500 inclusively::

                fl.sel({vertical.level: slice(300, 500)})

            Date and time related keys from the "time" field component are automatically normalised
            for comparison. This is also applied to the following keys from the raw
            metadata: "metadata.base_datetime", "metadata.valid_datetime" and "metadata.step_timedelta".

            For example, when filtering by "time.valid_datetime" the following calls are equivalent:

            >>> fl.sel({ "time.valid_datetime": "2018-08-01T12:00:00"})
            >>> fl.sel({ "time.valid_datetime": datetime(2018, 8, 1, 12, 0) })

            Similarly, when filtering by "time.step" the following calls are equivalent (values are assumed
            to be in hours when the unit is not specified):

            >>> fl.sel({ "time.step": "6h"})
            >>> fl.sel({ "time.step": 6})
            >>> fl.sel({ "time.step": "360m"})
            >>> fl.sel({ "time.step": timedelta(hours=6)})

        remapping: dict
            Define new metadata keys from existing ones to use in ``*args`` and ``**kwargs``.
            E.g. to define a new key "param_level" as the concatenated value of
            the "parameter.variable" and "vertical.level" keys use::

            >>> remapping={"param_level": "{parameter.variable}{vertical.level}"}

            See below for a more elaborate example.

        **kwargs: dict, optional
            Other keyword arguments specifying the filter conditions.

        Returns
        -------
        MaskFieldlist, FieldList
            Returns a MaskFieldList with the reordered fields. It provides a view to the data in the
            original object, so no data is copied. When called without any arguments it returns the
            original fieldlist.


        Examples
        --------
        How-to examples:

        - :ref:`/how-tos/grib/grib_selection.ipynb`

        More examples:

        >>> import earthkit.data as ekd
        >>> fl = ekd.from_source("sample", "tuv_pl.grib").to_fieldlist()
        >>> len(fl)
        18

        Selecting by a single key ("parameter.variable") with a single value:

        >>> fl1 = fl.sel({parameter.variable: "t"})
        >>> for f in fl1:
        ...     print(f)
        ...
        Field(t,1000,20180801,1200,0,0)
        Field(t,850,20180801,1200,0,0)
        Field(t,700,20180801,1200,0,0)
        Field(t,500,20180801,1200,0,0)
        Field(t,400,20180801,1200,0,0)
        Field(t,300,20180801,1200,0,0)

        Selecting by multiple keys ("parameter.variable", "vertical.level") with a list and slice of values:

        >>> fl1 = fl.sel(
        ...     {parameter.variable: ["u", "v"], vertical.level: slice(400, 700)}
        ... )
        >>> for f in fl1:
        ...     print(f)
        ...
        Field(u,700,20180801,1200,0,0)
        Field(v,700,20180801,1200,0,0)
        Field(u,500,20180801,1200,0,0)
        Field(v,500,20180801,1200,0,0)
        Field(u,400,20180801,1200,0,0)
        Field(v,400,20180801, 1200,0,0)

        Using ``remapping`` to specify the selection by a key created from two other keys
        (we created key "param_level" from "parameter.variable" and "vertical.level"):

        >>> fl1 = fl.sel(
        ...     param_level=["t850", "u1000"],
        ...     remapping={"param_level": "{parameter.variable}{vertical.level}"},
        ... )
        >>> for f in fl1:
        ...     print(f)
        ...
        Field(u,1000,20180801,1200,0,0)
        Field(t,850,20180801,1200,0,0)
        """
        return super().sel(*args, remapping=remapping, **kwargs)

    def order_by(self, *args, remapping=None, patch=None, **kwargs):
        """Change the order of the fields in a fieldlist.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the metadata keys to perform the ordering on. Each argument can be
            a single key (str) or multiple keys as a list/tuple of str or a dictionary.
            Any metadata keys that :meth:`earthkit.data.core.field.Field.get` accepts can be
            used here. The order of the keys defines the priority of the ordering. When a dictionary is used it
            must specify the ordering direction or the order of the values for each key. The ordering direction
            can be either "ascending" or "descending" (the default is "ascending"). The order of values for
            a key is defined by a list of values for that key, which must include all the available values
            for that key in the fieldlist. See the examples below for more details.
        remapping: dict
            Define new metadata keys from existing ones to use in ``*args`` and
            ``**kwargs``. E.g. to define a new
            key "param_level" as the concatenated value of the "parameter.variable"
            and "vertical.level" keys use::

                remapping={"param_level": "{parameter.variable}{vertical.level}"}

            See below for a more elaborate example.

        **kwargs: dict, optional
            Other keyword arguments specifying the metadata keys to perform the ordering on. Used in
            the same way as a dictionary in ``*args``.


        Returns
        -------
        MaskFieldList, FieldList
            Returns a MaskFieldList with the reordered fields. It provides a view to the data in the
            original object, so no data is copied. When called without any arguments it returns the
            original fieldlist.

        Examples
        --------
        How-to examples:

        - :ref:`/how-tos/grib/grib_order_by.ipynb`


        Ordering by a single metadata key ("parameter.variable"). The default ordering direction
        is ``ascending``:

        >>> import earthkit.data as ekd
        >>> fl = ekd.from_source("sample", "test6.grib").to_fieldlist()
        >>> for f in fl.order_by("parameter.variable"):
        ...     print(f)
        ...
        Field(t,850,20180801,1200,0,0)
        Field(t,1000,20180801,1200,0,0)
        Field(u,850,20180801,1200,0,0)
        Field(u,1000,20180801,1200,0,0)
        Field(v,850,20180801,1200,0,0)
        Field(v,1000,20180801,1200,0,0)

        Ordering by multiple keys (first by "vertical.level" then by "parameter.variable"). The default ordering
        direction is ``ascending`` for both keys:

        >>> for f in fl.order_by(["vertical.level", "parameter.variable"]):
        ...     print(f)
        ...
        Field(t,850,20180801,1200,0,0)
        Field(u,850,20180801,1200,0,0)
        Field(v,850,20180801,1200,0,0)
        Field(t,1000,20180801,1200,0,0)
        Field(u,1000,20180801,1200,0,0)
        Field(v,1000,20180801,1200,0,0)

        Specifying the ordering direction:

        >>> for f in fl.order_by(
        ...     {"parameter.variable": "ascending", "vertical.level": "descending"}
        ... ):
        ...     print(f)
        Field(t,1000,20180801,1200,0,0)
        Field(t,850,20180801,1200,0,0)
        Field(u,1000,20180801,1200,0,0)
        Field(u,850,20180801,1200,0,0)
        Field(v,1000,20180801,1200,0,0)
        Field(v,850,20180801,1200,0,0)

        Using the list of all the values of a key ("parameter.variable") to define the order:

        >>> for f in fl.order_by({"parameter.variable": ["u", "t", "v"]}):
        ...     print(f)
        Field(u,1000,20180801,1200,0,0)
        Field(u,850,20180801,1200,0,0)
        Field(t,1000,20180801,1200,0,0)
        Field(t,850,20180801,1200,0,0)
        Field(v,1000,20180801,1200,0,0)
        Field(v,850,20180801,1200,0,0)

        Using ``remapping`` to specify the order by a key created from two other keys
        (we created key "param_level" from "parameter.variable" and "vertical.level"):

        >>> ordering = ["t850", "t1000", "u1000", "v850", "v1000", "u850"]
        >>> remapping = {"param_level": "{parameter.variable}{vertical.level}"}
        >>> for f in fl.order_by({"param_level": ordering}, remapping=remapping):
        ...     print(f)
        Field(t,850,20180801,1200,0,0)
        Field(t,1000,20180801,1200,0,0)
        Field(u,1000,20180801,1200,0,0)
        Field(v,850,20180801,1200,0,0)
        Field(v,1000,20180801,1200,0,0)
        Field(u,850,20180801,1200,0,0)
        """
        return super().order_by(*args, remapping=remapping, patch=patch, **kwargs)

    def batched(self, n):
        """Iterate through the fieldlist in batches of ``n`` fields.

        Parameters
        ----------
        n: int
            Batch size.

        Returns
        -------
        object
            Returns an iterator yielding batches of ``n`` fields. Each batch is a new fieldlist
            containing a view to the data in the original object, so no data is copied. The last
            batch may contain fewer than ``n`` fields.
        """
        return super().batched(n)

    def group_by(self, *keys, sort=True):
        """Iterate through the fieldlist in groups defined by metadata keys.

        Parameters
        ----------
        *keys: tuple
            Positional arguments specifying the metadata keys to group by.
            Keys can be a single or multiple str, or a list or tuple of str.

        sort: bool, optional
            If ``True`` (default), the fieldlist is sorted by the metadata ``keys`` before grouping.

        Returns
        -------
        object
            Returns an iterator yielding batches of fields grouped by the metadata ``keys``. Each
            batch is a new fieldlist containing a view to the data in the original object, so no data
            is copied. It generates a new group every time the value of the ``keys`` change.

        """
        return super().group_by(*keys, sort=sort)


@wrap_maths
class IndexFieldListBase(XarrayMixIn, PandasMixIn, IndexForFieldList, FieldList):
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

    def set(self, *args, **kwargs):
        kwargs = kwargs.copy()
        for a in args:
            if a is None:
                continue
            if isinstance(a, dict):
                kwargs.update(a)
                continue
            raise ValueError(f"Cannot use arg={a}. Only dict allowed.")

        if not kwargs:
            return self

        return self.from_fields([f.set(**kwargs) for f in self])

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

    def to_fieldlist(self, array_namespace=None, device=None, flatten=False, dtype=None):
        return self.from_fields([
            f.to_array_field(array_namespace=array_namespace, device=device, flatten=flatten, dtype=dtype) for f in self
        ])

    def to_tensor(self, *args, **kwargs):
        from earthkit.data.indexing.tensor import FieldListTensor

        return FieldListTensor.from_fieldlist(self, *args, **kwargs)

    def to_cube(self, *args, **kwargs):
        from earthkit.data.indexing.cube import FieldCube

        return FieldCube(self, *args, **kwargs)

    @staticmethod
    def _normalise_key_values(**kwargs):
        from ..core.field import Field

        return Field._normalise_key_values(**kwargs)

    def _unary_op(self, oper):
        from earthkit.data.utils.compute import get_method

        method = "loop"
        return get_method(method).unary_op(oper, self)

    def _binary_op(self, oper, y):
        from earthkit.data.utils.compute import get_method

        method = "loop"
        r = get_method(method).binary_op(oper, self, y)
        return r

    def to_target(self, target, *args, **kwargs):
        from earthkit.data.targets import to_target

        to_target(target, *args, data=self, **kwargs)

    def _default_encoder(self):
        return self[0]._default_encoder() if len(self) > 0 else None

    def _encode(self, encoder, hints=None, **kwargs):
        if hints and hints.get("path_allowed", False) and hasattr(self, "_encode_path"):
            result = self._encode_path(encoder, **kwargs)
            if result is not None:
                return result
        return self._encode_default(encoder, **kwargs)

    def _encode_default(self, encoder, **kwargs):
        return encoder._encode_fieldlist(self, **kwargs)

    def to_data_object(self):
        from earthkit.data.data.fieldlist import FieldListData

        return FieldListData(self)

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

    def _default_encoder(self):
        for i in self._indexes:
            encoder = i._default_encoder()
            if encoder is not None:
                return encoder
        return None
