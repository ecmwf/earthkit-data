# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import abstractmethod

from earthkit.data.core.constants import ZERO_TIMEDELTA
from earthkit.data.utils.dates import datetime_from_date_and_time, to_datetime, to_timedelta

from .component import (
    SimpleFieldComponent,
    component_keys,
    mark_alias,
    mark_get_key,
    normalise_create_kwargs,
    normalise_set_kwargs,
)


@component_keys
class BaseTime(SimpleFieldComponent):
    @mark_get_key
    @abstractmethod
    def base_datetime(self):
        """Return the base datetime of the time object."""
        pass

    @mark_get_key
    @abstractmethod
    def base_date(self):
        """Return the base datetime of the time object."""
        pass

    @mark_get_key
    @abstractmethod
    def base_time(self):
        """Return the base datetime of the time object."""
        pass

    @mark_get_key
    @abstractmethod
    def valid_datetime(self):
        """Return the valid datetime of the time object."""
        pass

    @mark_get_key
    @abstractmethod
    def step(self):
        """Return the forecast period of the time object."""
        pass

    @mark_alias("base_datetime")
    def forecast_reference_time(self):
        """Return the forecast reference time (alias of `base_datetime`)."""
        pass

    @mark_alias("step")
    def forecast_period(self):
        """Return the forecast period (alias of `step`)."""
        pass

    @mark_get_key
    @abstractmethod
    def forecast_month(self):
        """Return the forecast month."""
        pass

    @mark_get_key
    @abstractmethod
    def indexing_datetime(self):
        """Return the indexing datetime."""
        pass


def create_time(d: dict) -> "BaseTime":
    """Create a BaseTime object from a dictionary.

    Parameters
    ----------
    d : dict
        Dictionary containing time data.

    Returns
    -------
    BaseTime
        The created BaseTime instance.
    """
    if not isinstance(d, dict):
        raise TypeError(f"Cannot create Time from {type(d)}, expected dict")

    # TODO: improve this logic
    if "forecast_month" in d:
        cls = MonthlyForecastTime
    else:
        cls = ForecastTime

    return cls.from_dict(d)


class EmptyTime(BaseTime):
    def base_datetime(self):
        return None

    def base_date(self):
        return None

    def base_time(self):
        return None

    def valid_datetime(self):
        return None

    def step(self):
        return None

    def forecast_month(self):
        return None

    def indexing_datetime(self):
        return None

    @classmethod
    def from_dict(cls, d):
        return cls()

    def to_dict(self):
        return {}

    def set(self, *args, **kwargs):
        raise ValueError("Cannot set values on NoTime")

    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        self.__init__()


