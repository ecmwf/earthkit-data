# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import functools

from earthkit.data.utils.dates import datetime_from_grib
from earthkit.data.utils.dates import to_timedelta

NAMESPACES = [
    "ls",
    "geography",
    "mars",
    "parameter",
    "statistics",
    "time",
    "vertical",
]

CUSTOM_KEYS = {"message", "handle"}


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


class GribMetadata:

    NAME = "grib"
    KEY_PREFIX = "grib."

    def __init__(self, handle):
        self._handle = handle
        self._cache = {}

    # def from_dict(self, d):
    #     raise NotImplementedError()

    @property
    def handle(self):
        return self._handle

    def __len__(self):
        return sum(map(lambda i: 1, self.keys()))

    def __contains__(self, key):
        return key in CUSTOM_KEYS or self._handle.__contains__(key)

    def __iter__(self):
        return self.keys()

    def keys(self):
        return self._handle.keys()

    def items(self):
        return self._handle.items()

    def __getitem__(self, key):
        return self.get(key, raise_on_missing=True)

    # def __getitem__(self, key):
    #     if key in self.handle:
    #         return self.handle.get(key)
    #     raise KeyError(f"Label '{key}' not found in GribLabels")

    # def metadata(self, keys=None, default=None):
    #     return self.handle.get(keys=keys, default=default)

    def metadata(self, *args, **kwargs):
        return self.get(*args, **kwargs)

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

        key = _key_name(key)

        _kwargs = {}
        if not raise_on_missing:
            _kwargs["default"] = default

        if key == "step_timedelta":
            return self.step_timedelta()
        if key == "valid_datetime":
            return self.valid_datetime()
        elif key == "base_datetime":
            return self.base_datetime()
        elif key == "reference_datetime":
            return self.reference_datetime()
        elif key == "indexing_datetime":
            return self.indexing_datetime()
        elif key == "message":
            return self.message()
        elif key == "handle":
            return self._handle

        v = self._handle.get(key, ktype=astype, **_kwargs)

        # special case when  "shortName" is "~".
        if key == "shortName" and v == "~":
            v = self._handle.get("paramId", ktype=str, **_kwargs)
        return v

    def set(self, d):
        raise NotImplementedError("GribMetadata.set is not implemented")

    def _datetime(self, date_key, time_key):
        date = self.get(date_key, None)
        if date is not None:
            time = self.get(time_key, None)
            if time is not None:
                return datetime_from_grib(date, time)
        return None

    def base_datetime(self):
        return self._datetime("dataDate", "dataTime")

    def valid_datetime(self):
        try:
            return self.base_datetime() + self.step_timedelta()
        except Exception:
            pass
        return self._datetime("validityDate", "validityTime")

    def reference_datetime(self):
        return self._datetime("referenceDate", "referenceTime")

    def indexing_datetime(self):
        return self._datetime("indexingDate", "indexingTime")

    def step_timedelta(self):
        v = self.get("endStep", None)
        if v is None:
            v = self.get("step", None)
        return to_timedelta(v)

    def message(self):
        r"""Return a buffer containing the encoded message.

        Returns
        -------
        bytes
        """
        return self.handle.get_buffer()

    def namespace(self, owner, name, result, ns=None, prefix_keys=False):
        if isinstance(name, str):
            name = [name]
        elif name is None or name == [None]:
            name = NAMESPACES

        if isinstance(name, (list, tuple)):
            for ns in name:
                r = self.handle.as_namespace(ns)
                if prefix_keys:
                    r = {f"{self.KEY_PREFIX}{k}": v for k, v in r.items()}
                result[self.NAME] = r

    def new_array_field(self, field, array_namespace=None, **kwargs):
        from earthkit.data.field.grib.create import new_array_grib_field

        return new_array_grib_field(field, self._handle, array_namespace=array_namespace, **kwargs)

    def sync(self, owner):
        handle_new = None
        for k, v in owner._parts.items():
            if hasattr(v, "handle") and v.handle is not self._handle:
                handle_new = v._handle
                break

        if handle_new:
            self._handle = handle_new
            for k, v in owner._parts.items():
                if hasattr(v, "handle") and hasattr(v, "from_handle") and v.handle is not self.handle:
                    owner._parts[k] = v.from_handle(handle_new)

    def __getstate__(self):
        state = {}
        state["handle"] = self.handle
        return state

    def __setstate__(self, state):
        self.__init__(state["handle"])


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
