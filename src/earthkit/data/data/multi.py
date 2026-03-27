# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from . import SimpleData


class MultiData(SimpleData):
    def __init__(self, sources):
        """Initialize a MultiData object with multiple sources.

        Parameters
        ----------
        sources : list
            List of data sources to combine.
        """
        self.sources = sources
        self._source = sources
        # self.datas = [s._reader._to_data_object() for s in self.sources.sources]

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        types = set()
        for d in self.sources:
            types.update(d.available_types)
        return sorted(types)

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
        # return self.sources.to_fieldlist(*args, **kwargs)
        data = [s.to_data_object() for s in self.sources.sources]
        fs = [d.to_fieldlist(*args, **kwargs) for d in data]
        from earthkit.data.mergers import merge_by_class

        merged = merge_by_class(fs)
        if merged is not None:
            return merged.mutate()

        raise NotImplementedError("Conversion of MultiData to fieldlist is not implemented")

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
        return self.sources.to_xarray(*args, **kwargs)

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
        pass

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
