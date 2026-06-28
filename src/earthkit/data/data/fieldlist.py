# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .source import SourceData


class FieldListData(SourceData):
    _TYPE_NAME = "FieldList"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        r = [self._FIELDLIST]
        if hasattr(self._source, "to_xarray"):
            r.append(self._XARRAY)
        return r

    def describe(self):
        """Provide a description of the FieldList data.

        Returns
        -------
        str
            A description of the FieldList data including the number of fields.
        """
        return f"FieldList data with {len(self._fieldlist)} fields"

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
        :py:class:`earthkit.data.core.fieldlist.FieldList`
            The source FieldList object.
        """
        return self._source

    def to_xarray(self, *args, **kwargs):
        """Convert into an Xarray dataset.

        Parameters
        ----------
        *args
            Positional arguments to pass to the source's to_xarray method.
        **kwargs
            Keyword arguments to pass to the source's to_xarray method.

        Returns
        -------
        :py:class:`xarray.Dataset`
            An Xarray dataset containing the FieldList data.

        Raises
        ------
        NotImplementedError
            If conversion to Xarray is not supported.
        """
        if hasattr(self._source, "to_xarray"):
            return self._source.to_xarray(*args, **kwargs)
        self._conversion_not_implemented()
