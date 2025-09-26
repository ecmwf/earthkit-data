# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.specs.parameter import SimpleParameter

LOG = logging.getLogger(__name__)


class XArrayParameter(SimpleParameter):
    """A class to represent a parameter in an xarray dataset."""

    def __init__(self, owner, selection=None) -> None:
        """Create a new XArrayParameter object.

        Parameters
        ----------
        owner : Variable
            The variable that owns this field.
        selection : XArrayDataArray
            A 2D sub-selection of the variable's underlying array.
            This is actually a nD object, but the first dimensions are always 1.
            The other two dimensions are latitude and longitude.
        """
        # self.owner = owner
        name = owner.name
        units = owner.variable.attrs.get("units", None)
        super().__init__(name, units)
