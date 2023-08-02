# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import ABCMeta, abstractmethod


class Metadata(metaclass=ABCMeta):
    @abstractmethod
    def keys(self):
        pass

    @abstractmethod
    def items(self):
        pass

    @abstractmethod
    def __getitem__(self, key):
        pass

    @abstractmethod
    def __contains__(self, key):
        pass

    @abstractmethod
    def get(self, key, *args):
        pass

    def _get(self, key, astype=None, **kwargs):
        if "default" in kwargs:
            default = kwargs.pop("default")
            v = self.get(key, default)
        else:
            v = self.get(key)

        if astype is None:
            try:
                return astype(v)
            except Exception:
                return None
        return v

    @abstractmethod
    def override(self, *args, **kwargs):
        pass

    def ls_keys(self):
        return []

    def namespaces(self):
        return {}

    def as_namespace(self, ns):
        return {}

    def latitudes(self):
        return None

    def longitudes(self):
        return None

    def x(self):
        return None

    def y(self):
        return None

    def shape(self):
        return (0,)

    def _unique_grid_id(self):
        return None

    def projection(self):
        return None

    def bounding_box(self):
        return None

    def datetime(self):
        return None

    def dump(self, **kwargs):
        return None


class RawMetadata(Metadata):
    def __init__(self, d):
        self._d = dict(d)

    def keys(self):
        return self._d.keys()

    def items(self):
        return self._d.items()

    def __getitem__(self, key):
        return self._d.__getitem__(key)

    def __contains__(self, key):
        return key in self._d

    def get(self, key, *args):
        if len(args) == 1:
            return self._d.get(key, args[0])
        elif len(args) == 0:
            if key in self._d:
                return self._d.get(key)
            else:
                raise KeyError
        else:
            raise TypeError(f"get: expected at most 2 arguments, got {1+len(args)}")

    def override(self, *args, **kwargs):
        d = dict(**self._d)
        d.update(*args, **kwargs)
        return RawMetadata(d)
