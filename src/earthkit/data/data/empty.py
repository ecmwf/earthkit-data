# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from typing import Any

from . import SimpleData


class EmptyData(SimpleData):
    _TYPE_NAME = "Empty"

    """
    A class representing an empty data object.
    This class is used to represent a data object that contains no data.
    """

    @property
    def available_types(self):
        """list[str] or None: Return the list of available types that this data object can be converted to."""
        return [self._FIELDLIST]

    def describe(self) -> Any:
        """Provide a description of empty data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the empty data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="Empty data", path=self.path, types=self.available_types)

    def __repr__(self) -> str:
        return f"EmptyData(path={self.path})"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_fieldlist(self, *args, **kwargs):
        """Convert into a FieldList.

        Parameters
        ----------
        *args
            Positional arguments (unused).
        **kwargs
            Keyword arguments (unused).

        Returns
        -------
        :py:class:`earthkit.data.indexing.empty.EmptyFieldList`
            An empty FieldList object.
        """
        from earthkit.data.indexing.empty import EmptyFieldList

        return EmptyFieldList()
