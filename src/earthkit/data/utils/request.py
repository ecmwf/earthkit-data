# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
from abc import ABCMeta
from abc import abstractmethod

from earthkit.data.decorators import thread_safe_cached_property

LOG = logging.getLogger(__name__)


class RequestMapper(metaclass=ABCMeta):
    metadata_alias = None

    def __init__(self, request, **kwargs):
        self.request = request

    @thread_safe_cached_property
    def field_requests(self):
        return self._build()

    @abstractmethod
    def _build(self):
        pass

    def request_at(self, index):
        return self.field_requests[index]

    def index_from_request(self, request):
        for i, r in enumerate(self.field_requests):
            if r == request:
                return i
        return -1

    def __len__(self):
        return len(self.field_requests)
