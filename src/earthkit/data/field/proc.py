# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .component.proc import BaseProc
from .core import SimpleFieldComponentHandler


class ProcFieldComponentHandler(SimpleFieldComponentHandler):
    """A specification of a vertical level or layer."""

    PART_CLS = BaseProc
    NAME = "proc"

    def get_grib_context(self, context) -> dict:
        from earthkit.data.field.grib.proc import COLLECTOR

        COLLECTOR.collect(self, context)

    def set(self, *args, **kwargs):
        spec = self._spec.set(*args, **kwargs)
        return ProcFieldComponentHandler(spec)
