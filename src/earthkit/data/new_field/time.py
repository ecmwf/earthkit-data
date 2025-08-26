# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.utils.dates import to_datetime
from earthkit.data.utils.dates import to_timedelta

from .spec import Aliases
from .spec import Spec
from .spec import normalise_set_kwargs
from .spec import spec_aliases

ZERO_TIMEDELTA = to_timedelta(0)


@spec_aliases
class Time(Spec):
    """A specification for a time object."""

    KEYS = ("base_datetime", "step", "step_range", "valid_datetime")
    ALIASES = Aliases({"base_datetime": ("forecast_reference_time",), "step": ("forecast_period",)})

    # Do not call this directly, use one of the from_* methods

    _base_datetime = None
    _valid_datetime = None
    _hcast_datetime = None
    _step = ZERO_TIMEDELTA
    _step_range = ZERO_TIMEDELTA

    @classmethod
    def from_valid_datetime(cls, valid_datetime):
        """Set the valid datetime of the time object."""
        return Analysis(valid_datetime=to_datetime(valid_datetime))

    @classmethod
    def from_valid_datetime_and_step(cls, valid_datetime, step, step_range=None):
        """Set the valid datetime of the time object."""
        valid_datetime = to_datetime(valid_datetime)
        step = to_timedelta(step)
        print(f"valid_datetime: {valid_datetime}, step: {step}")
        base_datetime = valid_datetime - step
        return Forecast(base_datetime=base_datetime, step=step, step_range=step_range)

    @classmethod
    def from_base_datetime_and_step(cls, base_datetime, step=None, step_range=None):
        """Set the base datetime of the time object."""
        base_datetime = to_datetime(base_datetime)
        step = to_timedelta(step) if step is not None else to_timedelta(0)
        step_range = to_timedelta(step_range) if step_range is not None else to_timedelta(0)
        return Forecast(
            base_datetime=base_datetime,
            step=step,
            step_range=step_range,
        )

    @classmethod
    def from_dict(cls, d):
        """Create a UserTime object from a dictionary."""
        if not isinstance(d, dict):
            raise TypeError("data must be a dictionary")

        keys = set(list(d.keys()))

        if keys == {"valid_datetime"}:
            return cls.from_valid_datetime(d["valid_datetime"])
        elif keys == {"valid_datetime", "step"}:
            return cls.from_valid_datetime_and_step(
                d["valid_datetime"],
                d["step"],
            )
        elif keys == {"base_datetime"}:
            return cls.from_base_datetime_and_step(d["base_datetime"])
        elif "base_datetime" in keys and "step" in keys:
            return cls.from_base_datetime_and_step(
                d["base_datetime"],
                step=d.get("step"),
                step_range=d.get("step_range", None),
            )

        raise ValueError(f"Invalid keys in data: {keys}. Expected one of {cls.KEYS}.")

    @classmethod
    def from_grib(cls, handle):
        from .grib.time import from_grib

        spec = cls.from_dict(from_grib(handle))
        setattr(spec, "_handle", handle)
        return spec

    def set(self, *args, **kwargs):
        kwargs = normalise_set_kwargs(self, *args, add_spec_keys=False, **kwargs)
        spec = self.from_dict(kwargs)
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
    def step_range(self):
        """Return the forecast period of the time object."""
        return self._step_range


class Analysis(Time):
    """A time specification for analysis data."""

    def __init__(self, valid_datetime, range=None):
        self._base_datetime = to_datetime(valid_datetime)
        self._range = ZERO_TIMEDELTA if range is None else to_timedelta(range)

    @classmethod
    def from_valid_datetime(cls, valid_datetime, step_range=None):
        """Create an AnalysisTimeSpec object from a valid datetime."""
        return cls(valid_datetime, step_range=step_range)

    @property
    def valid_datetime(self):
        """Return the valid datetime of the time object."""
        return self._base_datetime


class Forecast(Time):
    """A time specification for forecast data."""

    # Do not call this directly, use one of the from_* methods
    def __init__(self, base_datetime=None, step=None, step_range=None):
        self._base_datetime = base_datetime
        self._step = step if step is not None else to_timedelta(0)
        self._step_range = step_range if step_range is not None else to_timedelta(0)

    @property
    def base_datetime(self):
        """Return the base datetime of the time object."""
        return self._base_datetime


# class HindcastTimeSpec(ForecastTimeSpec):
#     """A time specification for hindcast data."""

#     def __init__(self, base_datetime=None, step=None, step_range=None, h_datetime=None):
#         super().__init__(base_datetime, step, step_range)
