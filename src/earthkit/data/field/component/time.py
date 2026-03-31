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

from earthkit.data.core.constants import ZERO_TIMEDELTA
from earthkit.data.utils.dates import datetime_from_date_and_time, to_datetime, to_timedelta

from .component import (
    SimpleFieldComponent,
    _normalise_create_kwargs,
    _normalise_set_kwargs,
    component_keys,
    mark_alias,
    mark_get_key,
)


@component_keys
class TimeBase(SimpleFieldComponent):
    """Base class for time component of a field.

    This class defines the interface for time components, which can represent
    different types of time information. Some of the methods may not be applicable to all time
    types (e.g. :meth:`forecast_month`), and may return None.

    The temporal information can be accessed by methods like :meth:`base_datetime`,
    :meth:`valid_datetime`, and :meth:`step`. Each of these methods has an associated key
    that can be used in the :meth:`get` method to retrieve the corresponding information. The list
    of supported keys are as follows:

    - "base_datetime"
    - "base_date"
    - "base_time"
    - "valid_datetime"
    - "step"
    - "forecast_month"
    - "indexing_datetime"
    - "forecast_reference_time" (alias of "base_datetime")
    - "forecast_period" (alias of "step")

    Depending on the type of time information available, some of these keys may not be supported
    and will return None in the subclasses. For example, the "forecast_month" key is only supported
    for monthly forecast time, and will return None for other time types.

    Typically, this object is used as a component of a field, and can be accessed via the :attr:`time`
    attribute of a field. The keys above can also be accessed via the :meth:`get` method of the field,
    using the "time." prefix.

    The following example demonstrates how to access the time information from a field using
    various methods and keys:

        >>> import earthkit.data as ekd
        >>> field = ekd.from_source("sample", "test.grib").to_fieldlist()[0]
        >>> field.time.base_datetime()
        datetime.datetime(2020, 1, 1, 0, 0)
        >>> field.time.get("base_datetime")
        datetime.datetime(2020, 1, 1, 0, 0)
        >>> field.get("time.base_datetime")
        datetime.datetime(2020, 1, 1, 0, 0)

    The time component is immutable. The :meth:`set` method to create a new
    instance with updated values. For example, the following code creates a new time
    component with an updated step:

        >>> new_time = field.time.set(step=3)
        >>> new_time.step()
        datetime.timedelta(hours=3)

    We can also call the Field's :meth:`set` method to create a new field with an updated time component:

        >>> new_field = field.set({"time.step": 3})
        >>> new_field.time.step()
        datetime.timedelta(hours=3)

    """

    @mark_get_key
    @abstractmethod
    def base_datetime(self) -> "datetime.datetime":
        """Return the base datetime.

        The base datetime is the datetime from which a forecast is made. For analysis data, the
        base datetime is the same as the valid datetime.

        Returns
        -------
        datetime.datetime
            The base datetime of the time object.
        """
        pass

    @mark_get_key
    @abstractmethod
    def base_date(self) -> "datetime.date":
        """Return the date part of the :meth:`base_datetime`.

        Returns
        -------
        datetime.date
            The date part of the base datetime.
        """
        pass

    @mark_get_key
    @abstractmethod
    def base_time(self) -> "datetime.time":
        """Return the time part of the :meth:`base_datetime`.

        Returns
        -------
        datetime.time
            The time part of the base datetime.
        """
        pass

    @mark_get_key
    @abstractmethod
    def valid_datetime(self) -> "datetime.datetime":
        """Return the valid datetime.

        Returns
        -------
        datetime.datetime
            The valid datetime.
        """
        pass

    @mark_get_key
    @abstractmethod
    def step(self) -> "datetime.timedelta":
        """Return the forecast period.

        Returns
        -------
        datetime.timedelta
            The forecast period.
        """
        pass

    @mark_alias("base_datetime")
    def forecast_reference_time(self) -> "datetime.datetime":
        pass

    @mark_alias("step")
    def forecast_period(self) -> "datetime.timedelta":
        pass

    @mark_get_key
    @abstractmethod
    def forecast_month(self) -> int:
        """Return the forecast month.

        Returns
        -------
        int
            The forecast month. For non-monthly forecast time types, this method returns None.
        """
        pass

    @mark_get_key
    @abstractmethod
    def indexing_datetime(self) -> "datetime.datetime":
        """Return the indexing datetime.

        Returns
        -------
        datetime.datetime
            The indexing datetime. For non-indexed time types, this method returns None.
        """
        pass


def create_time(d: dict) -> "TimeBase":
    """Create a TimeBase object from a dictionary.

    Parameters
    ----------
    d : dict
        Dictionary containing time data.

    Returns
    -------
    TimeBase
        The created TimeBase instance.
    """
    if not isinstance(d, dict):
        raise TypeError(f"Cannot create Time from {type(d)}, expected dict")

    # TODO: improve this logic
    if "forecast_month" in d:
        cls = MonthlyForecastTime
    else:
        cls = ForecastTime

    return cls.from_dict(d)


