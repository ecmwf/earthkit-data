# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,  # noqa: F401
)

from .source import SourceData

if TYPE_CHECKING:
    import pandas  # type: ignore[import]


class ODBData(SourceData):
    """
    Represents data in the ODB format.

    :xref:`odb` is a bespoke format developed at ECMWF to store observations.

    ODB data can be converted with the following methods:

    - :obj:`to_pandas`

    """

    _TYPE_NAME = "ODB"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._PANDAS]

    def describe(self) -> Any:
        """Provide a description of the ODB data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the ODB data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="ODB file", path=self._reader.path, types=self.available_types)

    def __repr__(self) -> str:
        return f"ODBData(path={self._reader.path})"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_pandas(self, odc_read_odb_kwargs=None) -> "pandas.DataFrame":
        """Convert into a pandas DataFrame.

        It is implemented by :xref:`pyodc`.

        Parameters
        ----------
        odc_read_odb_kwargs : dict, None,optional
            Keyword arguments to pass to :xref:`read_odb`. Please note if
            the ``single`` argument is not provided, it will be set to ``True``
            by default.

        Returns
        -------
        :py:class:`pandas.DataFrame`
            A pandas DataFrame created from the ODB data.

        """
        return self._reader.to_pandas(odc_read_odb_kwargs=odc_read_odb_kwargs)
