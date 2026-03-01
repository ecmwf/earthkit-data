# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.vocabularies.aliases import unalias

_UNITS = {"t": "K", "r": "%"}


class MarsParameterBuilder:
    @staticmethod
    def build(request, build_empty=False):
        from earthkit.data.field.component.parameter import Parameter
        from earthkit.data.field.handler.parameter import ParameterFieldComponentHandler

        d = MarsParameterBuilder._build_dict(request)
        if not d and not build_empty:
            return None

        component = Parameter.from_dict(d)
        handler = ParameterFieldComponentHandler.from_component(component)
        return handler

    @staticmethod
    def _build_dict(request):
        param = request.get("param", None)

        if param is None:
            return dict()

        param = unalias("grib-paramid", param)

        units = _UNITS.get(param, None)

        return dict(
            variable=param,
            units=units,
        )
