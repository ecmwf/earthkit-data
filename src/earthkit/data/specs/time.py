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
from .time_span import TimeSpan

ZERO_TIMEDELTA = datetime.timedelta(hours=0)


@spec_aliases
class Time(SimpleSpec):
    """A specification for a time object."""

    KEYS = (
        "base_datetime",
        "valid_datetime",
        "step",
        "time_span",
        "time_span_value",
        "time_span_method",
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
    def time_span_value(self):
        pass

    @property
    @abstractmethod
    def time_span_method(self):
        """TimeSpanMethod: Return the time span method of the time object."""
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
    _time_span = TimeSpan()
    _indexing_datetime = None
    _reference_datetime = None

    def __init__(
        self,
        base_datetime=None,
        step=None,
        time_span=None,
        indexing_datetime=None,
        reference_datetime=None,
    ):
        if base_datetime is not None:
            self._base_datetime = to_datetime(base_datetime)

        if step is not None:
            self._step = to_timedelta(step)

        if time_span is not None:
            self._time_span = TimeSpan.build(time_span)

        if indexing_datetime is not None:
            self._indexing_datetime = to_datetime(indexing_datetime)

        if reference_datetime is not None:
            self._reference_datetime = to_datetime(reference_datetime)

    @classmethod
    def from_date_and_time(cls, *, date=None, time=None, step=None, time_span=None):
        dt = datetime_from_date_and_time(date, time)
        return cls.from_base_datetime_and_step(base_datetime=dt, step=step)

    @classmethod
    def from_valid_datetime(
        cls,
        *,
        valid_datetime=None,
        step=None,
        time_span=None,
        indexing_datetime=None,
        reference_datetime=None,
    ):
        """Set the valid datetime of the time object."""
        valid_datetime = to_datetime(valid_datetime)
        step = to_timedelta(step) if step is not None else ZERO_TIMEDELTA
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
        *,
        base_datetime=None,
        valid_datetime=None,
        time_span=None,
        indexing_datetime=None,
        reference_datetime=None,
    ):
        valid_datetime = to_datetime(valid_datetime)
        base_datetime = to_datetime(base_datetime)
        step = valid_datetime - base_datetime
        return cls(
            base_datetime=base_datetime,
            step=step,
            time_span=time_span,
            indexing_datetime=indexing_datetime,
            reference_datetime=reference_datetime,
        )

    @classmethod
    def from_base_datetime(
        cls, *, base_datetime=None, step=None, time_span=None, indexing_datetime=None, reference_datetime=None
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
            cls, add_spec_keys=False, remove_nones=True, extra_keys=CREATE_METHOD_MAP.CORE_KEYS, **d
        )

        method_name, method_kwargs = CREATE_METHOD_MAP.get(d.keys())
        if method_name:
            method = getattr(cls, method_name)
            d = {k: d[k] for k in method_kwargs if k in d}
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

    def _to_dict(self):
        res = self.to_dict()
        res.pop("valid_datetime", None)
        return res

    def get_grib_context(self, context) -> dict:
        from .grib.time import COLLECTOR

        COLLECTOR.collect(self, context)

    # @classmethod
    # def from_xarray(cls, owner, selection):
    #     from .xarray.time import from_xarray

    #     spec = cls.from_dict(from_xarray(owner, selection))
    #     return spec

    def set(self, *args, **kwargs):
        d = normalise_set_kwargs(self, *args, add_spec_keys=False, remove_nones=True, **kwargs)
        method_name, method_kwargs = UPDATE_METHOD_MAP.get(d.keys())
        if method_name:
            method = getattr(self, method_name)
            d = {k: d[k] for k in method_kwargs if k in d}
            return method(**d)

        return None

    def _set_generic(
        self,
        *,
        base_datetime=None,
        step=None,
        time_span=None,
        indexing_datetime=None,
        reference_datetime=None,
    ):
        d = self._to_dict()

        def _add(key, value):
            if value is not None:
                d[key] = value

        _add("base_datetime", base_datetime)
        _add("step", step)
        _add("time_span", time_span)
        _add("indexing_datetime", indexing_datetime)
        _add("reference_datetime", reference_datetime)

        # if base_datetime is not None:
        #     d["base_datetime"] = to_datetime(base_datetime)
        # if step is not None:
        #     d["step"] = to_timedelta(step)
        # if time_span is not None:
        #     d["time_span"] = TimeSpan.make(time_span)
        # if indexing_datetime is not None:
        #     d["indexing_datetime"] = to_datetime(indexing_datetime)
        # if reference_datetime is not None:
        #     d["reference_datetime"] = to_datetime(reference_datetime)

        # print("generic", d)

        return self.__class__(**d)

    def _set_valid_datetime(self, *, valid_datetime=None, time_span=None):
        valid_datetime = to_datetime(valid_datetime)
        step = valid_datetime - self._base_datetime
        return self._set_generic(step=step, time_span=time_span)

    def _set_valid_datetime_and_step(self, *, valid_datetime=None, step=None, time_span=None):
        valid_datetime = to_datetime(valid_datetime)
        step = to_timedelta(step)
        base_datetime = valid_datetime - step
        return self._set_generic(base_datetime=base_datetime, step=step, time_span=time_span)

    def _set_base_datetime_and_valid_datetime(
        self,
        *,
        base_datetime=None,
        valid_datetime=None,
        time_span=None,
    ):
        base_datetime = to_datetime(base_datetime)
        valid_datetime = to_datetime(valid_datetime)
        step = valid_datetime - base_datetime
        return self._set_generic(base_datetime=base_datetime, step=step, time_span=time_span)

    def _set_base_datetime_valid_datetime_and_step(
        self, *, base_datetime=None, valid_datetime=None, step=None, time_span=None
    ):
        base_datetime = to_datetime(base_datetime)
        valid_datetime = to_datetime(valid_datetime)
        step = to_timedelta(step)
        if valid_datetime - base_datetime != step:
            raise ValueError(f"Inconsistent step value. {base_datetime=} + {step=} != {valid_datetime=}")
        return self._set_generic(base_datetime=base_datetime, step=step, time_span=time_span)

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
    def time_span_value(self):
        return self._time_span.value

    @property
    def time_span_method(self):
        return self._time_span.method

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


