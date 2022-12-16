# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import copy
import warnings

import xarray as xr

from emohawk.wrappers.xarray import XArrayDatasetWrapper

from . import Reader


def mix_kwargs(
    user,
    default,
    forced={},
):
    kwargs = copy.deepcopy(default)

    for k, v in user.items():
        if k in forced and v != forced[k]:
            continue

        kwargs[k] = v

    kwargs.update(forced)

    return kwargs


class GRIBReader(Reader):
    """
    Class for reading and polymorphing GRIB files.
    """

    appendable = True  # GRIB messages can be added to the same file

    def __init__(self, source, **kwargs):
        super().__init__(source, **kwargs)
        self.__xarray_wrapper = None
        self.__xarray_kwargs = dict()

    def _xarray_wrapper(self, **kwargs):
        if self.__xarray_wrapper is None or kwargs != self.__xarray_kwargs:
            self.__xarray_kwargs = kwargs.copy()

            xarray_open_dataset_kwargs = {}

            if "xarray_open_mfdataset_kwargs" in kwargs:
                warnings.warn(
                    "xarray_open_mfdataset_kwargs is deprecated, "
                    "please use xarray_open_dataset_kwargs instead."
                )
                kwargs["xarray_open_dataset_kwargs"] = kwargs.pop(
                    "xarray_open_mfdataset_kwargs"
                )

            user_xarray_open_dataset_kwargs = kwargs.get(
                "xarray_open_dataset_kwargs", {}
            )

            for key in ["backend_kwargs"]:
                xarray_open_dataset_kwargs[key] = mix_kwargs(
                    user=user_xarray_open_dataset_kwargs.pop(key, {}),
                    default={"errors": "raise"},
                    forced={},
                )
            xarray_open_dataset_kwargs.update(
                mix_kwargs(
                    user=user_xarray_open_dataset_kwargs,
                    default={"squeeze": False},
                    forced={
                        "errors": "raise",
                        "engine": "cfgrib",
                    },
                )
            )

            result = xr.open_dataset(self.source, **xarray_open_dataset_kwargs)
            self.__xarray_wrapper = XArrayDatasetWrapper(result)
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

    def to_netcdf(self, file_name, **kwargs):
        """
        Save the data to a netCDF file.

        Parameters
        ----------
        file_name : str
            The file name to which the netCDF file will be saved.
        """
        return self._xarray_wrapper(**kwargs).to_netcdf(file_name)

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


def reader(path, magic=None, deeper_check=False):
    if magic is None or magic[:4] == b"GRIB":
        return GRIBReader(path)
