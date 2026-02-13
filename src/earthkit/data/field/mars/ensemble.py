# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


class MarsEnsembleBuilder:
    @staticmethod
    def build(request, build_empty=False):
        from earthkit.data.field.component.ensemble import Ensemble
        from earthkit.data.field.ensemble import EnsembleFieldComponentHandler

        d = MarsEnsembleBuilder._build_dict(request)
        if not d and not build_empty:
            return None

        component = Ensemble.from_dict(d)
        handler = EnsembleFieldComponentHandler.from_component(component)
        return handler

    @staticmethod
    def _build_dict(request):
        member = request.get("number", None)

        return dict(
            member=member,
        )
