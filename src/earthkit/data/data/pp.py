# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .source import SourceData


class PPData(SourceData):
    _TYPE_NAME = "PP"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._XARRAY, self._FIELDLIST]

    def describe(self):
        """Provide a description of the PP data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the PP data.
        """
        pass

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
            A FieldList containing the PP data.
        """
        return self._reader.to_fieldlist(*args, **kwargs)

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
            An Xarray dataset containing the PP data.
        """
        return self._reader.to_xarray(*args, **kwargs)

    def _default_encoder(self):
        """Return the default encoder for PP data.

        Returns
        -------
        Encoder
            The default encoder object.
        """
        return self._source._default_encoder()
