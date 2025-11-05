# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.wrappers import Wrapper


class FloatWrapper(Wrapper):
    def __init__(self, data):
        self.data = data

    @property
    def values(self):
        return self.data


def wrapper(data, *args, fieldlist=False, **kwargs):
    if isinstance(data, float):
        return FloatWrapper(data)
    return None
