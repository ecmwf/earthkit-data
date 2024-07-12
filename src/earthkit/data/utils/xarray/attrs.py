# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

LOG = logging.getLogger(__name__)


class GlobalAttrs:
    def __init__(self, profile):
        self.profile = profile
        self.strategy = profile.global_attrs_strategy

    def attrs(self, ds):
        attrs = dict(**self.profile.global_attrs)

        if self.strategy == "unique_keys":
            for k in self.profile.index_keys:
                v = ds.index(k)
                if len(v) == 1:
                    attrs[k] = v[0]

        for k in self.profile.drop_global_attrs:
            if k in attrs:
                del attrs[k]

        return attrs
