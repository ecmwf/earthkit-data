# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.field.component.parameter import Parameter
from earthkit.data.field.parameter import ParameterFieldComponentHandler

LOG = logging.getLogger(__name__)


class XArrayParameter(ParameterFieldComponentHandler):
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
        spec = Parameter.from_dict(dict(variable=name, units=units))
        super().__init__(spec)
