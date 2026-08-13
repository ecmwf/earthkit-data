# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.field.handler.data import DataFieldComponentHandler

from .collector import GribEncoderCollector, GribIndexerCollector, GribIndexerFieldKeysCollector, MultiCollector


class GribDataEncoderCollector(GribEncoderCollector):
    @staticmethod
    def _collect(spec, context):
        from earthkit.utils.array import convert

        r = {
            "values": convert(spec.values, array_namespace="numpy"),
        }
        context.update(r)


class GribDataIndexerFieldKeysCollector(GribIndexerFieldKeysCollector):
    @staticmethod
    def _collect(handler, context):
        pass


class GribDataIndexerCollector(GribIndexerCollector):
    @staticmethod
    def _collect(handle, context):
        keys = GribDataIndexerCollector.indexer_keys()
        GribIndexerCollector._collect_keys(keys, handle, context)

    @staticmethod
    def indexer_keys():
        return ["bitsPerValue"]


COLLECTOR = MultiCollector(encoder=GribDataEncoderCollector(), indexer=GribDataIndexerFieldKeysCollector())
DATA_INDEXER_COLLECTOR = GribDataIndexerCollector()


class GribData(DataFieldComponentHandler):
    COLLECTOR = COLLECTOR

    def __init__(self, handle):
        self.handle = handle

    def get_values(self, dtype=None, copy=True, index=None):
        """Get the values stored in the field as an array."""
        # the code below relies on the fact that get_values() of
        # the GRIB handle always returns a new array (i.e. a copy of the data)
        v = self.handle.get_values(dtype=dtype)
        if dtype is not None:
            from earthkit.utils.array import array_namespace

            # since v is already a copy of the data we do not need to copy it
            # again when converting to the requested dtype
            v = array_namespace(v).astype(v, dtype, copy=False)
        return v

    def check(self, owner):
        pass

    def __getstate__(self):
        state = {}
        state["handle"] = self.handle
        return state

    def __setstate__(self, state):
        self.__init__(state["handle"])
