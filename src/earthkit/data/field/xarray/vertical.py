# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


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
    if coord is None:
        return None
    return coord.levtype


def from_xarray(owner, selection):
    from earthkit.data.new_field.xarray.coordinates import LevelCoordinate

    coord = None
    for c in owner.coordinates:
        if isinstance(c, LevelCoordinate):
            coord = c

    level = get_level(coord, selection)
    level_type = get_level_type(coord)
    return dict(level=level, level_type=level_type)


# class XArrayVertical(Vertical):
#     """A class to represent a vertical coordinate in an xarray dataset."""

#     def __init__(self, owner: Any, selection: Any) -> None:
#         """Create a new XArrayVertical object.

#         Parameters
#         ----------
#         owner : Variable
#             The variable that owns this field.
#         selection : XArrayDataArray
#             A 2D sub-selection of the variable's underlying array.
#             This is actually a nD object, but the first dimensions are always 1.
#             The other two dimensions are latitude and longitude.
#         """
#         from earthkit.data.new_field.xarray.coordinates import LevelCoordinate

#         self.owner = owner
#         self.selection = selection
#         self.coord = None
#         for c in owner.coordinates:
#             if isinstance(c, LevelCoordinate):
#                 self.coord = c

#     @property
#     def level(self) -> str:
#         """Return the level of the vertical coordinate."""
#         if self.coord is None:
#             return None
#         name = self.coord.name

#         v = self.selection[name].values
#         if len(v.shape) == 0:
#             return v.item()
#         else:
#             return v[0]

#     @property
#     def level_type(self) -> str:
#         """Return the type of the vertical coordinate."""
#         if self.coord is None:
#             return None
#         return self.coord.levtype
