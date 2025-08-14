# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import ABCMeta
from abc import abstractmethod

from earthkit.data.utils.dates import datetime_from_grib
from earthkit.data.utils.dates import to_datetime
from earthkit.data.utils.dates import to_timedelta


class FieldTimeBase(metaclass=ABCMeta):
    KEYS = (
        "base_datetime",
        "forecast_reference_time",
        "valid_datetime",
        "step",
        "range",
    )

    @property
    @abstractmethod
    def base_datetime(self):
        """Return the valid datetime of the time object."""
        pass

    @property
    def forecast_reference_time(self):
        """Return the forecast reference time of the time object."""
        return self.base_datetime

    @property
    @abstractmethod
    def valid_datetime(self):
        """Return the valid datetime of the time object."""
        pass

    @property
    @abstractmethod
    def step(self):
        """Return the forecast period of the time object."""
        pass

    @property
    @abstractmethod
    def step_range(self):
        """Return the forecast period of the time object."""
        pass

    @property
    @abstractmethod
    def spec(self):
        """Return the specification of the time object."""
        pass

    # def _get(self, key):
    #     """Get the value of the key."""
    #     if key in self.KEYS:
    #         return getattr(self, key)
    #     raise KeyError(f"Key '{key}' not found in Time object.")


class FieldTime(FieldTimeBase):
    _spec = None

    def __init__(self, spec=None):
        if spec is not None:
            self._spec = spec

    @property
    def base_datetime(self):
        """Return the base datetime of the time object."""
        return self.spec.base_datetime

    @property
    def valid_datetime(self):
        """Return the valid datetime of the time object."""
        return self.spec.valid_datetime

    @property
    def step(self):
        """Return the forecast period of the time object."""
        return self.spec.step

    @property
    def step_range(self):
        """Return the forecast period of the time object."""
        return self.spec.step_range

    @property
    def spec(self):
        """Return the specification of the time object."""
        if self._spec is None:
            raise ValueError("Time specification is not set.")
        return self._spec

    def set(self, **kwargs):
        """Set the time specification."""
        _kwargs = {k: v for k, v in kwargs.items() if k in self.KEYS}
        if _kwargs:
            spec = self.spec.set(**_kwargs)
            return FieldTime(spec=spec)
        return self

    # def __getattr__(self, item):
    #     # print("calling __getattr__ on WrappedTime", item)
    #     return getattr(self.spec, item)


# TODO: this will be implemented in a separate package
class TimeSpec:
    """A specification for a time object."""

    KEYS = {"base_datetime", "step", "step_range", "valid_datetime"}

    # Do not call this directly, use one of the from_* methods
    def __init__(self, base_datetime=None, step=None, step_range=None):
        self._base_datetime = base_datetime
        self._step = step if step is not None else to_timedelta(0)
        self._step_range = step_range if step_range is not None else to_timedelta(0)

    @classmethod
    def from_valid_datetime(cls, valid_datetime):
        """Set the valid datetime of the time object."""
        return cls(base_datetime=to_datetime(valid_datetime), step=to_timedelta(0))

    @classmethod
    def from_valid_datetime_and_step(cls, valid_datetime, step, step_range=None):
        """Set the valid datetime of the time object."""
        valid_datetime = to_datetime(valid_datetime)
        step = to_timedelta(step)
        base_datetime = valid_datetime - step
        return cls(base_datetime=base_datetime, step=step, step_range=step_range)

    @classmethod
    def from_base_datetime(cls, base_datetime, step=None, step_range=None):
        """Set the base datetime of the time object."""
        base_datetime = to_datetime(base_datetime)
        step = to_timedelta(step) if step is not None else to_timedelta(0)
        step_range = to_timedelta(step_range) if step_range is not None else to_timedelta(0)
        return cls(
            base_datetime=base_datetime,
            step=step,
            step_range=step_range,
        )

    @classmethod
    def from_spec(cls, spec, **kwargs):
        """Create a TimeSpec object from a field."""
        kwargs = kwargs.copy()
        _kwargs = {}

        for name in cls.KEYS:
            v = kwargs.pop(name, None)
            if v is not None:
                _kwargs[name] = v
            else:
                _kwargs[name] = getattr(spec, name)

        return cls(**_kwargs, **kwargs)

    @classmethod
    def from_dict(cls, data):
        """Create a UserTime object from a dictionary."""
        if not isinstance(data, dict):
            raise TypeError("data must be a dictionary")

        keys = [k for k in data.keys() if k in cls.KEYS]
        if keys == ["valid_datetime"]:
            return cls.from_valid_datetime(data["valid_datetime"])
        elif keys == ["valid_datetime", "step"]:
            return cls.from_valid_datetime_and_step(
                data["valid_datetime"],
                data["step"],
            )
        elif "base_datetime" in keys and "step" in keys:
            return cls.from_base_datetime(
                data["base_datetime"],
                step=data.get("step"),
                step_range=data.get("step_range", None),
            )

        raise ValueError(f"Invalid keys in data: {keys}. Expected one of {cls.KEYS}.")

    @classmethod
    def from_grib(cls, handle):
        def _get(key, default=None):
            return handle.get(key, default)

        def _datetime(date_key, time_key):
            date = _get(date_key, None)
            if date is not None:
                time = _get(time_key, None)
                if time is not None:
                    return datetime_from_grib(date, time)
            return None

        base = _datetime("dataDate", "dataTime")
        v = _get("endStep", None)
        if v is None:
            v = _get("step", None)
        step = to_timedelta(v)

        end = _get("endStep", None)
        if end is None:
            return to_timedelta(0)

        start = _get("startStep", None)
        if start is None:
            start = to_timedelta(0)

        step_range = to_timedelta(end) - to_timedelta(start)

        return cls(
            base_datetime=to_datetime(base),
            step=step,
            step_range=step_range,
        )

    def to_dict(self):
        """Convert the TimeSpec object to a dictionary."""
        return {
            "base_datetime": self.base_datetime,
            "valid_datetime": self.valid_datetime,
            "step": self.step,
            "range": self.range,
        }

    @property
    def base_datetime(self):
        """Return the base datetime of the time object."""
        return self._base_datetime

    @property
    def forecast_reference_time(self):
        """Return the forecast reference time of the time object."""
        return self._base_datetime

    @property
    def valid_datetime(self):
        """Return the valid datetime of the time object."""
        return self._base_datetime + self._step

    @property
    def step(self):
        """Return the forecast period of the time object."""
        return self._step

    @property
    def step_range(self):
        """Return the forecast period of the time object."""
        return self._step_range

    def set_step(self, step):
        """Set the step value."""
        step = to_timedelta(step)
        return TimeSpec.from_spec(
            self,
            step=step,
        )

    def set(self, **kwargs):
        """Set the time specification."""

        if "step" in kwargs:
            return self.set_step(kwargs["step"])

        return None