class ForecastTime(BaseTime):
    _base_datetime = None
    _step = ZERO_TIMEDELTA

    def __init__(
        self,
        base_datetime=None,
        step=None,
    ):
        if base_datetime is not None:
            self._base_datetime = to_datetime(base_datetime)

        if step is not None:
            self._step = to_timedelta(step)

    def base_datetime(self):
        """Return the base datetime of the time object."""
        return self._base_datetime

    def base_date(self):
        """Return the base datetime of the time object."""
        return self._base_datetime.date()

    def base_time(self):
        """Return the base datetime of the time object."""
        return self._base_datetime.time()

    def valid_datetime(self):
        """Return the valid datetime of the time object."""
        return self._base_datetime + self._step

    def step(self):
        """Return the forecast period of the time object."""
        return self._step

    def forecast_month(self):
        """Return the forecast month."""
        return None

    def indexing_datetime(self):
        """Return the indexing datetime."""
        return None

    def to_dict(self):
        return {
            "valid_datetime": self.valid_datetime(),
            "base_datetime": self.base_datetime(),
            "step": self.step(),
        }

    @classmethod
    def from_base_datetime(
        cls,
        *,
        base_datetime=None,
        step=None,
    ):
        """Set the base datetime of the time object."""
        return cls(
            base_datetime=base_datetime,
            step=step,
        )

    @classmethod
    def from_base_date_and_time(cls, *, base_date=None, base_time=None, step=None):
        dt = datetime_from_date_and_time(base_date, base_time)
        return cls.from_base_datetime(base_datetime=dt, step=step)

    @classmethod
    def from_valid_datetime(
        cls,
        *,
        valid_datetime=None,
        step=None,
    ):
        """Set the valid datetime of the time object."""
        valid_datetime = to_datetime(valid_datetime)
        step = to_timedelta(step) if step is not None else ZERO_TIMEDELTA
        base_datetime = valid_datetime - step
        return cls(
            base_datetime=base_datetime,
            step=step,
        )

    @classmethod
    def from_base_datetime_and_valid_datetime(
        cls,
        *,
        base_datetime=None,
        valid_datetime=None,
    ):
        valid_datetime = to_datetime(valid_datetime)
        base_datetime = to_datetime(base_datetime)
        step = valid_datetime - base_datetime
        return cls(
            base_datetime=base_datetime,
            step=step,
        )

    @classmethod
    def from_dict(cls, d):
        if not isinstance(d, dict):
            raise TypeError("data must be a dictionary")

        KEYS = {
            "valid_datetime",
            "base_datetime",
            "step",
            "base_date",
            "base_time",
        }

        d1 = cls.normalise_create_kwargs(d, allowed_keys=KEYS, remove_nones=True)

        if not d1:
            return cls()

        found = tuple(sorted(d1.keys()))
        METHODS = {
            ("base_datetime", "step"): cls.from_base_datetime,
            ("base_datetime",): cls.from_base_datetime,
            ("base_date",): cls.from_base_date_and_time,
            ("base_date", "base_time"): cls.from_base_date_and_time,
            ("base_date", "base_time", "step"): cls.from_base_date_and_time,
            ("valid_datetime",): cls.from_valid_datetime,
            ("step", "valid_datetime"): cls.from_valid_datetime,
            ("base_datetime", "valid_datetime"): cls.from_base_datetime_and_valid_datetime,
        }

        method = METHODS.get(found)
        if method:
            data = method(**d1)
            return data

        raise ValueError(f"Invalid keys in data: {list(d.keys())}. Expected one of {KEYS}.")

    def set(self, *args, **kwargs):
        KEYS = {
            "valid_datetime",
            "base_datetime",
            "step",
            "base_date",
            "base_time",
        }

        d = self.normalise_set_kwargs(*args, allowed_keys=KEYS, **kwargs)

        if not d:
            return self

        found = tuple(sorted(d.keys()))
        METHODS = {
            ("step",): self._set_generic,
            ("base_datetime",): self._set_generic,
            ("base_datetime", "step"): self._set_generic,
            ("valid_datetime",): self._set_valid_datetime,
            ("step", "valid_datetime"): self._set_valid_datetime_and_step,
            ("base_datetime", "valid_datetime"): self._set_base_datetime_and_valid_datetime,
            (
                "base_datetime",
                "stepvalid_datetime",
            ): self._set_base_datetime_valid_datetime_and_step,
            ("base_date",): self._set_base_date_and_time,
            ("base_date", "base_time"): self._set_base_date_and_time,
            ("base_date", "base_time", "step"): self._set_base_date_and_time,
        }

        method = METHODS.get(found)
        if method:
            data = method(**d)
            return data

        raise ValueError(f"Invalid keys in data: {list(d.keys())}. Allowed keys: {KEYS}.")

    def _set_generic(
        self,
        *,
        base_datetime=None,
        step=None,
    ):
        d = self.to_dict()
        d.pop("valid_datetime", None)

        def _add(key, value):
            if value is not None:
                d[key] = value

        _add("base_datetime", base_datetime)
        _add("step", step)

        return ForecastTime(**d)

    def _set_valid_datetime(self, *, valid_datetime=None):
        valid_datetime = to_datetime(valid_datetime)
        step = valid_datetime - self.base_datetime()
        return self._set_generic(step=step)

    def _set_valid_datetime_and_step(self, *, valid_datetime=None, step=None):
        valid_datetime = to_datetime(valid_datetime)
        step = to_timedelta(step)
        base_datetime = valid_datetime - step
        return self._set_generic(base_datetime=base_datetime, step=step)

    def _set_base_datetime_and_valid_datetime(
        self,
        *,
        base_datetime=None,
        valid_datetime=None,
    ):
        base_datetime = to_datetime(base_datetime)
        valid_datetime = to_datetime(valid_datetime)
        step = valid_datetime - base_datetime
        return self._set_generic(base_datetime=base_datetime, step=step)

    def _set_base_datetime_valid_datetime_and_step(
        self,
        *,
        base_datetime=None,
        valid_datetime=None,
        step=None,
    ):
        base_datetime = to_datetime(base_datetime)
        valid_datetime = to_datetime(valid_datetime)
        step = to_timedelta(step)
        if valid_datetime - base_datetime != step:
            raise ValueError(f"Inconsistent step value. {base_datetime=} + {step=} != {valid_datetime=}")
        return self._set_generic(base_datetime=base_datetime, step=step)

    def _set_base_date_and_time(self, *, base_date, base_time=None, step=None):
        if base_time is None:
            base_time = self.base_datetime.time()
        if step is None:
            step = self.step
        dt = datetime_from_date_and_time(base_date, base_time)
        return self._set_generic(base_datetime=dt, step=step)

    def __getstate__(self):
        state = {}
        state["base_datetime"] = self._base_datetime
        state["step"] = self._step
        return state

    def __setstate__(self, state):
        self.__init__(
            base_datetime=state["base_datetime"],
            step=state["step"],
        )


