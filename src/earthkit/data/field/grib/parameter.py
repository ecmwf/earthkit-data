# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .collector import GribContextCollector
from .core import GribFieldPartHandler


class GribParameterBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.field.parameter import ParameterFieldPartHandler
        from earthkit.data.field.part.parameter import Parameter

        d = GribParameterBuilder._build_dict(handle)
        part = Parameter.from_dict(d)
        handler = ParameterFieldPartHandler.from_part(part)
        return handler

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


class GribParameter(GribFieldPartHandler):
    BUILDER = GribParameterBuilder
    COLLECTOR = COLLECTOR
