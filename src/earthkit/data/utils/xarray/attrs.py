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


class Attr:
    """Generic attribute class.

    Parameters
    ----------
    name : str
        The name of the attribute. Used as a metadata key to
        retrieve the attribute value.
    """

    def __init__(self, name):
        self.name = name

    def value(self):
        return None

    def get(self, metadata):
        return {self.name: metadata.get(self.name, default=None)}

    def fixed(self):
        False

    def __repr__(self) -> str:
        return f"Attr({self.name})"


class FixedAttr(Attr):
    """Fixed attribute.

    Parameters
    ----------
    name : str
        The name of the attribute.
    value : str, bool, int, float
        The value of the attribute.
    """

    def __init__(self, name, value):
        super().__init__(name)
        self._value = value

    def value(self):
        return self._value

    def fixed(self):
        return True

    def __repr__(self) -> str:
        return f"FixedAttr({self.name}, {self._value})"


class NamespaceAttr(Attr):
    """Namespace attribute.

    Parameters
    ----------
    name : str
        The name of the metadata namespace
    """

    def get(self, metadata):
        return metadata.as_namespace(self.name)

    def __repr__(self) -> str:
        return f"NamespaceAttr({self.name})"


class CallableAttr(Attr):
    """Callable attribute.

    Parameters
    ----------
    name : str, None
        The name of the attribute. Can be None.
    func : callable
        The function that returns the value of the attribute.
    """

    def __init__(self, name, func):
        super().__init__(name)
        self.func = func

    def __call__(self, metadata):
        if self.name is None:
            return self.func(metadata)
        else:
            res = self.func(self.name, metadata)
            return {self.name: res}

    def __repr__(self) -> str:
        return f"CallableAttr({self.name})"


class AttrList(list):
    def __init__(self, attrs):
        attrs = ensure_iterable(attrs)
        for k in attrs:
            if isinstance(k, str):
                if k.startswith("namespace="):
                    self.append(NamespaceAttr(k[len("namespace=") :]))
                else:
                    self.append(Attr(k))
            elif callable(k):
                self.append(CallableAttr(None, k))
            elif isinstance(k, dict):
                for k1, v1 in k.items():
                    if callable(v1):
                        self.append(CallableAttr(k1, v1))
                    else:
                        self.append(FixedAttr(k1, v1))
            else:
                raise ValueError(f"Invalid  attribute: {k}. Must be a str, callable or dict.")

    def fixed(self):
        return [attr for attr in self if attr.fixed()]

    def non_fixed(self):
        return [attr for attr in self if not attr.fixed()]


class Attrs:
    def __init__(self, profile, attrs_mode, attrs, variable_attrs, global_attrs, coord_attrs, rename_attrs):
        self.profile = profile
        self.attrs = AttrList(attrs)
        self.variable_attrs = AttrList(variable_attrs)
        self.global_attrs = AttrList(global_attrs)
        self.coord_attrs = ensure_dict(coord_attrs)
        self.rename_attrs_map = ensure_dict(rename_attrs)

        # attrs must be unique and contain all variable and global attrs
        for k in self.variable_attrs + self.global_attrs:
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
        for item in self.attrs.global_attrs.fixed():
            if item.name not in global_attrs:
                global_attrs[item.name] = item.value()

        # TODO: make it optional
        global_attrs.pop("units", None)

        return global_attrs


class UniqueAttrBuilder(AttrsBuilder):
    def _build(self, ds, t_vars, rename=None):
        attrs = defaultdict(set)

        for var_obj in t_vars.values():
            s, _ = var_obj.collect_attrs(self.attrs.attrs, strict=self.profile.strict)
            for k, v in s.items():
                attrs[k].update(ensure_iterable(v))

        global_attrs = defaultdict(list)
        for k, v in attrs.items():
            if len(v) == 1 and k not in self.attrs.variable_attrs:
                global_attrs[k] = list(v)[0]

        for var_obj in t_vars.values():
            var_obj.adjust_attrs(drop_keys=global_attrs.keys(), rename=rename)

        for k in self.attrs.variable_attrs:
            if k in global_attrs:
                global_attrs.pop(k)

        global_attrs = {k: v for k, v in global_attrs.items() if v is not None}

        return global_attrs


class FixedAttrBuilder(AttrsBuilder):
    def _build(self, ds, t_vars, rename=None):
        global_attrs = dict()

        for i, var_obj in enumerate(t_vars.values()):
            if i == 0:
                _, global_attrs = var_obj.collect_attrs(
                    self.attrs.variable_attrs,
                    strict=self.profile.strict,
                    extra_attrs=self.attrs.global_attrs.non_fixed(),
                )
            else:
                var_obj.collect_attrs(self.attrs.variable_attrs, strict=self.profile.strict)

            var_obj.adjust_attrs(rename=rename)

        return global_attrs
