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

    def describe(self):
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="Xarray DataArray", types=self.available_types)

    def __repr__(self) -> str:
        return "XarrayDataArrayData"

    def _repr_html_(self):
        return self.describe()._repr_html_()

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

    def describe(self):
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="Xarray Dataset", types=self.available_types)

    def __repr__(self) -> str:
        return "XarrayDatasetData"

    def _repr_html_(self):
        return self.describe()._repr_html_()

    def to_fieldlist(self, *args, **kwargs):
        from earthkit.data.readers.xarray.fieldlist import XArrayFieldList

        fl = XArrayFieldList.from_xarray(self._data, **kwargs)
        if len(fl) == 0:
            raise ValueError("No fields found in Xarray Dataset")
        return fl

    def to_numpy(self, flatten=False, copy=True, dtype=None, index=None, **kwargs):
        return self._to_numpy(self._data.to_array(), flatten=flatten, copy=copy, dtype=dtype, index=index, **kwargs)


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
