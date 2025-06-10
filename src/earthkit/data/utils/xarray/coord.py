# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import logging

from .dim import DATE_KEYS
from .dim import DATETIME_KEYS
from .dim import LEVEL_KEYS
from .dim import MONTH_KEYS
from .dim import STEP_KEYS
from .dim import TIME_KEYS

LOG = logging.getLogger(__name__)


class Coord:
    def __init__(self, name, vals, dims=None, ds=None, component=None):
        self.name = name
        self.vals = vals
        self.dims = dims
        if not self.dims:
            self.dims = (self.name,)
        self.component = component

        if self.component:
            assert isinstance(self.component, tuple)
            assert len(self.component) == 2
            if len(self.vals) != len(self.component[1]):
                raise ValueError(
                    (
                        f"Invalid remapping for {name=}. Number of coordinate values"
                        " does not match number of component values,"
                        f" {len(self.vals)} != {len(self.component[1])}"
                    )
                )

    @staticmethod
    def make(name, *args, **kwargs):
        if name in DATETIME_KEYS:
            return DateTimeCoord(name, *args, **kwargs)
        elif name in DATE_KEYS:
            return DateCoord(name, *args, **kwargs)
        elif name in TIME_KEYS:
            return TimeCoord(name, *args, **kwargs)
        elif name in MONTH_KEYS:
            return MonthCoord(name, *args, **kwargs)
        elif name in STEP_KEYS:
            return StepCoord(name, *args, **kwargs)
        elif name in LEVEL_KEYS:
            return LevelCoord(name, *args, **kwargs)
        return Coord(name, *args, **kwargs)

    def to_xr_var(self, profile):
        import xarray

        # LOG.debug(f"{self.name=}" + str(self.convert(profile)))

        name = self.name
        return xarray.Variable(
            self.dims,
            self.convert(profile),
            self.attrs(name, profile),
        )

    def convert(self, profile):
        return self.vals

    def encoding(self, profile):
        return {}

    def attrs(self, name, profile):
        attrs = profile.attrs.coord_attrs.get(name, {})
        if profile.add_earthkit_attrs and self.component:
            attrs["_earthkit"] = {"keys": self.component[0], "values": self.component[1]}
        return attrs

    @staticmethod
    def _to_datetime_list(vals):
        import numpy as np

        from earthkit.data.utils.dates import to_datetime_list

        # datetime64 arrays are already in the required format
        if isinstance(vals, np.ndarray):
            if not np.issubdtype(vals.dtype, np.datetime64):
                return to_datetime_list(vals.tolist())
        else:
            return to_datetime_list(vals)

        return vals


class DateTimeCoord(Coord):
    def convert(self, profile):
        return Coord._to_datetime_list(self.vals)

    def attrs(self, name, profile):
        attrs = profile.attrs.coord_attrs.get(name, {})
        if self.component:
            attrs["_earthkit"] = {"keys": self.component[0]}
        return attrs


class DateCoord(Coord):
    def convert(self, profile):
        if profile.decode_times:
            return Coord._to_datetime_list(self.vals)
        return super().convert(profile)


class TimeCoord(Coord):
    def convert(self, profile):
        if profile.decode_timedelta:
            from earthkit.data.utils.dates import to_time
            from earthkit.data.utils.dates import to_timedelta

            return [to_timedelta(to_time(x)) for x in self.vals]
        return super().convert(profile)

    def encoding(self, profile):
        if profile.decode_timedelta:
            return ({"dtype": "timedelta64[s]"},)
        return {}


class StepCoord(Coord):
    resolution = None
    RESOLUTION_UNITS = {
        datetime.timedelta(hours=1): "hours",
        datetime.timedelta(minutes=1): "minutes",
        datetime.timedelta(seconds=1): "seconds",
    }

    def convert(self, profile):
        from earthkit.data.utils.dates import to_timedelta

        vals = [to_timedelta(x) for x in self.vals]

        if profile.decode_timedelta:
            return vals
        else:
            from earthkit.data.utils.dates import timedeltas_to_int

            vals, self.resolution = timedeltas_to_int(vals)

        return vals

    def encoding(self, profile):
        if profile.decode_timedelta:
            return ({"dtype": "timedelta64[s]"},)
        return {}

    def attrs(self, name, profile):
        attrs = super().attrs(name, profile)
        if self.resolution:
            if self.resolution in self.RESOLUTION_UNITS:
                attrs["units"] = self.RESOLUTION_UNITS[self.resolution]
            else:
                raise ValueError(f"Unsupported step resolution {self.resolution}")
        return attrs


class MonthCoord(Coord):
    def attrs(self, name, profile):
        attrs = super().attrs(name, profile)
        attrs["units"] = "months"
        return attrs


class LevelCoord(Coord):
    def __init__(self, name, vals, dims=None, ds=None, **kwargs):
        self.level_type = {}
        if ds is not None:
            for k in ["levtype", "typeOfLevel"]:
                v = ds[0].metadata(k, default=None)
                if v is not None:
                    self.level_type[k] = v

        super().__init__(name, vals, dims, **kwargs)

    def attrs(self, name, profile):
        attrs = profile.attrs
        conf = attrs.coord_attrs.get(name, {})
        if conf:
            key = conf["key"]
            if key in self.level_type:
                level_type = self.level_type[key]
                return conf.get(level_type, {})
        return {}
        # raise ValueError(f"Cannot determine level type for coordinate {name}")
