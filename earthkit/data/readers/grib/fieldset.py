# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import json
import logging
from collections import defaultdict

from earthkit.data.core.caching import auxiliary_cache_file
from earthkit.data.core.index import ScaledIndex
from earthkit.data.utils.bbox import BoundingBox

from .pandas import PandasMixIn
from .xarray import XarrayMixIn

LOG = logging.getLogger(__name__)

GRIB_LS_KEYS = [
    "centre",
    "shortName",
    "typeOfLevel",
    "level",
    "dataDate",
    "dataTime",
    "stepRange",
    "dataType",
    "number",
    "gridType",
]


GRIB_DESCRIBE_KEYS = [
    "shortName",
    "typeOfLevel",
    "level",
    "date",
    "time",
    "step",
    "number",
    "paramId",
    "marsClass",
    "marsStream",
    "marsType",
    "experimentVersionNumber",
]


class FieldSetMixin(PandasMixIn, XarrayMixIn):
    _statistics = None
    _indices = {}

    def _find_index_values(self, key):
        values = set()
        for i in self:
            v = i.metadata(key, default=None)
            if v is not None:
                values.add(v)
        return sorted(list(values))

    def _find_all_index_dict(self):
        from earthkit.data.indexing.database import GRIB_KEYS_NAMES

        indices = defaultdict(set)
        for f in self:
            for k in GRIB_KEYS_NAMES:
                v = f.metadata(k, default=None)
                if v is None:
                    continue
                indices[k].add(v)

        return {k: sorted(list(v)) for k, v in indices.items()}

    def indices(self, squeeze=False):
        r"""Returns the unique, sorted values for a set of metadata keys across all the
        fields. By default it uses a set of keys from the mars ecCodes namespace, but keys
        with no valid values are not included. Keys that :obj:`index` is called with are automatically
        added to original set of keys used in :obj:`indices`.

        Parameters
        ----------
        squeeze : False
            When it is True only returns the metadata keys that have more than one values.

        Returns
        -------
        dict
            Unique, sorted metadata values across all the fields.

        """
        if not self._indices:
            self._indices = self._find_all_index_dict()
        if squeeze:
            return {k: v for k, v in self._indices.items() if len(v) > 1}
        else:
            return self._indices

    def index(self, key):
        r"""Returns the unique, sorted values of the specified metadata ``key` across all the fields.
        ``key`` will be automatically added to the keys returned by :obj:`indices`.

        Parameters
        ----------
        key : str
            Metadata key.

        Returns
        -------
        list
            Unique, sorted values of ``key`` across all the fields.

        """
        if key in self.indices():
            return self.indices()[key]

        self._indices[key] = self._find_index_values(key)
        return self._indices[key]

    def to_numpy(self, **kwargs):
        import numpy as np

        return np.array([f.to_numpy(**kwargs) for f in self])

    @property
    def values(self):
        import numpy as np

        return np.array([f.values for f in self])

    def metadata(self, *args, **kwargs):
        result = []
        for s in self:
            result.append(s.metadata(*args, **kwargs))
        return result

    def ls(self, *args, **kwargs):
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

        ns = kwargs.pop("namespace", None)
        keys = GRIB_LS_KEYS if ns is None else dict(namespace=ns)
        return ls(_proc, keys, *args, **kwargs)

    def head(self, n=5, **kwargs):
        if n <= 0:
            raise ValueError("head: n must be > 0")
        return self.ls(n=n, **kwargs)

    def tail(self, n=5, **kwargs):
        if n <= 0:
            raise ValueError("n must be > 0")
        return self.ls(n=-n, **kwargs)

    def describe(self, *args, **kwargs):
        from earthkit.data.utils.summary import format_describe

        def _proc():
            for f in self:
                yield (f._attributes(GRIB_DESCRIBE_KEYS))

        return format_describe(_proc(), *args, **kwargs)

    def datetime(self, **kwargs):
        base = set()
        valid = set()
        for s in self:
            d = s.datetime()
            base.add(d["base_time"])
            valid.add(d["valid_time"])
        return {"base_time": sorted(base), "valid_time": sorted(valid)}

    def bounding_box(self):
        return BoundingBox.multi_merge([s.bounding_box() for s in self])

    def statistics(self):
        import numpy as np

        if self._statistics is not None:
            return self._statistics

        if False:
            cache = auxiliary_cache_file(
                "grib-statistics--",
                self.path,
                content="null",
                extension=".json",
            )

            with open(cache) as f:
                self._statistics = json.load(f)

            if self._statistics is not None:
                return self._statistics

        stdev = None
        average = None
        maximum = None
        minimum = None
        count = 0

        for s in self:
            v = s.values
            if count:
                stdev = np.add(stdev, np.multiply(v, v))
                average = np.add(average, v)
                maximum = np.maximum(maximum, v)
                minimum = np.minimum(minimum, v)
            else:
                stdev = np.multiply(v, v)
                average = v
                maximum = v
                minimum = v

            count += 1

        nans = np.count_nonzero(np.isnan(average))
        assert nans == 0, "Statistics with missing values not yet implemented"

        maximum = np.amax(maximum)
        minimum = np.amin(minimum)
        average = np.mean(average) / count
        stdev = np.sqrt(np.mean(stdev) / count - average * average)

        self._statistics = dict(
            minimum=minimum,
            maximum=maximum,
            average=average,
            stdev=stdev,
            count=count,
        )

        if False:
            with open(cache, "w") as f:
                json.dump(self._statistics, f)

        return self._statistics

    def save(self, filename):
        with open(filename, "wb") as f:
            self.write(f)

    def write(self, f):
        for s in self:
            s.write(f)

    def scaled(self, method=None, offset=None, scaling=None):
        if method == "minmax":
            assert offset is None and scaling is None
            stats = self.statistics()
            offset = stats["minimum"]
            scaling = 1.0 / (stats["maximum"] - stats["minimum"])

        return ScaledIndex(self, offset, scaling)
