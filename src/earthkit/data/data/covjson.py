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
    """Represent CoverageJSON data.

    CoverageJSON is a format for encoding multi-dimensional gridded data, often used in geospatial
    contexts. This class provides an interface for working with CoverageJSON data, allowing for conversion
    to an Xarray dataset.

    CoverageJSON data can be converted with the following methods:

    - :py:func:`to_xarray`
    - :py:func:`to_geojson`

    """

    _TYPE_NAME = "Covjson"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._XARRAY, "geojson"]

    def describe(self):
        """Provide a description of the CovJSON data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the CovJSON data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="CovJSON file", path=self._reader.path, types=self.available_types)

    def __repr__(self) -> str:
        return f"CovJSONData(path={self._reader.path})"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_xarray(self, **kwargs):
        """Convert into an Xarray dataset.

        The conversion uses :xref:`covjsonkit` to decode the CovJSON data
        and convert it into an Xarray dataset.

        Parameters
        ----------
        **kwargs
            Not used for this conversion, but included for consistency with other conversion methods.

        Returns
        -------
        :py:class:`xarray.Dataset`
            An Xarray dataset containing the CovJSON data.
        """
        return self._reader.to_xarray(**kwargs)

    def to_geojson(self, **kwargs) -> dict:
        """Convert into GeoJSON format.

        The conversion uses :xref:`covjsonkit` to decode the CovJSON data.

        Parameters
        ----------
        **kwargs
            Not used for this conversion, but included for consistency with other conversion methods.

        Returns
        -------
        dict
            The data in GeoJSON format.
        """
        return self._reader.to_geojson(**kwargs)
