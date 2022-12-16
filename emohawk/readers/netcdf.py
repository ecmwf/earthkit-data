# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


from emohawk.wrappers.xarray import XArrayDatasetWrapper

from . import Reader


class NetCDFReader(Reader):
    """Class for reading and polymorphing netCDF files."""

    def __init__(self, source, **kwargs):
        super().__init__(source, **kwargs)
        self.__xarray_wrapper = None
        self.__xarray_kwargs = dict()

    def _xarray_wrapper(self, **kwargs):
        if self.__xarray_wrapper is None or kwargs != self.__xarray_kwargs:
            dataset = type(self).to_xarray_multi_from_paths([self.source], **kwargs)
            self.__xarray_kwargs = kwargs.copy()
            self.__xarray_wrapper = XArrayDatasetWrapper(dataset)
        return self.__xarray_wrapper

    def axis(self, axis, **kwargs):
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
        return self._xarray_wrapper(**kwargs).axis(axis)

    def component(self, component, **kwargs):
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
        return self._xarray_wrapper(**kwargs).component(component)

    def to_netcdf(self, **kwargs):
        """
        Save the data to a netCDF file.

        Parameters
        ----------
        See `xarray.DataSet.to_netcdf`.
        """
        self.save(**kwargs)

    def to_numpy(self, **kwargs):
        """
        Return a numpy `ndarray` representation of the data.

        Returns
        -------
        numpy.ndarray
        """
        return self._xarray_wrapper(**self.__xarray_kwargs).to_numpy(**kwargs)

    def to_pandas(self, **kwargs):
        """
        Return a pandas `dataframe` representation of the data.

        Returns
        -------
        pandas.core.frame.DataFrame
        """
        return self._xarray_wrapper(**self.__xarray_kwargs).to_pandas(**kwargs)

    def _to_xarray(self, *args, **kwargs):
        """
        Return an xarray representation of the data.

        Returns
        -------
        xarray.core.dataarray.DataArray
        """
        return self._xarray_wrapper(**self.__xarray_kwargs)._to_xarray()

    @classmethod
    def to_xarray_multi_from_paths(cls, paths, **kwargs):
        import xarray as xr

        options = dict()
        options.update(kwargs.get("xarray_open_mfdataset_kwargs", {}))

        return xr.open_mfdataset(paths, **options)


def reader(path, magic=None, deeper_check=False):
    if magic is None or magic[:4] in (b"\x89HDF", b"CDF\x01", b"CDF\x02"):
        return NetCDFReader(path)
