# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.core.constants import ZERO_TIMEDELTA
from earthkit.data.utils.dates import datetime_from_date_and_time
from earthkit.data.utils.dates import to_datetime
from earthkit.data.utils.dates import to_timedelta

from .spec import Aliases
from .spec import spec_aliases_1


def normalise_create_kwargs(cls, *args, remove_nones=True, **kwargs):
    kwargs = kwargs.copy()

    for a in args:
        if a is None:
            continue
        if isinstance(a, dict):
            kwargs.update(a)
            continue
        raise ValueError(f"Cannot use arg={a}. Only dict allowed.")

    _kwargs = {}
    for k, v in kwargs.items():
        k = cls._ALIASES.get(k, k)
        if k in cls._CREATE_KEYS:
            _kwargs[k] = v
        else:
            raise ValueError(f"Cannot use key={k} to create {cls.__class__.__name__}")

    if remove_nones:
        _kwargs = {k: v for k, v in _kwargs.items() if v is not None}

    return _kwargs


def normalise_set_kwargs(cls, *args, remove_nones=True, **kwargs):
    kwargs = kwargs.copy()

    for a in args:
        if a is None:
            continue
        if isinstance(a, dict):
            kwargs.update(a)
            continue
        raise ValueError(f"Cannot use arg={a}. Only dict allowed.")

    _kwargs = {}
    for k, v in kwargs.items():
        k = cls._ALIASES.get(k, k)
        if k in cls._SET_KEYS:
            _kwargs[k] = v
        else:
            raise ValueError(f"Cannot use key={k} to modify {cls.__class__.__name__}")

    if remove_nones:
        _kwargs = {k: v for k, v in _kwargs.items() if v is not None}

    return _kwargs


@spec_aliases_1
class Time:
    _base_datetime = None
    _hcast_datetime = None
    _step = ZERO_TIMEDELTA
    _indexing_datetime = None
    _reference_datetime = None

    _KEYS = (
        "base_datetime",
        "valid_datetime",
        "step",
        "indexing_datetime",
        "reference_datetime",
    )
    _CREATE_KEYS = (
        "base_datetime",
        "valid_datetime",
        "step",
        "indexing_datetime",
        "reference_datetime",
        "date",
        "time",
    )
    _SET_KEYS = (
        "base_datetime",
        "valid_datetime",
        "step",
    )
    _ALIASES = Aliases({"base_datetime": ("forecast_reference_time",), "step": ("forecast_period",)})

    def __init__(
        self,
        base_datetime=None,
        step=None,
        indexing_datetime=None,
        reference_datetime=None,
    ):
        if base_datetime is not None:
            self._base_datetime = to_datetime(base_datetime)

        if step is not None:
            self._step = to_timedelta(step)

        if indexing_datetime is not None:
            self._indexing_datetime = to_datetime(indexing_datetime)

        if reference_datetime is not None:
            self._reference_datetime = to_datetime(reference_datetime)

    @property
    def base_datetime(self):
        """Return the base datetime of the time object."""
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
    def indexing_datetime(self):
        return self._indexing_datetime

    @property
    def reference_datetime(self):
        return self._reference_datetime

    def to_dict(self):
        return {
            "valid_datetime": self.valid_datetime,
            "base_datetime": self.base_datetime,
            "step": self.step,
            "indexing_datetime": self.indexing_datetime,
            "reference_datetime": self.reference_datetime,
        }

    def __getstate__(self):
        state = {}
        state["base_datetime"] = self._base_datetime
        state["hcast_datetime"] = self._hcast_datetime
        state["step"] = self._step
        state["indexing_datetime"] = self._indexing_datetime
        state["reference_datetime"] = self._reference_datetime
        return state

    def __setstate__(self, state):
        self.__init__(
            base_datetime=state["base_datetime"],
            hcast_datetime=state["hcast_datetime"],
            step=state["step"],
            indexing_datetime=state["indexing_datetime"],
            reference_datetime=state["reference_datetime"],
        )

    @classmethod
    def from_dict(cls, d):
        if not isinstance(d, dict):
            raise TypeError("data must be a dictionary")

        d = normalise_create_kwargs(cls, remove_nones=True, **d)

        method, method_kwargs = CREATE_METHOD_MAP.get(d.keys())
        if method:
            d = {k: d[k] for k in method_kwargs if k in d}
            data = method(**d)
            return data

        if not d:
            return cls()

        raise ValueError(f"Invalid keys in data: {list(d.keys())}. Expected one of {cls._CREATE_KEYS}.")

    @classmethod
    def from_date_and_time(cls, *, date=None, time=None, step=None):
        dt = datetime_from_date_and_time(date, time)
        return cls.from_base_datetime(base_datetime=dt, step=step)

    @classmethod
    def from_valid_datetime(
        cls,
        *,
        valid_datetime=None,
        step=None,
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
            indexing_datetime=indexing_datetime,
            reference_datetime=reference_datetime,
        )

    @classmethod
    def from_base_datetime_and_valid_datetime(
        cls,
        *,
        base_datetime=None,
        valid_datetime=None,
        indexing_datetime=None,
        reference_datetime=None,
    ):
        valid_datetime = to_datetime(valid_datetime)
        base_datetime = to_datetime(base_datetime)
        step = valid_datetime - base_datetime
        return cls(
            base_datetime=base_datetime,
            step=step,
            indexing_datetime=indexing_datetime,
            reference_datetime=reference_datetime,
        )

    @classmethod
    def from_base_datetime(
        cls, *, base_datetime=None, step=None, indexing_datetime=None, reference_datetime=None
    ):
        """Set the base datetime of the time object."""
        return cls(
            base_datetime=base_datetime,
            step=step,
            indexing_datetime=indexing_datetime,
            reference_datetime=reference_datetime,
        )

    def set(self, *args, **kwargs):
        d = normalise_set_kwargs(self, *args, remove_nones=True, **kwargs)
        method, method_kwargs = SET_METHOD_MAP.get(d.keys())
        if method:
            # method = getattr(cls, method_name)
            d = {k: d[k] for k in method_kwargs if k in d}
            return method(self, **d)

        return None

    def _set_generic(
        self,
        *,
        base_datetime=None,
        step=None,
        indexing_datetime=None,
        reference_datetime=None,
    ):
        d = self.to_dict()
        d.pop("valid_datetime", None)

        def _add(key, value):
            if value is not None:
                d[key] = value

        _add("base_datetime", base_datetime)
        _add("step", step)
        _add("indexing_datetime", indexing_datetime)
        _add("reference_datetime", reference_datetime)

        return Time(**d)

    def _set_valid_datetime(self, *, valid_datetime=None):
        valid_datetime = to_datetime(valid_datetime)
        step = valid_datetime - self.base_datetime
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


