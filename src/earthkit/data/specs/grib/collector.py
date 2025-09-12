# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import ABCMeta
from abc import abstractmethod


class GribContextCollector(metaclass=ABCMeta):
    def collect(self, spec, context):
        if hasattr(spec, "handle"):
            handle = spec.handle
            if handle is not None:
                if "handle" not in context:
                    context["handle"] = handle
        else:
            self.collect_keys(spec, context)

    @staticmethod
    @abstractmethod
    def collect_keys(spec, context):
        pass

    # @staticmethod
    # def get_handle(spec):
    #     return spec.get_private_data("handle")
