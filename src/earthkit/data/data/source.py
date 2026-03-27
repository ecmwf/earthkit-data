# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from . import SimpleData


class SourceData(SimpleData):
    def __init__(self, source_or_reader):
        """Initialize a SourceData object with a source or reader.

        Parameters
        ----------
        source_or_reader : Source or Reader
            The source or reader object that provides access to the data.

        Raises
        ------
        TypeError
            If source_or_reader is not a Source or Reader.
        ValueError
            If no valid Reader can be extracted from source_or_reader.
        """
        from earthkit.data.readers import Reader
        from earthkit.data.sources import Source

        self._source = None
        self._reader = None

        if isinstance(source_or_reader, Source):
            self._source = source_or_reader
            if isinstance(source_or_reader, Reader):
                self._reader = source_or_reader
            elif hasattr(source_or_reader, "_reader") and isinstance(source_or_reader._reader, Reader):
                self._reader = source_or_reader._reader
            else:
                self._reader = self._source
        elif isinstance(source_or_reader, Reader):
            self._reader = source_or_reader
            self._source = source_or_reader.source
        else:
            raise TypeError(f"Invalid type={type(source_or_reader)}. Must be a Source or Reader")

        if self._reader is None:
            raise ValueError(f"SourceData no Source or Reader found in {source_or_reader=}")

    def _default_encoder(self):
        """Return the default encoder for this data object.

        Returns
        -------
        Encoder
            The default encoder object.

        Raises
        ------
        NotImplementedError
            If no default encoder is found.
        """
        if hasattr(self._source, "_default_encoder"):
            return self._source._default_encoder()
        elif hasattr(self._reader, "_default_encoder"):
            return self._reader._default_encoder()
        raise NotImplementedError("No default encoder found for this data object")

    def to_target(self, target, *args, **kwargs):
        """Write the data to a target.

        Parameters
        ----------
        target: str
            The target to write to. See :py:func:`to_target` for more details on the supported targets.
        *args
            Positional arguments to pass to the :func:`to_target`
        **kwargs
            Keyword arguments to pass to the :func:`to_target`. Cannot specify ``data`` in kwargs.

        See Also
        --------
        :py:func:`to_target`
        """
        from earthkit.data.targets import to_target

        to_target(target, *args, data=self._source, **kwargs)


class DefaultSourceData(SourceData):
    def __init__(self, source_or_reader):
        """Initialize a DefaultSourceData object with a source or reader.

        Parameters
        ----------
        source_or_reader : Source or Reader
            The source or reader object that provides access to the data.
        """
        super().__init__(source_or_reader)
        self._types = []
        for name in [
            self._XARRAY,
            self._FIELDLIST,
            self._PANDAS,
            self._GEOPANDAS,
            self._FEATURELIST,
            self._NUMPY,
            self._ARRAY,
        ]:
            if hasattr(self._reader, f"to_{name}"):
                self._types.append(name)

    def describe(self):
        """Provide a description of the data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the data.
        """
        pass

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return self._types

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
            A FieldList containing the data.

        Raises
        ------
        NotImplementedError
            If conversion to FieldList is not supported.
        """
        if self._FIELDLIST in self._types:
            return getattr(self._reader, f"to_{self._FIELDLIST}")(*args, **kwargs)
        else:
            self._conversion_not_implemented()

    def to_xarray(self, *args, **kwargs):
        """Convert into an Xarray dataset.

        Parameters
        ----------
        *args
            Positional arguments to pass to the reader's to_xarray method.
        **kwargs
            Keyword arguments to pass to the reader's to_xarray method.

        Returns
        -------
        :py:class:`xarray.Dataset`
            An Xarray dataset containing the data.

        Raises
        ------
        NotImplementedError
            If conversion to Xarray is not supported.
        """
        if self._XARRAY in self._types:
            return getattr(self._reader, f"to_{self._XARRAY}")(*args, **kwargs)
        else:
            self._conversion_not_implemented()

    def to_pandas(self, *args, **kwargs):
        """Convert into a Pandas DataFrame.

        Parameters
        ----------
        *args
            Positional arguments to pass to the reader's to_pandas method.
        **kwargs
            Keyword arguments to pass to the reader's to_pandas method.

        Returns
        -------
        :py:class:`pandas.DataFrame`
            A Pandas DataFrame containing the data.

        Raises
        ------
        NotImplementedError
            If conversion to Pandas is not supported.
        """
        if self._PANDAS in self._types:
            return getattr(self._reader, f"to_{self._PANDAS}")(*args, **kwargs)
        else:
            self._conversion_not_implemented()

    def to_geopandas(self, **kwargs):
        """Convert into a GeoPandas GeoDataFrame.

        Parameters
        ----------
        **kwargs
            Keyword arguments to pass to the reader's to_geopandas method.

        Returns
        -------
        :py:class:`geopandas.GeoDataFrame`
            A GeoPandas GeoDataFrame containing the data.

        Raises
        ------
        NotImplementedError
            If conversion to GeoPandas is not supported.
        """
        if self._GEOPANDAS in self._types:
            return getattr(self._reader, f"to_{self._GEOPANDAS}")(**kwargs)
        else:
            self._conversion_not_implemented()

    def to_featurelist(self, *args, **kwargs):
        """Convert into a FeatureList.

        Parameters
        ----------
        *args
            Positional arguments to pass to the reader's to_featurelist method.
        **kwargs
            Keyword arguments to pass to the reader's to_featurelist method.

        Returns
        -------
        FeatureList
            A FeatureList containing the data.

        Raises
        ------
        NotImplementedError
            If conversion to FeatureList is not supported.
        """
        if self._FEATURELIST in self._types:
            return getattr(self._reader, f"to_{self._FEATURELIST}")(*args, **kwargs)
        else:
            self._conversion_not_implemented()

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
            A NumPy array containing the data.

        Raises
        ------
        NotImplementedError
            If conversion to NumPy is not supported.
        """
        if self._NUMPY in self._types:
            return getattr(self._reader, f"to_{self._NUMPY}")(*args, **kwargs)
        else:
            self._conversion_not_implemented()

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
            An array containing the data.

        Raises
        ------
        NotImplementedError
            If conversion to array is not supported.
        """
        if self._ARRAY in self._types:
            return getattr(self._reader, f"to_{self._ARRAY}")(*args, **kwargs)
        else:
            self._conversion_not_implemented()
