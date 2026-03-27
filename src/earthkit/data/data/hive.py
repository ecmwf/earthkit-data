# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from .source import SourceData


class HiveFilePatternData(SourceData):
    """Represent hive file pattern data.

    This data is generated with the :ref:`data-sources-file-pattern` source
    when ``hive_partitioning==True`` in
    :ref:`from-source() <data-sources-file-pattern>`.

    Hive file pattern data only allows conversion into a fieldlist with the following method:

    - :py:func:`to_fieldlist`

    """

    _TYPE_NAME = "HiveFilePattern"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._FIELDLIST]

    def describe(self):
        """Provide a description of the hive file pattern data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the ODB data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="hive file pattern", types=self.available_types)

    def __repr__(self) -> str:
        return f"HiveFilePatternData(pattern={self._source.pattern}, params={self._source.scanner.params})"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_fieldlist(self, *args, **kwargs):
        """Convert into a FieldList.

        The conversion is done in two steps. First, a filesystem scan is performed to find all
        the files matching the filter conditions specified in ``*args`` and ``**kwargs``. For this
        check only the keys appearing in the hive pattern definition are used and only the file
        paths are inspected, the files themselves are not opened. The matching files
        are loaded into a FieldList. Second, if there are other keys in the filter conditions
        that are not part of the hive pattern definition, then
        :py:func:`earthkit.data.core.fieldlist.FieldList.sel` is called on the FieldList
        with these keys as filter conditions. This produces the final FieldList.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the filter condition as dict.
        **kwargs: dict, optional
            Other keyword arguments specifying the filter conditions.

        Returns
        -------
        :py:class:`earthkit.data.core.fieldlist.FieldList`
            A FieldList matching the filter conditions.

        See Also
        --------
        :ref:`Using hive partitioning <file-pattern-hive-partitioning>`
        """
        return self._source.to_fieldlist(*args, **kwargs)
