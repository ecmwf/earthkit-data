# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import warnings
from abc import abstractmethod
from functools import cached_property

from earthkit.data.core.geography import Geography
from earthkit.data.core.metadata import Metadata
from earthkit.data.decorators import cached_method
from earthkit.data.indexing.database import GRIB_KEYS_NAMES
from earthkit.data.readers.grib.gridspec import make_gridspec
from earthkit.data.utils.bbox import BoundingBox


def missing_is_none(x):
    return None if x == 2147483647 else x


class GribFieldGeography(Geography):
    def __init__(self, metadata):
        self.metadata = metadata
        self.check_rotated_support()

    def latitudes(self, dtype=None):
        r"""Return the latitudes of the field.

        Returns
        -------
        ndarray
        """
        return self.metadata._handle.get_latitudes(dtype=dtype)

    def longitudes(self, dtype=None):
        r"""Return the longitudes of the field.

        Returns
        -------
        ndarray
        """
        return self.metadata._handle.get_longitudes(dtype=dtype)

    def x(self, dtype=None):
        r"""Return the x coordinates in the field's original CRS.

        Returns
        -------
        ndarray
        """
        grid_type = self.metadata.get("gridType", None)
        if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
            return self.longitudes(dtype=dtype)

    def y(self, dtype=None):
        r"""Return the y coordinates in the field's original CRS.

        Returns
        -------
        ndarray
        """
        grid_type = self.metadata.get("gridType", None)
        if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
            return self.latitudes(dtype=dtype)

    def shape(self):
        r"""Get the shape of the field.

        For structured grids the shape is a tuple in the form of (Nj, Ni) where:

        - ni: the number of gridpoints in i direction (longitude for a regular latitude-longitude grid)
        - nj: the number of gridpoints in j direction (latitude for a regular latitude-longitude grid)

        For other grid types the number of gridpoints is returned as ``(num,)``

        Returns
        -------
        tuple
        """
        Nj = missing_is_none(self.metadata.get("Nj", None))
        Ni = missing_is_none(self.metadata.get("Ni", None))
        if Ni is None or Nj is None:
            n = self.metadata.get("numberOfDataPoints", None)
            return (n,)  # shape must be a tuple
        return (Nj, Ni)

    def _unique_grid_id(self):
        return self.metadata.get("md5GridSection", None)

    def projection(self):
        r"""Return information about the projection.

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
        from earthkit.data.utils.projections import Projection

        return Projection.from_proj_string(self.metadata.get("projTargetString", None))

    def bounding_box(self):
        r"""Return the bounding box of the field.

        Returns
        -------
        :obj:`BoundingBox <data.utils.bbox.BoundingBox>`
        """
        return BoundingBox(
            north=self.metadata.get("latitudeOfFirstGridPointInDegrees", None),
            south=self.metadata.get("latitudeOfLastGridPointInDegrees", None),
            west=self.metadata.get("longitudeOfFirstGridPointInDegrees", None),
            east=self.metadata.get("longitudeOfLastGridPointInDegrees", None),
        )

    def gridspec(self):
        return make_gridspec(self.metadata)

    def resolution(self):
        grid_type = self.metadata.get("gridType")

        if grid_type in ("reduced_gg", "reduced_rotated_gg"):
            return self.metadata.get("gridName")

        if grid_type in ("regular_ll", "rotated_ll"):
            x = self.metadata.get("DxInDegrees")
            y = self.metadata.get("DyInDegrees")
            x = round(x * 1_000_000) / 1_000_000
            y = round(y * 1_000_000) / 1_000_000
            assert x == y, (x, y)
            return x

        if grid_type == "lambert":
            x = self.metadata.get("DxInMetres")
            y = self.metadata.get("DyInMetres")
            assert x == y, (x, y)
            return str(x / 1000).replace(".", "p") + "km"

        raise ValueError(f"Unknown gridType={grid_type}")

    def mars_grid(self):
        if len(self.shape()) == 2:
            return [
                self.metadata.get("iDirectionIncrementInDegrees"),
                self.metadata.get("jDirectionIncrementInDegrees"),
            ]

        return self.metadata.get("gridName")

    def mars_area(self):
        north = self.metadata.get("latitudeOfFirstGridPointInDegrees")
        south = self.metadata.get("latitudeOfLastGridPointInDegrees")
        west = self.metadata.get("longitudeOfFirstGridPointInDegrees")
        east = self.metadata.get("longitudeOfLastGridPointInDegrees")
        return [north, west, south, east]

    @property
    def rotation(self):
        return (
            self.metadata.get("latitudeOfSouthernPoleInDegrees"),
            self.metadata.get("longitudeOfSouthernPoleInDegrees"),
            self.metadata.get("angleOfRotationInDegrees"),
        )

    @cached_property
    def rotated(self):
        grid_type = self.metadata.get("gridType")
        return "rotated" in grid_type

    @cached_property
    def rotated_iterator(self):
        return self.metadata.get("iteratorDisableUnrotate") is not None

    def check_rotated_support(self):
        if self.rotated and self.metadata.get("gridType") == "reduced_rotated_gg":
            from earthkit.data.utils.message import ECC_FEATURES

            if not ECC_FEATURES.version >= (2, 35, 0):
                raise RuntimeError("gridType=rotated_reduced_gg requires ecCodes >= 2.35.0")

    def latitudes_unrotated(self, **kwargs):
        if not self.rotated:
            return self.latitudes(**kwargs)

        if not self.rotated_iterator:
            from earthkit.geo.rotate import unrotate

            grid_type = self.metadata.get("gridType")
            warnings.warn(f"ecCodes does not support rotated iterator for {grid_type}")
            lat, lon = self.latitudes(**kwargs), self.longitudes(**kwargs)
            south_pole_lat, south_pole_lon, _ = self.rotation
            lat, lon = unrotate(lat, lon, south_pole_lat, south_pole_lon)
            return lat

        with self.metadata._handle._set_tmp("iteratorDisableUnrotate", 1, 0):
            return self.latitudes(**kwargs)

    def longitudes_unrotated(self, **kwargs):
        if not self.rotated:
            return self.longitudes(**kwargs)

        if not self.rotated_iterator:
            from earthkit.geo.rotate import unrotate

            grid_type = self.metadata.get("gridType")
            warnings.warn(f"ecCodes does not support rotated iterator for {grid_type}")
            lat, lon = self.latitudes(**kwargs), self.longitudes(**kwargs)
            south_pole_lat, south_pole_lon, _ = self.rotation
            lat, lon = unrotate(lat, lon, south_pole_lat, south_pole_lon)
            return lon

        with self.metadata._handle._set_tmp("iteratorDisableUnrotate", 1, 0):
            return self.longitudes(**kwargs)


class GribMetadata(Metadata):
    """GRIB metadata.

    :obj:`GribMetadata` is an abstract class and should not be instantiated directly.
    There are two concrete implementations: :class:`GribFieldMetadata` and
    :class:`StandAloneGribMetadata`.
    """

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

    NAMESPACES = [
        "default",
        "ls",
        "geography",
        "mars",
        "parameter",
        "statistics",
        "time",
        "vertical",
    ]

    DATA_FORMAT = "grib"

    __handle_type = None

    @abstractmethod
    def _handle(self):
        pass

    def __init__(self, shrunk=False, **kwargs):
        self._geo = None
        self._shrunk = shrunk
        super().__init__(**kwargs)

    @staticmethod
    def _handle_type():
        """Return the expected handle type. Implemented like this
        to avoid cyclic import
        """
        if GribMetadata.__handle_type is None:
            from earthkit.data.readers.grib.codes import GribCodesHandle

            GribMetadata.__handle_type = GribCodesHandle
        return GribMetadata.__handle_type

    def _len(self):
        return sum(map(lambda i: 1, self._keys()))

    def _contains(self, key):
        return self._handle.__contains__(key)

    def _keys(self):
        return self._handle.keys()

    def _items(self):
        return self._handle.items()

    def _get(self, key, astype=None, default=None, raise_on_missing=False):
        def _key_name(key):
            if key == "param":
                key = "shortName"
            elif key == "_param_id":
                key = "paramId"
            return key

        _kwargs = {}
        if not raise_on_missing:
            _kwargs["default"] = default

        key = _key_name(key)

        # special case when  "shortName" is "~".
        v = self._handle.get(key, ktype=astype, **_kwargs)
        if key == "shortName" and v == "~":
            v = self._handle.get("paramId", ktype=str, **_kwargs)
        return v

    def _is_custom_key(self, key):
        return key in self.CUSTOM_KEYS

    def override(self, *args, headers_only_clone=True, **kwargs):
        d = dict(*args, **kwargs)

        new_value_size = None
        extra = None
        gridspec = d.pop("gridspec", None)
        if gridspec is not None:
            from earthkit.data.readers.grib.gridspec import GridSpecConverter

            edition = d.get("edition", self["edition"])
            md, new_value_size = GridSpecConverter.to_metadata(gridspec, edition=edition)
            d.update(md)

        handle = self._handle.clone(headers_only=headers_only_clone)

        if self._shrunk:
            shrunk = True
            extra = self.extra
        elif headers_only_clone:
            # whether headers_only=True works depends on the eccCodes version and the
            # message properties. We check it by comparing the message lengths.
            shrunk = handle.get_long("totalLength") < self._handle.get_long("totalLength")

            # some keys, needed later, are not copied into the clone when
            # headers_only=True. We store them as extra keys.
            if shrunk:
                extra = {"bitsPerValue": self._handle.get("bitsPerValue", default=0)}
            else:
                extra = None
        else:
            shrunk = False

        if d:
            handle.set_multiple(d)

        # we need to set the values to the new size otherwise the clone generated
        # with headers_only=True will be inconsistent
        if new_value_size is not None and new_value_size > 0:
            import numpy as np

            vals = np.zeros(new_value_size)
            handle.set_values(vals)

        return StandAloneGribMetadata(handle, extra=extra, shrunk=shrunk)

    def as_namespace(self, namespace=None):
        r"""Return all the keys/values from a namespace.

        Parameters
        ----------
        namespace: str, None
            The :xref:`eccodes_namespace`. earthkit-data also defines the "default" namespace,
            which contains all the GRIB keys that ecCodes can access without specifying a namespace.
            When `namespace` is None or an empty :obj:`str` all the available
            keys/values are returned.

        Returns
        -------
        dict
            All the keys/values from the `namespace`.

        """
        if not isinstance(namespace, str) and namespace is not None:
            raise TypeError("namespace must be a str or None")

        if namespace == "default" or namespace == "":
            namespace = None
        return self._handle.as_namespace(namespace)

    @property
    def geography(self):
        if self._geo is None:
            self._geo = GribFieldGeography(self)
        return self._geo

    def _base_datetime(self):
        date = self.get("date", None)
        time = self.get("time", None)
        return self._build_datetime(date, time)

    def _valid_datetime(self):
        date = self.get("validityDate", None)
        time = self.get("validityTime", None)
        return self._build_datetime(date, time)

    def _build_datetime(self, date, time):
        return datetime.datetime(
            date // 10000,
            date % 10000 // 100,
            date % 100,
            time // 100,
            time % 100,
        )

    def dump(self, namespace=all, **kwargs):
        r"""Generate dump with all the metadata keys belonging to ``namespace``.

        In a Jupyter notebook it is represented as a tabbed interface.

        Parameters
        ----------
        namespace: :obj:`str`, :obj:`list`, :obj:`tuple`, :obj:`None` or :obj:`all`
            The namespace to dump. Any :xref:`eccodes_namespace` can be used here.
            earthkit-data also defines the "default" namespace, which contains all the GRIB keys
            that ecCodes can access without specifying a namespace. The following `namespace` values
            have a special meaning:

            - :obj:`all`: all the available namespaces will be used (including "default").
            - None or empty str: the "default" namespace will be used.

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

        namespace = self.NAMESPACES if namespace is all else [namespace]
        r = []
        for ns in namespace:
            v = self.as_namespace(ns)
            if v:
                r.append(
                    {
                        "title": ns if ns else "default",
                        "data": v,
                        "tooltip": f"Keys in the ecCodes {ns} namespace",
                    }
                )

        return format_namespace_dump(r, selected="parameter", details=self.__class__.__name__, **kwargs)


