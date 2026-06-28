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
    TypeAlias,
)

from .source import SourceData

if TYPE_CHECKING:
    import numpy  # type: ignore[import]
    import pandas  # type: ignore[import]
    import xarray  # type: ignore[import]

    from earthkit.data.core.fieldlist import FieldList  # type: ignore[import]

ArrayLike: TypeAlias = Any


class GribData(SourceData):
    """
    Represent GRIB data.

    GRIB is the WMO's format for binary gridded data consisting of GRIB messages. The earthkit-data
    GRIB interface is based on :xref:`eccodes` and can handle both GRIB `edition 1
    <https://community.wmo.int/activity-areas/wmo-codes/manual-codes/grib-edition-1>`_ and
    `edition 2 <https://library.wmo.int/index.php?lvl=notice_display&id=10684>`_.

    This class provides methods to convert GRIB data into various formats such as FieldLists, Xarray datasets,
    Pandas DataFrames, and NumPy arrays.

    GRIB data can be converted with the following methods:

    - :py:func:`to_fieldlist`
    - :py:func:`to_xarray`
    - :py:func:`to_pandas`
    - :py:func:`to_numpy`
    - :py:func:`to_array`
    """

    _TYPE_NAME = "GRIB"

    @property
    def available_types(self) -> list[str]:
        return [self._FIELDLIST, self._PANDAS, self._XARRAY, self._NUMPY, self._ARRAY]

    def describe(self) -> Any:
        """Provide a description of the GRIB data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the GRIB data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="GRIB file", path=self._reader.path, types=self.available_types)

    def __repr__(self) -> str:
        return f"GribData(path={self._reader.path})"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_fieldlist(self) -> "FieldList":
        """Convert into a FieldList.

        Returns
        -------
        :py:class:`earthkit.data.core.fieldlist.FieldList`
            A FieldList containing the GRIB data.
        """
        return self._reader.to_fieldlist()

    def to_xarray(self, **kwargs) -> "xarray.Dataset":
        """Convert into an Xarray dataset.

        It is done by first converting the GRIB data into a FieldList and then converting
        the FieldList into an Xarray dataset by calling the FieldList's
        :py:func:`to_xarray <earthkit.data.readers.grib.xarray.XarrayMixIn.to_xarray>`
        method.

        Parameters
        ----------
        **kwargs
            Keyword arguments to pass to
            :py:func:`to_xarray <earthkit.data.readers.grib.xarray.XarrayMixIn.to_xarray>`

        Returns
        -------
        :py:class:`xarray.Dataset`
             An Xarray dataset containing the GRIB data.

        See Also
        --------
        :py:func:`to_xarray <earthkit.data.readers.grib.xarray.XarrayMixIn.to_xarray>`
        """
        return self._reader.to_xarray(**kwargs)

    def to_pandas(self, **kwargs) -> "pandas.DataFrame":
        """Convert into a Pandas DataFrame.

        It is done by first converting the GRIB data into a fieldList and then converting
        the fieldList into a Pandas DataFrame by calling the fieldlist's
        :py:func:`to_pandas <earthkit.data.readers.grib.pandas.PandasMixIn.to_pandas>` method.

        Parameters
        ----------
        **kwargs
            Keyword arguments to pass to
            :py:func:`to_pandas <earthkit.data.readers.grib.pandas.PandasMixIn.to_pandas>`.

        Returns
        -------
        :py:class:`pandas.DataFrame`
             A Pandas DataFrame containing the GRIB data.

        See Also
        --------
        :py:func:`to_pandas <earthkit.data.readers.grib.pandas.PandasMixIn.to_pandas>`
        """
        return self._reader.to_pandas(**kwargs)

    def to_numpy(self, *args, **kwargs) -> "numpy.ndarray":
        """Convert into a NumPy array.

        It is done by fist converting the GRIB data into a fieldlist and calling the fieldlist's
        :py:func:`to_numpy <earthkit.data.core.fieldlist.FieldList.to_numpy>` method.

        Parameters
        ----------
        *args
            Positional arguments to pass to
            :py:func:`to_numpy <earthkit.data.core.fieldlist.FieldList.to_numpy>`
        **kwargs
            Keyword arguments to pass to
            :py:func:`to_numpy <earthkit.data.core.fieldlist.FieldList.to_numpy>`

        Returns
        -------
        numpy.ndarray
             A NumPy array containing the GRIB data.

        See Also
        --------
        :py:func:`to_numpy <earthkit.data.core.fieldlist.FieldList.to_numpy>`
        """
        return self._reader.to_numpy(*args, **kwargs)

    def to_array(self, *args, **kwargs) -> ArrayLike:
        """Convert into an array of a given array-like type.

        It is done by first converting the GRIB data into a fieldlist and calling the fieldlist's
        :py:func:`to_array <earthkit.data.core.fieldlist.FieldList.to_array>` method.

        Parameters
        ----------
        *args
            Positional arguments to pass to the fieldlist's
            :py:func:`to_array <earthkit.data.core.fieldlist.FieldList.to_array>` method.
        **kwargs
            Keyword arguments to pass to the fieldlist's
            :py:func:`to_array <earthkit.data.core.fieldlist.FieldList.to_array>` method.

        Returns
        -------
        ArrayLike
             An array containing the GRIB data.

        See Also
        --------
        :py:func:`to_array <earthkit.data.core.fieldlist.FieldList.to_array>`
        """
        return self._reader.to_array(*args, **kwargs)
