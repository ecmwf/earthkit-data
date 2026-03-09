# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from . import ObjectWrapperData


class XarrayData(ObjectWrapperData):
    @property
    def available_types(self):
        return [self._XARRAY, self._PANDAS, self._FIELDLIST, self._NUMPY, self._ARRAY]

    def to_xarray(self, *args, **kwargs):
        return self._data

    def to_pandas(self, *args, **kwargs):
        """Return a pandas `dataframe` representation of the data.

        Returns
        -------
        pandas.core.frame.DataFrame
        """
        return self._data.to_dataframe(*args, **kwargs)

    @staticmethod
    def _to_numpy(data_array, flatten=False, copy=True, dtype=None, index=None, **kwargs):
        """Return a numpy `ndarray` representation of the data.

        Returns
        -------
        numpy.ndarray
        """
        v = data_array.to_numpy()
        if copy:
            v = v.copy()
        if dtype is not None:
            v = v.astype(dtype)
        if flatten:
            v = v.flatten()
        if index is not None:
            v = v[index]
        return v

    def _default_encoder(self):
        return "netcdf"

    def _encode(self, encoder, **kwargs):
        """Encode the data using the specified encoder.

        Parameters
        ----------
        encoder : Encoder
            The encoder to use for encoding the data.
        **kwargs : dict
            Additional keyword arguments to pass to the encoder.

        Returns
        -------
        EncodedData
            The encoded data.
        """
        return encoder._encode_xarray(data=self._data, **kwargs)


class XarrayDataArrayData(XarrayData):
    _TYPE_NAME = "xarray.DataArray"

    def describe():
        pass

    def to_fieldlist(self, *args, **kwargs):
        from earthkit.data.readers.xarray.fieldlist import XArrayFieldList

        data = self._data.to_dataset()
        fl = XArrayFieldList.from_xarray(data, **kwargs)
        if len(fl) == 0:
            raise ValueError("No fields found in Xarray DataArray")
        return fl

    def to_numpy(self, flatten=False, copy=True, dtype=None, index=None, **kwargs):
        return self._to_numpy(self._data, flatten=flatten, copy=copy, dtype=dtype, index=index, **kwargs)


class XarrayDatasetData(XarrayData):
    _TYPE_NAME = "xarray.Dataset"

    def describe():
        pass

    def to_fieldlist(self, *args, **kwargs):
        from earthkit.data.readers.xarray.fieldlist import XArrayFieldList

        fl = XArrayFieldList.from_xarray(self._data, **kwargs)
        if len(fl) == 0:
            raise ValueError("No fields found in Xarray Dataset")
        return fl

    def to_numpy(self, flatten=False, copy=True, dtype=None, index=None, **kwargs):
        return self._to_numpy(
            self._data.to_array(), flatten=flatten, copy=copy, dtype=dtype, index=index, **kwargs
        )


# class XArrayDataArrayWrapper(Wrapper):
#     """Wrapper around an xarray `DataArray`, offering polymorphism and
#     convenience methods.
#     """

#     def __init__(self, data):
#         self.data = data

#     # def axis(self, axis):
#     #     """
#     #     Get the data along a specific coordinate axis.

#     #     Parameters
#     #     ----------
#     #     axis : str
#     #         The coordinate axis along which to extract data. Accepts values of
#     #         `x`, `y`, `z` (vertical level) or `t` (time) (case-insensitive).

#     #     Returns
#     #     -------
#     #     xarray.core.dataarray.DataArray
#     #         An xarray `DataArray` containing the data along the given
#     #         coordinate axis.
#     #     """
#     #     for coord in self.source.coords:
#     #         if self.source.coords[coord].attrs.get("axis", "").lower() == axis:
#     #             break
#     #     else:
#     #         candidates = AXES.get(axis, [])
#     #         for coord in candidates:
#     #             if coord in self.source.coords:
#     #                 break
#     #         else:
#     #             raise ValueError(f"No coordinate found with axis '{axis}'")
#     #     return self.source.coords[coord]

#     def to_xarray(self, *args, **kwargs):
#         """Return an xarray representation of the data.

#         Returns
#         -------
#         xarray.core.dataarray.DataArray
#         """
#         return self.data

#     def to_numpy(self, flatten=False):
#         """Return a numpy `ndarray` representation of the data.

#         Returns
#         -------
#         numpy.ndarray
#         """
#         arr = self.data.to_numpy()
#         if flatten:
#             arr = arr.flatten()
#         return arr

#     def to_pandas(self, *args, **kwargs):
#         """Return a pandas `dataframe` representation of the data.

#         Returns
#         -------
#         pandas.core.frame.DataFrame
#         """
#         return self.data.to_dataframe(*args, **kwargs)

#     def to_netcdf(self, *args, **kwargs):
#         """Save the data to a netCDF file.

#         Parameters
#         ----------
#         See `xarray.DataArray.to_netcdf`.
#         """
#         return self.data.to_netcdf(*args, **kwargs)

#     def _encode(self, encoder, **kwargs):
#         """Encode the data using the specified encoder.

#         Parameters
#         ----------
#         encoder : Encoder
#             The encoder to use for encoding the data.
#         **kwargs : dict
#             Additional keyword arguments to pass to the encoder.

#         Returns
#         -------
#         EncodedData
#             The encoded data.
#         """
#         return encoder._encode_xarray(data=self.data, **kwargs)


# class XArrayDatasetWrapper(XArrayDataArrayWrapper):
#     """Wrapper around an xarray `DataSet`, offering polymorphism and convenience
#     methods.
#     """

#     def to_numpy(self, flatten=False):
#         """Return a numpy `ndarray` representation of the data.

#         Returns
#         -------
#         numpy.ndarray
#         """
#         arr = self.data.to_array().to_numpy()
#         if flatten:
#             arr = arr.flatten()
#         return arr

#     # def component(self, component):
#     #     """
#     #     Get the data representing a specific vector component.

#     #     Parameters
#     #     ----------
#     #     component : str
#     #         The vector component to extract from the data. Accepts values of
#     #         `u` or `v` (case-insensitive).

#     #     Returns
#     #     -------
#     #     xarray.core.dataarray.DataArray
#     #         An xarray `DataArray` containing the data representing the given
#     #         component.
#     #     """
#     #     candidates = COMPONENTS.get(component, [])
#     #     for variable in candidates:
#     #         if variable in self.source.data_vars:
#     #             break
#     #     else:
#     #         raise ValueError(f"No variable found with direction '{component}'")
#     #     return self.source.data_vars[variable]


def wrapper(data, *args, **kwargs):
    from earthkit.data.utils import is_module_loaded

    if not is_module_loaded("xarray"):
        return None

    import xarray as xr

    if isinstance(data, xr.Dataset):
        return XarrayDatasetData(data, *args, **kwargs)
    elif isinstance(data, xr.DataArray):
        return XarrayDataArrayData(data, *args, **kwargs)
    return None
