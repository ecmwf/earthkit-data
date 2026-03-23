# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from . import Translator


class XArrayTranslator(Translator):
    """Translator class for xarray `DataArray` and `Dataset`."""

    def __init__(self, data, *args, **kwargs):
        super().__init__(data.to_xarray(*args, **kwargs))


class XArrayDataArrayTranslator(XArrayTranslator):
    """Wrapper around an xarray `DataArray`, offering polymorphism and
    convenience methods.
    """

    _name = "xarray.DataArray"

    def __call__(self):
        """Data-Array requested, if Dataset return the first data variable in dataset."""
        import xarray as xr

        if isinstance(self._data, xr.Dataset):
            first_data_var = list(self._data.data_vars)[0]
            return self._data[first_data_var]

        return self._data


class XArrayDatasetTranslator(XArrayTranslator):
    """Wrapper around an xarray `DataSet`, offering polymorphism and convenience
    methods.
    """

    _name = "xarray.Dataset"

    def __call__(self):
        """Dataset requested, if DataArray convert to Dataset."""
        import xarray as xr

        if isinstance(self._data, xr.DataArray):
            return self._data.to_dataset()

        return self._data


def translator(data, cls, *args, **kwargs):
    import xarray as xr

    if cls in [xr.DataArray]:
        return XArrayDataArrayTranslator(data, *args, **kwargs)
    if cls in [xr.Dataset]:
        return XArrayDatasetTranslator(data, *args, **kwargs)

    return None
