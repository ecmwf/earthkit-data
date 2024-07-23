# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
from collections import defaultdict

LOG = logging.getLogger(__name__)


class AttrsBuilder:
    def __init__(self, profile):
        self.profile = profile
        self.strategy = profile.attrs_strategy

    def build(self, *args, **kwargs):
        if self.strategy == "unique_keys":
            method = self._build_unique
        else:
            method = self._build

        global_attrs = method(*args, **kwargs)

        # add fixed global attrs
        for k in self.profile.global_attrs:
            if isinstance(k, dict):
                for k1, v1 in k.items():
                    if k1 not in global_attrs:
                        global_attrs[k1] = v1

        return global_attrs

    def _build_unique(self, ds, t_vars, remap=True):
        attrs = defaultdict(set)
        if remap:
            remap = self.profile.remap

        for var_obj in t_vars.values():
            var_obj.load_attrs_data(self.profile.attrs, strict=self.profile.strict)
            for k, v in var_obj.attrs.items():
                attrs[k].update(v)

        global_attrs = defaultdict(list)
        for k, v in attrs.items():
            if len(v) == 1 and k not in self.profile.variable_attrs:
                global_attrs[k] = list(v)[0]

        for var_obj in t_vars.values():
            var_obj.build_attrs(drop_keys=global_attrs.keys(), remap=remap)

        return global_attrs

    def _build(self, ds, t_vars, remap=True):
        global_attrs = dict()
        if remap:
            remap = self.profile.remap

        if self.profile.strict:
            for var_obj in t_vars.values():
                var_obj.load_attrs_data(self.profile.variable_attrs, strict=self.profile.strict)
                var_obj.build_attrs(remap=remap)
        else:
            for var_obj in t_vars.values():
                var_obj.load_attrs_data(self.profile.variable_attrs, strict=self.profile.strict)
                var_obj.build_attrs(remap=remap)

            global_attrs = dict()
            first = ds[0]
            for k, v in self.profile.global_attrs:
                if isinstance(v, str):
                    v = first.metadata(v, default=None)
                    if v is not None:
                        global_attrs[k] = v

        return global_attrs
