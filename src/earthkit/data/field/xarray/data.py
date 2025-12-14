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

from earthkit.data.field.data import DataFieldPart

LOG = logging.getLogger(__name__)


class XArrayData(DataFieldPart):
    def __init__(self, owner, selection: Any) -> None:
        self.owner = owner
        self.selection = selection

    def get_values(self, dtype=None, copy=True):
        """Get the values stored in the field as an array."""

        values = self.selection.values
        if dtype is not None:
            values = values.astype(dtype, copy=copy)
        return values

    def __getstate__(self):
        return super().__getstate__()

    def __setstate__(self, state):
        super().__setstate__(state)
