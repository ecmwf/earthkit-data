# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import ABCMeta, abstractmethod


class GribContextCollector(metaclass=ABCMeta):
    def collect(self, spec, context):
        if context._MODE == "encoder":
            if hasattr(spec, "handle"):
                handle = spec.handle
                if handle is not None:
                    if "handle" not in context:
                        context["handle"] = handle
            else:
                self.collect_for_encoder(spec, context)
        elif context._MODE == "indexer":
            self.collect_for_indexer(spec, context)
        else:
            raise ValueError(f"Unknown context mode: {context._MODE}")

    @staticmethod
    @abstractmethod
    def collect_for_encoder(spec, context):
        pass

    @staticmethod
    @abstractmethod
    def collect_for_indexer(spec, context):
        pass

    @staticmethod
    def _collect_keys(keys, spec, context):
        if "handle" in context:
            handle = context["handle"]
        else:
            return

        r = {}
        for k in keys:
            if k not in r:
                v = handle.get(k, default=None)
                if v is not None:
                    r[k] = v

        context.update(r)

    @staticmethod
    @abstractmethod
    def indexer_keys(spec):
        pass

    @staticmethod
    @property
    def all_indexer_keys():
        pass
