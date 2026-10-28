# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
from abc import ABCMeta, abstractmethod

from .context import GribIndexerContext

LOG = logging.getLogger(__name__)


class GribContextCollector(metaclass=ABCMeta):
    @abstractmethod
    def collect(self, data, context):
        pass


class MultiCollector:
    def __init__(self, encoder=None, indexer=None):
        self._collectors = {
            "encoder": encoder,
            "indexer": indexer,
        }

    def collect(self, handler, context):
        # Any context that is not an indexer context (e.g. a plain dict) is
        # handled by the encoder collector.
        if isinstance(context, GribIndexerContext):
            self._collectors["indexer"].collect(handler, context)
        else:
            self._collectors["encoder"].collect(handler, context)

    def collect_keys(self, handler, context):
        """Collect the keys needed by the encoder, ignoring any handle stored in ``handler``."""
        self._collectors["encoder"].collect_keys(handler, context)


class GribEncoderCollector(GribContextCollector):
    def collect(self, handler, context):
        if hasattr(handler, "handle"):
            handle = handler.handle
            if handle is not None:
                if "handle" not in context:
                    context["handle"] = handle
        else:
            self._collect(handler, context)

    @classmethod
    def collect_keys(cls, handler, context):
        cls._collect(handler, context)

    @staticmethod
    @abstractmethod
    def _collect(handler, context):
        pass


class GribIndexerFieldKeysCollector(GribContextCollector):
    def collect(self, handler, context):
        # A lazy GRIB component handler raises AttributeError (chained to the original error) when
        # the component cannot be built from the message, e.g. when the date is invalid. In
        # that case the keys of the component are left out and the other components are still
        # collected. Any other failure is a real error and is not caught.
        try:
            handler.component
        except AttributeError as e:
            if e.__cause__ is None:
                raise
            LOG.warning(
                f"Cannot build component {type(handler).__name__} for indexing, "
                f"its keys are not stored: {e.__cause__!r}"
            )
            return
        self._collect(handler, context)

    @staticmethod
    @abstractmethod
    def _collect(handler, context):
        pass
