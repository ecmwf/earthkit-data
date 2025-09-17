# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
from abc import abstractmethod

from earthkit.data.utils.dates import datetime_from_date_and_time
from earthkit.data.utils.dates import to_datetime
from earthkit.data.utils.dates import to_timedelta

from .spec import Aliases
from .spec import SimpleSpec
from .spec import normalise_set_kwargs
from .spec import spec_aliases

ZERO_TIMEDELTA = datetime.timedelta(hours=0)


@spec_aliases
class Time(SimpleSpec):
    """A specification for a time object."""

    KEYS = (
        "base_datetime",
        "step",
        "time_span",
        "valid_datetime",
        "indexing_datetime",
        "reference_datetime",
    )
    ALIASES = Aliases({"base_datetime": ("forecast_reference_time",), "step": ("forecast_period",)})
    INPUT_KEYS = ("date", "time", "step")

    @property
    @abstractmethod
    def base_datetime(self):
        """datetime.datetime: Return the base datetime of the time object."""
        pass

    @property
    @abstractmethod
    def valid_datetime(self):
        """datetime.datetime: Return the valid datetime of the time object."""
        pass

    @property
    @abstractmethod
    def hcast_datetime(self):
        pass

    @property
    @abstractmethod
    def step(self):
        """datetime.timedelta: Return the forecast period of the time object."""
        pass

    @property
    @abstractmethod
    def time_span(self):
        """datetime.timedelta: Return the time span of of the time object."""
        pass

    @property
    @abstractmethod
    def indexing_datetime(self):
        pass

    @property
    @abstractmethod
    def reference_datetime(self):
        pass


class SimpleTime(Time):
    """A specification for a time object."""

    _base_datetime = None
    _hcast_datetime = None
    _step = ZERO_TIMEDELTA
    _time_span = ZERO_TIMEDELTA
    _indexing_datetime = None
    _reference_datetime = None

    def __init__(
        self, base_datetime=None, step=None, time_span=None, indexing_datetime=None, reference_datetime=None
    ):
        if base_datetime is not None:
            self._base_datetime = to_datetime(base_datetime)

        if step is not None:
            self._step = to_timedelta(step)

        if time_span is not None:
            self._time_span = to_timedelta(time_span)

        if indexing_datetime is not None:
            self._indexing_datetime = to_datetime(indexing_datetime)

        if reference_datetime is not None:
            self._reference_datetime = to_datetime(reference_datetime)

    @classmethod
    def from_base_datetime(cls, base_datetime=None):
        """Set the base datetime of the time object."""
        return cls(
            base_datetime=base_datetime,
        )

    @classmethod
    def from_date_and_time(cls, date=None, time=None):
        dt = datetime_from_date_and_time(date, time)
        # return Analysis(valid_datetime=dt)
        return cls(base_datetime=dt)

    @classmethod
    def from_date_and_time_and_step(cls, date=None, time=None, step=None):
        dt = datetime_from_date_and_time(date, time)
        return cls.from_base_datetime_and_step(base_datetime=dt, step=step)

    @classmethod
    def from_valid_datetime(cls, valid_datetime=None, time_span=None):
        """Set the valid datetime of the time object."""
        # return Analysis(valid_datetime=valid_datetime)
        return cls(base_datetime=valid_datetime, time_span=time_span)

    @classmethod
    def from_valid_datetime_and_step(
        cls, valid_datetime=None, step=None, time_span=None, indexing_datetime=None, reference_datetime=None
    ):
        """Set the valid datetime of the time object."""
        valid_datetime = to_datetime(valid_datetime)
        step = to_timedelta(step)
        base_datetime = valid_datetime - step
        return cls(
            base_datetime=base_datetime,
            step=step,
            time_span=time_span,
            indexing_datetime=indexing_datetime,
            reference_datetime=reference_datetime,
        )

    @classmethod
    def from_base_datetime_and_valid_datetime(
        cls,
        base_datetime=None,
        valid_datetime=None,
        time_span=None,
        indexing_datetime=None,
        reference_datetime=None,
    ):
        valid_datetime = to_datetime(valid_datetime)
        base_datetime = to_datetime(base_datetime)
        step = base_datetime - valid_datetime
        return cls(
            base_datetime=base_datetime,
            step=step,
            time_span=time_span,
            indexing_datetime=indexing_datetime,
            reference_datetime=reference_datetime,
        )

    @classmethod
    def from_base_datetime_and_step(
        cls, base_datetime=None, step=None, time_span=None, indexing_datetime=None, reference_datetime=None
    ):
        """Set the base datetime of the time object."""
        return cls(
            base_datetime=base_datetime,
            step=step,
            time_span=time_span,
            indexing_datetime=indexing_datetime,
            reference_datetime=reference_datetime,
        )

    @classmethod
    def from_dict(cls, d):
        """Create a Time object from a dictionary."""
        if not isinstance(d, dict):
            raise TypeError("data must be a dictionary")

        d = normalise_set_kwargs(
            cls, add_spec_keys=False, remove_nones=True, extra_keys=METHOD_MAP.CORE_KEYS, **d
        )

        print("d =", d)
        method_name = METHOD_MAP.get(d.keys())
        if method_name:
            method = getattr(cls, method_name)
            if method_name == VALID_DATETIME_METHOD:
                return method(d["valid_datetime"])
            elif method_name == VALID_DATETIME_AND_STEP_METHOD:
                assert "base_datetime" not in d
                return method(**d)
            elif method_name == BASE_DATETIME_METHOD:
                return method(**d)
            elif method_name == BASE_DATETIME_AND_STEP_METHOD:
                return method(**d)
            elif method_name == DATE_AND_TIME_METHOD:
                return method(**d)
            elif method_name == DATE_AND_TIME_AND_STEP_METHOD:
                return method(**d)

        if not d:
            return cls()

        raise ValueError(f"Invalid keys in data: {list(d.keys())}. Expected one of {cls.KEYS}.")

    def to_dict(self):
        return {
            "valid_datetime": self.valid_datetime,
            "base_datetime": self.base_datetime,
            "step": self.step,
            "time_span": self.time_span,
            "indexing_datetime": self.indexing_datetime,
            "reference_datetime": self.reference_datetime,
        }

    def get_grib_context(self, context) -> dict:
        from .grib.time import COLLECTOR

        COLLECTOR.collect(self, context)

    # @classmethod
    # def from_xarray(cls, owner, selection):
    #     from .xarray.time import from_xarray

    #     spec = cls.from_dict(from_xarray(owner, selection))
    #     return spec

    def set(self, *args, **kwargs):
        kwargs = normalise_set_kwargs(self, *args, add_spec_keys=False, remove_nones=True, **kwargs)

        method_name = UPDATE_METHOD_MAP.get(kwargs.keys())
        if method_name:
            method = getattr(self, method_name)
            if method_name == STEP_UPDATE_METHOD:
                return method(**kwargs)

        return None

    def _set_step(self, step=None, time_span=None):
        d = self.to_dict()
        d.pop("valid_datetime", None)
        d.update(step=step, time_span=time_span)
        spec = self.from_dict(d)
        return spec

    @property
    def base_datetime(self):
        """Return the base datetime of the time object."""
        return self._base_datetime

    @property
    def valid_datetime(self):
        """Return the valid datetime of the time object."""
        return self._base_datetime + self._step

    @property
    def hcast_datetime(self):
        return self._hcast_datetime

    @property
    def step(self):
        """Return the forecast period of the time object."""
        return self._step

    @property
    def time_span(self):
        """Return the forecast period of the time object."""
        return self._time_span

    @property
    def indexing_datetime(self):
        return self._indexing_datetime

    @property
    def reference_datetime(self):
        return self._reference_datetime

    def namespace(self, owner, name, result):
        if name is None or name == "time" or (isinstance(name, (list, tuple)) and "time" in name):
            result["time"] = self.to_dict()

    def check(self, owner):
        pass

    def __getstate__(self):
        state = {}

        state["_base_datetime"] = self._base_datetime
        state["_hcast_datetime"] = self._hcast_datetime
        state["_step"] = self._step
        state["_time_span"] = self._time_span
        state["_indexing_datetime"] = self._indexing_datetime
        state["_reference_datetime"] = self._reference_datetime
        return state

    def __setstate__(self, state):
        self.__init__(
            base_datetime=state["_base_datetime"],
            hcast_datetime=state["_hcast_datetime"],
            step=state["_step"],
            time_span=state["_time_span"],
            indexing_datetime=state["_indexing_datetime"],
            reference_datetime=state["_reference_datetime"],
        )


