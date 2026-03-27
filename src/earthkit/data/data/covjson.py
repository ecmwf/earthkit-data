# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .source import SourceData


class CovJsonData(SourceData):
    _TYPE_NAME = "Covjson"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._XARRAY, self._FIELDLIST]

    def describe(self):
        """Provide a description of the CovJSON data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the CovJSON data.
        """
        pass

    def to_xarray(self, **kwargs):
        """Convert into an Xarray dataset.

        Parameters
        ----------
        **kwargs
            Keyword arguments to pass to the reader's to_xarray method.

        Returns
        -------
        :py:class:`xarray.Dataset`
            An Xarray dataset containing the CovJSON data.
        """
        return self._reader.to_xarray(**kwargs)

    def to_fieldlist(self, **kwargs):
        """Convert into a FieldList.

        Parameters
        ----------
        **kwargs
            Keyword arguments to pass to the reader's to_fieldlist method.

        Returns
        -------
        :py:class:`earthkit.data.core.fieldlist.FieldList`
            A FieldList containing the CovJSON data.
        """
        return self._reader.to_fieldlist(**kwargs)

    def to_geojson(self, **kwargs):
        """Convert into GeoJSON format.

        Parameters
        ----------
        **kwargs
            Keyword arguments to pass to the reader's to_geojson method.

        Returns
        -------
        dict or GeoJSON
            The data in GeoJSON format.
        """
        return self._reader.to_geojson(**kwargs)
