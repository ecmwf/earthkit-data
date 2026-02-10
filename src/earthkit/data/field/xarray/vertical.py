# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from typing import Any

from earthkit.data.field.component.level_type import LevelTypes
from earthkit.data.field.component.vertical import create_vertical
from earthkit.data.field.vertical import VerticalFieldComponentHandler


class XarrayLevelType:
    def __init__(self, keys, spec_type):
        self.keys = keys if isinstance(keys, (list, tuple)) else [keys]
        self.spec_type = spec_type


_TYPES = [
    XarrayLevelType("pl", LevelTypes.PRESSURE),
    XarrayLevelType("ml", LevelTypes.MODEL),
    XarrayLevelType("sfc", LevelTypes.SURFACE),
]

_XR_TYPES = dict()
for t in _TYPES:
    for k in t.keys if isinstance(t.keys, (list, tuple)) else [t.keys]:
        _XR_TYPES[k] = t


def get_level(coord, selection):
    if coord is None:
        return None
    name = coord.name

    v = selection[name].values
    if len(v.shape) == 0:
        return v.item()
    else:
        return v[0]


def get_level_type(coord):
    if coord is not None:
        t = _XR_TYPES.get(coord.levtype, None)
        if t is not None:
            return t.spec_type

    return LevelTypes.UNKNOWN


def from_xarray(owner, selection):
    from earthkit.data.loaders.xarray.coordinates import LevelCoordinate

    coord = None
    for c in owner.coordinates:
        if isinstance(c, LevelCoordinate):
            coord = c

    level = get_level(coord, selection)
    level_type = get_level_type(coord)

    return dict(level=level, type=level_type)


class XArrayVertical(VerticalFieldComponentHandler):
    def __init__(self, owner: Any, selection: Any) -> None:
        self.owner = owner
        self.selection = selection

        component = create_vertical(from_xarray(owner, selection))
        super().__init__(component)
