# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.decorators import thread_safe_cached_property
from earthkit.data.field.handler.data import DataFieldComponentHandler
from earthkit.data.indexing.indexed import IndexedFieldList

LOG = logging.getLogger(__name__)


class VirtualData(DataFieldComponentHandler):
    def __init__(self, owner, request):
        self.owner = owner
        self.request = request

    def get_values(self, **kwargs):
        """Get the values stored in the field as an array."""

        return self._field._components["data"].get_values(**kwargs)

    @property
    def _field(self):
        return self.owner.retriever.get(self.request)[0]

    def __getstate__(self):
        state = {}
        state["owner"] = self.owner
        state["request"] = self.request
        return state

    def __setstate__(self, state):
        self.__init__(state["owner"], state["request"])


def make_virtual_grib_field(owner, request):
    r = request.copy()
    param = r.pop("param", None)
    if param is not None:
        reference = owner._get_reference(param)
        data = VirtualData(owner, request)
        from earthkit.data.field.mars.create import new_mars_field

        f = new_mars_field(r, data=data, reference_field=reference)
        return f

    raise KeyError("Request must contain 'param' key")


class VirtualGribFieldList(IndexedFieldList):
    def __init__(self, request_mapper, retriever):
        self.request_mapper = request_mapper
        self.retriever = retriever

        self._reference_cache = {}

    def __len__(self):
        return len(self.request_mapper)

    def mutate(self):
        return self

    @thread_safe_cached_property
    def reference(self):
        return self.retriever.get(self.request_mapper.request_at(0))[0]

    def _getitem(self, n):
        if isinstance(n, int):
            if n < 0:
                n += len(self)
            if n >= len(self):
                raise IndexError(f"Index {n} out of range")

            if n == 0:
                return self.reference
            else:
                return make_virtual_grib_field(self, self.request_mapper.request_at(n))

    def _get_reference(self, param):
        if param in self._reference_cache:
            return self._reference_cache[param]

        ref_request = self.request_mapper.request_at(0)
        if param == ref_request.get("param"):
            r = self.reference
            # r = self.reference.get_as_dict(["variable", "units", "grib.cfName"])
        else:
            # TODO: refactor to avoid using the grib handle directly here
            handle = self.reference._get_grib().handle
            handle = handle.clone(headers_only=True)
            handle.set("paramId", param)
            r = handle
            from earthkit.data.field.grib.create import new_grib_field

            r = new_grib_field(handle)

        self._reference_cache[param] = r
        return r
