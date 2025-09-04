# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import functools

from earthkit.data.specs.labels import SimpleLabels

NAMESPACES = [
    "ls",
    "geography",
    "mars",
    "parameter",
    "statistics",
    "time",
    "vertical",
]


class MetadataCacheHandler:
    @staticmethod
    def make(cache=None):
        if cache is True:
            return dict()
        elif cache is not False and cache is not None:
            return cache

    @staticmethod
    def clone_empty(cache):
        if cache is not None:
            return cache.__class__()

    @staticmethod
    def serialise(cache):
        if cache is not None:
            return cache.__class__

    @staticmethod
    def deserialise(state):
        cache = state
        if state is not None:
            return cache()

    @staticmethod
    def cache_get(func):
        @functools.wraps(func)
        def wrapped(self, key, default=None, *, astype=None, raise_on_missing=False):
            if self._cache is not None:
                cache_id = (key, default, astype, raise_on_missing)
                if cache_id in self._cache:
                    return self._cache[cache_id]

                v = func(self, key, default=default, astype=astype, raise_on_missing=raise_on_missing)
                self._cache[cache_id] = v
                return v
            else:
                return func(self, key, default=default, astype=astype, raise_on_missing=raise_on_missing)

        return wrapped


class GribLabels(SimpleLabels):
    def __init__(self, handle):
        self.handle = handle
        self._cache = {}

    def __len__(self):
        return sum(map(lambda i: 1, self.keys()))

    def __contains__(self, key):
        if key.startswith("grib."):
            key = key[5:]
        return self.handle.__contains__(key)

    def __iter__(self):
        return self.keys()

    def keys(self):
        return self.handle.keys()

    def items(self):
        return self.handle.items()

    def __getitem__(self, key):
        return self.get(key, raise_on_missing=True)

    # def __getitem__(self, key):
    #     if key in self.handle:
    #         return self.handle.get(key)
    #     raise KeyError(f"Label '{key}' not found in GribLabels")

    def metadata(self, keys=None, default=None):
        return self.handle.get(keys=keys, default=default)

    def override(self, *args, headers_only_clone=True, **kwargs):
        pass

    @MetadataCacheHandler.cache_get
    def get(self, key, default=None, *, astype=None, raise_on_missing=False):
        def _key_name(key):
            if key == "param":
                key = "shortName"
            elif key == "_param_id":
                key = "paramId"
            return key

        _kwargs = {}
        if not raise_on_missing:
            _kwargs["default"] = default

        # allow using the "grib." prefix.
        if key.startswith("grib."):
            key = key[5:]

        # key = _key_name(key)

        v = self.handle.get(key, ktype=astype, **_kwargs)

        # special case when  "shortName" is "~".
        if key == "shortName" and v == "~":
            v = self.handle.get("paramId", ktype=str, **_kwargs)
        return v

    def set(self, d):
        return

    def message(self):
        r"""Return a buffer containing the encoded message.

        Returns
        -------
        bytes
        """
        return self.handle.get_buffer()

    def namespace(self, owner, name, result):
        if isinstance(name, str):
            name = [name]
        if isinstance(name, (list, tuple)):
            if name == ["grib"]:
                for ns in NAMESPACES:
                    result["grib." + ns] = self.handle.as_namespace(ns)

            else:
                for ns in name:
                    if ns.startswith("grib."):
                        result[ns] = self.handle.as_namespace(ns[5:])


# class GribLabels(SimpleLabels):
#     def __init__(self, handle):
#         self.handle = handle

#     def __len__(self):
#         return sum(map(lambda i: 1, self.keys()))

#     def __contains__(self, key):
#         if key.startswith("grib."):
#             key = key[5:]
#         return self.handle.__contains__(key)

#     def __iter__(self):
#         return self.keys()

#     def keys(self):
#         return self.handle.keys()

#     def items(self):
#         return self.handle.items()

#     def __getitem__(self, key):
#         return self.get(key, raise_on_missing=True)

#     # def __getitem__(self, key):
#     #     if key in self.handle:
#     #         return self.handle.get(key)
#     #     raise KeyError(f"Label '{key}' not found in GribLabels")

#     def metadata(self, keys=None, default=None):
#         return self.handle.get(keys=keys, default=default)

#     def override(self, *args, headers_only_clone=True, **kwargs):
#         pass

#     def get(self, key, default=None, *, astype=None, raise_on_missing=False):
#         def _key_name(key):
#             if key == "param":
#                 key = "shortName"
#             elif key == "_param_id":
#                 key = "paramId"
#             return key

#         _kwargs = {}
#         if not raise_on_missing:
#             _kwargs["default"] = default

#         # allow using the "grib." prefix.
#         if key.startswith("grib."):
#             key = key[5:]

#         # key = _key_name(key)

#         v = self.handle.get(key, ktype=astype, **_kwargs)

#         # special case when  "shortName" is "~".
#         if key == "shortName" and v == "~":
#             v = self.handle.get("paramId", ktype=str, **_kwargs)
#         return v

#     def set(self, d):
#         return

#     def message(self):
#         r"""Return a buffer containing the encoded message.

#         Returns
#         -------
#         bytes
#         """
#         return self.handle.get_buffer()
