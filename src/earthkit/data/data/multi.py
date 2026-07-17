# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.utils.decorators import experimental

from . import Data, SimpleData


class MultiData(SimpleData):
    _TYPE_NAME = "Multi"

    def __init__(self, sources):
        """Initialize a MultiData object with multiple sources.

        Parameters
        ----------
        sources : MultiSource
            A MultiSource object containing multiple data sources.
        """
        self._sources_legacy = sources
        self._source = sources

    @property
    def available_types(self):
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
    def sources(self):
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

    def describe(self):
        """Provide a description of the MultiData.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the MultiData.
        """
        pass

    def to_fieldlist(self, *args, **kwargs):
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

        data = self._datas()
        fs = [d.to_fieldlist(*args, **kwargs) for d in data]
        from earthkit.data.mergers import merge_by_class

        merged = merge_by_class(fs)
        if merged is not None:
            return merged.mutate()

        raise NotImplementedError("Cannot convert this MultiData object to a fieldlist")

    def to_xarray(self, *args, **kwargs):
        """Convert into an Xarray dataset.

        Parameters
        ----------
        *args
            Positional arguments to pass to the sources' to_xarray method.
        **kwargs
            Keyword arguments to pass to the sources' to_xarray method.

        Returns
        -------
        :py:class:`xarray.Dataset`
            An Xarray dataset containing data from all sources.
        """
        if "xarray" not in self.available_types:
            raise NotImplementedError("Cannot convert this MultiData object to xarray")

        data = self._datas()

        from earthkit.data.mergers import make_merger

        return make_merger(None, data).to_xarray(*args, **kwargs)

    def to_pandas(self, *args, **kwargs):
        """Convert into a Pandas DataFrame.

        Parameters
        ----------
        *args
            Positional arguments (unused).
        **kwargs
            Keyword arguments (unused).

        Returns
        -------
        :py:class:`pandas.DataFrame`
            A Pandas DataFrame containing data from all sources.
        """
        if "pandas" not in self.available_types:
            raise NotImplementedError("Cannot convert this MultiData object to pandas")

        data = self._datas()

        from earthkit.data.mergers import make_merger

        return make_merger(None, data).to_pandas(*args, **kwargs)

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

    def to_geojson(self, *args, **kwargs):
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
