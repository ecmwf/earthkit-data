# (C) Copyright 2020 ECMWF.
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
from collections import defaultdict

from earthkit.data.utils import ensure_dict
from earthkit.data.utils import ensure_iterable

LOG = logging.getLogger(__name__)


class GlobalAttrs:
    def __init__(self, attrs):
        self.fixed = {}
        self.keys = []
        attrs = ensure_iterable(attrs)
        for k in attrs:
            if isinstance(k, str):
                self.keys.append(k)
            elif isinstance(k, dict):
                for k1, v1 in k.items():
                    self.fixed[k1] = v1
            else:
                raise ValueError(f"Invalid global attribute: {k}. Must be a str or a dict.")


class Attrs:
    def __init__(self, profile, attrs_mode, attrs, variable_attrs, global_attrs, coord_attrs, rename_attrs):
        self.profile = profile
        self.attrs = ensure_iterable(attrs)
        self.variable_attrs = ensure_iterable(variable_attrs)
        self.global_attrs = GlobalAttrs(global_attrs)
        self.coord_attrs = ensure_dict(coord_attrs)
        self.rename_attrs_map = ensure_dict(rename_attrs)

        for k in self.variable_attrs + self.global_attrs.keys:
            if k not in self.attrs:
                self.attrs.append(k)

        self.builder = self._make_builder(attrs_mode)(profile, self)

    @staticmethod
    def _make_builder(mode):
        if mode == "unique":
            return UniqueAttrBuilder
        elif mode == "fixed":
            return FixedAttrBuilder
        else:
            raise ValueError(f"Invalid attrs_mode: {mode}. Must be one of 'unique', 'fixed'.")


class AttrsBuilder(metaclass=ABCMeta):
    def __init__(self, profile, attrs):
        self.profile = profile
        self.attrs = attrs

    @abstractmethod
    def _build(self, *args, **kwargs):
        pass

    def build(self, *args, rename=True, **kwargs):
        def _rename(d):
            return {self.attrs.rename_attrs_map.get(k, k): v for k, v in d.items()}

        def _id(x):
            return x

        if rename:
            rename = _rename
        else:
            rename = _id

        global_attrs = rename(self._build(*args, rename=rename, **kwargs))

        # add fixed global attrs
        for k, v in self.attrs.global_attrs.fixed.items():
            if k not in global_attrs:
                global_attrs[k] = v

        # TODO: make it optional
        global_attrs.pop("units", None)

        return global_attrs


class UniqueAttrBuilder(AttrsBuilder):
    def _build(self, ds, t_vars, rename=None):
        attrs = defaultdict(set)

        for var_obj in t_vars.values():
            var_obj.load_attrs(self.attrs.attrs, strict=self.profile.strict)
            attrs.update(var_obj.attrs)

        global_attrs = defaultdict(list)
        for k, v in attrs.items():
            if len(v) == 1 and k not in self.attrs.variable_attrs:
                global_attrs[k] = list(v)[0]

        for var_obj in t_vars.values():
            var_obj.adjust_attrs(drop_keys=global_attrs.keys(), rename=rename)

        return global_attrs


class FixedAttrBuilder(AttrsBuilder):
    def _build(self, ds, t_vars, rename=None):
        global_attrs = dict()

        for var_obj in t_vars.values():
            var_obj.load_attrs(self.attrs.variable_attrs, strict=self.profile.strict)
            var_obj.adjust_attrs(rename=rename)

        global_attrs = dict()
        first = ds[0]
        for k in self.attrs.global_attrs.keys:
            v = first.metadata(k, default=None)
            if v is not None:
                global_attrs[k] = v

        return global_attrs
