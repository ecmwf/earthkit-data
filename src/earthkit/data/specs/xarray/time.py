# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.new_field.xarray.coordinates import extract_single_value
from earthkit.data.new_field.xarray.coordinates import is_scalar


def from_xarray(owner, selection):
    _coords = {}
    for coord_name, coord_value in selection.coords.items():
        if is_scalar(coord_value):
            # Extract the single value from the scalar dimension
            # and store it in the metadata
            coordinate = owner.by_name[coord_name]
            _coords[coord_name] = coordinate.normalise(extract_single_value(coord_value))

    return owner.time.spec(_coords)


# class XArrayTime(Time):
#     def __init__(self, owner: Any, selection: Any) -> None:
#         self.owner = owner
#         self.selection = selection

#     @cached_property
#     def spec(self):
#         """Return the time specification."""
#         _coords = {}
#         for coord_name, coord_value in self.selection.coords.items():
#             if is_scalar(coord_value):
#                 # Extract the single value from the scalar dimension
#                 # and store it in the metadata
#                 coordinate = self.owner.by_name[coord_name]
#                 _coords[coord_name] = coordinate.normalise(extract_single_value(coord_value))

#         return self.owner.time.spec(_coords)
