# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,  # noqa: F401
)

from .source import SourceData

if TYPE_CHECKING:
    import pandas  # type: ignore[import]
    import xarray  # type: ignore[import]


class GeoTIFFData(SourceData):
    """Represent GeoTIFF data.

    GeoTIFF is a public domain metadata standard which allows georeferencing information to be
    embedded within a TIFF file. This class provides methods to convert GeoTIFF data into various formats
    such as Xarray datasets, Pandas DataFrames, and FieldLists.

    GeoTIFF data can be converted with the following methods:

    - :py:func:`to_xarray`
    - :py:func:`to_pandas`
    - :py:func:`to_fieldlist`

    """

    _TYPE_NAME = "GeoTIFF"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._XARRAY, self._PANDAS, self._FIELDLIST]

    def describe(self) -> Any:
        """Provide a description of the GeoTIFF data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the GeoTIFF data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="GeoTIFF file", path=self._reader.path, types=self.available_types)

    def __repr__(self) -> str:
        return f"GeoTIFFData(path={self._reader.path})"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_fieldlist(self):
        """Convert into a FieldList.

        -------
        :py:class:`earthkit.data.readers.geotiff.fieldlist.GeoTIFFFieldList`
            A FieldList containing the GeoTIFF data.
        """
        return self._reader.to_fieldlist()

    def to_pandas(self, *args, **kwargs) -> "pandas.DataFrame":
        """Convert into a Pandas DataFrame.

        Returns
        -------
        :py:class:`pandas.DataFrame`
            A Pandas DataFrame containing the GeoTIFF data.
        """
        return self._reader.to_pandas(**kwargs)

    def to_xarray(self, rioxarray_open_rasterio_kwargs=None, **kwargs) -> "xarray.Dataset":
        """Convert into an Xarray dataset.

        The conversion is done by using ``rioxarray``.

        Parameters
        ----------
        rioxarray_open_rasterio_kwargs: dict, None, optional
            Keyword arguments passed to :func:`rioxarray.open_rasterio`. This is used for safe parsing of
            kwargs via intermediate methods. Please note that if not specified, the following kwargs are
            set by default before passing to :func:`rioxarray.open_rasterio`:

                .. code-block:: python

                    {
                        "band_as_variable": True,
                        "mask_and_scale": True,
                        "decode_times": True,
                    }
        **kwargs
            Keyword arguments passed to :func:`rioxarray.open_rasterio` if
            ``rioxarray_open_rasterio_kwargs`` is not specified, otherwise they are ignored.

        Returns
        -------
        :py:class:`xarray.Dataset`
            An Xarray dataset containing the GeoTIFF data.
        """
        return self._reader.to_xarray(rioxarray_open_rasterio_kwargs=rioxarray_open_rasterio_kwargs, **kwargs)
