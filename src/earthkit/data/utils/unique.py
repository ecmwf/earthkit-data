# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
from collections import defaultdict


def build_remapping(remapping, patch):
    if remapping is not None or patch is not None:
        from earthkit.data.core.order import build_remapping

        remapping = build_remapping(remapping, patch)
    return None


class UniqueValuesCache:
    def __init__(self, index=None):
        # print(f"IndexDB: {index=}")
        self._index = index if index is not None else dict()

    def index(self, key, maker=None):
        # LOG.debug(f"index(): {key=} {self._index=}")
        if key not in self._index:
            # # LOG.debug(f"Key={key} not found in IndexDB")
            if maker is not None:
                self._index[key] = maker(key)[0][key]
            else:
                raise KeyError(f"Could not find index for {key=}")
        return self._index[key]

    def collect(self, keys):
        remaining_keys = list(keys)
        indices = dict()
        for k in keys:
            if k in self._index:
                indices[k] = self._index[k]
                remaining_keys.remove(k)
        return remaining_keys, indices

    # def filter(self, *args, **kwargs):
    #     kwargs = normalise_selection(*args, **kwargs)

    #     index = dict()

    #     for k in self._index:
    #         if k in kwargs:
    #             selection = IndexSelection(dict(k=kwargs[k]))
    #             idx = list(i for i, element in enumerate(self._index[k]) if selection.match_element(element))
    #             index[k] = [self._index[k][i] for i in idx]
    #         else:
    #             index[k] = self._index[k]
    #     return UniquesDB(index)

    def __repr__(self) -> str:
        return f"IndexDB(_index={self._index})"


class UniqueValuesCollector:
    r"""Collector for unique values for a given set of metadata keys

    Parameters
    ----------
    cache: bool, optional
        Whether to use a cache for previously collected unique values. Default is False.

    """

    def __init__(self, cache=False):
        if cache:
            self._cache = UniqueValuesCache()
        else:
            self._cache = None

    def collect(
        self,
        data,
        keys,
        sort=False,
        drop_none=True,
        squeeze=False,
        unwrap_single=False,
        remapping=None,
        patch=None,
        progress_bar=False,
    ):
        r"""Collect unique values for the given keys from data.

        Parameters
        ----------
        data: iterable
            The data to collect unique values from. It must be an iterable of objects supporting metadata
            access either via the standard ``get()`` method, or via the ``_get_fast()`` method for
            efficient retrieval of multiple keys at once.
        keys: str or list/ tuple of str
            The metadata keys for which to collect unique values. This can be a single string key or
            a list/tuple of string keys.
        sort: bool, optional
            Whether to sort the collected unique values. Default is False.
        drop_none: bool, optional
            Whether to drop None values from the collected unique values. Default is True.
        squeeze: bool, optional
            Whether to return a single value instead of a list if there is only one unique value for
        remapping: dict, optional
            A dictionary for remapping keys or values during collection. Default is None.
        patch: dict, optional
            A dictionary for patching key values during collection. Default is None.
        progress_bar: bool, optional
            Whether to display a progress bar during collection. Default is False.

        Returns
        -------
        dict of tuple
            A dictionary where each key is one of the input keys and the corresponding value is a tuple of
            unique values collected for that key from the data.
        """

        iterable = data

        if progress_bar:
            from earthkit.data.utils.progbar import progress_bar

            iterable = progress_bar(
                iterable=iterable,
                desc=f"Finding values for {keys=}",
            )

        if remapping or patch:
            remapping = build_remapping(remapping, patch)

        if isinstance(keys, str):
            keys = tuple([keys])

        if isinstance(keys, list):
            keys = tuple(keys)

        if self._cache is not None:
            result = self._collect_with_cache(
                iterable,
                keys,
                self._cache,
                sort=sort,
                drop_none=drop_none,
                squeeze=squeeze,
                remapping=remapping,
            )
        else:
            result = self._collect(
                iterable,
                keys,
                sort=sort,
                drop_none=drop_none,
                squeeze=squeeze,
                remapping=remapping,
            )

        if len(keys) == 1 and unwrap_single:
            return result.popitem()[1]
        else:
            return result

    def _post_proc(self, vals, sort=True, drop_none=True, squeeze=False):
        if drop_none:
            for k, v in vals.items():
                vals[k] = tuple([x for x in v if x is not None])

        if squeeze:
            for k in list(vals.keys()):
                if len(vals[k]) <= 1:
                    vals.pop(k)
        if sort:
            for k, v in vals.items():
                if all(isinstance(x, (int, datetime.timedelta)) for x in v):
                    vals[k] = tuple(sorted(v))
                else:
                    vals[k] = tuple(sorted(v, key=str))
        return None

    def _collect(self, iterable, keys, remapping=None, sort=False, drop_none=True, squeeze=False):
        assert isinstance(keys, tuple), keys

        astype = [None] * len(keys)
        default = [None] * len(keys)
        vals = defaultdict(dict)
        for f in iterable:
            r = f._get_fast(keys, default=default, astype=astype, remapping=remapping, output=list)
            for k, v in zip(keys, r):
                vals[k][v] = True

        vals = {k: tuple(values.keys()) for k, values in vals.items()}
        self._post_proc(vals, sort=sort, drop_none=drop_none, squeeze=squeeze)
        return vals

    def _collect_with_cache(
        self, iterable, keys, cache, remapping=None, sort=False, drop_none=True, squeeze=False
    ):
        assert isinstance(keys, tuple), keys

        ori_keys = keys

        keys, indices = cache.collect(keys)
        vals = dict()

        if keys:
            astype = [None] * len(keys)
            default = [None] * len(keys)
            vals = defaultdict(dict)
            for f in iterable:
                r = f._get_fast(keys, default=default, astype=astype, remapping=remapping, output=list)
                for k, v in zip(keys, r):
                    vals[k][v] = True

            vals = {k: tuple(values.keys()) for k, values in vals.items()}

        res = dict()
        for k in ori_keys:
            if k in indices:
                res[k] = indices[k]
            else:
                res[k] = vals.get(k, ())
                indices[k] = res[k]

        self._post_proc(res, sort=sort, drop_none=drop_none, squeeze=squeeze)
        return res
