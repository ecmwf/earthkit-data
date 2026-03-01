# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.field.handler.data import DataFieldComponentHandler

from .collector import GribContextCollector


class GribDataContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(spec, context):
        from earthkit.utils.array import convert

        r = {
            "values": convert(spec.values, array_namespace="numpy"),
        }
        context.update(r)


COLLECTOR = GribDataContextCollector()


class GribData(DataFieldComponentHandler):
    def __init__(self, handle):
        self.handle = handle

    def get_values(self, dtype=None, copy=True, index=None):
        """Get the values stored in the field as an array."""

        v = self.handle.get_values(dtype=dtype)
        if dtype is not None:
            from earthkit.utils.array import array_namespace

            v = array_namespace(v).astype(v, dtype, copy=False)
        return v

    def check(self, owner):
        pass

    def get_grib_context(self, context):
        COLLECTOR.collect_keys(self, context)

    def __getstate__(self):
        state = {}
        state["handle"] = self.handle
        return state

    def __setstate__(self, state):
        self.__init__(state["handle"])