class MethodMap:
    def __init__(self, core_keys, extra_keys, methods):
        self.core_keys = core_keys
        self.extra_keys = extra_keys or set()
        self.methods = methods

        assert self.core_keys
        assert isinstance(self.core_keys, set)
        assert isinstance(self.extra_keys, set)
        assert self.methods
        assert isinstance(self.methods, dict)

        self.mapping = {}
        self.method_kwargs = {}
        for k, method in self.methods.items():
            keys = sorted(list(k))
            if method not in self.method_kwargs:
                self.method_kwargs[method] = self.get_method_kwargs(method)

            kwargs = self.method_kwargs[method]
            assert set(keys).issubset(set(kwargs)), f"{method=} {keys=} {kwargs=}"
            assert set(keys).issubset(self.core_keys), f"{method=} {keys=} {self.core_keys=}"
            key = tuple(keys)
            self.mapping[key] = method
            self.method_kwargs[method] = kwargs

        # self.ALL_KEYS = set(self.CORE_KEYS).union(set(self.EXTRA_KEYS))

    def get(self, keys):
        keys_s = set(keys)
        found = tuple(sorted(list(self.core_keys.intersection(keys_s))))
        found = self.reduce(found)
        method = self.mapping.get(found, None)
        return method, self.method_kwargs.get(method)

    def get_method_kwargs(self, method):
        import inspect

        f = method
        r = inspect.signature(f)
        v = []
        for p in r.parameters.values():
            if p.kind == p.KEYWORD_ONLY:
                v.append(p.name)
        return v

    def reduce(self, keys):
        if len(keys) <= 1:
            return keys
        return tuple([k for k in keys if k not in self.extra_keys])