class MethodMap:
    CORE_KEYS = None
    EXTRA_KEYS = None
    METHODS = None

    def __init__(self):
        self.mapping = {}
        self.method_kwargs = {}
        for k, method in self.METHODS.items():
            keys = sorted(list(k))
            if method not in self.method_kwargs:
                self.method_kwargs[method] = self.get_method_kwargs(method)

            kwargs = self.method_kwargs[method]
            assert set(keys).issubset(set(kwargs))
            assert set(keys).issubset(self.CORE_KEYS)
            key = tuple(keys)
            self.mapping[key] = method
            self.method_kwargs[method] = kwargs

    def get(self, keys):
        keys_s = set(keys)
        found = tuple(sorted(list(self.CORE_KEYS.intersection(keys_s))))
        found = self.reduce(found)
        method = self.mapping.get(found, None)
        return method, self.method_kwargs.get(method)

    @staticmethod
    def get_method_kwargs(method_name):
        import inspect

        f = getattr(SimpleTime, method_name)
        r = inspect.signature(f)
        v = []
        for p in r.parameters.values():
            if p.kind == p.KEYWORD_ONLY:
                v.append(p.name)
        return v

    def reduce(self, keys):
        if len(keys) <= 1:
            return keys
        return tuple([k for k in keys if k not in self.EXTRA_KEYS])


class CreateMethodMap(MethodMap):
    CORE_KEYS = {"valid_datetime", "base_datetime", "step", "date", "time"}
    EXTRA_KEYS = {"time_span", "indexing_datetime", "reference_datetime"}
    METHODS = {
        ("valid_datetime",): "from_valid_datetime",
        ("valid_datetime", "step"): "from_valid_datetime",
        ("base_datetime",): "from_base_datetime",
        ("base_datetime", "valid_datetime"): "from_base_datetime_and_valid_datetime",
        ("base_datetime", "step"): "from_base_datetime",
        ("date",): "from_date_and_time",
        ("date", "time"): "from_date_and_time",
        ("date", "time", "step"): "from_date_and_time",
    }


class UpdateMethodMap(MethodMap):
    CORE_KEYS = set(["valid_datetime", "base_datetime", "step", "time_span"])
    EXTRA_KEYS = set(["time_span", "indexing_datetime", "reference_datetime"])
    METHODS = {
        ("step",): "_set_generic",
        ("time_span",): "_set_generic",
        ("base_datetime",): "_set_generic",
        ("base_datetime", "step"): "_set_generic",
        ("valid_datetime",): "_set_valid_datetime",
        ("valid_datetime", "step"): "_set_valid_datetime_and_step",
        ("base_datetime", "valid_datetime"): "_set_base_datetime_and_valid_datetime",
        ("base_datetime", "valid_datetime", "step"): "_set_base_datetime_valid_datetime_and_step",
    }


CREATE_METHOD_MAP = CreateMethodMap()
UPDATE_METHOD_MAP = UpdateMethodMap()
