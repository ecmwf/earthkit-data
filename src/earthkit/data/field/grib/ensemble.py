# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from .collector import GribEncoderCollector, GribIndexerCollector, GribIndexerFieldKeysCollector, MultiCollector
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


class GribEnsembleEncoderCollector(GribEncoderCollector):
    # _ALL_INDEXER_KEYS = ["perturbationNumber"]

    @staticmethod
    def _collect(handler, context):
        component = handler.component
        r = {
            "perturbationNumber": component.member(),
        }
        context.update(r)

    # @staticmethod
    # def collect_for_indexer(handler, context):
    #     keys = GribEnsembleContextCollector.indexer_keys(handler)
    #     GribContextCollector._collect_keys(keys, handler, context)

    # @staticmethod
    # def collect_for_indexer_from_handle(context):
    #     keys = GribEnsembleContextCollector._ALL_INDEXER_KEYS
    #     GribContextCollector._collect_keys(keys, context)

    # @staticmethod
    # def indexer_keys(handler):
    #     return GribEnsembleContextCollector._ALL_INDEXER_KEYS

    # @staticmethod
    # @property
    # def all_indexer_keys():
    #     return GribEnsembleContextCollector._ALL_INDEXER_KEYS


class GribEnsembleIndexerFieldKeysCollector(GribIndexerFieldKeysCollector):
    @staticmethod
    def _collect(handler, context):
        component = handler.component
        context["ensemble.member"] = component.member()


class GribEnsembleIndexerCollector(GribIndexerCollector):
    @staticmethod
    def _collect(handle, context):
        keys = GribEnsembleIndexerCollector.indexer_keys()
        GribIndexerCollector._collect_keys(keys, handle, context)

    @staticmethod
    def indexer_keys():
        return ["perturbationNumber"]


COLLECTOR = MultiCollector(encoder=GribEnsembleEncoderCollector(), indexer=GribEnsembleIndexerFieldKeysCollector())
ENSEMBLE_INDEXER_COLLECTOR = GribEnsembleIndexerCollector()


class GribEnsemble(GribFieldComponentHandler):
    BUILDER = GribEnsembleBuilder
    COLLECTOR = COLLECTOR
