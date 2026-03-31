# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import functools
import logging
from abc import abstractmethod

from earthkit.utils.decorators import thread_safe_cached_property

import earthkit.data
from earthkit.data.core import Encodable
from earthkit.data.core.order import build_remapping, normalise_order_by
from earthkit.data.core.select import normalise_selection
from earthkit.data.sources import Source
from earthkit.data.utils.unique import UniqueValuesCollector

LOG = logging.getLogger(__name__)


class OrderOrSelection:
    actions = {}

    def __str__(self):
        return f"{self.__class__.__name__}({self.actions})"

    @property
    def is_empty(self):
        return not self.actions


class Selection(OrderOrSelection):
    def __init__(self, kwargs, remapping=None):
        self.remapping = build_remapping(remapping)

        class InList:
            def __init__(self, lst):
                self.first = True
                self.lst = lst  # lazy casting: lst will be modified

            def __call__(self, x):
                if self.first and x is not None:
                    target_type = type(x)
                    self.lst = [y if isinstance(y, target_type) else target_type(y) for y in self.lst]
                    self.first = False
                return x in self.lst

        class InSlice:
            def __init__(self, slc):
                self.slc = slc
                if self.slc.start is None and self.slc.stop is None:
                    raise ValueError("Invalid selection value: slice(None, None)")

                if self.slc.start is not None and self.slc.stop is not None and self.slc.stop < self.slc.start:
                    self.slc = slice(self.slc.stop, self.slc.start)

            def __call__(self, x):
                return not (
                    (self.slc.start is not None and x < self.slc.start)
                    or (self.slc.stop is not None and x > self.slc.stop)
                )

        self.actions = {}
        for k, v in kwargs.items():
            if v is None or v is earthkit.data.ALL:
                self.actions[k] = lambda x: True
                continue

            if callable(v):
                self.actions[k] = v
                continue

            if isinstance(v, slice):
                self.actions[k] = InSlice(v)
                continue

            if not isinstance(v, (list, tuple, set)):
                v = [v]

            v = set(v)

            self.actions[k] = InList(v)

    def match_element(self, element):
        get = element._get_single
        if self.remapping:
            get = self.remapping(get)
        return all(v(get(k, default=None)) for k, v in self.actions.items())


class OrderBase(OrderOrSelection):
    def __init__(self, kwargs, remapping):
        self.actions = self.build_actions(kwargs)
        self.remapping = remapping

    @abstractmethod
    def build_actions(self, kwargs):
        raise NotImplementedError()

    def compare_elements(self, a, b):
        assert callable(self.remapping), (type(self.remapping), self.remapping)
        a_get = a._get_single
        b_get = b._get_single

        if self.remapping:
            a_get = self.remapping(a_get)
            b_get = self.remapping(b_get)

        for k, v in self.actions.items():
            n = v(
                a_get(k, default=None),
                b_get(k, default=None),
            )
            if n != 0:
                return n
        return 0


class Order(OrderBase):
    def build_actions(self, kwargs):
        actions = {}

        def ascending(a, b):
            if a is b or a == b:
                return 0

            if b is None:
                return 1

            if a is None:
                return -1

            if a > b:
                return 1

            if a < b:
                return -1

            raise ValueError(f"{a},{b}")

        def descending(a, b):
            return -ascending(a, b)

        class Compare:
            def __init__(self, order):
                self.order = order

            def __call__(self, a, b):
                return ascending(self.get(a), self.get(b))

            def get(self, x):
                return self.order[x]

        for k, v in kwargs.items():
            if v == "ascending" or v is None:
                actions[k] = ascending
                continue

            if v == "descending":
                actions[k] = descending
                continue

            if callable(v):
                actions[k] = v
                continue

            assert isinstance(v, (list, tuple)), f"Invalid argument for {k}: {v} ({type(v)})"

            order = {}
            for i, key in enumerate(v):
                order[str(key)] = i
                try:
                    order[int(key)] = i
                except ValueError:
                    pass
                except TypeError:
                    print('Cannot convert "%s" to int (%s)' % (key, type(key)))
                    raise
                try:
                    order[float(key)] = i
                except ValueError:
                    pass
            actions[k] = Compare(order)

        return actions


