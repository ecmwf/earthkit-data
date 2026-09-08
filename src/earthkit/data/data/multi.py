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

import deprecation

from . import Data, SimpleData

if TYPE_CHECKING:
    import pandas  # type: ignore[import]
    import xarray  # type: ignore[import]

    from earthkit.data.core.fieldlist import FieldList


class MultiData(SimpleData):
    """Represent multiple sources that cannot be reduced to a single, type-specific ``Data`` object.

    When :func:`earthkit.data.from_source` combines multiple inputs (e.g. a list of files), it first
    attempts to mutate them into a single, type-specific :class:`~earthkit.data.data.Data` object (e.g.
    ``GribData`` for a set of GRIB files) -- see :ref:`mergers` for how this merging works. A
    ``MultiData`` is returned instead whenever that is not possible, which happens in two situations:

    - the inputs are of mixed types and cannot be merged into a single typed object (e.g. one GRIB file
      and one NetCDF file);
    - the inputs are all of the same type, but that type does not support merging multiple inputs into
      one object (e.g. ``CSVData`` wraps a single reader per file, so multiple CSV files always yield a
      ``MultiData``).

    A ``MultiData`` wraps the underlying :class:`~earthkit.data.sources.multi.MultiSource` (see
    :obj:`_source`) and, for each conversion, builds the corresponding ``Data`` object of every
    sub-source (see :obj:`_data_objects`) and merges those, rather than merging the raw sources directly.
    """

    _TYPE_NAME = "Multi"

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
            for d in self._data_objects():
                types.update(d.available_types)
            return sorted(types)
        except Exception:
            pass

        return list()

    @property
    @deprecation.deprecated(
        deprecated_in="1.1.0",
        removed_in=None,
        details=(
            "The 'sources' property is deprecated and will be removed in a future release. "
            "Access to the underlying sources in MultiData is no longer part of the public API."
        ),
    )
    def sources(self) -> Any:
        """Deprecated. Access to the underlying sources is no longer part of the public API."""
        return self._sources_legacy

    def _data_objects(self, match: str | None = None):
        res = []
        for s in self._source.sources:
            if not isinstance(s, (Data)):
                d = s.to_data_object()
            else:
                d = s

            if isinstance(d, Data):
                if match is None or match in s.available_types:
                    res.append(d)
            # else:
            #     d = s.to_data_object()
            #     if match is None or match in d.available_types:
            #         res.append(d)

        return res

    def _data_sources(self, match: str | None = None):
        res = []
        for s in self._source.sources:
            if isinstance(s, Data):
                d = s
            else:
                d = s.to_data_object()

            if isinstance(d, Data):
                if match is None or match in d.available_types:
                    res.append(s)

            else:
                if match is None:
                    res.append(s)
            # else:
            #     d = s.to_data_object()
            #     if match is None or match in d.available_types:
            #         res.append(d)

        return res

    def describe(self) -> Any:
        """Provide a description of the MultiData.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the MultiData.
        """
        pass

    @property
    def path(self) -> str | list[str] | None:
        r = []
        for s in self._data_objects():
            try:
                p = s.path
                r.append(p)
            except Exception:
                pass

        return r

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
            raise ValueError(
                "Cannot convert this MultiData object to a FieldList. None of the objects support FieldList conversion."
            )
        sources = self._data_sources(match="fieldlist")
        if not sources:
            raise ValueError("No suitable sources available for conversion.")

        print("Sources for fieldlist conversion:", sources)
        for s in sources:
            print("Source:", s)

        print("merger:", self._source.merger)

        from earthkit.data.mergers import make_merger

        merged = make_merger(self._source.merger, sources).to_fieldlist(**kwargs)
        if merged is not None:
            return merged.mutate()

        raise ValueError("Cannot convert this MultiData object to a fieldlist")

        # fl = []
        # for d in data:
        #     if "fieldlist" not in d.available_types:
        #         continue
        #     fl.append(d.to_fieldlist(*args, **kwargs))

        # print("fl", fl)

        # # fs = [d.to_fieldlist(*args, **kwargs) for d in data]
        # from earthkit.data.mergers import merge_by_class

        # merged = merge_by_class(fl)
        # if merged is not None:
        #     return merged.mutate()

        # raise NotImplementedError("Cannot convert this MultiData object to a fieldlist")

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
        if "xarray" not in self.available_types:
            raise ValueError(
                "Cannot convert this MultiData object to Xarray. None of the objects support Xarray conversion."
            )

        sources = self._data_sources(match="xarray")
        if not sources:
            raise ValueError("No suitable sources available for conversion.")

        if xarray_open_mfdataset_kwargs:
            options = dict(xarray_open_mfdataset_kwargs=xarray_open_mfdataset_kwargs)
        else:
            options = dict(kwargs)

        from earthkit.data.mergers import make_merger

        merger = self._source.merger
        if merger and options:
            import warnings

            warnings.warn(
                "There seems to be a merger defined for the source, but additional options were provided. "
                "These options might be ignored."
            )

        return make_merger(merger, sources).to_xarray(**options)

    def to_pandas(self, comment="#", pandas_read_csv_kwargs=None) -> "pandas.DataFrame":
        """Convert into a Pandas DataFrame.

        Parameterss
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
        data = self._data_objects()

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
