# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .collector import GribContextCollector
from .core import GribFieldMember


class GribParameterBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.field.parameter import ParameterFieldMember

        d = GribParameterBuilder._build_dict(handle)
        spec = ParameterFieldMember.from_dict(d)
        # spec._set_private_data("handle", handle)
        return spec

    @staticmethod
    def _build_dict(handle):
        def _get(key, default=None):
            return handle.get(key, default=default)

        v = _get("shortName", None)
        if v == "~":
            v = handle.get("paramId", ktype=str, default=None)
        if v is None:
            v = _get("param", None)
        name = v

        units = _get("units", None)

        return dict(
            variable=name,
            units=units,
        )


class GribParameterContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(spec, context):
        r = {
            "shortName": spec.variable,
            # "units": param.units,
        }
        context.update(r)


COLLECTOR = GribParameterContextCollector()


class GribParameter(GribFieldMember):
    BUILDER = GribParameterBuilder
    COLLECTOR = COLLECTOR