CREATE_METHOD_MAP = MethodMap(
    core_keys={"valid_datetime", "base_datetime", "step", "date", "time"},
    extra_keys={"indexing_datetime", "reference_datetime"},
    methods={
        ("valid_datetime",): Time.from_valid_datetime,
        ("valid_datetime", "step"): Time.from_valid_datetime,
        ("base_datetime",): Time.from_base_datetime,
        ("base_datetime", "valid_datetime"): Time.from_base_datetime_and_valid_datetime,
        ("base_datetime", "step"): Time.from_base_datetime,
        ("date",): Time.from_date_and_time,
        ("date", "time"): Time.from_date_and_time,
        ("date", "time", "step"): Time.from_date_and_time,
    },
)


# SET_METHOD_MAP = MethodMap(
#     core_keys={"valid_datetime", "base_datetime", "step"},
#     extra_keys={"indexing_datetime", "reference_datetime"},
#     methods={
#         ("step",): TimeSetter._set_generic,
#         ("base_datetime",): TimeSetter._set_generic,
#         ("base_datetime", "step"): TimeSetter._set_generic,
#         ("valid_datetime",): TimeSetter._set_valid_datetime,
#         ("valid_datetime", "step"): TimeSetter._set_valid_datetime_and_step,
#         ("base_datetime", "valid_datetime"): TimeSetter._set_base_datetime_and_valid_datetime,
#         (
#             "base_datetime",
#             "valid_datetime",
#             "step",
#         ): TimeSetter._set_base_datetime_valid_datetime_and_step,
#     },
# )

# class TimeCreator:
#     METHOD_MAP = None

#     @classmethod
#     def from_dict(cls, d):
#         if not isinstance(d, dict):
#             raise TypeError("data must be a dictionary")

#         d = cls.normalise_create_kwargs(remove_nones=True, **d)

#         method, method_kwargs = cls.METHOD_MAP.get(d.keys())
#         if method:
#             d = {k: d[k] for k in method_kwargs if k in d}
#             data = method(**d)
#             return data

#         if not d:
#             return Time()

#         raise ValueError(f"Invalid keys in data: {list(d.keys())}. Expected one of {cls.KEYS}.")

#     @classmethod
#     def from_date_and_time(cls, *, date=None, time=None, step=None):
#         dt = datetime_from_date_and_time(date, time)
#         return cls.from_base_datetime_and_step(base_datetime=dt, step=step)

#     @classmethod
#     def from_valid_datetime(
#         cls,
#         *,
#         valid_datetime=None,
#         step=None,
#         indexing_datetime=None,
#         reference_datetime=None,
#     ):
#         """Set the valid datetime of the time object."""
#         valid_datetime = to_datetime(valid_datetime)
#         step = to_timedelta(step) if step is not None else ZERO_TIMEDELTA
#         base_datetime = valid_datetime - step
#         return Time(
#             base_datetime=base_datetime,
#             step=step,
#             indexing_datetime=indexing_datetime,
#             reference_datetime=reference_datetime,
#         )

#     @classmethod
#     def from_base_datetime_and_valid_datetime(
#         cls,
#         *,
#         base_datetime=None,
#         valid_datetime=None,
#         indexing_datetime=None,
#         reference_datetime=None,
#     ):
#         valid_datetime = to_datetime(valid_datetime)
#         base_datetime = to_datetime(base_datetime)
#         step = valid_datetime - base_datetime
#         return Time(
#             base_datetime=base_datetime,
#             step=step,
#             indexing_datetime=indexing_datetime,
#             reference_datetime=reference_datetime,
#         )

#     @classmethod
#     def from_base_datetime(
#         cls, *, base_datetime=None, step=None, indexing_datetime=None, reference_datetime=None
#     ):
#         """Set the base datetime of the time object."""
#         return Time(
#             base_datetime=base_datetime,
#             step=step,
#             indexing_datetime=indexing_datetime,
#             reference_datetime=reference_datetime,
#         )


# TimeCreator.METHOD_MAP = MethodMap(
#     core_keys={"valid_datetime", "base_datetime", "step", "date", "time"},
#     extra_keys={"indexing_datetime", "reference_datetime"},
#     methods={
#         ("valid_datetime",): TimeCreator.from_valid_datetime,
#         ("valid_datetime", "step"): TimeCreator.from_valid_datetime,
#         ("base_datetime",): TimeCreator.from_base_datetime,
#         ("base_datetime", "valid_datetime"): TimeCreator.from_base_datetime_and_valid_datetime,
#         ("base_datetime", "step"): TimeCreator.from_base_datetime,
#         ("date",): TimeCreator.from_date_and_time,
#         ("date", "time"): TimeCreator.from_date_and_time,
#         ("date", "time", "step"): TimeCreator.from_date_and_time,
#     },
# )


