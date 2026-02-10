# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import logging

from earthkit.data.decorators import thread_safe_cached_property
from earthkit.data.field.core import LazyFieldComponentHandler

LOG = logging.getLogger(__name__)


class GribFieldComponentHandler(LazyFieldComponentHandler):
    BUILDER = None
    COLLECTOR = None

    def __init__(self, handle):
        self.handle = handle

    @classmethod
    def from_handle(cls, handle):
        return cls(handle)

    @thread_safe_cached_property
    def _handler(self):
        try:
            return self.BUILDER.build(self.handle)
        except Exception as e:
            LOG.exception(e)
            self._exception = e
            raise

    def get_grib_context(self, context) -> dict:
        self.COLLECTOR.collect(self, context)

    def __getstate__(self):
        state = {}
        state["handle"] = self.handle
        return state

    def __setstate__(self, state):
        self.__init__(state["handle"])
