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
    _TYPE_NAME = "StreamFeatureList"

    def __init__(self, source_or_reader, data_type=None):
        """Initialize a StreamFeatureListData object with a source or reader.

        Parameters
        ----------
        source_or_reader : Source or Reader
            The source or reader object that provides access to the stream data.
        data_type : str, optional
            The type of data in the stream.
        """
        super().__init__(source_or_reader)
        self._data_type = data_type

    def is_stream(self):
        """Return True indicating this data object represents a stream.

        Returns
        -------
        bool
            Always returns True.
        """
        return True

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return ["featurelist"]

    def describe(self):
        """Provide a description of the stream data.

        Returns
        -------
        str
            A description of the stream data including the file path.
        """
        return f"Stream data from {self._reader.path}"

    def to_featurelist(self):
        """Convert into a FeatureList.

        Returns
        -------
        FeatureList
            The reader object that provides streaming access to features.
        """
        return self._reader


class StreamFieldListData(SourceData):
    _TYPE_NAME = "StreamFieldList"

    def is_stream(self):
        """Return True indicating this data object represents a stream.

        Returns
        -------
        bool
            Always returns True.
        """
        return True

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._FIELDLIST]

    def describe(self):
        """Provide a description of the stream data.

        Returns
        -------
        str
            A description of the stream data including the file path.
        """
        return f"Stream data from {self._reader.path}"

    def to_fieldlist(self, *args, read_all=False, **kwargs):
        """Convert into a FieldList.

        Parameters
        ----------
        *args
            Positional arguments (unused).
        read_all : bool, optional
            If True, read all fields from the stream into a SimpleFieldList.
            If False (default), return the reader for streaming access.
        **kwargs
            Keyword arguments (unused).

        Returns
        -------
        :py:class:`earthkit.data.core.fieldlist.FieldList`
            A FieldList object containing the stream data.
        """
        if read_all:
            from earthkit.data.indexing.simple import SimpleFieldList

            fields = [f for f in self._reader]
            r = SimpleFieldList(fields)
            return r

        return self._reader

    def _repr_html_(self):
        from earthkit.data.utils.summary import make_data_repr_html

        return make_data_repr_html(title="Stream of fields", path=None, types=self.available_types)