VALID_DATETIME_METHOD = "from_valid_datetime"
VALID_DATETIME_AND_STEP_METHOD = "from_valid_datetime_and_step"
BASE_DATETIME_METHOD = "from_base_datetime_and_step"
BASE_DATETIME_AND_VALID_DATETIME_METHOD = "from_base_datetime_and_valid_datetime"
BASE_DATETIME_AND_STEP_METHOD = "from_base_datetime_and_step"
DATE_AND_TIME_METHOD = "from_date_and_time"
DATE_AND_TIME_AND_STEP_METHOD = "from_date_and_time_and_step"

METHODS = {
    ("valid_datetime",): VALID_DATETIME_METHOD,
    ("valid_datetime", "step"): VALID_DATETIME_AND_STEP_METHOD,
    ("base_datetime",): BASE_DATETIME_METHOD,
    ("base_datetime", "valid_datetime"): BASE_DATETIME_AND_VALID_DATETIME_METHOD,
    ("base_datetime", "step"): BASE_DATETIME_AND_STEP_METHOD,
    ("date", "time"): DATE_AND_TIME_METHOD,
    ("date", "time", "step"): DATE_AND_TIME_AND_STEP_METHOD,
}


class MethodMap:
    CORE_KEYS = set(["valid_datetime", "base_datetime", "step", "date", "time"])
    MAPPING = {}

    def __init__(self, methods):
        for k, method in methods.items():
            keys = sorted(list(k))
            key = tuple(keys)
            self.MAPPING[key] = method

    @staticmethod
    def get(keys):
        keys_s = set(keys)
        found = tuple(sorted(list(MethodMap.CORE_KEYS.intersection(keys_s))))
        return MethodMap.MAPPING.get(found, None)


STEP_UPDATE_METHOD = "_set_step"

UPDATE_METHODS = {
    ("step",): STEP_UPDATE_METHOD,
}

METHOD_MAP = MethodMap(METHODS)

UPDATE_METHOD_MAP = MethodMap(UPDATE_METHODS)
