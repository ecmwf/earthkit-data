# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .source import SourceData


class StreamFeatureListData(SourceData):
    """Data object representing a stream of features.

    This class provides an interface for working with streaming data, allowing for
    efficient processing of large datasets without loading everything into memory at once.

    The stream can be converted to a FeatureList with :py:func:`to_featurelist` in two ways:

    - either by providing iteration through the stream of features once, which is more
      efficient for larger datasets and allows for processing data in chunks without consuming
      large amounts of memory. This is the default behaviour when calling :py:func:`to_featurelist`
      without any arguments, or with ``read_all=False``.
    - or by reading all features into memory, which may be suitable for smaller datasets or
      when random access is needed. This can be achieved by calling :py:func:`to_featurelist`
      with ``read_all=True``.
    """

    _TYPE_NAME = "StreamFeatureList"

    def __init__(self, source_or_reader, data_type=None):
        """Initialize a StreamFeatureListData object with a source or reader.

        Parameters
        ----------
        source_or_reader : Source|Reader
            The source or reader object that provides access to the stream data.
        data_type : str, optional
            The type of data in the stream.
        """
        super().__init__(source_or_reader)
        self._data_type = data_type

    def is_stream(self) -> bool:
        """Return True as this data object represents a stream."""
        return True

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._FEATURELIST]

    def describe(self):
        """Provide a description of the stream data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the stream data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="Stream of features", path=None, types=self.available_types)

    def __repr__(self) -> str:
        return "StreamFeatureListData"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_featurelist(self, read_all=False):
        """Convert into a FeatureList.

        Parameters
        ----------
        read_all : bool, optional
            If False (default), return a
            :py:class:`~earthkit.data.indexing.stream.StreamFeatureList` for streaming access.
            If True, read all features from the stream into memory and return a
            :py:class:`~earthkit.data.indexing.simple.SimpleFeatureList`.

        Returns
        -------
        FeatureList
            If ``read_all=False``, returns a
            :py:class:`~earthkit.data.indexing.stream.StreamFeatureList`, the that provides
            a single iteration through the stream of features.
            If ``read_all=True``, returns a
            :py:class:`~earthkit.data.indexing.simple.SimpleFeatureList` containing all features
            in memory read from the stream.
        """
        if read_all:
            from earthkit.data.featurelist.simple import SimpleFeatureList

            features = [f for f in self._reader]
            r = SimpleFeatureList(features)
            return r

        return self._reader


class StreamFieldListData(SourceData):
    """Data object representing a stream of fields.

    This class provides an interface for working with streaming data, allowing for
    efficient processing of large datasets without loading everything into memory at once.

    The stream can be converted to a FieldList with :py:func:`to_fieldlist` in two ways:

    - either by providing iteration through the stream of fields once, which is more
      efficient for larger datasets and allows for processing data in chunks without consuming
      large amounts of memory. This is the default behaviour when calling :py:func:`to_fieldlist`
      without any arguments, or with ``read_all=False``.
    - or by reading all fields into memory, which may be suitable for smaller datasets or
      when random access is needed. This can be achieved by calling :py:func:`to_fieldlist`
      with ``read_all=True``.
    """

    _TYPE_NAME = "StreamFieldList"

    def is_stream(self) -> bool:
        """Return True as this data object represents a stream."""
        return True

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._FIELDLIST]

    def describe(self):
        """Provide a description of the stream data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the stream data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="Stream of fields", path=None, types=self.available_types)

    def __repr__(self) -> str:
        return "StreamFieldListData"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_fieldlist(self, read_all=False):
        """Convert into a FieldList.

        Parameters
        ----------
        read_all : bool, optional
            If False (default), return a
            :py:class:`~earthkit.data.indexing.stream.StreamFieldList` for streaming access.
            If True, read all fields from the stream into memory and return a
            :py:class:`~earthkit.data.indexing.simple.SimpleFieldList`.

        Returns
        -------
        FieldList
            If ``read_all=False``, returns a
            :py:class:`~earthkit.data.indexing.stream.StreamFieldList`, the that provides
            a single iteration through the stream of fields.
            If ``read_all=True``, returns a
            :py:class:`~earthkit.data.indexing.simple.SimpleFieldList` containing all fields
            in memory read from the stream.
        """
        if read_all:
            from earthkit.data.indexing.simple import SimpleFieldList

            fields = [f for f in self._reader]
            r = SimpleFieldList(fields)
            return r

        return self._reader
