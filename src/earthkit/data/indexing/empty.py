# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from typing import Any


class EmptyFieldList:
    """A class to represent an empty list of fields."""

    def __len__(self) -> int:
        """Return the length of the field list."""
        return 0

    def __getitem__(self, i: int) -> Any:
        """Raise an IndexError when trying to access an item.

        Returns
        -------
        Any
            This method does not return anything as it raises an IndexError.

        Raises
        ------
        IndexError
            Always raised to indicate that the list is empty.

        Args
        ----
        i : int
            Index of the item to access.
        """
        raise IndexError(i)

    def __repr__(self) -> str:
        """Return a string representation of the EmptyFieldList."""
        return "EmptyFieldList()"