class Index(Source, Encodable):
    @classmethod
    def _new_mask_index(self, *args, **kwargs):
        return MaskIndex(*args, **kwargs)

    @abstractmethod
    def __len__(self):
        pass

    def __getitem__(self, n):
        if isinstance(n, slice):
            return self._from_slice(n)
        if isinstance(n, (tuple, list)):
            return self._from_sequence(n)
        if isinstance(n, dict):
            return self._from_dict(n)
        else:
            import numpy as np

            if isinstance(n, np.ndarray):
                return self._from_ndarray(n)

        return self._getitem(n)

    def _from_slice(self, s):
        indices = range(len(self))[s]
        return self.new_mask_index(self, indices)

    def _from_mask(self, lst):
        indices = [i for i, x in enumerate(lst) if x]
        return self.new_mask_index(self, indices)

    def _from_sequence(self, s):
        return self.new_mask_index(self, s)

    def _from_ndarray(self, a):
        return self._from_sequence(a.tolist())

    @abstractmethod
    def _getitem(self, n):
        pass

    @abstractmethod
    def _normalise_key_values(self, **kwargs):
        pass

    def sel(self, *args, remapping=None, **kwargs):
        """Uses metadata values to select a subset of the elements from a fieldlist object.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the filter condition as dict.
            (See below for details).
        remapping: dict
            Creates new metadata keys from existing ones that we can refer to in ``*args`` and
            ``**kwargs``. E.g. to define a new
            key "param_level" as the concatenated value of the "param" and "level" keys use::

                remapping={"param_level": "{param}{level}"}

            See below for a more elaborate example.

        **kwargs: dict, optional
            Other keyword arguments specifying the filter conditions.
            (See below for details).

        Returns
        -------
        object
            Returns a new object with the filtered elements. It contains a view to the data in the
            original object, so no data is copied.

        Notes
        -----
        Filter conditions are specified by a set of **metadata** keys either by a dictionary (in
        ``*args``) or a set of ``**kwargs``. Both single or multiple keys are allowed to use and each
        can specify the following type of filter values:

        - single value::

            ds.sel({"parameter.variable": "t"})

        - list of values::

            ds.sel({"parameter.variable": ["u", "v"]})

        - **slice** of values (defines a **closed interval**, so treated as inclusive of both the start
        and stop values, unlike normal Python indexing)::

            # filter levels between 300 and 500 inclusively
            ds.sel({"vertical.level": slice(300, 500)})

        Examples
        --------
        >>> import earthkit.data
        >>> fl = earthkit.data.from_source("sample", "tuv_pl.grib").to_fieldlist()
        >>> len(fl)
        18

        Selecting by a single key ("parameter.variable") with a single value:

        >>> fl1 = fl.sel({"parameter.variable": "t"})
        >>> for f in fl1:
        ...     print(f)
        ...
        Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
        Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 850, pressure, 0, regular_ll)
        Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 700, pressure, 0, regular_ll)
        Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 500, pressure, 0, regular_ll)
        Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 400, pressure, 0, regular_ll)
        Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 300, pressure, 0, regular_ll)

        Selecting by multiple keys ("parameter.variable", "vertical.level") with a list and slice of values:

        >>> fl1 = fl.sel({"parameter.variable": ["u", "v"], "vertical.level": slice(400, 700)})
        >>> for f in fl1:
        ...     print(f)
        ...
        Field(u, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 700, pressure, 0, regular_ll)
        Field(v, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 700, pressure, 0, regular_ll)
        Field(u, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 500, pressure, 0, regular_ll)
        Field(v, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 500, pressure, 0, regular_ll)
        Field(u, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 400, pressure, 0, regular_ll)
        Field(v, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 400, pressure, 0, regular_ll)

        Using ``remapping`` to specify the selection by a key created from two other keys
        (we created key "param_level" from "parameter.variable" and "vertical.level"):

        >>> fl1 = fl.sel(
        ...    {"param_level": ["t850", "u1000"],
        ...    "remapping": {"param_level": "{parameter.variable}{vertical.level}"}})
        ... )
        >>> for f in fl1:
        ...     print(f)
        ...
        Field(u, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
        Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 850, pressure, 0, regular_ll)
        """
        kwargs, remapping_kwarg = normalise_selection(*args, **kwargs)
        if not kwargs:
            return self

        if remapping_kwarg and remapping:
            raise ValueError("Cannot specify remapping both as a positional argument and a keyword argument")

        if remapping_kwarg:
            remapping = remapping_kwarg

        kwargs = self._normalise_key_values(**kwargs)

        selection = Selection(kwargs, remapping=remapping)
        if selection.is_empty:
            return self

        indices = (i for i, element in enumerate(self) if selection.match_element(element))

        return self.new_mask_index(self, indices)

    def order_by(self, *args, remapping=None, patch=None, **kwargs):
        """Change the order of the elements in a fieldlist object.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the metadata keys to perform the ordering on.
            (See below for details)
        remapping: dict
            Defines new metadata keys from existing ones that we can refer to in ``*args`` and
            ``**kwargs``. E.g. to define a new
            key "param_level" as the concatenated value of the "param" and "level" keys use::

                remapping={"param_level": "{param}{level}"}

            See below for a more elaborate example.

        **kwargs: dict, optional
            Other keyword arguments specifying the metadata keys to perform the ordering on.
            (See below for details)

        Returns
        -------
        object
            Returns a new object with reordered elements. It contains a view to the data in the
            original object, so no data is copied.

        Examples
        --------
        Ordering by a single metadata key ("param"). The default ordering direction
        is ``ascending``:

        >>> import earthkit.data as ekd
        >>> ds = ekd.from_source("sample", "test6.grib").to_fieldlist()
        >>> for f in ds.order_by("parameter.variable"):
        ...     print(f)
        ...
        Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
        Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 850, pressure, 0, regular_ll)
        Field(u, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
        Field(u, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 850, pressure, 0, regular_ll)
        Field(v, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
        Field(v, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 850, pressure, 0, regular_ll)

        Ordering by multiple keys (first by "vertical.level" then by "parameter.variable"):

        >>> for f in ds.order_by(["vertical.level", "parameter.variable"]):
        ...     print(f)
        ...
        Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 850, pressure, 0, regular_ll)
        Field(u, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 850, pressure, 0, regular_ll)
        Field(v, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 850, pressure, 0, regular_ll)
        Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
        Field(u, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
        Field(v, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)

        Specifying the ordering direction:

        >>> for f in ds.order_by(**{"parameter.variable": "ascending", "vertical.level": "descending"}):
        ...     print(f)
        ...
        Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
        Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 850, pressure, 0, regular_ll)
        Field(u, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
        Field(u, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 850, pressure, 0, regular_ll)
        Field(v, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
        Field(v, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 850, pressure, 0, regular_ll)

        Using the list of all the values of a key ("parameter.variable") to define the order:

        >>> for f in ds.order_by(**{"parameter.variable": ["u", "t", "v"]}):
        ...     print(f)
        ...
        Field(u, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
        Field(u, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 850, pressure, 0, regular_ll)
        Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
        Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 850, pressure, 0, regular_ll)
        Field(v, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
        Field(v, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 850, pressure, 0, regular_ll)

        Using ``remapping`` to specify the order by a key created from two other keys
        (we created key "param_level" from "param" and "levelist"):

        >>> ordering = ["t850", "t1000", "u1000", "v850", "v1000", "u850"]
        >>> remapping = {"param_level": "{parameter.variable}{vertical.level}"}
        >>> for f in ds.order_by(param_level=ordering, remapping=remapping):
        ...     print(f)
        ...
        Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 850, pressure, 0, regular_ll)
        Field(t, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
        Field(u, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
        Field(v, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 850, pressure, 0, regular_ll)
        Field(v, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 1000, pressure, 0, regular_ll)
        Field(u, 2018-08-01 12:00:00, 2018-08-01 12:00:00, 0:00:00, 850, pressure, 0, regular_ll)
        """
        kwargs = normalise_order_by(*args, **kwargs)

        remapping = build_remapping(remapping, patch)

        if not kwargs:
            return self

        order = Order(kwargs, remapping=remapping)
        # order = Order(*args, **kwargs)
        if order.is_empty:
            return self

        def cmp(i, j):
            return order.compare_elements(self[i], self[j])

        indices = list(range(len(self)))
        indices = sorted(indices, key=functools.cmp_to_key(cmp))
        return self.new_mask_index(self, indices)

    @thread_safe_cached_property
    def _cached_unique_collector(self):
        return UniqueValuesCollector(cache=True)

    def unique(
        self,
        *args,
        sort=False,
        drop_none=True,
        squeeze=False,
        unwrap_single=False,
        remapping=None,
        patch=None,
        progress_bar=False,
        cache=True,
    ):
        """Given a list of metadata attributes, such as date, param, levels,
        returns the list of unique values for each attributes.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the metadata keys to collect unique values for.
        sort: bool, optional
            Whether to sort the collected unique values. Default is False.
        drop_none: bool, optional
            Whether to drop None values from the collected unique values. Default is True.
        squeeze: bool, optional
            Whether to return a single value instead of a list if there is only one unique
            value for a key. Default is False.
        remapping: dict, optional
            A dictionary for remapping keys or values during collection. Default is None.
        patch: dict, optional
            A dictionary for patching key values during collection. Default is None.
        progress_bar: bool, optional
            Whether to display a progress bar during collection. Default is False.
        cache: bool, optional
            Whether to use a cached collector. Default is False.
        """
        keys = []
        for arg in args:
            if isinstance(arg, str):
                keys.append(arg)
            elif isinstance(arg, (list, tuple)):
                keys.extend(arg)
            else:
                raise ValueError(f"Invalid argument: {arg} ({type(arg)})")

        if cache:
            collector = self._cached_unique_collector
        else:
            collector = UniqueValuesCollector()

        return collector.collect(
            self,
            keys=keys,
            sort=sort,
            drop_none=drop_none,
            squeeze=squeeze,
            unwrap_single=unwrap_single,
            remapping=remapping,
            patch=patch,
            progress_bar=progress_bar,
        )

    @classmethod
    def merge(cls, sources):
        assert all(isinstance(_, Index) for _ in sources)
        return MultiIndex(sources)

    def to_numpy(self, *args, **kwargs):
        import numpy as np

        return np.array([f.to_numpy(*args, **kwargs) for f in self])

    def batched(self, n):
        """Iterate through the object in batches of ``n``.

        Parameters
        ----------
        n: int
            Batch size.

        Returns
        -------
        object
            Returns an iterator yielding batches of ``n`` elements. Each batch is a new object
            containing a view to the data in the original object, so no data is copied. The last
            batch may contain fewer than ``n`` elements.

        """
        from earthkit.data.utils.batch import batched

        return batched(self, n, mode="indexed")

    def group_by(self, *keys, sort=True):
        """Iterate through the object in groups defined by metadata keys.

        Parameters
        ----------
        *keys: tuple
            Positional arguments specifying the metadata keys to group by.
            Keys can be a single or multiple str, or a list or tuple of str.

        sort: bool, optional
            If ``True`` (default), the object is sorted by the metadata ``keys`` before grouping.
            Sorting is only applied if the object is supporting the sorting operation.

        Returns
        -------
        object
            Returns an iterator yielding batches of elements grouped by the metadata ``keys``. Each
            batch is a new object containing a view to the data in the original object, so no data
            is copied. It generates a new group every time the value of the ``keys`` change.

        """
        from earthkit.data.utils.batch import group_by

        return group_by(self, *keys, sort=sort, mode="indexed")


