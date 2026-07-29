# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .source import SourceData


class UnknownData(SourceData):
    _TYPE_NAME = "Unknown"

    @property
    def available_types(self):
        """list[str] or None: Return the list of available types that this data object can be converted to."""
        return None

    def describe(self):
        """Provide a description of the unknown data.

        Returns
        -------
        str
            A description of the unknown data including the file path.
        """
        return f"Unknown data from {self.path}"

    @property
    def path(self) -> str | list[str] | None:
        try:
            return self._reader.path
        except Exception:
            return None

    def __repr__(self) -> str:
        return f"UnknownData(path={self.path})"

    def _repr_html_(self) -> str:
        return f"<p>{self.describe()}</p>"
