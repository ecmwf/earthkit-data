# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


from earthkit.data.utils.array import outer_indexing

from . import ObjectWrapperData


class NumpyNDArrayWrapper(ObjectWrapperData):
    """Wrapper around an numpy `ndarray`, offering polymorphism and
    convenience methods.
    """

    _TYPE_NAME = "numpy.ndarray"

    @property
    def available_types(self):
        return [self._NUMPY, self._ARRAY, self._XARRAY]

    def describe():
        pass

    def to_numpy(self, flatten=False, dtype=None, copy=True, index=None, **kwargs):
        """Return a numpy `ndarray` representation of the data.

        Returns
        -------
        numpy.ndarray
        """
        v = self._data
        if copy:
            v = v.copy()
        if dtype:
            v = v.astype(dtype)
        if flatten:
            v = v.flatten()
        if index is not None:
            v = outer_indexing(v, index)
            # v = v[index]

        return v

    def to_xarray(self, **kwargs):
        """Return an xarray.DataArray representation of the data.

        Returns
        -------
        xarray.DataArray
        """
        import xarray as xr

        return xr.DataArray(self._data, **kwargs)


def wrapper(data, *args, **kwargs):
    import numpy as np

    if isinstance(data, np.ndarray):
        return NumpyNDArrayWrapper(data, *args, **kwargs)
    return None
