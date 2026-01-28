# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


from earthkit.data.wrappers import Wrapper

import logging

LOG = logging.getLogger(__name__)

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
    
    def convert_units(
        self,
        source_units: str | None = None,
        target_units: str | None = None,
        **kwargs,
    ):
        """Convert the units of the data.
        Parameters
        ----------
        source_units : str
            The source unit.
        target_units : str
            The target unit.

        Returns:
            nummpy.ndarray with converted units.
        """
        
        if source_units is None or target_units is None:
            raise ValueError(
                "source_units and target_units must be provided for unit conversion of numpy.ndarray."
            )
        
        if len(kwargs) > 0:
            LOG.debug(
                f"Ignoring unexpected keyword arguments: {list(kwargs.keys())}",
            )
        
        from earhtkit.utils.units import convert
        
        return convert(self.data, source_units, target_units)
        



def wrapper(data, *args, fieldlist=False, **kwargs):
    import numpy as np

    if isinstance(data, np.ndarray):
        return NumpyNDArrayWrapper(data, *args, **kwargs)
    return None
