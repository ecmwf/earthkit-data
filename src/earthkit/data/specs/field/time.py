# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from ..time import Time
from .spec import SimpleSpec

# @spec_aliases
# class TimeField(Time, SimpleSpec):
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


class TimeFieldSpec(SimpleSpec):
    """A specification for a time object."""

    KEYS = (
        "base_datetime",
        "valid_datetime",
        "step",
        "indexing_datetime",
        "reference_datetime",
    )

    def __init__(self, data) -> None:
        assert isinstance(data, Time)
        self._data = data

    @property
    def data(self):
        """Return the time data."""
        return self._data

    @classmethod
    def from_dict(cls, d):
        """Create a Time object from a dictionary."""
        if not isinstance(d, dict):
            raise TypeError("data must be a dictionary")

        data = Time.from_dict(d)
        return cls(data)

    # @classmethod
    # def normalise_create_kwargs(cls, *args, remove_nones=True, **kwargs):
    #     kwargs = kwargs.copy()

    #     for a in args:
    #         if a is None:
    #             continue
    #         if isinstance(a, dict):
    #             kwargs.update(a)
    #             continue
    #         raise ValueError(f"Cannot use arg={a}. Only dict allowed.")

    #     _kwargs = {}
    #     for k, v in kwargs.items():
    #         k = cls.ALIASES.get(k, k)
    #         if k in cls.CREATE_KEYS:
    #             _kwargs[k] = v
    #         else:
    #             raise ValueError(f"Cannot use key={k} to create {cls.__name__}")

    #     if remove_nones:
    #         _kwargs = {k: v for k, v in _kwargs.items() if v is not None}

    #     return _kwargs

    # def to_dict(self):
    #     return {
    #         "valid_datetime": self.valid_datetime,
    #         "base_datetime": self.base_datetime,
    #         "step": self.step,
    #         "time_span": self.time_span,
    #         "indexing_datetime": self.indexing_datetime,
    #         "reference_datetime": self.reference_datetime,
    #     }

    # def _to_dict(self):
    #     res = self.to_dict()
    #     res.pop("valid_datetime", None)
    #     return res

    def get_grib_context(self, context) -> dict:
        from earthkit.data.specs.grib.time import COLLECTOR

        COLLECTOR.collect(self, context)

    # @classmethod
    # def from_xarray(cls, owner, selection):
    #     from .xarray.time import from_xarray

    #     spec = cls.from_dict(from_xarray(owner, selection))
    #     return spec

    def set(self, *args, **kwargs):
        data = self._data.set(*args, **kwargs)
        return TimeFieldSpec(data)
        # data = TimeSetter.set(self.data, *args, **kwargs)
        # spec = FieldTimeSpec(data)
        # return spec

        # d = normalise_set_kwargs(self, *args, add_spec_keys=False, remove_nones=True, **kwargs)
        # method_name, method_kwargs = UPDATE_METHOD_MAP.get(d.keys())
        # if method_name:
        #     method = getattr(self, method_name)
        #     d = {k: d[k] for k in method_kwargs if k in d}
        #     return method(**d)

        # return None

    def namespace(self, owner, name, result):
        if name is None or name == "time" or (isinstance(name, (list, tuple)) and "time" in name):
            result["time"] = self.to_dict()

    def check(self, owner):
        pass

    def __getstate__(self):
        state = {}
        state["data"] = self._data
        return state

    def __setstate__(self, state):
        self.__init__(data=state["data"])
