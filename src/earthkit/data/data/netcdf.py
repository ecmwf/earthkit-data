# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .source import SourceData


class NetCDFData(SourceData):
    _TYPE_NAME = "NetCDF"

    @property
    def available_types(self):
        return [self._XARRAY, self._PANDAS, self._FIELDLIST, self._NUMPY, self._ARRAY]

    def describe(self):
        """Provide a description of the NetCDF data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the NetCDF data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="NetCDF file", path=self._reader.path, types=self.available_types)

    def __repr__(self) -> str:
        return f"NetCDFData(path={self._reader.path})"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_fieldlist(self, *args, **kwargs):
        """Convert into a FieldList.

        Parameters
        ----------
        *args
            Positional arguments to pass to the reader's to_fieldlist method.
        **kwargs
            Keyword arguments to pass to the reader's to_fieldlist method.

        Returns
        -------
        :py:class:`earthkit.data.core.fieldlist.FieldList`
            A FieldList containing the NetCDF data.
        """
        return self._reader.to_fieldlist(*args, **kwargs)

    def to_xarray(self, *args, xarray_open_mfdataset_kwargs=None, **kwargs):
        """Convert into an Xarray dataset.

        The conversion is performed by using :py:func:`xarray.open_dataset` for a
        single file and :py:func:`xarray.open_mfdataset` for multiple files.

        Parameters
        ----------
        *args
            Positional arguments to pass to the reader's to_xarray method.
            Not used currently. It is there to allow for future extensions or
            additional parameters that may be needed for specific use cases.
        xarray_open_mfdataset_kwargs: dict, None, optional
            Keyword arguments passed to :py:func:`xarray.open_mfdataset`.
            Can only be used when converting multiple NetCDF files into a single
            Xarray dataset. When specified, this argument takes precedence over
            any other keyword arguments passed to the method.
        **kwargs
            Keyword arguments passed to :py:func:`xarray.open_dataset` for
            single file conversion or to :py:func:`xarray.open_mfdataset` for
            multiple file conversion. Ignored if `xarray_open_mfdataset_kwargs`
            is specified.

        Returns
        -------
        :py:class:`xarray.Dataset`
            An Xarray dataset containing the NetCDF data.
        """
        if xarray_open_mfdataset_kwargs:
            options = dict(xarray_open_mfdataset_kwargs=xarray_open_mfdataset_kwargs)
        else:
            options = dict()

        return self._reader.to_xarray(*args, **options, **kwargs)

    def to_pandas(self, *args, **kwargs):
        """Convert into a Pandas DataFrame.

        Parameters
        ----------
        *args
            Positional arguments to pass to the conversion method.
        **kwargs
            Keyword arguments to pass to the conversion method.

        Returns
        -------
        :py:class:`pandas.DataFrame`
            A Pandas DataFrame containing the NetCDF data.
        """
        pass

    def to_numpy(self, *args, **kwargs):
        """Convert into a NumPy array.

        Parameters
        ----------
        *args
            Positional arguments to pass to the reader's to_numpy method.
        **kwargs
            Keyword arguments to pass to the reader's to_numpy method.

        Returns
        -------
        numpy.ndarray
            A NumPy array containing the NetCDF data.
        """
        return self._reader.to_numpy(*args, **kwargs)

    def to_array(self, *args, **kwargs):
        """Convert into an array of a given array-like type.

        Parameters
        ----------
        *args
            Positional arguments to pass to the reader's to_array method.
        **kwargs
            Keyword arguments to pass to the reader's to_array method.

        Returns
        -------
        ArrayLike
            An array containing the NetCDF data.
        """
        return self._reader.to_array(*args, **kwargs)

    def _default_encoder(self):
        """Return the default encoder for NetCDF data.

        Returns
        -------
        Encoder
            The default encoder object.
        """
        return self._source._default_encoder()
