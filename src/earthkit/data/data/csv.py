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


class CSVData(SourceData):
    """Represent data in the CSV format.

    CSV (Comma-Separated Values) is a simple file format used to store tabular data, such as
    a spreadsheet or database.

    CSV data can be converted with the following methods:

    - :py:func:`to_pandas`
    - :py:func:`to_xarray`

    """

    _TYPE_NAME = "CSV"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._PANDAS, self._XARRAY]

    def describe(self) -> Any:
        """Provide a description of the CSV data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the CSV data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="CSV file", path=self._reader.path, types=self.available_types)

    def __repr__(self) -> str:
        return f"CSVData(path={self._reader.path})"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_pandas(self, comment="#", pandas_read_csv_kwargs=None) -> "pandas.DataFrame":
        """Convert into a Pandas DataFrame.

        Parameters
        ----------
        comment: str
            Character that represents a comment line in the CSV file. This value is ignored if the
            comment character is defined in ``pandas_read_csv_kwargs``.
        pandas_read_csv_kwargs: dict, None, optional
            Keyword arguments passed to :func:`pandas.read_csv`. This is used for safe parsing of
            kwargs via intermediate methods.

        Returns
        -------
        :py:class:`pandas.DataFrame`
            A Pandas DataFrame containing the CSV data.
        """
        return self._reader.to_pandas(comment=comment, pandas_read_csv_kwargs=pandas_read_csv_kwargs)

    def to_xarray(self, pandas_read_csv_kwargs=None, **kwargs):
        """Convert into an Xarray dataset.

        First, the data is converted into a :py:class:`pandas.DataFrame` with :py:func:`pandas.read_csv`,
        then :py:meth:`pandas.DataFrame.to_xarray` is called to generate the xarray object.

        Parameters
        ----------
        pandas_read_csv_kwargs: dict, None, optional
            Keyword arguments passed to :py:func:`pandas.read_csv`.
        **kwargs
            Keyword arguments passed to :py:meth:`pandas.DataFrame.to_xarray`.

        Returns
        -------
        :py:class:`xarray.Dataset`
            An Xarray dataset containing the CSV data.
        """
        return self._reader.to_xarray(**kwargs)