# class TimeSetter:
#     @staticmethod
#     def set(obj, *args, **kwargs):
#         d = normalise_set_kwargs(obj, *args, remove_nones=True, **kwargs)
#         method, method_kwargs = SET_METHOD_MAP.get(d.keys())
#         if method:
#             # method = getattr(cls, method_name)
#             d = {k: d[k] for k in method_kwargs if k in d}
#             return method(obj, **d)

#         return None

#     @staticmethod
#     def _set_generic(
#         obj,
#         *,
#         base_datetime=None,
#         step=None,
#         indexing_datetime=None,
#         reference_datetime=None,
#     ):
#         d = obj._to_dict()

#         def _add(key, value):
#             if value is not None:
#                 d[key] = value

#         _add("base_datetime", base_datetime)
#         _add("step", step)
#         _add("indexing_datetime", indexing_datetime)
#         _add("reference_datetime", reference_datetime)

#         return Time(**d)

#     @staticmethod
#     def _set_valid_datetime(obj, *, valid_datetime=None):
#         valid_datetime = to_datetime(valid_datetime)
#         step = valid_datetime - obj.base_datetime
#         return TimeSetter._set_generic(obj, step=step)

#     @classmethod
#     def _set_valid_datetime_and_step(cls, data, *, valid_datetime=None, step=None):
#         valid_datetime = to_datetime(valid_datetime)
#         step = to_timedelta(step)
#         base_datetime = valid_datetime - step
#         return cls._set_generic(data, base_datetime=base_datetime, step=step)

#     @classmethod
#     def _set_base_datetime_and_valid_datetime(
#         cls,
#         data,
#         *,
#         base_datetime=None,
#         valid_datetime=None,
#     ):
#         base_datetime = to_datetime(base_datetime)
#         valid_datetime = to_datetime(valid_datetime)
#         step = valid_datetime - base_datetime
#         return cls._set_generic(data, base_datetime=base_datetime, step=step)

#     @classmethod
#     def _set_base_datetime_valid_datetime_and_step(
#         cls,
#         data,
#         *,
#         base_datetime=None,
#         valid_datetime=None,
#         step=None,
#     ):
#         base_datetime = to_datetime(base_datetime)
#         valid_datetime = to_datetime(valid_datetime)
#         step = to_timedelta(step)
#         if valid_datetime - base_datetime != step:
#             raise ValueError(f"Inconsistent step value. {base_datetime=} + {step=} != {valid_datetime=}")
#         return cls._set_generic(data, base_datetime=base_datetime, step=step)


# TIME_SETTER = TimeSetter()


SET_METHOD_MAP = MethodMap(
    core_keys={"valid_datetime", "base_datetime", "step"},
    extra_keys={"indexing_datetime", "reference_datetime"},
    methods={
        ("step",): Time._set_generic,
        ("base_datetime",): Time._set_generic,
        ("base_datetime", "step"): Time._set_generic,
        ("valid_datetime",): Time._set_valid_datetime,
        ("valid_datetime", "step"): Time._set_valid_datetime_and_step,
        ("base_datetime", "valid_datetime"): Time._set_base_datetime_and_valid_datetime,
        (
            "base_datetime",
            "valid_datetime",
            "step",
        ): Time._set_base_datetime_valid_datetime_and_step,
    },
)

# @spec_aliases
# class TimeSpec(SimpleSpec):
#     """A specification for a time object."""

#     KEYS = (
#         "base_datetime",
#         "valid_datetime",
#         "step",
#         "indexing_datetime",
#         "reference_datetime",
#     )
#     SET_KEYS = (
#         "base_datetime",
#         "valid_datetime",
#         "step",
#     )
#     ALIASES = Aliases({"base_datetime": ("forecast_reference_time",), "step": ("forecast_period",)})
#     CREATE_KEYS = (
#         "base_datetime",
#         "valid_datetime",
#         "step",
#         "indexing_datetime",
#         "reference_datetime",
#         "date",
#         "time",
#     )

#     @property
#     @abstractmethod
#     def base_datetime(self):
#         """datetime.datetime: Return the base datetime of the time object."""
#         pass