class MaskIndex(Index):
    def __init__(self, index, indices):
        self._index = index
        self._indices = list(indices)
        # super().__init__(
        #     *self.index._init_args,
        #     order_by=self.index._init_order_by,
        #     **self.index._init_kwargs,
        # )

    def _getitem(self, n):
        n = self._indices[n]
        return self._index[n]

    def __len__(self):
        return len(self._indices)

    def __repr__(self):
        return "MaskIndex(%r,%s)" % (self._index, self._indices)


class MultiIndex(Index):
    def __init__(self, indexes, *args, **kwargs):
        self._indexes = list(self._flatten(indexes))
        super().__init__(*args, **kwargs)
        # self.indexes = list(i for i in indexes if len(i))
        # TODO: propagate  index._init_args, index._init_order_by, index._init_kwargs, for each i in indexes?

    def _flatten(self, indexes):
        for i in indexes:
            if isinstance(i, MultiIndex):
                yield from self._flatten(i._indexes)
            else:
                yield i

    def sel(self, *args, **kwargs):
        if not args and not kwargs:
            return self
        return self.__class__(i.sel(*args, **kwargs) for i in self._indexes)

    def _getitem(self, n):
        k = 0
        while n >= len(self._indexes[k]):
            n -= len(self._indexes[k])
            k += 1
        return self._indexes[k][n]

    def __len__(self):
        return sum(len(i) for i in self._indexes)

    def graph(self, depth=0):
        print(" " * depth, self.__class__.__name__)
        for s in self._indexes:
            s.graph(depth + 3)

    def __repr__(self):
        return "%s(%s)" % (
            self.__class__.__name__,
            ",".join(repr(i) for i in self._indexes),
        )
