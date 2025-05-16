# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
from functools import cached_property

from earthkit.data.core.fieldlist import Field
from earthkit.data.core.metadata import WrappedMetadata
from earthkit.data.utils.dates import date_to_grib
from earthkit.data.utils.dates import datetime_from_grib
from earthkit.data.utils.dates import time_to_grib
from earthkit.data.utils.dates import to_timedelta

from .index import GribFieldList

LOG = logging.getLogger(__name__)


class VirtualGribField(Field):
    def __init__(self, owner, request, metadata_alias, reference=None):
        self.owner = owner
        self.request = request
        self.metadata_alias = metadata_alias
        self.reference = reference

        self.extra = {}
        if "param" in request:
            if "shortName" not in request:
                self.extra = self.owner._get_info(self.request["param"])
            if "shortName" not in self.extra:
                self.extra["shortName"] = request["param"]
            else:
                self.extra["param"] = self.extra["shortName"]

    @property
    def _data_datetime(self):
        if "date" in self.request and "time" in self.request:
            return datetime_from_grib(self.request["date"], self.request["time"])
        return None

    @property
    def _valid_datetime(self):
        base = self._data_datetime
        if base is None:
            return None
        if "step" in self.request:
            step = self.request["step"]
            return base + to_timedelta(step)
        return base

    def _attributes(self, names, remapping=None, joiner=None, default=None):
        result = {}
        metadata = self.metadata
        if remapping is not None:
            metadata = remapping(metadata, joiner=joiner)

        for name in names:
            result[name] = metadata(name, default=default)
        return result

    def metadata(self, *keys, astype=None, remapping=None, patches=None, **kwargs):
        if (not kwargs or kwargs == {"default": None}) and keys:
            if isinstance(keys[0], (list, tuple)):
                keys = keys[0]
            if keys and isinstance(keys[0], str):
                r = []
                for k in keys:
                    r.append(self._one_metadata(k, astype=astype, remapping=remapping, patches=patches))
                if len(r) == 1:
                    return r[0]
                return r

        return super().metadata(
            *keys,
            astype=astype,
            remapping=remapping,
            patches=patches,
            **kwargs,
        )

    def _one_metadata(self, key, remapping=None, patches=None, **kwargs):
        # print(f"one_metadata key={key} kwargs={kwargs}")
        if key in self.extra:
            return self.extra[key]
        if key in self.request:
            return self.request[key]
        if key in self.metadata_alias and key in self.request:
            return self.request[self.metadata_alias[key]]

        if key == "number":
            return 0
        if key == "validityDate":
            return date_to_grib(self._valid_datetime)
        if key == "validityTime":
            return time_to_grib(self._valid_datetime)
        if key in ("forecast_reference_time", "base_time", "base_datetime"):
            # print("here")
            return self._data_datetime.isoformat()
        if key in ("valid_datetime", "valid_time"):
            return self._valid_datetime.isoformat()

        return self._metadata.get(key, **kwargs)

    @property
    def _metadata(self):
        r = {**self.request, **self.extra}
        for k, v in self.metadata_alias.items():
            if k not in r and v in r:
                r[k] = r[v]

        return WrappedMetadata(self.owner.reference._metadata, extra=r)

    def _values(self, dtype=None):
        return self._field._values(dtype=dtype)

    @property
    def _field(self):
        if self.reference:
            return self.reference
        else:
            return self.owner.retriever.get(self.request)[0]


class VirtualGribFieldList(GribFieldList):
    def __init__(self, request_mapper, retriever):
        self.request_mapper = request_mapper
        self.retriever = retriever

        self._info_cache = {}

    def __len__(self):
        return len(self.request_mapper)

    def mutate(self):
        return self

    @cached_property
    def reference(self):
        return self.retriever.get(self.request_mapper.request_at(0))[0]

    def _getitem(self, n):
        if isinstance(n, int):
            if n < 0:
                n += len(self)
            if n >= len(self):
                raise IndexError(f"Index {n} out of range")

            return VirtualGribField(
                self,
                self.request_mapper.request_at(n),
                self.request_mapper.metadata_alias,
                reference=self.reference if n == 0 else None,
            )

    def _get_info(self, param):
        if param in self._info_cache:
            return self._info_cache[param]

        ref_request = self.request_mapper.request_at(0)
        if param == ref_request.get("param"):
            r = self.reference._attributes(["shortName", "name", "units", "cfName"])
        else:
            md = self.reference.metadata().override(paramId=param)
            r = {k: md.get(k, None) for k in ["shortName", "name", "units", "cfName"]}

        self._info_cache[param] = r
        return r
