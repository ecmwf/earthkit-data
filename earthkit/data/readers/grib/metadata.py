# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime

from earthkit.data.core.metadata import Metadata
from earthkit.data.indexing.database import GRIB_KEYS_NAMES
from earthkit.data.utils.bbox import BoundingBox
from earthkit.data.utils.projections import Projection


def missing_is_none(x):
    return None if x == 2147483647 else x


class GribMetadata(Metadata):
    LS_KEYS = [
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

    DESCRIBE_KEYS = [
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

    INDEX_KEYS = list(GRIB_KEYS_NAMES)

    NAMESPACES = {
        k: k
        for k in (
            "default",
            "ls",
            "geography",
            "mars",
            "parameter",
            "statistics",
            "time",
            "vertical",
        )
    }
    NAMESPACES["default"] = None

    __handle_type = None

    def __init__(self, handle):
        if not isinstance(handle, self._handle_type()):
            raise TypeError(
                f"GribMetadata: expected handle type {self._handle_type()}, got {type(handle)}"
            )
        self._handle = handle

    @staticmethod
    def _handle_type():
        """Returns the expected handle type. Implemented like this
        to avoid cyclic import
        """
        if GribMetadata.__handle_type is None:
            from earthkit.data.readers.grib.codes import GribCodesHandle

            GribMetadata.__handle_type = GribCodesHandle
        return GribMetadata.__handle_type

    def keys(self):
        self._handle.keys()

    def items(self):
        return self._handle.items()

    def __getitem__(self, key):
        return self.get(key)

    def __contains__(self, key):
        return self._handle.__contains(key)

    def get(self, key, *args):
        if len(args) == 1:
            return self._handle.get(key, default=args[0])
        elif len(args) == 0:
            return self._handle.get(key)
        else:
            raise TypeError(f"get: expected at most 2 arguments, got {1+len(args)}")

    def _get(self, key, astype=None, **kwargs):
        def _key_name(key):
            if key == "param":
                key = "shortName"
            elif key == "_param_id":
                key = "paramId"
            return key

        return self._handle.get(_key_name(key), ktype=astype, **kwargs)

    def override(self, *args, **kwargs):
        d = dict(*args, **kwargs)
        handle = self._handle.clone()
        handle.set_multiple(d)
        return GribMetadata(handle)

    def as_namespace(self, ns):
        return self._handle.as_namespace(ns)

    def ls_keys(self):
        return self.LS_KEYS

    def describe_keys(self):
        return self.DESCRIBE_KEYS

    def index_keys(self):
        return self.INDEX_KEYS

    def namespaces(self):
        return self.NAMESPACES

    def latitudes(self):
        return self._handle.get_latitudes()

    def longitudes(self):
        return self._handle.get_longitudes()

    def x(self):
        grid_type = self.get("gridType", None)
        if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
            return self.longitudes()

    def y(self):
        grid_type = self.get("gridType", None)
        if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
            return self.latitudes()

    def shape(self):
        Nj = missing_is_none(self.get("Nj", None))
        Ni = missing_is_none(self.get("Ni", None))
        if Ni is None or Nj is None:
            n = self.get("numberOfDataPoints", None)
            return (n,)  # shape must be a tuple
        return (Nj, Ni)

    def _unique_grid_id(self):
        return self.get("md5GridSection", None)

    def datetime(self):
        r"""Returns the date and time of the GRIB message.

        Returns
        -------
        dict of datatime.datetime
            Dict with items "base_time" and "valid_time".


        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "tests/data/t_time_series.grib")
        >>> ds[4].datetime()
        {'base_time': datetime.datetime(2020, 12, 21, 12, 0),
        'valid_time': datetime.datetime(2020, 12, 21, 18, 0)}

        """
        return {
            "base_time": self._base_datetime(),
            "valid_time": self._valid_datetime(),
        }

    def _base_datetime(self):
        date = self.get("date", None)
        time = self.get("time", None)
        return datetime.datetime(
            date // 10000,
            date % 10000 // 100,
            date % 100,
            time // 100,
            time % 100,
        )

    def _valid_datetime(self):
        step = self.get("endStep", None)
        return self._base_datetime() + datetime.timedelta(hours=step)

    def projection(self):
        r"""Returns information about the projection.

        Returns
        -------
        :obj:`Projection`

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> ds.projection()
        <Projected CRS: +proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=0.0 +to ...>
        Name: unknown
        Axis Info [cartesian]:
        - E[east]: Easting (unknown)
        - N[north]: Northing (unknown)
        - h[up]: Ellipsoidal height (metre)
        Area of Use:
        - undefined
        Coordinate Operation:
        - name: unknown
        - method: Equidistant Cylindrical
        Datum: Unknown based on WGS 84 ellipsoid
        - Ellipsoid: WGS 84
        - Prime Meridian: Greenwich
        >>> ds.projection().to_proj_string()
        '+proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=0.0 +to_meter=111319.4907932736 +no_defs +type=crs'
        """
        return Projection.from_proj_string(self.get("projTargetString", None))

    def bounding_box(self):
        r"""Returns the bounding box of the field.

        Returns
        -------
        :obj:`BoundingBox <data.utils.bbox.BoundingBox>`
        """
        return BoundingBox(
            north=self.get("latitudeOfFirstGridPointInDegrees", None),
            south=self.get("latitudeOfLastGridPointInDegrees", None),
            west=self.get("longitudeOfFirstGridPointInDegrees", None),
            east=self.get("longitudeOfLastGridPointInDegrees", None),
        )

    def dump(self, namespace=None, **kwargs):
        r"""Generates dump with all the metadata keys belonging to ``namespace``
        offering a tabbed interface in a Jupyter notebook.

        Parameters
        ----------
        namespace: :obj:`str`, :obj:`list` or :obj:`tuple`
            The namespace to dump. Any :xref:`eccodes_namespace` can be used here.
            :obj:`dump` also defines the "default" namespace, which contains all the GRIB keys
            that ecCodes can access without specifying a namespace.
            When ``namespace`` is None all the available namespaces will be used.
        **kwargs: dict, optional
            Other keyword arguments used for testing only

        Returns
        -------
        NamespaceDump
            Dict-like object with one item per namespace. In a Jupyter notebook represented
            as a tabbed interface to browse the dump contents.

        Examples
        --------
        :ref:`/examples/grib_metadata.ipynb`

        """
        from earthkit.data.utils.summary import format_namespace_dump

        namespace = self.NAMESPACES.keys() if namespace is None else [namespace]
        r = [
            {
                "title": ns,
                "data": self.as_namespace(self.NAMESPACES.get(ns)),
                "tooltip": f"Keys in the ecCodes {ns} namespace",
            }
            for ns in namespace
        ]

        return format_namespace_dump(
            r, selected="parameter", details=self.__class__.__name__, **kwargs
        )
