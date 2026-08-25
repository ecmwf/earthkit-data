# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from typing import Any

from earthkit.data.field.component.time import create_time
from earthkit.data.field.handler.time import TimeFieldComponentHandler
from earthkit.data.readers.xarray.coordinates import extract_single_value, is_scalar


def from_xarray(owner, selection):
    _coords = {}

    for coord in owner.coordinates:
        if coord.is_time or coord.is_step:
            name = coord.name
            v = selection.coords.get(name, None)
            if v is not None and is_scalar(v):
                _coords[name] = coord.normalise(extract_single_value(v))

    return owner.time.spec(_coords)


class XArrayTimeHandler(TimeFieldComponentHandler):
    def __init__(self, owner: Any, selection: Any) -> None:
        self.owner = owner
        self.selection = selection

        part = create_time(from_xarray(owner, selection))
        super().__init__(part)
