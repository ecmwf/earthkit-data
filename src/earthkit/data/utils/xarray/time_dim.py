# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.utils.dates import datetime_from_grib

from .dim import DATE_KEYS
from .dim import DATETIME_KEYS
from .dim import STEP_KEYS
from .dim import TIME_KEYS
from .dim import VALID_DATETIME_KEYS
from .dim import Dim
from .dim import DimBuilder
from .dim import DimMode
from .dim import get_keys
from .dim import make_dim


class DateDim(Dim):
    name = "date"
    drop = get_keys(DATE_KEYS + DATETIME_KEYS, drop="date")


class TimeDim(Dim):
    name = "time"
    drop = get_keys(TIME_KEYS + DATETIME_KEYS, drop="time")


# class StepDim(Dim):
#     name = "step"
#     drop = get_keys(STEP_KEYS + VALID_DATETIME_KEYS, drop="step")


class StepDim(Dim):
    name = "step"
    drop = get_keys(STEP_KEYS + VALID_DATETIME_KEYS, drop=["step_timedelta"])


class ValidTimeDim(Dim):
    name = "valid_time"
    drop = get_keys(DATE_KEYS + TIME_KEYS + DATETIME_KEYS, drop="valid_time")


class ForecastRefTimeDim(Dim):
    name = "forecast_reference_time"
    drop = get_keys(DATE_KEYS + TIME_KEYS + DATETIME_KEYS, drop="forecast_reference_time")
    alias = ["base_datetime"]


class IndexingTimeDim(Dim):
    name = "indexing_time"
    drop = get_keys(DATE_KEYS + TIME_KEYS + DATETIME_KEYS, drop="indexing_time")


class ReferenceTimeDim(Dim):
    name = "reference_time"
    drop = get_keys(DATE_KEYS + TIME_KEYS + DATETIME_KEYS, drop="reference_time")


class CustomForecastRefDim(Dim):
    @staticmethod
    def _datetime(val):
        if not val:
            return None
        else:
            try:
                date, time = val.split("_")
                return datetime_from_grib(int(date), int(time)).isoformat()
            except Exception:
                return val

    def __init__(self, owner, keys, *args, active=True, **kwargs):
        if isinstance(keys, str):
            self.key = keys
        elif isinstance(keys, list) and len(keys) == 2:
            date = keys[0]
            time = keys[1]
            self.key = self._name(date, time)
            self.drop = [date, time]
            if active:
                owner.register_remapping(
                    {self.key: "{" + date + "}_{" + time + "}"},
                    patch={self.key: CustomForecastRefDim._datetime},
                )
        else:
            raise ValueError(f"Invalid keys={keys}")
        super().__init__(owner, *args, active=active, **kwargs)

    def _name(self, date, time):
        if date.endswith("Date") and time.endswith("Time") and date[:-4] == time[:-4]:
            return date[:-4] + "_time"
        return f"{date}_{time}"


class ForecastTimeDimMode(DimMode):
    name = "forecast"
    DATES = ["date", "dataDate"]
    TIMES = ["time", "dataTime"]

    def build(self, profile, owner, active=True):
        ref_time_key, ref_time_name = owner.dim_roles.role("forecast_reference_time", raise_error=False)

        if ref_time_key == "forecast_reference_time":
            ref_time_dim = ForecastRefTimeDim(owner, name=ref_time_name, active=active)
        elif ref_time_key:
            ref_time_dim = make_dim(owner, name=ref_time_name, key=ref_time_key, active=active)
        else:
            date, _ = owner.dim_roles.role("date")
            time, _ = owner.dim_roles.role("time")
            built_in = date in self.DATES and time in self.TIMES
            if built_in:
                ref_time_dim = ForecastRefTimeDim(owner, name=ref_time_name, active=active)
            else:
                ref_time_dim = CustomForecastRefDim(owner, [date, time], name=ref_time_name, active=active)

        step_key, step_name = owner.dim_roles.role("step")
        step_dim = make_dim(owner, name=step_name, key=step_key, active=active)

        self.register_ref_time_key(ref_time_dim.key)
        self.register_step_key(step_dim.key)

        return {d.name: d for d in [ref_time_dim, step_dim]}

    def register_ref_time_key(self, name):
        global BASE_DATETIME_KEYS
        global VALID_DATETIME_KEYS
        if name not in BASE_DATETIME_KEYS:
            BASE_DATETIME_KEYS.append(name)

    def register_step_key(self, name):
        global STEP_KEYS
        if name not in STEP_KEYS:
            STEP_KEYS.append(name)


class ValidTimeDimMode(DimMode):
    name = "valid_time"
    default = {"valid_time": "valid_time"}


class RawTimeDimMode(DimMode):
    name = "raw"

    def build(self, profile, owner, active=True):
        dims = {}
        for k in ["date", "time", "step"]:
            key, name = owner.dim_roles.role(k)
            dims[name] = key
        return super().build(profile, owner, active=active, dims=dims)


class TimeDimBuilder(DimBuilder):
    name = "time"

    def __init__(self, profile, owner, data=None):
        if owner.time_dim_mode == "auto":
            mode = self.find_mode(data)

        mode = TIME_DIM_MODES.get(owner.time_dim_mode, None)
        if mode is None:
            raise ValueError(f"Unknown time_dim_mode={owner.time_dim_mode}")

        mode = mode()
        self.used = mode.build(profile, owner)
        self.ignored = {
            k: v().build(profile, owner, active=False) for k, v in TIME_DIM_MODES.items() if v != mode
        }

    @staticmethod
    def find_mode(data):
        """Determine the time dimension mode based on the metadata of the first field in the data."""
        FORECAST_MODE = ForecastTimeDimMode.name
        VALID_TIME_MODE = ValidTimeDimMode.name

        keys = ["stream", "type", "class", "stepType"]
        field = data[0]
        md = field.metadata(keys, default=None)

        if md["type"] == "an":
            return VALID_TIME_MODE
        if md["stream"] == "oper" and md["type"] == "fc":
            return FORECAST_MODE

        return FORECAST_MODE


TIME_DIM_MODES = {v.name: v for v in [ForecastTimeDimMode, ValidTimeDimMode, RawTimeDimMode]}
PREDEFINED_DIMS = [ForecastRefTimeDim, DateDim, TimeDim, StepDim, ValidTimeDim]
