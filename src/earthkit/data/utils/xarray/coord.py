# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import math

LOG = logging.getLogger(__name__)


class DictDiffInfo:
    def __init__(self, same, diff_dict={}, diff_text=str()):
        self.same = same
        self.diff_dict = dict(**diff_dict)
        self.diff_text = diff_text


class DictDiff:
    @staticmethod
    def diff(vals1, vals2):
        if not isinstance(vals1, dict):
            raise ValueError(f"Unsupported type for vals1: {type(vals1)}. Expecting dict")

        if not isinstance(vals2, dict):
            raise ValueError(f"Unsupported type for vals2: {type(vals2)}. Expecting dict")

        diff_dict = {}
        if len(vals1) != len(vals2):
            return ListDiffInfo(False, ListDiff.VALUE_DIFF, f"Length mismatch: {len(vals1)} != {len(vals2)}")

        for k, v1 in vals1.items():
            if k not in vals2:
                diff_dict[k] = (None, v1)
            else:
                v2 = vals2[k]
                same, _ = ListDiff._compare(v1, v2)
                if not same:
                    diff_dict[k] = (v2, v1)

        if diff_dict:
            diff_text = ", ".join([f"{k}: {v[0]} != {v[1]}" for k, v in diff_dict.items()])
            return DictDiffInfo(False, diff_dict=diff_dict, diff_text=diff_text)
        else:
            return DictDiffInfo(True)


class ListDiffInfo:
    def __init__(self, same, diff_type=None, diff_text=str(), diff_index=-1):
        self.same = same
        self.type = diff_type
        self.diff_text = diff_text
        self.diff_index = diff_index


class ListDiff:
    VALUE_DIFF = 0
    TYPE_DIFF = 1

    @staticmethod
    def _compare(v1, v2):
        if isinstance(v1, int) and isinstance(v2, int):
            return v1 == v2, ListDiff.VALUE_DIFF
        elif isinstance(v1, float) and isinstance(v2, float):
            return math.isclose(v1, v2, rel_tol=1e-9), ListDiff.VALUE_DIFF
        elif isinstance(v1, str) and isinstance(v2, str):
            return v1 == v2, ListDiff.VALUE_DIFF
        elif type(v1) is not type(v2):
            return False, ListDiff.TYPE_DIFF
        else:
            raise ValueError(f"Unsupported type: {type(v1)}")

    @staticmethod
    def diff(vals1, vals2, name=str()):
        if not isinstance(vals1, (list, tuple)):
            raise ValueError(f"Unsupported type for vals1: {type(vals1)}. Expecting list/tuple")

        if not isinstance(vals2, (list, tuple)):
            raise ValueError(f"Unsupported type for vals2: {type(vals2)}. Expecting list/tuple")

        if len(vals1) != len(vals2):
            return ListDiffInfo(False, ListDiff.VALUE_DIFF, f"Length mismatch: {len(vals1)} != {len(vals2)}")

        for i, (v1, v2) in enumerate(zip(vals1, vals2)):
            same, diff = ListDiff._compare(v1, v2)
            if not same:
                if diff == ListDiff.VALUE_DIFF:
                    diff = f"Value mismatch at {name}[{i}]: {v1} != {v2}"
                elif diff == ListDiff.TYPE_DIFF:
                    diff = f"Type mismatch at {name}[{i}]: {type(v1)} != {type(v2)}"
                return ListDiffInfo(False, ListDiff.VALUE_DIFF, diff, i)
        return ListDiffInfo(True)


def list_to_str(vals, n=10):
    try:
        if len(vals) <= n:
            return str(vals)
        else:
            lst = "[" + ", ".join(str(vals[: n - 1])) + "..., " + str(vals[-1]) + "]"
            return lst
    except Exception:
        return vals


class Coord:
    def __init__(self, name, vals, dims=None, ds=None):
        self.name = name
        self.vals = vals
        self.dims = dims
        if not self.dims:
            self.dims = (self.name,)

    @staticmethod
    def make(name, *args, **kwargs):
        if name in [
            "forecast_reference_time",
            "date",
            "hdate",
            "andate",
            "valid_time",
            "valid_datetime",
            "base_datetime" "reference_time",
            "indexing_time",
        ]:
            return DateTimeCoord(name, *args, **kwargs)
        if name in ["time", "antime"]:
            return TimeCoord(name, *args, **kwargs)
        elif name in ["step"]:
            return StepCoord(name, *args, **kwargs)
        elif name in ["level", "levelist"]:
            return LevelCoord(name, *args, **kwargs)
        return Coord(name, *args, **kwargs)

    def to_xr_var(self, profile):
        import xarray

        c = profile.rename_coords({self.name: None})
        name = list(c.keys())[0]
        return xarray.Variable(
            profile.rename_dims(self.dims), self.convert(profile), self.attrs(name, profile)
        )

    def convert(self, profile):
        return self.vals

    def encoding(self, profile):
        return {}

    def attrs(self, name, profile):
        return profile.add_coord_attrs(name)


class DateTimeCoord(Coord):
    def convert(self, profile):
        if profile.decode_time:
            from earthkit.data.utils.dates import to_datetime_list

            return to_datetime_list(self.vals)
        return super().convert(profile)


class TimeCoord(Coord):
    pass
    # def convert(self, profile):
    #     if profile.decode_time:
    #         from earthkit.data.utils.dates import to_time_list

    #         return to_time_list(self.vals)
    #     return super().convert(profile)


class StepCoord(Coord):
    def convert(self, profile):
        if profile.decode_time:
            from earthkit.data.utils.dates import step_to_delta

            return [step_to_delta(x) for x in self.vals]
        return super().convert(profile)

    def encoding(self, profile):
        if profile.decode_time:
            return ({"dtype": "timedelta64[s]"},)
        return {}


class LevelCoord(Coord):
    def __init__(self, name, vals, dims=None, ds=None):
        self.levtype = {}
        if ds is not None:
            for k in ["levtype", "typeOfLevel"]:
                if k in ds.indices():
                    self.levtype[k] = ds.index(k)[0]
                else:
                    v = ds[0].metadata(k, default=None)
                    if v is not None:
                        self.levtype[k] = v

        super().__init__(name, vals, dims)

    def attrs(self, name, profile):
        return profile.add_level_coord_attrs(name, self.levtype)
