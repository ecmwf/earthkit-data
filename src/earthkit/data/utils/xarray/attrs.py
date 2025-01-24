# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os
from abc import ABCMeta
from abc import abstractmethod
from collections import defaultdict
from functools import cached_property

from earthkit.data.utils import ensure_dict
from earthkit.data.utils import ensure_iterable

LOG = logging.getLogger(__name__)


class CFAttrs:
    def _load(self):
        here = os.path.dirname(__file__)
        path = os.path.join(here, "cf_attrs.yaml")
        if os.path.exists(path):
            import yaml

            try:
                with open(path, "r") as f:
                    return yaml.safe_load(f)
            except Exception as e:
                LOG.exception(f"Failed read CF attributes file {path}. {e}")
                raise
        else:
            raise ValueError(f"CF attributes file not found! path={path}")

    @cached_property
    def attrs(self):
        return self._load()

    def can_be_global(self, name):
        item = self.attrs.get(name, None)
        if item:
            return "G" in item["use"]
        return True


CF_ATTRS = CFAttrs()


class Attr:
    """Generic attribute class.

    Parameters
    ----------
    name : str
        The name of the attribute.
    """

    def __init__(self, name):
        self.name = name

    def value(self):
        return None

    def fixed(self):
        False


class KeyAttr(Attr):
    """Metadata key attribute class.

    Parameters
    ----------
    name : str
        The name of the attribute.
    key : str, None
        The metadata key to retrieve the attribute value. If None,
        the name is used as the key.
    """

    def __init__(self, name, key=None):
        super().__init__(name)
        self.key = key if key is not None else name

    def get(self, metadata):
        return {self.name: metadata.get(self.key, default=None)}

    def __repr__(self) -> str:
        return f"KeyAttr({self.name})"


class NamespaceAttr(Attr):
    """Namespace attribute.

    Parameters
    ----------
    name : str
        The name of the metadata namespace
    """

    def __init__(self, name, ns=None):
        super().__init__(name)
        self.ns = ns if ns is not None else name

    def get(self, metadata):
        return {self.name: metadata.as_namespace(self.ns)}

    def __repr__(self) -> str:
        return f"NamespaceAttr({self.name}, ns={self.ns})"


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

    def get(self, metadata):
        return self._value

    def fixed(self):
        return True

    def __repr__(self) -> str:
        return f"FixedAttr({self.name}, {self._value})"


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
            if isinstance(k, dict):
                for k1, v1 in k.items():
                    self.append(self._make(v1, name=k1))
            else:
                self.append(self._make(k))

    @staticmethod
    def _make(val, name=None):
        if name is not None and not isinstance(name, str):
            raise ValueError(f"Attribute name must be a string: {name=}")

        if isinstance(val, Attr):
            return val
        elif isinstance(val, str):
            if val.startswith("namespace="):
                ns = val[len("namespace=") :]
                if name is None:
                    name = ns
                return NamespaceAttr(name, ns=ns)
            elif val.startswith("key="):
                key = val[len("key=") :]
                if name is None:
                    name = key
                return KeyAttr(name, key=key)
            elif name is None:
                name = val
                key = val
                return KeyAttr(val, key=key)
            else:
                return FixedAttr(name, val)
        elif callable(val):
            return CallableAttr(name, val)
        elif name is not None:
            return FixedAttr(name, val)
        else:
            raise ValueError(f"Invalid attribute: {name=} value={val}")

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
        # global_attrs.pop("units", None)

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

        # Some attrs cannot be global according to the CF convention.
        # These are removed from global attrs and kept as variable attrs.
        global_attrs_keys = list(global_attrs.keys())
        global_attrs_renamed_keys = global_attrs_keys
        if rename:
            global_attrs_renamed_keys = list(rename(global_attrs).keys())

        for k1, k2 in zip(global_attrs_keys, global_attrs_renamed_keys):
            if not CF_ATTRS.can_be_global(k1) or not CF_ATTRS.can_be_global(k2):
                global_attrs.pop(k1)

        for k in self.attrs.variable_attrs:
            if k in global_attrs:
                global_attrs.pop(k)

        for var_obj in t_vars.values():
            var_obj.adjust_attrs(drop_keys=global_attrs.keys(), rename=rename)

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