class EmptyTime(TimeBase):
    """A TimeBase object representing an empty time component."""

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
        raise ValueError("Cannot set values on EmptyTime")

    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        self.__init__()


class ForecastTime(TimeBase):
    """Field time component for forecasts.

    Parameters
    ----------
    base_datetime : datetime.datetime, optional
        The base datetime of the forecast. Default is None.
    step : datetime.timedelta, string, or number, optional
        The forecast period. Default is None. Integer values are treated a
        hours, and string values are parsed using the `to_timedelta` function.

    """

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

    def base_datetime(self) -> "datetime.datetime":
        return self._base_datetime

    def base_date(self) -> "datetime.date":
        return self._base_datetime.date()

    def base_time(self) -> "datetime.time":
        return self._base_datetime.time()

    def valid_datetime(self) -> "datetime.datetime":
        """Return the valid datetime of the time object.

        It is calculated as the sum of the base datetime and the step.
        """
        return self._base_datetime + self._step

    def step(self) -> "datetime.timedelta":
        return self._step

    def forecast_month(self) -> None:
        """Return the forecast month.

        Forecast month is not defined for this time type, so return None.
        """
        return None

    def indexing_datetime(self) -> None:
        """Return the indexing datetime.

        Indexing datetime is not defined for this time type, so return None.
        """
        return None

    def to_dict(self):
        """Return a dictionary representation of the time object."""
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
        """Create a ForecastTime object from a base datetime and step.

        Parameters
        ----------
        base_datetime : datetime.datetime, string, int
            The base datetime of the forecast. String or integer values are parsed
            using the `to_datetime` function.
        step : datetime.timedelta, string, or number, optional
            The forecast period. Default is None, which is treated as zero timedelta.
            Integer values are treated as hours, and string values
            are parsed using the `to_timedelta` function.

        Returns
        -------
        ForecastTime
            The created ForecastTime instance.
        """
        return cls(
            base_datetime=base_datetime,
            step=step,
        )

    @classmethod
    def from_base_date_and_time(cls, *, base_date=None, base_time=None, step=None):
        """Create a ForecastTime object from a base date, base time, and  step.

        Parameters
        ----------
        base_date : datetime.date, string, int, optional
            The base date of the forecast. String or integer values are parsed
            using the `to_datetime` function.
        base_time : datetime.time, string, int, optional
            The base time of the forecast. Default is None, which is treated as 00:00:00.
            String or integer values are parsed using the `to_time` function.
        step : datetime.timedelta, string, or number
            The forecast period. Default is None, which is treated as zero timedelta.
            Integer values are treated as hours, and string values are parsed using
            the `to_timedelta` function.

        Returns
        -------
        ForecastTime
            The created ForecastTime instance.
        """
        dt = datetime_from_date_and_time(base_date, base_time)
        return cls.from_base_datetime(base_datetime=dt, step=step)

    @classmethod
    def from_valid_datetime(
        cls,
        *,
        valid_datetime=None,
        step=None,
    ):
        """Create a ForecastTime object from a valid datetime and step.

        The base datetime is calculated as the difference between the valid datetime and the step.

        Parameters
        ----------
        valid_datetime : datetime.datetime, string, int
            The valid datetime of the forecast. String or integer values are
            parsed using the `to_datetime` function.
        step : datetime.timedelta, string, or number
            The forecast period. Default is None, which is treated as zero timedelta.
            Integer values are treated as hours, and string values are parsed using the
            `to_timedelta` function.


        Returns
        -------
        ForecastTime
            The created ForecastTime instance.
        """
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
        """Create a ForecastTime object from a base datetime and valid datetime.

        The step is calculated as the difference between the valid datetime and the base datetime.

        Parameters
        ----------
        base_datetime : datetime.datetime, string, int
            The base datetime of the forecast. String or integer values are
            parsed using the `to_datetime` function.
        valid_datetime : datetime.datetime, string, int
            The valid datetime of the forecast. String or integer values are
            parsed using the `to_datetime` function.

        Returns
        -------
        ForecastTime
            The created ForecastTime instance.
        """
        valid_datetime = to_datetime(valid_datetime)
        base_datetime = to_datetime(base_datetime)
        step = valid_datetime - base_datetime
        return cls(
            base_datetime=base_datetime,
            step=step,
        )

    @classmethod
    def from_dict(cls, d):
        """Create a ForecastTime object from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary containing time data. The allowed keys are:

            - "valid_datetime"
            - "base_datetime"
            - "step"
            - "base_date"
            - "base_time"

            All aliases of these keys are also allowed. The method used to create the
            ForecastTime object is determined by the combination of keys provided in the dictionary.

            The datetime values can be provided as datetime objects, strings, or integers.
            String and integer values are parsed using the `to_datetime` function.

            The date values can be provided as datetime.date objects, strings, or integers.
            String and integer values are parsed using the `to_datetime` function.

            The time values can be provided as datetime.time objects, strings, or integers.
            String and integer values are parsed using the `to_time` function.

            The "step" value can be a datetime.timedelta, string, or number. Integer values are treated
            as hours, and string values are parsed using the `to_timedelta` function.

        Returns
        -------
        ForecastTime
            The created ForecastTime instance.

        """
        if not isinstance(d, dict):
            raise TypeError("data must be a dictionary")

        KEYS = {
            "valid_datetime",
            "base_datetime",
            "step",
            "base_date",
            "base_time",
        }

        d1 = cls._normalise_create_kwargs(d, allowed_keys=KEYS, remove_nones=True)

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
        """Create a new instance with updated data.

        Parameters
        ----------
        args : tuple
            Positional arguments containing time data. Only dictionaries are allowed.
        kwargs : dict
            Keyword arguments containing time data.

        Returns
        -------
        ForecastTime
            The created ForecastTime instance.

        Notes
        -----
        The allowed keys in the dictionaries and keyword arguments are:

        - "valid_datetime"
        - "base_datetime"
        - "step"
        - "base_date"
        - "base_time"

        All aliases of these keys are also allowed. The method used to create the
        new ForecastTime object is determined by the combination of keys provided in the arguments.

        The "step" value can be a datetime.timedelta, string, or number. Integer values are treated
        as hours, and string values are parsed using the `to_timedelta` function.

        The following special rules apply for ambiguous cases:

        - If only "base_datetime" are provided, the "step" from the current object is kept
          and the "valid_datetime" is updated accordingly.
        - If only "step" is provided, the "base_datetime" from the current object is kept
          and the "valid_datetime" is updated accordingly.
        """
        KEYS = {
            "valid_datetime",
            "base_datetime",
            "step",
            "base_date",
            "base_time",
        }

        d = self._normalise_set_kwargs(*args, allowed_keys=KEYS, **kwargs)

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
                "step",
                "valid_datetime",
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


