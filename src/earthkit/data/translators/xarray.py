# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from earthkit.data.translators import Translator


class XArrayDataArrayTranslator(Translator):
    """Wrapper around an xarray `DataArray`, offering polymorphism and
    convenience methods.
    """

    def __init__(self, data, *args, **kwargs):
        self.data = data.to_xarray(*args, **kwargs)

    def __call__(self):
        """Data-Array requested, if Dataset return the first data variable in dataset."""
        import xarray as xr

        if isinstance(self.data, xr.Dataset):
            # TODO: consider a warning under a strict=False mode?
            if len(self.data.data_vars) > 1:
                raise ValueError(
                    "xarray.Dataset contains more than one data variable, cannot convert to DataArray"
                )
            elif len(self.data.data_vars) == 0:
                raise ValueError("xarray.Dataset contains no data variables, cannot convert to DataArray")
            first_data_var = list(self.data.data_vars)[0]
            return self.data[first_data_var]

        return self.data


class XArrayDatasetTranslator(XArrayDataArrayTranslator):
    """Wrapper around an xarray `DataSet`, offering polymorphism and convenience
    methods.
    """

    def __call__(self):
        """Dataset requested, if DataArray convert to Dataset."""
        import xarray as xr

        if isinstance(self.data, xr.DataArray):
            return self.data.to_dataset()

        return self.data


def translator(data, cls, *args, **kwargs):
    import xarray as xr

    if cls in [xr.DataArray]:
        return XArrayDataArrayTranslator(data, *args, **kwargs)
    if cls in [xr.Dataset]:
        return XArrayDatasetTranslator(data, *args, **kwargs)

    return None