class AnalysisTime(BaseTime):
    def __init__(
        self,
        valid_datetime=None,
    ):
        if valid_datetime is not None:
            self._valid_datetime = to_datetime(valid_datetime)

    def base_datetime(self):
        """Return the base datetime of the time object."""
        return self._valid_datetime

    def valid_datetime(self):
        """Return the valid datetime of the time object."""
        return self._valid_datetime

    def step(self):
        """Return the forecast period of the time object."""
        return None

    def forecast_month(self):
        """Return the forecast month."""
        return None

    def indexing_datetime(self):
        """Return the indexing datetime."""
        return None

    def to_dict(self):
        return {
            "valid_datetime": self.valid_datetime,
        }

    @classmethod
    def from_valid_datetime(
        cls,
        *,
        valid_datetime=None,
    ):
        """Set the valid datetime of the time object."""
        return cls(
            valid_datetime=valid_datetime,
        )

    @classmethod
    def from_dict(cls, d):
        if not isinstance(d, dict):
            raise TypeError("data must be a dictionary")

        KEYS = {
            "valid_datetime",
        }

        d1 = normalise_create_kwargs(cls, d, allowed_keys=KEYS)
        return cls.from_valid_datetime(**d1)

    def set(self, *args, **kwargs):
        KEYS = {
            "valid_datetime",
        }

        d = normalise_set_kwargs(self, *args, allowed_keys=KEYS, **kwargs)
        return self.from_valid_datetime(**d)

    def __getstate__(self):
        state = {}
        state["valid_datetime"] = self._valid_datetime
        return state

    def __setstate__(self, state):
        self.__init__(
            valid_datetime=state["valid_datetime"],
        )