class AnalysisTime(TimeBase):
    """Field time component for analyses.

    Parameters
    ----------
    valid_datetime : datetime.datetime, optional
        The valid datetime of the analysis. Default is None.

    """

    def __init__(
        self,
        valid_datetime=None,
    ):
        if valid_datetime is not None:
            self._valid_datetime = to_datetime(valid_datetime)

    def base_datetime(self) -> "datetime.datetime":
        """Return the base datetime of the time object.

        This is the same as the valid datetime for analysis time.

        Returns
        -------
        datetime.datetime
            The base datetime of the time object.
        """
        return self._valid_datetime

    def valid_datetime(self) -> "datetime.datetime":
        """Return the valid datetime of the time object."""
        return self._valid_datetime

    def step(self) -> None:
        """Return the forecast period of the time object.

        For analysis time, the step is not defined, so return None.
        """
        return None

    def forecast_month(self) -> None:
        """Return the forecast month.

        For analysis time, the forecast month is not defined, so return None.
        """
        return None

    def indexing_datetime(self) -> None:
        """Return the indexing datetime.

        For analysis time, the indexing datetime is not defined, so return None.
        """
        return None

    def to_dict(self) -> dict:
        """Return a dictionary representation of the time object."""
        return {
            "valid_datetime": self.valid_datetime,
        }

    @classmethod
    def from_valid_datetime(
        cls,
        *,
        valid_datetime=None,
    ):
        """Create an AnalysisTime object from a valid datetime.

        Parameters
        ----------
        valid_datetime : datetime.datetime

        Returns
        -------
        AnalysisTime
            The created AnalysisTime instance.
        """
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

        d1 = _normalise_create_kwargs(cls, d, allowed_keys=KEYS)
        return cls.from_valid_datetime(**d1)

    def set(self, *args, **kwargs):
        KEYS = {
            "valid_datetime",
        }

        d = _normalise_set_kwargs(self, *args, allowed_keys=KEYS, **kwargs)
        return self.from_valid_datetime(**d)

    def __getstate__(self):
        state = {}
        state["valid_datetime"] = self._valid_datetime
        return state

    def __setstate__(self, state):
        self.__init__(
            valid_datetime=state["valid_datetime"],
        )


