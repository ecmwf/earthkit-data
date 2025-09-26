# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
from typing import Any

from earthkit.data.specs.data import SimpleData

LOG = logging.getLogger(__name__)


class XArrayData(SimpleData):
    def __init__(self, owner, selection: Any) -> None:
        self.owner = owner
        self.selection = selection

    def get_values(self, dtype=None, copy=True, index=None):
        """Get the values stored in the field as an array."""

        values = self.selection.values
        if index is not None:
            values = values[index]
        if dtype is not None:
            values = values.astype(dtype, copy=copy)
        return values
