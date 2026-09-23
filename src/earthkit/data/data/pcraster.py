# (C) Copyright 2026 ECMWF.
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
    pass  # type: ignore[import]


class PCRasterData(SourceData):
    """Represent data in the PCRaster format.

    PCRaster data can be converted with the following methods:

    - :py:func:`to_numpy`

    """

    _TYPE_NAME = "PCRaster"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._NUMPY]

    def describe(self) -> Any:
        """Provide a description of the PCRaster data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the PCRaster data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="PCRaster file", path=self.path, types=self.available_types)

    @property
    def path(self) -> str | list[str] | None:
        try:
            return self._reader.path
        except Exception:
            return None

    def __repr__(self) -> str:
        return f"PCRasterData(path={self.path})"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_numpy(self, missing_to_nan=True):
        """Convert into an numpy array.

        Parameters
        ----------
        mask: bool, optional
            Whether or not to represent missing values as nans.

        Returns
        -------
        :py:class:`numpy.array`
            A numpy array containing the PCRaster data.
        """
        return self._reader.to_numpy(missing_to_nan=missing_to_nan)