class MonthlyForecastTime(TimeBase):
    """
    Field time component for monthly forecasts.

    Parameters
    ----------
    base_datetime : datetime.datetime, optional
        The base datetime of the forecast. Default is None.
    step : datetime.timedelta, string, or number, optional
        The forecast period. Default is None. Integer values are treated
        as hours, and string values are parsed using the `to_timedelta` function.
    forecast_month : int, optional
        The forecast month. Default is None.
    indexing_datetime : datetime.datetime, optional
        The indexing datetime. Default is None.

    """

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

    def base_datetime(self) -> "datetime.datetime":
        return self._base_datetime

    def base_date(self) -> "datetime.date":
        return self._base_datetime.date()

    def base_time(self) -> "datetime.time":
        return self._base_datetime.time()

    def valid_datetime(self) -> "datetime.datetime":
        """Return the valid datetime of the time object.

        It is calculated as the sum of the base datetime and the step
        """
        return self._base_datetime + self._step

    def step(self) -> "datetime.timedelta":
        return self._step

    def forecast_month(self) -> int:
        """Return the forecast month."""
        return self._forecast_month

    def indexing_datetime(self) -> "datetime.datetime":
        """Return the indexing datetime."""
        return self._indexing_datetime

    def to_dict(self) -> dict:
        """Return a dictionary representation of the time object."""
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
        """Create a MonthlyForecastTime object from a base datetime and step.

        Parameters
        ----------
        base_datetime : datetime.datetime, optional
            The base datetime of the forecast. Default is None.
        step : datetime.timedelta, string, or number, optional
            The forecast period. Default is None. Integer values are treated
            as hours, and string values are parsed using the `to_timedelta` function.
        forecast_month : int, optional
            The forecast month. Default is None.
        indexing_datetime : datetime.datetime, optional
            The indexing datetime. Default is None.

        Returns
        -------
        MonthlyForecastTime
            A new MonthlyForecastTime object.
        """
        return cls(
            base_datetime=base_datetime,
            step=step,
            forecast_month=forecast_month,
            indexing_datetime=indexing_datetime,
        )

    @classmethod
    def from_base_date_and_time(cls, *, base_date=None, base_time=None, step=None, forecast_month=None):
        """Create a MonthlyForecastTime object from a base date and time.

        Parameters
        ----------
        base_date : datetime.date, optional
            The base date of the forecast. Default is None.
        base_time : datetime.time, optional
            The base time of the forecast. Default is None.
        step : datetime.timedelta, string, or number, optional
            The forecast period. Default is None. Integer values are treated
            as hours, and string values are parsed using the `to_timedelta` function.
        forecast_month : int, optional
            The forecast month. Default is None.

        Returns
        -------
        MonthlyForecastTime
            A new MonthlyForecastTime object.
        """
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
        """Create a MonthlyForecastTime object from a valid datetime.

        The base datetime is calculated as the difference between the valid datetime and the step.

        Parameters
        ----------
        valid_datetime : datetime.datetime, optional
            The valid datetime of the forecast. Default is None.
        step : datetime.timedelta, string, or number, optional
            The forecast period. Default is None. Integer values are treated
            as hours, and string values are parsed using the `to_timedelta` function.
        forecast_month : int, optional
            The forecast month. Default is None.
        indexing_datetime : datetime.datetime, optional
            The indexing datetime. Default is None.

        Returns
        -------
        MonthlyForecastTime
            A new MonthlyForecastTime object.
        """
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
        """Create a MonthlyForecastTime object from a base datetime and valid datetime.


        The step is calculated as the difference between the valid datetime and the base datetime.

        Parameters
        ----------
        base_datetime : datetime.datetime, optional
            The base datetime of the forecast. Default is None.
        valid_datetime : datetime.datetime, optional
            The valid datetime of the forecast. Default is None.
        forecast_month : int, optional
            The forecast month. Default is None.
        indexing_datetime : datetime.datetime, optional
            The indexing datetime. Default is None.

        Returns
        -------
        MonthlyForecastTime
            A new MonthlyForecastTime object.
        """
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
    def from_dict(cls, d):
        """Create a MonthlyForecastTime object from a dictionary.

        Parameters
        ----------
        d : dict
            A dictionary containing the keys and values to create the MonthlyForecastTime object.
            The allowed keys are:

            - "valid_datetime"
            - "base_datetime"
            - "step"
            - "base_date"
            - "base_time"
            - "forecast_month"
            - "indexing_datetime"

        The "step" value can be a datetime.timedelta, string, or number. Integer values are treated
        as hours, and string values are parsed using the `to_timedelta` function.

        Returns
        -------
        MonthlyForecastTime
            A new MonthlyForecastTime object.
        """
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

        d1 = cls._normalise_create_kwargs(d, allowed_keys=KEYS, remove_nones=True)

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
        """Create a new instance with updated data.

        This method is not implemented yet, as the logic for determining the method to use based
        on the provided keys is more complex than for the ForecastTime class, due to the additional
        keys "forecast_month" and "indexing_datetime".
        """
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
