# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import logging

from earthkit.data.readers.grib.index import FieldList

LOG = logging.getLogger(__name__)


class VirtualGribField(dict):
    KEY_TYPES = {
        "s": str,
        "l": int,
        "d": float,
        "str": str,
        "int": int,
        "float": float,
        "": None,
    }

    NAME_LOOKUP = {
        "dataDate": "date",
        "dataTime": "time",
        "level": "levelist",
        "step": "endStep",
    }

    for k in list(NAME_LOOKUP.keys()):
        NAME_LOOKUP[NAME_LOOKUP[k]] = k

    def metadata(self, name, **kwargs):
        name, _, key_type_str = name.partition(":")
        try:
            key_type = self.KEY_TYPES[key_type_str]
        except KeyError:
            raise ValueError(f"Key type={key_type_str} not supported")

        try:
            if key_type is not None:
                return key_type(self._get(name))
            else:
                return self._get(name)
        except Exception:
            return None

    def __getitem__(self, name):
        return self.metadata(name)

    def _get(self, name):
        if name in VirtualGribField.NAME_LOOKUP:
            return self._get_with_replace(name, VirtualGribField.NAME_LOOKUP[name])
        elif name == "stepRange":
            return self.steprange()
        return self.get(name, None)

    def _get_with_replace(self, name, other_name):
        v = self.get(name, None)
        if v is None:
            return self.get(other_name, None)
        else:
            return v

    def steprange(self):
        v = self.get("stepRange", None)
        if v is None:
            for k in ["step", "endStep"]:
                v = self.get(k, None)
                if v is not None:
                    try:
                        return str(v)
                    except Exception:
                        v = None
        return v

    @property
    def values(self):
        return self["values"]

    def to_numpy(self, flatten=False):
        return self.values if flatten else self.values.reshape(self.shape)

    @property
    def shape(self):
        Nj = self.get("Nj", None)
        Ni = self.get("Ni", None)
        if Ni is None or Nj is None:
            return len(self.values)
        return (Nj, Ni)

    def datetime(self, **kwargs):
        return {
            "base_time": self._base_datetime(),
            "valid_time": self._valid_datetime(),
        }

    def _base_datetime(self):
        date = self._get("date", None)
        time = self._get("time", None)
        return datetime.datetime(
            date // 10000,
            date % 10000 // 100,
            date % 100,
            time // 100,
            time % 100,
        )

    def _valid_datetime(self):
        step = self._get("endStep", None)
        return self._base_datetime() + datetime.timedelta(hours=step)

    def _attributes(self, names):
        result = {}
        for name in names:
            result[name] = self._get(name)
        return result


class GribFromDicts(FieldList):
    def __init__(self, list_of_dicts, *args, **kwargs):
        self.list_of_dicts = list_of_dicts
        super().__init__(*args, **kwargs)

    def __getitem__(self, n):
        return VirtualGribField(self.list_of_dicts[n])

    def __len__(self):
        return len(self.list_of_dicts)


source = GribFromDicts
