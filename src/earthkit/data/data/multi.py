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

from earthkit.utils.decorators import experimental

from . import Data, SimpleData

if TYPE_CHECKING:
    import pandas  # type: ignore[import]
    import xarray  # type: ignore[import]

    from earthkit.data.core.fieldlist import FieldList


class MultiData(SimpleData):
    _TYPE_NAME = "Multi"

    """Represent multiple sources that cannot be represented by a single Data object."""

    def __init__(self, sources):
        """Initialize a MultiData object.

        Parameters
        ----------
        sources : MultiSource
            A MultiSource object containing multiple data sources.
        """
        self._sources_legacy = sources
        self._source = sources

    @property
    def available_types(self) -> list[str]:
        """list[str]: Return the list of available types that this data object can be converted to."""
        types = set()
        try:
            for d in self._datas():
                types.update(d.available_types)
            return sorted(types)
        except Exception:
            pass

        return list()

    @property
    @experimental(msg="MultiData.sources is experimental and may change or be removed without notice. Do not use it.")
    def _legacy_sources(self) -> Any:
        """Experimental property and may change or be removed in future versions."""
        return self._sources_legacy

    def _datas(self):
        res = []
        for s in self._source.sources:
            if isinstance(s, Data):
                res.append(s)
            else:
                res.append(s.to_data_object())

        return res

    def describe(self) -> Any:
        """Provide a description of the MultiData.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the MultiData.
        """
        pass

    def to_fieldlist(self, *args, **kwargs) -> FieldList:
        """Convert into a FieldList.

        Parameters
        ----------
        *args
            Positional arguments to pass to the conversion method.
        **kwargs
            Keyword arguments to pass to the conversion method.

        Returns
        -------
        :py:class:`earthkit.data.core.fieldlist.FieldList`
            A merged FieldList containing data from all sources.

        Raises
        ------
        NotImplementedError
            If conversion to FieldList is not implemented for this combination of sources.
        """
        if "fieldlist" not in self.available_types:
            raise NotImplementedError("Cannot convert this MultiData object to a fieldlist")

        # TODO: review this merger usage
        data = self._datas()
        fs = [d.to_fieldlist(*args, **kwargs) for d in data]
        from earthkit.data.mergers import merge_by_class

        merged = merge_by_class(fs)
        if merged is not None:
            return merged.mutate()

        raise NotImplementedError("Cannot convert this MultiData object to a fieldlist")

    def to_xarray(self, *args, xarray_open_mfdataset_kwargs=None, **kwargs) -> "xarray.Dataset":
        """Convert into an Xarray dataset.

        The conversion is performed by using :py:func:`xarray.open_mfdataset`.

        Parameters
        ----------
        *args
            Positional arguments to pass to the reader's to_xarray method.
            Not used currently. It is there to allow for future extensions or
            additional parameters that may be needed for specific use cases.
        xarray_open_mfdataset_kwargs: dict, None, optional
            Keyword arguments passed to :py:func:`xarray.open_mfdataset`.
            When specified, this argument takes precedence over
            any other keyword arguments passed to the method. It is used for safe
            parsing of kwargs via intermediate methods.
        **kwargs
            Keyword arguments passed :py:func:`xarray.open_mfdataset`.
            Ignored if `xarray_open_mfdataset_kwargs` is specified.

        Returns
        -------
        :py:class:`xarray.Dataset`
            An Xarray dataset containing data from all objects in the MultiData.
        """
        if xarray_open_mfdataset_kwargs:
            options = dict(xarray_open_mfdataset_kwargs=xarray_open_mfdataset_kwargs)
        else:
            options = dict()

        if "xarray" not in self.available_types:
            raise NotImplementedError(
                "Cannot convert this MultiData object to Xarray. Not all objects support Xarray conversion."
            )

        # TODO: review this merger usage
        return self._source.to_xarray(*args, **options, **kwargs)

    def to_pandas(self, comment="#", pandas_read_csv_kwargs=None) -> "pandas.DataFrame":
        """Convert into a Pandas DataFrame.

        Parameters
        ----------
        comment: str
            Character that represents a comment line in a CSV file. This value is ignored if the
            comment character is defined in ``pandas_read_csv_kwargs``. Applied to all the CSV data
            sources in the current object.
        pandas_read_csv_kwargs: dict, None, optional
            Keyword arguments passed to :func:`pandas.read_csv`. This is used for safe parsing of
            kwargs via intermediate methods. Applied to all the CSV data sources in the current object.

        Returns
        -------
        :py:class:`pandas.DataFrame`
            A Pandas DataFrame containing the data from all objects in the MultiData.
        """
        if "pandas" not in self.available_types:
            raise NotImplementedError(
                "Cannot convert this MultiData object to pandas. Not all objects support pandas conversion."
            )

        # TODO: review this merger usage
        data = self._datas()

        from earthkit.data.mergers import make_merger

        pandas_read_csv_kwargs = dict(pandas_read_csv_kwargs) if pandas_read_csv_kwargs is not None else {}
        if "comment" not in pandas_read_csv_kwargs:
            pandas_read_csv_kwargs["comment"] = comment

        return make_merger(None, data).to_pandas(pandas_read_csv_kwargs=pandas_read_csv_kwargs)

    def to_geopandas(self, *args, **kwargs):
        """Convert into a GeoPandas GeoDataFrame.

        Parameters
        ----------
        *args
            Positional arguments (unused).
        **kwargs
            Keyword arguments (unused).

        Raises
        ------
        NotImplementedError
            Conversion of MultiData to GeoPandas is not implemented.
        """
        raise NotImplementedError("Conversion of MultiData to geopandas is not implemented")

    def to_geojson(self, *args, **kwargs) -> dict:
        """Convert into GeoJSON format.

        Parameters
        ----------
        *args
            Positional arguments (unused).
        **kwargs
            Keyword arguments (unused).

        Raises
        ------
        NotImplementedError
            Conversion of MultiData to GeoJSON is not implemented.
        """
        raise NotImplementedError("Conversion of MultiData to geojson is not implemented")

    def to_featurelist(self, *args, **kwargs):
        """Convert into a FeatureList.

        Parameters
        ----------
        *args
            Positional arguments (unused).
        **kwargs
            Keyword arguments (unused).

        Raises
        ------
        NotImplementedError
            Conversion of MultiData to FeatureList is not implemented.
        """
        raise NotImplementedError("Conversion of MultiData to featurelist is not implemented")

    def to_numpy(self, *args, **kwargs):
        """Convert into a NumPy array.

        Parameters
        ----------
        *args
            Positional arguments (unused).
        **kwargs
            Keyword arguments (unused).

        Raises
        ------
        NotImplementedError
            Conversion of MultiData to NumPy is not implemented.
        """
        raise NotImplementedError("Conversion of MultiData to numpy is not implemented")

    def to_array(self, *args, **kwargs):
        """Convert into an array of a given array-like type.

        Parameters
        ----------
        *args
            Positional arguments (unused).
        **kwargs
            Keyword arguments (unused).

        Raises
        ------
        NotImplementedError
            Conversion of MultiData to array is not implemented.
        """
        raise NotImplementedError("Conversion of MultiData to array is not implemented")
