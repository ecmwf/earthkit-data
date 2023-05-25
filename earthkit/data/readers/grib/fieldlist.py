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


class FieldListMixin(PandasMixIn, XarrayMixIn):
    r"""Represents a list of
    :obj:`GribField <data.readers.grib.codes.GribField>`\ s.
    """

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
        r"""Returns the unique, sorted values for a set of metadata keys (see below)
        from all the fields. Individual keys can be also queried by :obj:`index`.

        Parameters
        ----------
        squeeze : False
            When True only returns the metadata keys that have more than one values.

        Returns
        -------
        dict
            Unique, sorted metadata values from all the
            :obj:`GribField <data.readers.grib.codes.GribField>`\ s.

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/tuv_pl.grib")
        >>> ds.indices()
        {'class': ['od'], 'stream': ['oper'], 'levtype': ['pl'], 'type': ['an'],
        'expver': ['0001'], 'date': [20180801], 'time': [1200], 'domain': ['g'],
        'number': [0], 'levelist': [300, 400, 500, 700, 850, 1000],
        'param': ['t', 'u', 'v']}
        >>> ds.indices(squeeze=True)
        {'levelist': [300, 400, 500, 700, 850, 1000], 'param': ['t', 'u', 'v']}
        >>> ds.index("level")
        [300, 400, 500, 700, 850, 1000]

        By default :obj:`indices` uses the following metadata keys taken from the
        "mars" :xref:`eccodes_namespace`:

            .. code-block:: python

                [
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

        Keys with no valid values are not included. Keys that :obj:`index` is called with ar
        automatically added to the original set of keys used in :obj:`indices`.

        """
        if not self._indices:
            self._indices = self._find_all_index_dict()
        if squeeze:
            return {k: v for k, v in self._indices.items() if len(v) > 1}
        else:
            return self._indices

    def index(self, key):
        r"""Returns the unique, sorted values of the specified metadata ``key`` from all the fields.
        ``key`` will be automatically added to the keys returned by :obj:`indices`.

        Parameters
        ----------
        key : str
            Metadata key.

        Returns
        -------
        list
            Unique, sorted values of ``key`` from all the
            :obj:`GribField <data.readers.grib.codes.GribField>`\ s.

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/tuv_pl.grib")
        >>> ds.index("level")
        [300, 400, 500, 700, 850, 1000]

        """
        if key in self.indices():
            return self.indices()[key]

        self._indices[key] = self._find_index_values(key)
        return self._indices[key]

    def to_numpy(self, **kwargs):
        r"""Returns the field values as an ndarray. It is formed by calling
        :obj:`GribField.to_numpy() <data.readers.grib.codes.GribField.to_numpy>`
        per field.

        Parameters
        ----------
        **kwargs:
            Keyword arguments passed to
            :obj:`GribField.to_numpy() <data.readers.grib.codes.GribField.to_numpy>`

        Returns
        -------
        ndarray
            Array containing the field values.

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> for f in ds:
        ...     print(f.to_numpy().shape)
        ...
        (11, 19)
        (11, 19)
        >>> v = ds.to_numpy()
        >>> v.shape
        (2, 11, 19)
        >>> v[0][0, 0]
        262.7802734375

        """
        import numpy as np

        return np.array([f.to_numpy(**kwargs) for f in self])

    @property
    def values(self):
        r"""ndarray: Gets the field values as a 2D ndarray. It is formed as the array of
        :obj:`GribField.values <data.readers.grib.codes.GribField.values>` per field.

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
        import numpy as np

        return np.array([f.values for f in self])

    def metadata(self, *args, **kwargs):
        r"""Returns the metadata values for each field.

        Parameters
        ----------
        *args:
            Positional arguments defining the metadata keys. Passed to
            :obj:`GribField.metadata() <data.readers.grib.codes.GribField.metadata>`
        **kwargs:
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
        result = []
        for s in self:
            result.append(s.metadata(*args, **kwargs))
        return result

    def ls(self, n=None, keys=None, extra_keys=None, namespace=None, **kwargs):
        r"""Generates a list like summary of the specified
        :obj:`GribField <data.readers.grib.codes.GribField>`\ s using a set of metadata keys.

        Parameters
        ----------
        n: int, None
            The number of :obj:`GribField <data.readers.grib.codes.GribField>`\ s to be
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
            The :xref:`eccodes_namespace` to choose the ``keys`` from. When it is set ``keys`` and
            ``extra_keys`` are omitted.
        **kwargs:
            Other keyword arguments:

            print: bool, optional
                Enables printing the DataFrame to standard output when not in a Jupyter notebook.
                Default: False

        Returns
        -------
        Pandas DataFrame
            If not in a Jupyter notebook and ``print`` is True the DataFrame is printed to
            the standard output

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

        _keys = GRIB_LS_KEYS if namespace is None else dict(namespace=namespace)
        return ls(_proc, _keys, n=n, keys=keys, extra_keys=extra_keys, **kwargs)

    def head(self, n=5, **kwargs):
        r"""Generates a list like summary of the first ``n``
        :obj:`GribField <data.readers.grib.codes.GribField>`\ s using a set of metadata keys.
        Same as calling :obj:`ls` with ``n``.

        Parameters
        ----------
        n: int, None
            The number of messages (``n`` > 0) to be printed from the front.
        **kwargs:
            Other keyword arguments passed to :obj:`ls`.

        Returns
        -------
        Pandas DataFrame
            See  :obj:`ls`.


        The following calls are equivalent:

            .. code-block:: python

                ds.head()
                ds.head(5)
                ds.head(n=5)
                ds.ls(5)
                ds.ls(n=5)

        """
        if n <= 0:
            raise ValueError("head: n must be > 0")
        return self.ls(n=n, **kwargs)

    def tail(self, n=5, **kwargs):
        r"""Generates a list like summary of the last ``n``
        :obj:`GribField <data.readers.grib.codes.GribField>`\ s using a set of metadata keys.
        Same as calling :obj:`ls` with ``-n``.

        Parameters
        ----------
        n: int, None
            The number of messages (``n`` > 0)  to be printed from the back.
        **kwargs:
            Other keyword arguments passed to :obj:`ls`.

        Returns
        -------
        Pandas DataFrame
            See  :obj:`ls`.


        The following calls are equivalent:

            .. code-block:: python

                ds.tail()
                ds.tail(5)
                ds.tail(n=5)
                ds.ls(-5)
                ds.ls(n=-5)

        """
        if n <= 0:
            raise ValueError("n must be > 0")
        return self.ls(n=-n, **kwargs)

    def describe(self, *args, **kwargs):
        r"""Generates a summary of the fieldlist."""
        from earthkit.data.utils.summary import format_describe

        def _proc():
            for f in self:
                yield (f._attributes(GRIB_DESCRIBE_KEYS))

        return format_describe(_proc(), *args, **kwargs)

    def datetime(self):
        r"""Returns the unique, sorted list of dates and times in the fieldlist.

        Returns
        -------
        dict of datatime.datetime
            Dict with items "base_time" and "valid_time".


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
        for s in self:
            d = s.datetime()
            base.add(d["base_time"])
            valid.add(d["valid_time"])
        return {"base_time": sorted(base), "valid_time": sorted(valid)}

    def bounding_box(self):
        r"""Returns the bounding box for each field.

        Returns
        -------
        list
            List with one :obj:`BoundingBox` per
            :obj:`GribField <data.readers.grib.codes.GribField>`
        """
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
        r"""Writes all the fields into a file. The target file will be overwritten if
        already exists.

        Parameters
        ----------
        filename: str
            The target file path.
        """
        with open(filename, "wb") as f:
            self.write(f)

    def write(self, f):
        r"""Writes all the fields to a file object.

        Parameters
        ----------
        f: file object
            The target file object.
        """
        for s in self:
            s.write(f)

    def scaled(self, method=None, offset=None, scaling=None):
        if method == "minmax":
            assert offset is None and scaling is None
            stats = self.statistics()
            offset = stats["minimum"]
            scaling = 1.0 / (stats["maximum"] - stats["minimum"])

        return ScaledIndex(self, offset, scaling)
