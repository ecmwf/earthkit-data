# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .core import SpecFieldPart
from .core import wrap_spec_methods
from .spec.proc import Proc


@wrap_spec_methods(keys=["time", "time_value", "time_method", "items"])
class ProcFieldPart(SpecFieldPart):
    """A specification of a vertical level or layer."""

    SPEC_CLS = Proc
    NAME = "proc"
    NAMESPACE_KEYS = tuple()

    def get_grib_context(self, context) -> dict:
        from earthkit.data.field.grib.proc import COLLECTOR

        COLLECTOR.collect(self, context)

    def set(self, *args, **kwargs):
        spec = self._spec.set(*args, **kwargs)
        return ProcFieldPart(spec)
