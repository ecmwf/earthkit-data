# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from .core import SpecFieldMember
from .core import wrap_spec_methods
from .spec.time import Time


@wrap_spec_methods(keys=["base_datetime", "valid_datetime", "step"])
class TimeFieldMember(SpecFieldMember):
    """A specification for a time object."""

    SPEC_CLS = Time
    NAME = "time"
    NAMESPACE_KEYS = ("base_datetime", "valid_datetime", "step")

    def get_grib_context(self, context) -> dict:
        from earthkit.data.field.grib.time import COLLECTOR

        COLLECTOR.collect(self, context)

    def set(self, *args, **kwargs):
        spec = self._spec.set(*args, **kwargs)
        return TimeFieldMember(spec)
