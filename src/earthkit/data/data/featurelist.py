# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from typing import Any

from .source import SourceData


class FeatureListData(SourceData):
    _TYPE_NAME = "FeatureList"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        r = [self._FEATURELIST]
        if hasattr(self._source, "to_xarray"):
            r.append(self._XARRAY)
        return r

    def describe(self) -> Any:
        """Provide a description of FeatureList data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the FeatureList data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="FeatureList", path=self.path, types=self.available_types)

    @property
    def path(self) -> str | list[str] | None:
        try:
            return self._reader.path
        except Exception:
            return None

    def __repr__(self) -> str:
        return f"FeatureListData(path={self.path})"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_featurelist(self, *args, **kwargs):
        """Convert into a FeatureList.

        Parameters
        ----------
        *args
            Positional arguments (unused).
        **kwargs
            Keyword arguments (unused).

        Returns
        -------
        FeatureList
            The source FeatureList object.
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
            An Xarray dataset containing the FeatureList data.

        Raises
        ------
        NotImplementedError
            If conversion to Xarray is not supported.
        """
        if hasattr(self._source, "to_xarray"):
            return self._source.to_xarray(*args, **kwargs)
        self._conversion_not_implemented()