class GribFieldMetadata(GribMetadata):
    """Represent the metadata of a GRIB field.

    :obj:`GribFieldMetadata` is created internally by a :obj:`GribField`. It does not
    own the ecCodes GRIB handle but can access it through the :obj:`GribField`.
    Calling :meth:`metadata` without arguments on a :obj:`GribField` returns this object.
    """

    def __init__(self, field, **kwargs):
        self._field = field
        assert field is not None
        super().__init__(**kwargs)

    @property
    def _handle(self):
        return self._field.handle

    def _hide_internal_keys(self):
        r = self.override()
        return RestrictedGribMetadata(r)


class StandAloneGribMetadata(GribMetadata):
    """Represent standalone GRIB metadata owning an ecCodes GRIB handle.

    :class:`StandAloneGribMetadata` possesses its own ecCodes handle. Calling
    :meth:`override` on :obj:`GribMetadata` always returns a
    :class:`StandAloneGribMetadata` object.

    >>> ds = earthkit.data.from_source("file", "docs/examples/test4.grib")
    >>> md = ds[0].metadata()
    >>> md["shortName"]
    't'
    >>> md.get("shortName")
    't'
    >>> md.get("nonExistentKey")
    >>> md.get("nonExistentKey", 12)
    12

    Examples
    --------
    :ref:`/examples/grib_metadata_object.ipynb`

    """

    def __init__(self, handle, **kwargs):
        if not isinstance(handle, self._handle_type()):
            raise TypeError(f"GribMetadata: expected handle type {self._handle_type()}, got {type(handle)}")
        self.__handle = handle
        self._kwargs = dict(**kwargs)
        super().__init__(**kwargs)

    @property
    def _handle(self):
        return self.__handle

    def _hide_internal_keys(self):
        return RestrictedGribMetadata(self)


