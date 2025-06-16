# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.utils.array import array_to_numpy
from earthkit.utils.array import convert_array

from earthkit.data.core.base import Base


class Field(Base):
    def __init__(
        self, data=None, time=None, parameter=None, geometry=None, vertical=None, labels=None, **kwargs
    ):
        r"""Initialize a Field object."""
        self.data = data
        self.time = time
        self.parameter = parameter
        self.geometry = geometry
        self.vertical = vertical
        self.labels = labels

    @classmethod
    def from_grib(cls, handle, **kwargs):
        from .grib import GribData
        from .grib import GribGeography
        from .grib import GribParameter
        from .grib import GribTime
        from .grib import GribVertical

        data = GribData(handle)
        parameter = GribParameter(handle)
        time = GribTime(handle)
        geometry = GribGeography(handle)
        vertical = GribVertical(handle)

        return cls(
            data=data,
            parameter=parameter,
            time=time,
            geometry=geometry,
            vertical=vertical,
            **kwargs,
        )

    @property
    def shape(self):
        return self.geometry.shape

    @property
    def values(self):
        """Return the values of the field."""
        return self.data.values

    def to_numpy(self, flatten=False, dtype=None):
        r"""Return the values stored in the field as an ndarray.

        Parameters
        ----------
        flatten: bool
            When it is True a flat ndarray is returned. Otherwise an ndarray with the field's
            :obj:`shape` is returned.
        dtype: str, numpy.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.

        Returns
        -------
        ndarray
            Field values

        """
        v = array_to_numpy(self.data.get_values(dtype=dtype))
        shape = self.data.target_shape(v, flatten, self.shape)
        return self.data.reshape(v, shape)

    def to_array(self, flatten=False, dtype=None, array_backend=None):
        r"""Return the values stored in the field.

        Parameters
        ----------
        flatten: bool
            When it is True a flat array is returned. Otherwise an array with the field's
            :obj:`shape` is returned.
        dtype: str, array.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.
        array_backend: str, module or None
            The array backend to be used. When it is :obj:`None` the underlying array format
            of the field is used.

        Returns
        -------
        array-array
            Field values.

        """
        v = self.data.get_values(dtype=dtype)
        if array_backend is not None:
            v = convert_array(v, target_backend=array_backend)

        shape = self.data.target_shape(v, flatten, self.shape)
        return self.data.reshape(v, shape)


def _create_handle(path, offset):
    from earthkit.data.readers.grib.codes import GribCodesReader

    return GribCodesReader.from_cache(path).at_offset(offset)


def _create_grib_field(path, offset):
    handle = _create_handle(path, offset)
    return Field.from_grib(handle)
