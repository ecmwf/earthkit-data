# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.specs.parameter import Parameter

LOG = logging.getLogger(__name__)


def from_xarray(owner, selection) -> "Parameter":
    """Create a Parameter instance from an xarray dataset.

    Parameters
    ----------
    owner : Variable
        The variable that owns this parameter.
    selection : XArrayDataArray
        The xarray data array selection.

    Returns
    -------
    Parameter
        The created Parameter instance.
    """
    name = owner.name
    units = owner.variable.attrs.get("units", None)
    return {"variable": name, "units": units}


# class XArrayParameter(Parameter):
#     """A class to represent a parameter in an xarray dataset."""

#     def __init__(self, owner: Any, selection=None) -> None:
#         """Create a new XArrayParameter object.

#         Parameters
#         ----------
#         owner : Variable
#             The variable that owns this field.
#         selection : XArrayDataArray
#             A 2D sub-selection of the variable's underlying array.
#             This is actually a nD object, but the first dimensions are always 1.
#             The other two dimensions are latitude and longitude.
#         """
#         self.owner = owner

#         # Copy the metadata from the owner
#         # self._md = owner._metadata.copy()

#     @property
#     def name(self):
#         return self.owner.name

#     @property
#     def units(self):
#         return self.owner.variable.attrs.get("units", None)
