# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import logging
import os

import eccodes
import numpy as np

from earthkit.data.core import Base
from earthkit.data.utils.bbox import BoundingBox
from earthkit.data.utils.message import (
    CodesHandle,
    CodesMessagePositionIndex,
    CodesReader,
)
from earthkit.data.utils.metadata import metadata_argument
from earthkit.data.utils.projections import Projection

LOG = logging.getLogger(__name__)

_GRIB_NAMESPACES = {"default": None}

for k in ("ls", "geography", "mars", "parameter", "statistics", "time", "vertical"):
    _GRIB_NAMESPACES[k] = k


def missing_is_none(x):
    return None if x == 2147483647 else x


class GribCodesMessagePositionIndex(CodesMessagePositionIndex):
    # This does not belong here, should be in the C library
    def _get_message_positions(self, path):
        fd = os.open(path, os.O_RDONLY)
        try:

            def get(count):
                buf = os.read(fd, count)
                assert len(buf) == count
                return int.from_bytes(
                    buf,
                    byteorder="big",
                    signed=False,
                )

            offset = 0
            while True:
                code = os.read(fd, 4)
                if len(code) < 4:
                    break

                if code != b"GRIB":
                    offset = os.lseek(fd, offset + 1, os.SEEK_SET)
                    continue

                length = get(3)
                edition = get(1)

                if edition == 1:
                    if length & 0x800000:
                        sec1len = get(3)
                        os.lseek(fd, 4, os.SEEK_CUR)
                        flags = get(1)
                        os.lseek(fd, sec1len - 8, os.SEEK_CUR)

                        if flags & (1 << 7):
                            sec2len = get(3)
                            os.lseek(fd, sec2len - 3, os.SEEK_CUR)

                        if flags & (1 << 6):
                            sec3len = get(3)
                            os.lseek(fd, sec3len - 3, os.SEEK_CUR)

                        sec4len = get(3)

                        if sec4len < 120:
                            length &= 0x7FFFFF
                            length *= 120
                            length -= sec4len
                            length += 4

                if edition == 2:
                    length = get(8)

                yield offset, length
                offset = os.lseek(fd, offset + length, os.SEEK_SET)

        finally:
            os.close(fd)


class GribCodesHandle(CodesHandle):
    PRODUCT_ID = eccodes.CODES_PRODUCT_GRIB

    # TODO: just a wrapper around the base class implementation to handle the
    # s,l,d qualifiers. Once these are implemented in the base class this method can
    # be removed. md5GridSection is also handled!
    def get(self, name, ktype=None, **kwargs):
        if name == "values":
            return self.get_values()
        elif name == "md5GridSection":
            return self.get_md5GridSection()

        return super().get(name, ktype, **kwargs)

    def get_md5GridSection(self):
        # Special case because:
        #
        # 1) eccodes is returning size > 1 for 'md5GridSection'
        # (size = 16 : it is the number of bytes of the value)
        # This is already fixed in eccodes 2.27.1
        #
        # 2) sometimes (see below), the value for "shapeOfTheEarth" is inconsistent.
        # This impacts the (computed on-the-fly) value of "md5GridSection".
        # ----------------
        # Example of data with inconsistent values:
        # S2S data, origin='ecmf', param='tp', step='24', number='0', date=['20201203','20200702']
        # the 'md5GridSection' are different
        # This is because one has "shapeOfTheEarth" set to 0, the other to 6.
        # This is only impacting the metadata.
        # Since this has no impact on the data itself,
        # this is unlikely to be fixed. Therefore this hacky patch.
        #
        # Obviously, the patch causes an inconsistency between the value of md5GridSection
        # read by this code, and the value read by another code without this patch.

        save = eccodes.codes_get_long(self._handle, "shapeOfTheEarth")
        eccodes.codes_set_long(self._handle, "shapeOfTheEarth", 255)
        result = eccodes.codes_get_string(self._handle, "md5GridSection")
        eccodes.codes_set_long(self._handle, "shapeOfTheEarth", save)
        return result

    def as_namespace(self, namespace, param="shortName"):
        r = {}
        ignore = {
            "distinctLatitudes",
            "distinctLongitudes",
            "distinctLatitudes",
            "latLonValues",
            "latitudes",
            "longitudes",
            "values",
        }
        for key in self.keys(namespace=namespace):
            if key not in ignore:
                r[key] = self.get(param if key == "param" else key)
        return r

    # TODO: once missing value handling is implemented in the base class this method
    # can be removed
    def get_values(self):
        eccodes.codes_set(self._handle, "missingValue", CodesHandle.MISSING_VALUE)
        vals = eccodes.codes_get_values(self._handle)
        if self.get_long("bitmapPresent"):
            vals[vals == CodesHandle.MISSING_VALUE] = np.nan
        return vals

    def get_latitudes(self):
        return self.get("latitudes")

    def get_longitudes(self):
        return self.get("longitudes")

    def get_data_points(self):
        return eccodes.codes_grib_get_data(self._handle)

    # def clone(self):
    #     return CodesHandle(eccodes.codes_clone(self._handle), None, None)

    def set_values(self, values):
        assert self.path is None, "Only cloned handles can have values changed"
        eccodes.codes_set_values(self._handle, values.flatten())
        # This is writing on the GRIB that something has been modified (255=unknown)
        eccodes.codes_set_long(self._handle, "generatingProcessIdentifier", 255)

    def set_multiple(self, values):
        assert self.path is None, "Only cloned handles can have values changed"
        eccodes.codes_set_key_vals(self._handle, values)


