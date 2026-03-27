# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .source import SourceData


class ZarrData(SourceData):
    """Data object representing Zarr data.

    This object is generated when data is read via the :ref:`data-source-zarr`
    source with :ref:`from_source() <data-source-zarr>`.

    The Zarr data can be converted to a FieldList or an Xarray dataset using the
    corresponding methods provided by this class:

    - :py:func:`to_xarray`
    - :py:func:`to_fieldlist`

    """

    _TYPE_NAME = "ZARR"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._XARRAY, self._FIELDLIST]

    def describe(self):
        """Provide a description of the Zarr data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the Zarr data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="Zarr", path=self._reader.path, types=self.available_types)

    def __repr__(self) -> str:
        return f"ZarrData(path={self._reader.path})"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_fieldlist(self, *args, **kwargs):
        """Convert into a FieldList.

        This method first converting the Zarr data into an Xarray dataset with :func:`to_xarray`
        and then converting the resulting Xarray dataset into
        a FieldList.

        Parameters
        ----------
        **kwargs
            Keyword arguments to pass to :func:`to_xarray` method, which is
            used internally to read the Zarr data before converting it to a FieldList.

        Returns
        -------
        :py:class:`earthkit.data.readers.zarr.fieldlist.ZarrFieldList`
            A FieldList containing the Zarr data.
        """
        return self._reader.to_fieldlist(*args, **kwargs)

    def to_xarray(self, xarray_open_zarr_kwargs=None):
        """Convert into an Xarray dataset.

                This method uses :py:func:`xarray.open_zarr` to read the Zarr data and convert it
                into an Xarray dataset.
        s

        Parameters
        ----------
                xarray_open_zarr_kwargs : dict, None, optional
                    Keyword arguments to pass to :func:`xarray.open_zarr` when opening the Zarr file.
                **kwargs: dict
                    Additional keyword arguments to pass to the reader's to_xarray method.

        Returns
        -------
                :py:class:`xarray.Dataset`
                    An Xarray dataset containing the Zarr data.
        """
        return self._reader.to_xarray(xarray_open_zarr_kwargs=xarray_open_zarr_kwargs)

    def _default_encoder(self):
        """Return the default encoder for Zarr data.

        Returns
        -------
        Encoder
            The default encoder object.
        """
        return self._source._default_encoder()
