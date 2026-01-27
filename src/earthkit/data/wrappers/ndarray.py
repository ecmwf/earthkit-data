# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


from earthkit.data.wrappers import Wrapper


class NumpyNDArrayWrapper(Wrapper):
    """Wrapper around an numpy `ndarray`, offering polymorphism and
    convenience methods.
    """

    def __init__(self, data):
        self.data = data

    def to_numpy(self):
        """Return a numpy `ndarray` representation of the data.

        Returns
        -------
        numpy.ndarray
        """
        return self.data

    def to_xarray(self, **kwargs):
        """Return an xarray.DataArray representation of the data.

        Returns
        -------
        xarray.DataArray
        """
        import xarray as xr

        return xr.DataArray(self.data, **kwargs)
    
    def convert_units(self, source_unit: str | None = None, target_unit: str | None = None):
        """Convert the units of the data.
        Parameters
        ----------
        source_unit : str
            The source unit.
        target_unit : str
            The target unit.

        Returns:
            nummpy.ndarray with converted units.
        """
        
        if source_unit is None or target_unit is None:
            raise ValueError(
                "source_unit and target_unit must be provided for unit conversion of numpy.ndarray."
            )
        
        from earhtkit.utils.units import convert
        
        return convert(self.data, source_unit, target_unit)
        



def wrapper(data, *args, fieldlist=False, **kwargs):
    import numpy as np

    if isinstance(data, np.ndarray):
        return NumpyNDArrayWrapper(data, *args, **kwargs)
    return None