# TODO: this is a temporary solution
class RestrictedGribMetadata(StandAloneGribMetadata):
    """Hide internal keys and namespaces in GRIB metadata.

    Examples
    --------
    :ref:`/examples/grib_metadata_object.ipynb`
    """

    EKD_NAMESPACE = "grib"

    # ideally bitsPerValue should be here. However, it is treated as an
    # extra key and cannot be an internal key.
    INTERNAL_KEYS = [
        "minimum",
        "maximum",
        "average",
        "standardDeviation",
        "skewness",
        "kurtosis",
        "min",
        "max",
        "avg",
        "sd",
        "skew",
        "kurt",
        "const",
        "isConstant",
        "numberOfMissing",
        "numberOfCodedValues",
        "bitmapPresent",
        "offsetValuesBy",
        "packingError",
        "referenceValue",
        "referenceValueError",
        "unpackedError",
        "values",
    ]
    INTERNAL_NAMESPACES = ["statistics"]

    def __init__(self, md):
        assert isinstance(md, StandAloneGribMetadata)
        super().__init__(md._handle, shrunk=md._shrunk, extra=md.extra)

    @cached_method
    def _len(self):
        if self.INTERNAL_KEYS:
            # NOTE: argumentless super cannot be used in list comprehension
            m = super()._contains
            surplus = [1 for x in self.INTERNAL_KEYS if not m(x)]
            return super()._len() + len(surplus)
        else:
            return super()._len()

    def _is_internal(self, key):
        ns, _, name = key.partition(".")
        if name == "":
            name = key
            ns = ""

        if ns == self.EKD_NAMESPACE:
            return False
        else:
            return name in self.INTERNAL_KEYS

    def _contains(self, key):
        if self.INTERNAL_KEYS:
            return not self._is_internal(key) and super()._contains(key)
        else:
            return super()._contains(key)

    def _keys(self):
        if self.INTERNAL_KEYS:
            r = []
            for k in super()._keys():
                if k not in self.INTERNAL_KEYS:
                    r.append(k)
            return r
        else:
            return super()._keys()

    def _items(self):
        if self.INTERNAL_KEYS:
            r = {}
            for k, v in super()._items():
                if k not in self.INTERNAL_KEYS:
                    r[k] = v
            return r.items()
        else:
            return super()._items()

    def get(self, key, default=None, *, astype=None, raise_on_missing=False):
        ns, _, name = key.partition(".")
        if name == "":
            name = key
            ns = ""

        if ns == self.EKD_NAMESPACE:
            key = name
        else:
            if name in self.INTERNAL_KEYS:
                if raise_on_missing:
                    raise KeyError(key)
                else:
                    return default

        return super().get(key, default=default, astype=astype, raise_on_missing=raise_on_missing)

    def namespaces(self):
        if self.INTERNAL_NAMESPACES:
            return [x for x in super().namespaces() if x not in self.INTERNAL_NAMESPACES]
        else:
            return super().namespaces()

    def as_namespace(self, namespace):
        if namespace in self.INTERNAL_NAMESPACES:
            return {}

        r = super().as_namespace(namespace)
        for k in list(r.keys()):
            if k in self.INTERNAL_KEYS:
                del r[k]
        return r

    def _hide_internal_keys(self):
        return self
