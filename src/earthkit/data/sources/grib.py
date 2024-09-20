# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#
#

import glob

from earthkit.data import from_source
from earthkit.data.indexing.fieldlist import FieldArray
from earthkit.data.utils.patterns import Pattern


def _load(context, name, record):
    ds = None

    param = record["param"]

    if "path" in record:
        context.info(f"Using {name} from {record['path']} (param={param})")
        ds = from_source("file", record["path"])

    if "url" in record:
        context.info(f"Using {name} from {record['url']} (param={param})")
        ds = from_source("url", record["url"])

    ds = ds.sel(param=param)

    assert len(ds) == 1, f"{name} {param}, expected one field, got {len(ds)}"
    ds = ds[0]

    return ds.to_numpy(flatten=True), ds.metadata("uuidOfHGrid")


class Geography:
    """This class retrieve the latitudes and longitudes of unstructured grids,
    and checks if the fields are compatible with the grid.
    """

    def __init__(self, context, latitudes, longitudes):

        latitudes, uuidOfHGrid_lat = _load(context, "latitudes", latitudes)
        longitudes, uuidOfHGrid_lon = _load(context, "longitudes", longitudes)

        assert (
            uuidOfHGrid_lat == uuidOfHGrid_lon
        ), f"uuidOfHGrid mismatch: lat={uuidOfHGrid_lat} != lon={uuidOfHGrid_lon}"

        context.info(f"Latitudes: {len(latitudes)}, Longitudes: {len(longitudes)}")
        assert len(latitudes) == len(longitudes)

        self.uuidOfHGrid = uuidOfHGrid_lat
        self.latitudes = latitudes
        self.longitudes = longitudes
        self.first = True

    def check(self, field):
        if self.first:
            # We only check the first field, for performance reasons
            assert (
                field.metadata("uuidOfHGrid") == self.uuidOfHGrid
            ), f"uuidOfHGrid mismatch: {field.metadata('uuidOfHGrid')} != {self.uuidOfHGrid}"
            self.first = False


class AddGrid:
    """An earth-kit.data.Field wrapper that adds grid information."""

    def __init__(self, field, geography):
        self._field = field

        geography.check(field)

        self._latitudes = geography.latitudes
        self._longitudes = geography.longitudes

    def __getattr__(self, name):
        return getattr(self._field, name)

    def __repr__(self) -> str:
        return repr(self._field)

    def grid_points(self):
        return self._latitudes, self._longitudes

    @property
    def resolution(self):
        return "unknown"


def check(ds, paths, **kwargs):
    count = 1
    for k, v in kwargs.items():
        if isinstance(v, (tuple, list)):
            count *= len(v)

    if len(ds) != count:
        raise ValueError(f"Expected {count} fields, got {len(ds)} (kwargs={kwargs}, paths={paths})")


def _expand(paths):
    for path in paths:
        cnt = 0
        for p in glob.glob(path):
            yield p
            cnt += 1
        if cnt == 0:
            yield path


class GRIBSource:
    def init(self, context, dates, path, latitudes=None, longitudes=None, *args, **kwargs):
        self.context = context
        self.dates = []
        self.path = None
        self.latitudes = None
        self.longitudes = None
        self.args = args
        self.kwargs = {}

    def mutate(self):
        return self.execute(
            self.context, self.dates, self.path, self.latitudes, self.longitudes, *self.args, **self.kwargs
        )

    @staticmethod
    def execute(context, dates, path, latitudes=None, longitudes=None, *args, **kwargs):
        given_paths = path if isinstance(path, list) else [path]

        geography = None
        if latitudes is not None and longitudes is not None:
            geography = Geography(context, latitudes, longitudes)

        ds = from_source("empty")
        dates = [d.isoformat() for d in dates]

        for path in given_paths:
            paths = Pattern(path, ignore_missing_keys=True).substitute(*args, date=dates, **kwargs)

            for name in ("grid", "area", "rotation", "frame", "resol", "bitmap"):
                if name in kwargs:
                    raise ValueError(f"MARS interpolation parameter '{name}' not supported")

            for path in _expand(paths):
                context.trace("📁", "PATH", path)
                s = from_source("file", path)
                s = s.sel(valid_datetime=dates, **kwargs)
                ds = ds + s

        if kwargs:
            check(ds, given_paths, valid_datetime=dates, **kwargs)

        if geography is not None:
            ds = FieldArray([AddGrid(_, geography) for _ in ds])

        return ds


source = GRIBSource
