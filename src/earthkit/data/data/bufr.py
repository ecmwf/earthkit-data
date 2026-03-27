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

    from earthkit.data.readers.bufr.file import BUFRList


class BUFRData(SourceData):
    """
    Represent BUFR data.

    BUFR (Binary Universal Form for Representation of meteorological data) is a binary data format
    maintained by WMO. The earthkit-data interface supports both BUFR `edition 3
    <https://community.wmo.int/en/activity-areas/wmo-codes/manual-codes/bufr-edition-3-and-crex-edition-1>`_
    and `edition 4 <https://library.wmo.int/index.php?lvl=notice_display&id=10684>`_.

    BUFR data can be converted with the following methods:

    - :obj:`to_pandas`
    - :obj:`to_featurelist`

    """

    _TYPE_NAME = "BUFR"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._PANDAS, self._FEATURELIST]

    def describe(self) -> Any:
        """Provide a description of the BUFR data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the BUFR data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="BUFR file", path=self._reader.path, types=self.available_types)

    def __repr__(self) -> str:
        return f"BUFRData(path={self._reader.path})"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_pandas(self, **kwargs) -> "pandas.DataFrame":
        """Convert into a pandas DataFrame.

        It is done by first converting the BUFR data into a featurelist and calling
        the featurelist's
        :py:func:`to_pandas <earthkit.data.readers.bufr.file.BUFRList.to_pandas>` method.

        Parameters
        ----------
        **kwargs
            Keyword arguments to pass to
            :py:func:`to_pandas <earthkit.data.readers.bufr.file.BUFRList.to_pandas>`

        Returns
        -------
        :py:class:`pandas.DataFrame`
            A pandas DataFrame created from the BUFR data.

        See Also
        --------
        :py:func:`to_featurelist <earthkit.data.readers.bufr.file.BUFRList.to_featurelist>`

        Examples
        --------
        - :ref:`/examples/bufr/bufr_temp.ipynb`
        - :ref:`/examples/bufr/bufr_synop.ipynb`

        """
        return self._reader.to_pandas(**kwargs)

    def to_featurelist(self) -> "BUFRList":
        """Convert into a BUFR featurelist.

        Returns
        -------
        earthkit.data.readers.bufr.file.BUFRList
            A BUFR featurelist containing the BUFR data.
        """
        return self._reader.to_featurelist()