class MonthlyForecastTime(BaseTime):
    _base_datetime = None
    _step = ZERO_TIMEDELTA

    def __init__(
        self,
        base_datetime=None,
        step=None,
        forecast_month=None,
        indexing_datetime=None,
    ):
        if base_datetime is not None:
            self._base_datetime = to_datetime(base_datetime)

        if step is not None:
            self._step = to_timedelta(step)

        self._forecast_month = forecast_month
        if self._forecast_month is not None:
            self._forecast_month = int(self._forecast_month)

        self._indexing_datetime = indexing_datetime
        if self._indexing_datetime is not None:
            self._indexing_datetime = to_datetime(self._indexing_datetime)

    def base_datetime(self):
        """Return the base datetime of the time object."""
        return self._base_datetime

    def base_date(self):
        """Return the base datetime of the time object."""
        return self._base_datetime.date()

    def base_time(self):
        """Return the base datetime of the time object."""
        return self._base_datetime.time()

    def valid_datetime(self):
        """Return the valid datetime of the time object."""
        return self._base_datetime + self._step

    def step(self):
        """Return the forecast period of the time object."""
        return self._step

    def forecast_month(self):
        """Return the forecast month."""
        return self._forecast_month

    def indexing_datetime(self):
        """Return the indexing datetime."""
        return self._indexing_datetime

    def to_dict(self):
        return {
            "valid_datetime": self.valid_datetime,
            "base_datetime": self.base_datetime,
            "step": self.step,
            "forecast_month": self.forecast_month,
            "indexing_datetime": self.indexing_datetime,
        }

    @classmethod
    def from_base_datetime(
        cls,
        *,
        base_datetime=None,
        step=None,
        forecast_month=None,
        indexing_datetime=None,
    ):
        """Set the base datetime of the time object."""
        return cls(
            base_datetime=base_datetime,
            step=step,
            forecast_month=forecast_month,
            indexing_datetime=indexing_datetime,
        )

    @classmethod
    def from_base_date_and_time(cls, *, base_date=None, base_time=None, step=None, forecast_month=None):
        dt = datetime_from_date_and_time(base_date, base_time)
        return cls.from_base_datetime(base_datetime=dt, step=step, forecast_month=forecast_month)

    @classmethod
    def from_valid_datetime(
        cls,
        *,
        valid_datetime=None,
        step=None,
        forecast_month=None,
        indexing_datetime=None,
    ):
        """Set the valid datetime of the time object."""
        valid_datetime = to_datetime(valid_datetime)
        step = to_timedelta(step) if step is not None else ZERO_TIMEDELTA
        base_datetime = valid_datetime - step
        return cls(
            base_datetime=base_datetime,
            step=step,
            forecast_month=forecast_month,
            indexing_datetime=indexing_datetime,
        )

    @classmethod
    def from_base_datetime_and_valid_datetime(
        cls,
        *,
        base_datetime=None,
        valid_datetime=None,
        forecast_month=None,
        indexing_datetime=None,
    ):
        valid_datetime = to_datetime(valid_datetime)
        base_datetime = to_datetime(base_datetime)
        step = valid_datetime - base_datetime
        return cls(
            base_datetime=base_datetime,
            step=step,
            forecast_month=forecast_month,
            indexing_datetime=indexing_datetime,
        )

    @classmethod
    def from_dict(cls, d, allow_unused=False):
        if not isinstance(d, dict):
            raise TypeError("data must be a dictionary")

        KEYS = {
            "valid_datetime",
            "base_datetime",
            "step",
            "base_date",
            "base_time",
            "forecast_month",
            "indexing_datetime",
        }

        d1 = cls.normalise_create_kwargs(d, allowed_keys=KEYS, remove_nones=True)

        d1_reduced = d1.copy()
        d1_reduced.pop("forecast_month", None)
        d1_reduced.pop("indexing_datetime", None)
        d1_reduced.pop("valid_datetime", None)

        found = tuple(sorted(d1_reduced.keys()))
        METHODS = {
            ("base_datetime",): cls.from_base_datetime,
            ("base_datetime", "step"): cls.from_base_datetime,
            ("base_date",): cls.from_base_date_and_time,
            ("base_date", "base_time"): cls.from_base_date_and_time,
            ("base_date", "base_time", "step"): cls.from_base_date_and_time,
        }

        method = METHODS.get(found)
        if method:
            data = method(**d1)
            return data

        raise ValueError(f"Invalid keys in data: {list(d.keys())}. Expected one of {KEYS}.")

    def set(self, *args, **kwargs):
        raise NotImplementedError("Setting values on MonthlyForecastTime is not implemented yet.")

    def __getstate__(self):
        state = {}
        state["base_datetime"] = self._base_datetime
        state["step"] = self._step
        return state

    def __setstate__(self, state):
        self.__init__(
            base_datetime=state["base_datetime"],
            step=state["step"],
        )
