# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

_UNITS = {"t": "K"}


class MarsParameterBuilder:
    @staticmethod
    def build(request):
        from earthkit.data.field.component.parameter import Parameter
        from earthkit.data.field.parameter import ParameterFieldComponentHandler

        d = MarsParameterBuilder._build_dict(request)
        component = Parameter.from_dict(d)
        handler = ParameterFieldComponentHandler.from_component(component)
        return handler

    @staticmethod
    def _build_dict(request):
        param = request.get("param", None)
        units = _UNITS.get(param, None)

        return dict(
            variable=param,
            units=units,
        )
