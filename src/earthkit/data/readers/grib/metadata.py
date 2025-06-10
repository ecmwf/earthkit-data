# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import warnings
from abc import abstractmethod
from functools import cached_property

from earthkit.data.core.geography import Geography
from earthkit.data.core.metadata import Metadata
from earthkit.data.core.metadata import MetadataAccessor
from earthkit.data.core.metadata import MetadataCacheHandler
from earthkit.data.core.metadata import WrappedMetadata
from earthkit.data.indexing.database import GRIB_KEYS_NAMES
from earthkit.data.readers.grib.gridspec import make_gridspec
from earthkit.data.utils.bbox import BoundingBox
from earthkit.data.utils.dates import datetime_from_grib
from earthkit.data.utils.dates import to_timedelta

LOG = logging.getLogger(__name__)


def missing_is_none(x):
    return None if x == 2147483647 else x


class GribFieldGeography(Geography):
    def __init__(self, metadata):
        self.metadata = metadata
        self.check_rotated_support()

    @cached_property
    def spectral(self):
        return self.metadata._handle.get("gridType", "") == "sh"

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

    def distinct_latitudes(self, dtype=None):
        return self.metadata._handle.get("distinctLatitudes", dtype=dtype)

    def distinct_longitudes(self, dtype=None):
        return self.metadata._handle.get("distinctLongitudes", dtype=dtype)

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
            return x if x == y else None

        if grid_type in ["lambert", "lambert_azimuthal_equal_area"]:
            x = self.metadata.get("DxInMetres")
            y = self.metadata.get("DyInMetres")
            if x == y:
                return str(x / 1000).replace(".", "p") + "km"
            else:
                return None

        # raise ValueError(f"Unknown gridType={grid_type}")

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
            try:
                from earthkit.geo.rotate import unrotate
            except ImportError:
                raise ImportError(
                    "GribFieldGeography.latitudes_unrotated requires 'earthkit-geo' to be installed"
                )

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
            try:
                from earthkit.geo.rotate import unrotate
            except ImportError:
                raise ImportError(
                    "GribFieldGeography.longitudes_unrotated requires 'earthkit-geo' to be installed"
                )

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

    ACCESSORS = {
        "valid_datetime": ["valid_datetime", "valid_time"],
        "gridspec": ["grid_spec", "gridspec"],
        "base_datetime": ["base_datetime", "forecast_reference_time", "base_time"],
        "reference_datetime": "reference_datetime",
        "indexing_datetime": ["indexing_time", "indexing_datetime"],
        "step_timedelta": "step_timedelta",
        "param_level": "param_level",
    }

    __handle_type = None

    def __init__(self, cache=None, **kwargs):
        self._cache = MetadataCacheHandler.make(cache)

    @staticmethod
    def _handle_type():
        """Return the expected handle type. Implemented like this
        to avoid cyclic import
        """
        if GribMetadata.__handle_type is None:
            from earthkit.data.readers.grib.codes import GribCodesHandle

            GribMetadata.__handle_type = GribCodesHandle
        return GribMetadata.__handle_type

    @abstractmethod
    def _handle(self):
        pass

    def __len__(self):
        return sum(map(lambda i: 1, self.keys()))

    def __contains__(self, key):
        return self._handle.__contains__(key)

    def __iter__(self):
        return self.keys()

    def keys(self):
        return self._handle.keys()

    def items(self):
        return self._handle.items()

    @MetadataCacheHandler.cache_get
    @MetadataAccessor(ACCESSORS)
    def get(self, key, default=None, *, astype=None, raise_on_missing=False):
        def _key_name(key):
            if key == "param":
                key = "shortName"
            elif key == "_param_id":
                key = "paramId"
            return key

        _kwargs = {}
        if not raise_on_missing:
            _kwargs["default"] = default

        # allow using the "grib." prefix.
        if key.startswith("grib."):
            key = key[5:]

        key = _key_name(key)

        v = self._handle.get(key, ktype=astype, **_kwargs)

        # special case when  "shortName" is "~".
        if key == "shortName" and v == "~":
            v = self._handle.get("paramId", ktype=str, **_kwargs)
        return v

    def _copy_key(self, target_handle, key):
        v_ori = self._handle.get(key, default=None)
        v_new = target_handle.get(key, default=None)
        if v_ori is not None and v_new is not None and v_ori != v_new:
            target_handle.set_long(key, v_ori)

    def override(self, *args, headers_only_clone=True, **kwargs):
        r"""Create a new metadata object by cloning a new GRIB handle and setting the keys in it.

        Parameters
        ----------
        *args: tuple
            Positional arguments. When present must be a dict with the GRIB keys to set in
            the new GRIB handle.
        headers_only_clone: bool, optional
            If True, the new GRIB handle will be created with headers_only=True to reduce the
            data section. With this the GRIB handle size will be significantly smaller, but the
            data section becomes unusable. Default is True.
        **kwargs: dict, optional
            Other keyword arguments specifying the GRIB keys to set.

        Returns
        -------
        :class:`WrappedMetadata`
            The new metadata object. There is always a :class:`StandAloneGribMetadata` object
            created containing the new GRIB handle updated with the specified keys.
            It is then wrapped in a :class:`WrappedMetadata` object storing ``"bitsPerValue"``
            as an extra key.


        Notes
        -----
        - When ``"bitsPerValue"`` is a key to set it is not written to the new handle. Instead, it
          is stored as an extra key in the resulting :class:`WrappedMetadata` object.
        """
        d = dict(*args, **kwargs)

        new_value_size = None
        gridspec = d.pop("gridspec", None)
        if gridspec is not None:
            from earthkit.data.readers.grib.gridspec import GridSpecConverter

            edition = d.get("edition", self["edition"])
            md, new_value_size = GridSpecConverter.to_metadata(gridspec, edition=edition)
            d.update(md)

        handle = self._handle.clone(headers_only=headers_only_clone)

        extra = {}

        # For the steps below consider the followings:
        # - we cannot reliably determine whether the original handle is reduced or not
        # - "bitsPerValue" needs a special treatment, because it cannot be set without
        #   repacking the data.
        # - we want to carry "bitsPerValue" over to the clone if possible

        # When headers_only=True, "bitsPerValue" in the clone is unreliable. Since we need to
        # carry "bitsPerValue" over ideally we should copy it into the clone but we
        # cannot do it since we just trimmed down the data section, so a proper repacking
        # is not possible. As a solution, we will generate a WrappedMetadata object and
        # store the original "bitsPerValue" in the extra dict.
        # When headers_only=False, we do not know whether the original handle was trimmed down
        # or not. Therefore, instead of applying complicated logic we follow the same
        # approach as for headers_only=True.
        key = "bitsPerValue"
        if key in d:
            extra[key] = d.pop(key)
        else:
            # we get the value form the original metadata object and not from the handle since
            # the handle can already be trimmed down
            v = self.get(key, default=None)
            if v is not None and v > 0:
                extra[key] = v
            # as a fallback we try to get the value from the clone
            else:
                v_clone = handle.get(key, None)
                if v_clone is not None and v_clone > 0:
                    extra[key] = v_clone

        if d:
            single = {}
            multiple = {}
            for k, v in d.items():
                if isinstance(v, (int, float, str, bool)):
                    single[k] = v
                else:
                    multiple[k] = v

            try:
                # Try to set all metadata at once
                # This is needed when we set multiple keys that are interdependent
                handle.set_multiple(single)
            except Exception as e:
                LOG.error("Failed to set metadata at once: %s", e)
                # Try again, but one by one
                for k, v in single.items():
                    handle.set(k, v)

            for k, v in multiple.items():
                handle.set(k, v)

        # we need to set the values to the new size otherwise the clone generated
        # with headers_only=True will be inconsistent
        if new_value_size is not None and new_value_size > 0:
            import numpy as np

            vals = np.zeros(new_value_size)
            handle.set_values(vals)

        # ensure that the cache settings are the same
        r = StandAloneGribMetadata(
            handle,
            cache=MetadataCacheHandler.clone_empty(self._cache),
        )

        if extra:
            r = WrappedMetadata(r, extra=extra)

        return r

    def namespaces(self):
        return self.NAMESPACES

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
        r = self._handle.as_namespace(namespace)

        # special case when  "param" is "~".
        if r is not None:
            for k in ("shortName", "param"):
                if k in r and r[k] == "~":
                    r[k] = self.get(k)
        return r

    @cached_property
    def geography(self):
        return GribFieldGeography(self)

    def datetime(self):
        return {
            "base_time": self.base_datetime(),
            "valid_time": self.valid_datetime(),
        }

    def base_datetime(self):
        return self._datetime("dataDate", "dataTime")

    def valid_datetime(self):
        return self._datetime("validityDate", "validityTime")

    def reference_datetime(self):
        return self._datetime("referenceDate", "referenceTime")

    def indexing_datetime(self):
        return self._datetime("indexingDate", "indexingTime")

    def step_timedelta(self):
        v = self.get("endStep", None)
        if v is None:
            v = self.get("step", None)
        return to_timedelta(v)

    def _datetime(self, date_key, time_key):
        date = self.get(date_key, None)
        if date is not None:
            time = self.get(time_key, None)
            if time is not None:
                return datetime_from_grib(date, time)
        return None

    def param_level(self):
        return f"{self.get('shortName')}{self.get('level', default='')}"

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

        if namespace is all:
            namespace = self.namespaces()
        else:
            if isinstance(namespace, str):
                namespace = [namespace]

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

    def ls_keys(self):
        return self.LS_KEYS

    def describe_keys(self):
        return self.DESCRIBE_KEYS

    def index_keys(self):
        return self.INDEX_KEYS

    def data_format(self):
        return "grib"

    @property
    def gridspec(self):
        return self.geography.gridspec()

    def _make_restricted(self, r):
        return RestrictedGribMetadata(self)


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
        super().__init__(**kwargs)

    @property
    def _handle(self):
        return self.__handle

    def _hide_internal_keys(self):
        return RestrictedGribMetadata(self)

    def __getstate__(self) -> dict:
        ret = {}
        ret["_handle"] = self._handle.get_buffer()
        # we do not serialize the cache contents
        ret["_cache"] = MetadataCacheHandler.serialise(self._cache)
        return ret

    def __setstate__(self, state: dict):
        from earthkit.data.readers.grib.memory import GribMessageMemoryReader

        self._cache = MetadataCacheHandler.deserialise(state.pop("_cache"))
        self.__handle = next(GribMessageMemoryReader(state.pop("_handle"))).handle


class RestrictedGribMetadata(WrappedMetadata):
    """Hide internal keys and namespaces in GRIB metadata.

    Examples
    --------
    :ref:`/examples/grib_metadata_object.ipynb`
    """

    EKD_NAMESPACE = ["grib"]

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
        # "numberOfPoints",
        # "numberOfDataPoints",
        "latLonValues",
    ]
    INTERNAL_NAMESPACES = ["statistics"]

    def __init__(self, metadata):
        super().__init__(
            metadata,
            hidden=self.INTERNAL_KEYS,
            hidden_namespaces=self.INTERNAL_NAMESPACES,
            enforced_namespaces=self.EKD_NAMESPACE,
        )

    def _hide_internal_keys(self):
        return self

    def __getstate__(self) -> dict:
        state = super().__getstate__()
        return state

    def __setstate__(self, state: dict):
        super().__setstate__(state)