#     @property
#     @abstractmethod
#     def valid_datetime(self):
#         """datetime.datetime: Return the valid datetime of the time object."""
#         pass

#     @property
#     @abstractmethod
#     def hcast_datetime(self):
#         pass

#     @property
#     @abstractmethod
#     def step(self):
#         """datetime.timedelta: Return the forecast period of the time object."""
#         pass

#     @property
#     @abstractmethod
#     def indexing_datetime(self):
#         pass

#     @property
#     @abstractmethod
#     def reference_datetime(self):
#         pass


# class SimpleTimeSpec(TimeSpec):
#     """A specification for a time object."""

#     def __init__(self, data) -> None:
#         assert isinstance(data, Time)
#         self._data = data

#     @property
#     def data(self):
#         """Return the time data."""
#         return self._data

#     # @classmethod
#     # def from_date_and_time(cls, *, date=None, time=None, step=None, time_span=None):
#     #     dt = datetime_from_date_and_time(date, time)
#     #     return cls.from_base_datetime_and_step(base_datetime=dt, step=step)

#     # @classmethod
#     # def from_valid_datetime(
#     #     cls,
#     #     *,
#     #     valid_datetime=None,
#     #     step=None,
#     #     time_span=None,
#     #     indexing_datetime=None,
#     #     reference_datetime=None,
#     # ):
#     #     """Set the valid datetime of the time object."""
#     #     valid_datetime = to_datetime(valid_datetime)
#     #     step = to_timedelta(step) if step is not None else ZERO_TIMEDELTA
#     #     base_datetime = valid_datetime - step
#     #     return cls(
#     #         base_datetime=base_datetime,
#     #         step=step,
#     #         time_span=time_span,
#     #         indexing_datetime=indexing_datetime,
#     #         reference_datetime=reference_datetime,
#     #     )

#     # @classmethod
#     # def from_base_datetime_and_valid_datetime(
#     #     cls,
#     #     *,
#     #     base_datetime=None,
#     #     valid_datetime=None,
#     #     time_span=None,
#     #     indexing_datetime=None,
#     #     reference_datetime=None,
#     # ):
#     #     valid_datetime = to_datetime(valid_datetime)
#     #     base_datetime = to_datetime(base_datetime)
#     #     step = valid_datetime - base_datetime
#     #     return cls(
#     #         base_datetime=base_datetime,
#     #         step=step,
#     #         time_span=time_span,
#     #         indexing_datetime=indexing_datetime,
#     #         reference_datetime=reference_datetime,
#     #     )

#     # @classmethod
#     # def from_base_datetime(
#     #     cls, *, base_datetime=None, step=None, time_span=None, indexing_datetime=None, reference_datetime=None
#     # ):
#     #     """Set the base datetime of the time object."""
#     #     return cls(
#     #         base_datetime=base_datetime,
#     #         step=step,
#     #         time_span=time_span,
#     #         indexing_datetime=indexing_datetime,
#     #         reference_datetime=reference_datetime,
#     #     )

#     @classmethod
#     def from_dict(cls, d):
#         """Create a Time object from a dictionary."""
#         if not isinstance(d, dict):
#             raise TypeError("data must be a dictionary")

#         d = cls.normalise_create_kwargs(remove_nones=True, **d)

#         method_name, method_kwargs = CREATE_METHOD_MAP.get(d.keys())
#         if method_name:
#             method = getattr(cls, method_name)
#             d = {k: d[k] for k in method_kwargs if k in d}
#             data = method(**d)
#             return cls(data)

#         if not d:
#             return cls(Time())

#         raise ValueError(f"Invalid keys in data: {list(d.keys())}. Expected one of {cls.KEYS}.")

#     @classmethod
#     def normalise_create_kwargs(cls, *args, remove_nones=True, **kwargs):
#         kwargs = kwargs.copy()

#         for a in args:
#             if a is None:
#                 continue
#             if isinstance(a, dict):
#                 kwargs.update(a)
#                 continue
#             raise ValueError(f"Cannot use arg={a}. Only dict allowed.")

#         _kwargs = {}
#         for k, v in kwargs.items():
#             k = cls.ALIASES.get(k, k)
#             if k in cls.CREATE_KEYS:
#                 _kwargs[k] = v
#             else:
#                 raise ValueError(f"Cannot use key={k} to create {cls.__name__}")

