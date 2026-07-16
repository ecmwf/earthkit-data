# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from __future__ import annotations

from typing import Any  # noqa: F401

from .source import SourceData


class TextData(SourceData):
    """Represents text data read from a source.

    Text data cannot be converted into any other type.
    """

    _TYPE_NAME = "Text"

    @property
    def available_types(self):
        """list[str] or None: Return the list of available types that this data object can be converted to."""
        return None

    def describe(self) -> Any:
        """Provide a description of the Text data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the Text data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="Text file", path=self._reader.path, types=self.available_types)

    def __repr__(self) -> str:
        return f"TextData(path={self._reader.path})"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()
