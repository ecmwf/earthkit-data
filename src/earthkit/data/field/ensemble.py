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
from .spec.ensemble import Ensemble


@wrap_spec_methods(keys=["member"])
class EnsembleFieldMember(SpecFieldMember):
    """A specification of an ensemble field."""

    SPEC_CLS = Ensemble
    NAME = "ensemble"
    NAMESPACE_KEYS = ("member",)

    def get_grib_context(self, context) -> dict:
        from earthkit.data.field.grib.ensemble import COLLECTOR

        COLLECTOR.collect(self, context)

    def set(self, *args, **kwargs):
        spec = self._spec.set(*args, **kwargs)
        return EnsembleFieldMember(spec)