#         if remove_nones:
#             _kwargs = {k: v for k, v in _kwargs.items() if v is not None}

#         return _kwargs

#     def to_dict(self):
#         return {
#             "valid_datetime": self.valid_datetime,
#             "base_datetime": self.base_datetime,
#             "step": self.step,
#             "time_span": self.time_span,
#             "indexing_datetime": self.indexing_datetime,
#             "reference_datetime": self.reference_datetime,
#         }

#     def _to_dict(self):
#         res = self.to_dict()
#         res.pop("valid_datetime", None)
#         return res

#     def get_grib_context(self, context) -> dict:
#         from .grib.time import COLLECTOR

#         COLLECTOR.collect(self, context)

#     # @classmethod
#     # def from_xarray(cls, owner, selection):
#     #     from .xarray.time import from_xarray

#     #     spec = cls.from_dict(from_xarray(owner, selection))
#     #     return spec

#     def set(self, *args, **kwargs):
#         d = normalise_set_kwargs(self, *args, add_spec_keys=False, remove_nones=True, **kwargs)
#         method_name, method_kwargs = UPDATE_METHOD_MAP.get(d.keys())
#         if method_name:
#             method = getattr(self, method_name)
#             d = {k: d[k] for k in method_kwargs if k in d}
#             return method(**d)

#         return None

#     def _set_generic(
#         self,
#         *,
#         base_datetime=None,
#         step=None,
#         time_span=None,
#         indexing_datetime=None,
#         reference_datetime=None,
#     ):
#         d = self._to_dict()

#         def _add(key, value):
#             if value is not None:
#                 d[key] = value

#         _add("base_datetime", base_datetime)
#         _add("step", step)
#         _add("time_span", time_span)
#         _add("indexing_datetime", indexing_datetime)
#         _add("reference_datetime", reference_datetime)

#         # if base_datetime is not None:
#         #     d["base_datetime"] = to_datetime(base_datetime)
#         # if step is not None:
#         #     d["step"] = to_timedelta(step)
#         # if time_span is not None:
#         #     d["time_span"] = TimeSpan.make(time_span)
#         # if indexing_datetime is not None:
#         #     d["indexing_datetime"] = to_datetime(indexing_datetime)
#         # if reference_datetime is not None:
#         #     d["reference_datetime"] = to_datetime(reference_datetime)

#         # print("generic", d)

#         return self.__class__(**d)

#     def _set_valid_datetime(self, *, valid_datetime=None, time_span=None):
#         valid_datetime = to_datetime(valid_datetime)
#         step = valid_datetime - self._base_datetime
#         return self._set_generic(step=step, time_span=time_span)

#     def _set_valid_datetime_and_step(self, *, valid_datetime=None, step=None, time_span=None):
#         valid_datetime = to_datetime(valid_datetime)
#         step = to_timedelta(step)
#         base_datetime = valid_datetime - step
#         return self._set_generic(base_datetime=base_datetime, step=step, time_span=time_span)

#     def _set_base_datetime_and_valid_datetime(
#         self,
#         *,
#         base_datetime=None,
#         valid_datetime=None,
#         time_span=None,
#     ):
#         base_datetime = to_datetime(base_datetime)
#         valid_datetime = to_datetime(valid_datetime)
#         step = valid_datetime - base_datetime
#         return self._set_generic(base_datetime=base_datetime, step=step, time_span=time_span)

#     def _set_base_datetime_valid_datetime_and_step(
#         self, *, base_datetime=None, valid_datetime=None, step=None, time_span=None
#     ):
#         base_datetime = to_datetime(base_datetime)
#         valid_datetime = to_datetime(valid_datetime)
#         step = to_timedelta(step)
#         if valid_datetime - base_datetime != step:
#             raise ValueError(f"Inconsistent step value. {base_datetime=} + {step=} != {valid_datetime=}")
#         return self._set_generic(base_datetime=base_datetime, step=step, time_span=time_span)

#     @property
#     def base_datetime(self):
#         """Return the base datetime of the time object."""
#         return self._base_datetime

#     @property
#     def valid_datetime(self):
#         """Return the valid datetime of the time object."""
#         return self._base_datetime + self._step

#     @property
#     def hcast_datetime(self):
#         return self._hcast_datetime

#     @property
#     def step(self):
#         """Return the forecast period of the time object."""
#         return self._step