class GribCodesReader(CodesReader):
    PRODUCT_ID = eccodes.CODES_PRODUCT_GRIB
    HANDLE_TYPE = GribCodesHandle


class GribField(Base):
    r"""Represents a GRIB message in a GRIB file.

    Parameters
    ----------
    path: str
        Path to the GRIB file
    offset: number
        File offset of the message (in bytes)
    length: number
        Size of the message (in bytes)
    """

    def __init__(self, path, offset, length):
        self.path = path
        self._offset = offset
        self._length = length
        self._handle = None

    @property
    def handle(self):
        r""":class:`CodesHandle`: Gets an object providing access to the low level GRIB message structure."""
        if self._handle is None:
            assert self._offset is not None
            self._handle = GribCodesReader.from_cache(self.path).at_offset(self._offset)
        return self._handle

    @property
    def values(self):
        r"""ndarray: Gets the values stored in the GRIB field as a 1D ndarray."""
        return self.handle.get_values()

    @property
    def offset(self):
        r"""number: Gets the offset (in bytes) of the GRIB field within the GRIB file."""
        if self._offset is None:
            self._offset = int(self.handle.get("offset"))
        return self._offset

    @property
    def shape(self):
        r"""tuple: Gets the shape of the GRIB field. For structured grids the shape is a tuple
        in the form of (Nj, Ni) where:

        - ni: the number of gridpoints in i direction (longitude for a regular latitude-longitude grid)
        - nj: the number of gridpoints in j direction (latitude for a regular latitude-longitude grid)

        For other grid types the number of gridpoints is returned as ``(num,)``
        """
        Nj = missing_is_none(self.handle.get("Nj", default=None))
        Ni = missing_is_none(self.handle.get("Ni", default=None))
        if Ni is None or Nj is None:
            n = self.handle.get("numberOfDataPoints", default=None)
            return (n,)  # shape must be a tuple
        return (Nj, Ni)

    def data(self, keys=("lat", "lon", "value"), flatten=False):
        r"""Returns the values and/or the geographical coordinates for each grid point.

        Parameters
        ----------
        keys: :obj:`str`, :obj:`list` or :obj:`tuple`
            Specifies the type of data to be returned. Any combination of "lat", "lon" and "value"
            is allowed here.
        flatten: bool
            When it is True a flat ndarray per key is returned. Otherwise an ndarray with the field's
            :obj:`shape` is returned for each key.

        Returns
        -------
        ndarray or tuple of ndarrays
            When ``keys`` is a single value an ndarray is returned. Otherwise a tuple containing one ndarray
            per key is returned (following the order in ``keys``).

        See Also
        --------
        to_points
        to_numpy
        values

        """
        _keys = dict(
            lat=self.handle.get_latitudes,
            lon=self.handle.get_longitudes,
            value=self.handle.get_values,
        )

        if isinstance(keys, str):
            keys = [keys]

        for k in keys:
            if k not in _keys:
                raise ValueError(f"data: invalid argument: {k}")

        r = [_keys[k]() for k in keys]
        if not flatten:
            shape = self.shape
            r = [x.reshape(shape) for x in r]
        return r[0] if len(r) == 1 else tuple(r)

    def to_numpy(self, flatten=False, dtype=None):
        r"""Returns the values stored in the GRIB field as an ndarray.

        Parameters
        ----------
        flatten: bool
            When it is True a flat ndarray is returned. Otherwise an ndarray with the field's
            :obj:`shape` is returned.
        dtype: str or dtype
            Typecode or data-type to which the array is cast.

        Returns
        -------
        ndarray
            Field values

        """
        values = self.values
        if not flatten:
            values = self.values.reshape(self.shape)
        if dtype is not None:
            values = values.astype(dtype)
        return values

    def to_points(self, flatten=False):
        r"""Returns the geographical coordinates in the data's original
        Coordinate Reference System (CRS).

        Parameters
        ----------
        flatten: bool
            When it is True 1D ndarrays are returned. Otherwise ndarrays with the field's
            :obj:`shape` are returned.

        Returns
        -------
        dict
            Dictionary with items "x" and "y", containing the ndarrays of the x and
            y coordinates, respectively.

        Raises
        ------
        ValueError
            When the coordinates in the data's original CRS are not available.

        """
        grid_type = self.metadata("gridType", default=None)
        if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
            lon, lat = self.data(("lon", "lat"), flatten=flatten)
            return dict(x=lon, y=lat)
        else:
            raise ValueError("grid_type={grid_type} is not supported in to_points()")

    def to_latlon(self, flatten=False):
        r"""Returns the latitudes/longitudes of all the gridpoints in the field.

        Parameters
        ----------
        flatten: bool
            When it is True 1D ndarrays are returned. Otherwise ndarrays with the field's
            :obj:`shape` are returned.

        Returns
        -------
        dict
            Dictionary with items "lat" and "lon", containing the ndarrays of the latitudes and
            longitudes, respectively.

        """
        lon, lat = self.data(("lon", "lat"), flatten=flatten)
        return dict(lat=lat, lon=lon)

    def __repr__(self):
        return "GribField(%s,%s,%s,%s,%s,%s)" % (
            self.handle.get("shortName", default=None),
            self.handle.get("levelist", default=None),
            self.handle.get("date", default=None),
            self.handle.get("time", default=None),
            self.handle.get("step", default=None),
            self.handle.get("number", default=None),
        )

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
        date = self.handle.get("date", default=None)
        time = self.handle.get("time", default=None)
        return datetime.datetime(
            date // 10000,
            date % 10000 // 100,
            date % 100,
            time // 100,
            time % 100,
        )

    def _valid_datetime(self):
        step = self.handle.get("endStep", default=None)
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
        return Projection.from_proj_string(
            self.handle.get("projTargetString", default=None)
        )

    def bounding_box(self):
        r"""Returns the bounding box of the field.

        Returns
        -------
        :obj:`BoundingBox <data.utils.bbox.BoundingBox>`
        """
        return BoundingBox(
            north=self.handle.get("latitudeOfFirstGridPointInDegrees", default=None),
            south=self.handle.get("latitudeOfLastGridPointInDegrees", default=None),
            west=self.handle.get("longitudeOfFirstGridPointInDegrees", default=None),
            east=self.handle.get("longitudeOfLastGridPointInDegrees", default=None),
        )

    def _attributes(self, names):
        result = {}
        for name in names:
            result[name] = self.handle.get(name, default=None)
        return result

    def _get(self, name):
        """Private, for testing only"""
        # paramId is renamed as param to get rid of the
        # additional '.128' (in earthkit/data/scripts/grib.py)
        if name == "param":
            name = "paramId"
        return self.handle.get(name)

    def metadata(self, *keys, namespace=None, astype=None, **kwargs):
        r"""Returns metadata values from the GRIB message.

        Parameters
        ----------
        *keys: tuple
            Positional arguments specifying metadata keys. Only ecCodes GRIB keys can be used
            here. Can be empty, in this case all the keys from the specified ``namespace`` will
            be used. (See examples below).
        namespace: :obj:`str`, :obj:`list` or :obj:`tuple`
            The namespace to choose the ``keys`` from. Any :xref:`eccodes_namespace` can be used here.
            :obj:`metadata` also defines the "default" namespace, which contains all the
            GRIB keys that ecCodes can access without specifying a namespace.
            When ``keys`` is empty and ``namespace`` is None all
            the available namespaces will be used. When ``keys`` is non empty ``namespace`` cannot
            specify multiple values.
        astype: type name, :obj:`list` or :obj:`tuple`
            Return types for ``keys``. A single value is accepted and applied to all the ``keys``.
            Otherwise, must have same the number of elements as ``keys``. Only used when
            ``keys`` is not empty.
        **kwargs: tuple, optional
            Other keyword arguments:

            * default: value, optional
                Specifies the same default value for all the ``keys`` specified. When ``default`` is
                **not present** and a key is not found or its value is a missing value
                :obj:`metadata` will raise KeyError.

        Returns
        -------
        single value, :obj:`list`, :obj:`tuple` or :obj:`dict`
            - when ``keys`` is not empty:
                - single value when ``keys`` is a str
                - otherwise the same type as that of ``keys`` (:obj:`list` or :obj:`tuple`)
            - when ``keys`` is empty:
                - when ``namespace`` is :obj:`str` returns a :obj:`dict` with the keys and values
                  in that namespace
                - otherwise returns a :obj:`dict` with one item per namespace (dict of dict)

        Raises
        ------
        KeyError
            If no ``default`` is set and a key is not found in the message or it has a missing value.


        Examples
        --------
        Getting keys with their native type:

        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> ds[0].metadata("param")
        '2t'
        >>> ds[0].metadata("param", "units")
        ('2t', 'K')
        >>> ds[0].metadata(("param", "units"))
        ('2t', 'K')
        >>> ds[0].metadata(["param", "units"])
        ['2t', 'K']
        >>> ds[0].metadata(["param"])
        ['2t']
        >>> ds[0].metadata("badkey")
        KeyError: 'badkey'
        >>> ds[0].metadata("badkey", default=None)
        <BLANKLINE>

        Prescribing key types:

        >>> ds[0].metadata("centre", astype=int)
        98
        >>> ds[0].metadata(["paramId", "centre"], astype=int)
        [167, 98]
        >>> ds[0].metadata(["centre", "centre"], astype=[int, str])
        [98, 'ecmf']

        Using namespaces:

        >>> ds[0].metadata(namespace="parameter")
        {'centre': 'ecmf', 'paramId': 167, 'units': 'K', 'name': '2 metre temperature', 'shortName': '2t'}
        >>> ds[0].metadata(namespace=["parameter", "vertical"])
        {'parameter': {'centre': 'ecmf', 'paramId': 167, 'units': 'K', 'name': '2 metre temperature',
         'shortName': '2t'},
         'vertical': {'typeOfLevel': 'surface', 'level': 0}}
        >>> r = ds[0].metadata()
        >>> r.keys()
        dict_keys(['default', 'ls', 'geography', 'mars', 'parameter', 'statistics', 'time', 'vertical'])

        """

        def _key_name(key):
            if key == "param":
                key = "shortName"
            elif key == "_param_id":
                key = "paramId"
            return key

        key, namespace, astype, key_arg_type = metadata_argument(
            *keys, namespace=namespace, astype=astype
        )

        assert isinstance(key, list)
        assert isinstance(namespace, (list, tuple))

        if key:
            assert isinstance(astype, (list, tuple))
            if namespace and namespace[0] != "default":
                key = [namespace[0] + "." + k for k in key]

            r = [
                self.handle.get(_key_name(k), ktype=kt, **kwargs)
                for k, kt in zip(key, astype)
            ]

            if key_arg_type == str:
                return r[0]
            elif key_arg_type == tuple:
                return tuple(r)
            else:
                return r
        else:
            if len(namespace) == 0:
                namespace = _GRIB_NAMESPACES.keys()

            r = {
                ns: self.handle.as_namespace(_GRIB_NAMESPACES.get(ns, ns))
                for ns in namespace
            }
            if len(r) == 1:
                return r[namespace[0]]
            else:
                return r

    def __getitem__(self, key):
        """Returns the value of the metadata ``key``."""
        return self.metadata(key)

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

        namespace = _GRIB_NAMESPACES.keys() if namespace is None else [namespace]
        r = [
            {
                "title": ns,
                "data": self.handle.as_namespace(_GRIB_NAMESPACES.get(ns)),
                "tooltip": f"Keys in the ecCodes {ns} namespace",
            }
            for ns in namespace
        ]

        return format_namespace_dump(
            r, selected="parameter", details=self.__class__.__name__, **kwargs
        )

    def write(self, f):
        r"""Writes the message to a file object.

        Parameters
        ----------
        f: file object
            The target file object.
        """
        # assert isinstance(f, io.IOBase)
        self.handle.write_to(f)

    def message(self):
        r"""Returns a buffer containing the encoded message.

        Returns
        -------
        bytes
        """
        return self.handle.get_buffer()
