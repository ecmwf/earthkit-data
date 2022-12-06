# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


from emohawk import Data
from emohawk.metadata import AXES, COMPONENTS


class XArrayDataArrayWrapper(Data):
    """Wrapper around an xarray `DataArray`, offering polymorphism and
    convenience methods.
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
        for coord in self.source.coords:
            if self.source.coords[coord].attrs.get("axis", "").lower() == axis:
                break
        else:
            candidates = AXES.get(axis, [])
            for coord in candidates:
                if coord in self.source.coords:
                    break
            else:
                raise ValueError(f"No coordinate found with axis '{axis}'")
        return self.source.coords[coord]

    def to_xarray(self):
        """
        Return an xarray representation of the data.

        Returns
        -------
        xarray.core.dataarray.DataArray
        """
        return self.source

    def to_numpy(self):
        """
        Return a numpy `ndarray` representation of the data.

        Returns
        -------
        numpy.ndarray
        """
        return self.source.to_numpy()

    def to_pandas(self, *args, **kwargs):
        """
        Return a pandas `dataframe` representation of the data.

        Returns
        -------
        pandas.core.frame.DataFrame
        """
        return self.source.to_dataframe(*args, **kwargs)

    def to_netcdf(self, *args, **kwargs):
        """
        Save the data to a netCDF file.

        Parameters
        ----------
        See `xarray.DataArray.to_netcdf`.
        """
        return self.source.to_netcdf(*args, **kwargs)


class XArrayDatasetWrapper(XArrayDataArrayWrapper):
    """
    Wrapper around an xarray `DataSet`, offering polymorphism and convenience
    methods.
    """

    def to_numpy(self):
        """
        Return a numpy `ndarray` representation of the data.

        Returns
        -------
        numpy.ndarray
        """
        return self.source.to_array().to_numpy()

    def component(self, component):
        """
        Get the data representing a specific vector component.

        Parameters
        ----------
        component : str
            The vector component to extract from the data. Accepts values of
            `u` or `v` (case-insensitive).

        Returns
        -------
        xarray.core.dataarray.DataArray
            An xarray `DataArray` containing the data representing the given
            component.
        """
        candidates = COMPONENTS.get(component, [])
        for variable in candidates:
            if variable in self.source.data_vars:
                break
        else:
            raise ValueError(f"No variable found with direction '{component}'")
        return self.source.data_vars[variable]


def wrapper(data, *args, **kwargs):
    import xarray as xr

    if isinstance(data, xr.Dataset):
        return XArrayDatasetWrapper(data, *args, **kwargs)

    if isinstance(data, xr.DataArray):
        try:
            return XArrayDatasetWrapper(data.to_dataset(), *args, **kwargs)
        except ValueError:
            return XArrayDataArrayWrapper(data, *args, **kwargs)

    return None


def translator(source, cls):
    import xarray as xr

    if cls in (xr.DataArray, xr.Dataset):
        return source.to_xarray

    return None
