# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from typing import Any

from earthkit.data.field.component.ensemble import Ensemble
from earthkit.data.field.handler.ensemble import EnsembleFieldComponentHandler


def get_member(coord, selection):
    if coord is None:
        return None
    name = coord.name

    v = selection[name].values
    if len(v.shape) == 0:
        return v.item()
    else:
        return v[0]


def from_xarray(owner, selection):
    from earthkit.data.loaders.xarray.coordinates import EnsembleCoordinate

    coord = None
    for c in owner.coordinates:
        if isinstance(c, EnsembleCoordinate):
            coord = c

    member = get_member(coord, selection)
    return dict(member=member)


class XArrayEnsemble(EnsembleFieldComponentHandler):
    def __init__(self, owner: Any, selection: Any) -> None:
        self.owner = owner
        self.selection = selection

        part = Ensemble.from_dict(from_xarray(owner, selection))
        super().__init__(part)
