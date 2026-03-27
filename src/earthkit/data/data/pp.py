# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from __future__ import annotations

from .source import SourceData


class PPData(SourceData):
    """Represent data in UK Met Office PP format.

    PP is a binary file format used by the UK Met Office to store meteorological data. This
    class provides methods to convert PP data into various formats such as Xarray datasets and FieldLists.

    PP data can be converted with the following methods:

    - :py:func:`to_xarray`
    - :py:func:`to_fieldlist`

    """

    _TYPE_NAME = "PP"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._XARRAY, self._FIELDLIST]

    def describe(self):
        """Provide a description of the PP data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the PP data.
        """
        pass

    def to_fieldlist(self, **kwargs):
        """Convert into a FieldList.

        This method first converting the PP data into an Xarray dataset with :func:`to_xarray`
        (using the Iris library), and then converting the resulting Xarray dataset into
        a FieldList.

        Parameters
        ----------
        **kwargs
            Keyword arguments to pass to :func:`to_xarray` method, which is
            used internally to read the PP data before converting it to a FieldList.

        Returns
        -------
        :py:class:`earthkit.data.readers.pp.fieldlist.PPFieldList`
            A FieldList containing the PP data.
        """
        return self._reader.to_fieldlist(**kwargs)

    def to_xarray(
        self,
        iris_open_kwargs: dict | None = None,
        iris_save_kwargs: dict | None = None,
        xr_load_kwargs: dict | None = None,
    ):
        """Convert into an Xarray dataset.

        This method uses the Iris library to read the PP file and convert it into an Xarray dataset.
        The conversion process involves reading the PP file with :py:func:`iris.load`, then calling
        :py:func:`ncdata.iris_xarray.cubes_to_xarray`.

        Parameters
        ----------
        iris_open_kwargs : dict, optional
            Keyword arguments to pass to :func:`iris.load` when opening the PP file.
        iris_save_kwargs : dict, optional
            Keyword arguments to pass as ``iris_save_kwargs`` to
            :py:func:`ncdata.iris_xarray.cubes_to_xarray`
        xr_load_kwargs : dict, optional
            Keyword arguments to pass as ``xr_load_kwargs`` to
            :py:func:`ncdata.iris_xarray.cubes_to_xarray`

        Returns
        -------
        :py:class:`xarray.Dataset`
            An Xarray dataset containing the PP data.
        """
        return self._reader.to_xarray(
            iris_open_kwargs=iris_open_kwargs,
            iris_save_kwargs=iris_save_kwargs,
            xr_load_kwargs=xr_load_kwargs,
        )

    def _default_encoder(self):
        """Return the default encoder for PP data.

        Returns
        -------
        Encoder
            The default encoder object.
        """
        return self._source._default_encoder()