#     @property
#     def time_span(self):
#         """Return the forecast period of the time object."""
#         return self._time_span

#     @property
#     def time_span_value(self):
#         return self._time_span.value

#     @property
#     def time_span_method(self):
#         return self._time_span.method

#     @property
#     def indexing_datetime(self):
#         return self._indexing_datetime

#     @property
#     def reference_datetime(self):
#         return self._reference_datetime

#     def namespace(self, owner, name, result):
#         if name is None or name == "time" or (isinstance(name, (list, tuple)) and "time" in name):
#             result["time"] = self.to_dict()

#     def check(self, owner):
#         pass

#     def __getstate__(self):
#         state = {}
#         state["_base_datetime"] = self._base_datetime
#         state["_hcast_datetime"] = self._hcast_datetime
#         state["_step"] = self._step
#         state["_time_span"] = self._time_span
#         state["_indexing_datetime"] = self._indexing_datetime
#         state["_reference_datetime"] = self._reference_datetime
#         return state

#     def __setstate__(self, state):
#         self.__init__(
#             base_datetime=state["_base_datetime"],
#             hcast_datetime=state["_hcast_datetime"],
#             step=state["_step"],
#             time_span=state["_time_span"],
#             indexing_datetime=state["_indexing_datetime"],
#             reference_datetime=state["_reference_datetime"],
#         )


# class MethodMap:
#     CORE_KEYS = None
#     EXTRA_KEYS = None
#     METHODS = None
#     CLASS = None

#     def __init__(self):
#         self.mapping = {}
#         self.method_kwargs = {}
#         for k, method in self.METHODS.items():
#             keys = sorted(list(k))
#             if method not in self.method_kwargs:
#                 self.method_kwargs[method] = self.get_method_kwargs(method)

#             kwargs = self.method_kwargs[method]
#             assert set(keys).issubset(set(kwargs))
#             assert set(keys).issubset(self.CORE_KEYS)
#             key = tuple(keys)
#             self.mapping[key] = method
#             self.method_kwargs[method] = kwargs

#     def get(self, keys):
#         keys_s = set(keys)
#         found = tuple(sorted(list(self.CORE_KEYS.intersection(keys_s))))
#         found = self.reduce(found)
#         method = self.mapping.get(found, None)
#         return method, self.method_kwargs.get(method)

#     def get_method_kwargs(self, method_name):
#         import inspect

#         f = getattr(self.CLASS, method_name)
#         r = inspect.signature(f)
#         v = []
#         for p in r.parameters.values():
#             if p.kind == p.KEYWORD_ONLY:
#                 v.append(p.name)
#         return v

#     def reduce(self, keys):
#         if len(keys) <= 1:
#             return keys
#         return tuple([k for k in keys if k not in self.EXTRA_KEYS])


# TimeCreator.METHOD_MAP = MethodMap(
#     core_keys={"valid_datetime", "base_datetime", "step", "date", "time"},
#     extra_keys={"indexing_datetime", "reference_datetime"},
#     methods={
#         ("valid_datetime",): TimeCreator.from_valid_datetime,
#         ("valid_datetime", "step"): TimeCreator.from_valid_datetime,
#         ("base_datetime",): TimeCreator.from_base_datetime,
#         ("base_datetime", "valid_datetime"): TimeCreator.from_base_datetime_and_valid_datetime,
#         ("base_datetime", "step"): TimeCreator.from_base_datetime,
#         ("date",): TimeCreator.from_date_and_time,
#         ("date", "time"): TimeCreator.from_date_and_time,
#         ("date", "time", "step"): TimeCreator.from_date_and_time,
#     },
# )


# TimeSetter.METHOD_MAP = MethodMap(
#     core_keys={"valid_datetime", "base_datetime", "step"},
#     extra_keys={"indexing_datetime", "reference_datetime"},
#     methods={
#         ("step",): "_set_generic",
#         ("base_datetime",): "_set_generic",
#         ("base_datetime", "step"): "_set_generic",
#         ("valid_datetime",): "_set_valid_datetime",
#         ("valid_datetime", "step"): "_set_valid_datetime_and_step",
#         ("base_datetime", "valid_datetime"): "_set_base_datetime_and_valid_datetime",
#         ("base_datetime", "valid_datetime", "step"): "_set_base_datetime_valid_datetime_and_step",
#     },
# )
