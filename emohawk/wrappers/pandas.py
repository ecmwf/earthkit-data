# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


from emohawk import Data
from emohawk.metadata import AXES
from emohawk.wrappers import xarray


class PandasFrameWrapper(Data):
    """
    Wrapper around a Pandas `DataFrame`, offering polymorphism and convenience
    methods.
    """

    def axis(self, axis):
        """
        Get the data along a specific coordinate axis.

        Parameters
        ----------
        axis : str
            The coordinate axis along which to extract data. Accepts values of
            `x`, `y`, `z` (vertical level) or `t` (time) (case-insensitive).

        Returns
        -------
        xarray.core.dataarray.DataArray
            An xarray `DataArray` containing the data along the given
            coordinate axis.
        """
        candidates = AXES.get(axis, [])
        for column in candidates:
            if column in self.source:
                break
        else:
            raise ValueError(f"No column found with axis '{axis}'")
        return self.source[column]

    def to_pandas(self):
        """
        Return a pandas `dataframe` representation of the data.

        Returns
        -------
        pandas.core.frame.DataFrame
        """
        return self.source

    def to_numpy(self, *args, **kwargs):
        """
        Return a numpy `ndarray` representation of the data.

        Returns
        -------
        numpy.ndarray
        """
        return self.source.to_numpy(*args, **kwargs)

    def _to_xarray(self, *args, **kwargs):
        """
        Return an xarray representation of the data.

        Returns
        -------
        xarray.core.dataarray.DataArray
        """
        return self.source.to_xarray(*args, **kwargs)

    def to_netcdf(self, *args, **kwargs):
        """
        Save the data to a netCDF file.

        Parameters
        ----------
        See `xarray.DataSet.to_netcdf`.
        """
        return xarray.XArrayDatasetWrapper(self.to_xarray()).to_netcdf(*args, **kwargs)


def wrapper(data, *args, **kwargs):
    import pandas as pd

    if isinstance(data, pd.DataFrame):
        return PandasFrameWrapper(data, *args, **kwargs)

    return None
