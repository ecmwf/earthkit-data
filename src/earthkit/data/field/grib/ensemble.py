# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from .collector import GribContextCollector
from .core import GribFieldComponentHandler


class GribEnsembleBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.field.component.ensemble import Ensemble
        from earthkit.data.field.handler.ensemble import EnsembleFieldComponentHandler

        d = GribEnsembleBuilder._build_dict(handle)
        component = Ensemble.from_dict(d)
        handler = EnsembleFieldComponentHandler.from_component(component)
        return handler

    @staticmethod
    def _build_dict(handle):
        def _get(key, default=None):
            return handle.get(key, default=default)

        v = _get("number")
        if v is None:
            v = _get("perturbationNumber")

        return dict(
            member=v,
        )


class GribEnsembleContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(handler, context):
        component = handler.component
        r = {
            "perturbationNumber": component.member(),
        }
        context.update(r)


COLLECTOR = GribEnsembleContextCollector()


class GribEnsemble(GribFieldComponentHandler):
    BUILDER = GribEnsembleBuilder
    COLLECTOR = COLLECTOR
