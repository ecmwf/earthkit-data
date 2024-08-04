# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from .dim import DATE_KEYS
from .dim import DATETIME_KEYS
from .dim import LEVEL_KEYS
from .dim import STEP_KEYS
from .dim import TIME_KEYS

LOG = logging.getLogger(__name__)


class Coord:
    def __init__(self, name, vals, dims=None, ds=None):
        self.name = name
        self.vals = vals
        self.dims = dims
        if not self.dims:
            self.dims = (self.name,)

    @staticmethod
    def make(name, *args, **kwargs):
        if name in DATETIME_KEYS:
            return DateTimeCoord(name, *args, **kwargs)
        elif name in DATE_KEYS:
            return DateCoord(name, *args, **kwargs)
        if name in TIME_KEYS:
            return TimeCoord(name, *args, **kwargs)
        elif name in STEP_KEYS:
            return StepCoord(name, *args, **kwargs)
        elif name in LEVEL_KEYS:
            return LevelCoord(name, *args, **kwargs)
        return Coord(name, *args, **kwargs)

    def to_xr_var(self, profile):
        import xarray

        c = profile.rename_coords({self.name: None})
        name = list(c.keys())[0]
        return xarray.Variable(
            profile.rename_dims(self.dims), self.convert(profile), self.attrs(name, profile)
        )

    def convert(self, profile):
        return self.vals

    def encoding(self, profile):
        return {}

    def attrs(self, name, profile):
        return profile.add_coord_attrs(name)

    @staticmethod
    def _to_datetime_list(vals):
        import numpy as np

        if not (isinstance(vals, np.ndarray) and np.issubdtype(vals.dtype, np.datetime64)):
            from earthkit.data.utils.dates import to_datetime_list

            return to_datetime_list(vals)
        return vals


class DateTimeCoord(Coord):
    def convert(self, profile):
        return Coord._to_datetime_list(self.vals)


class DateCoord(Coord):
    def convert(self, profile):
        if profile.decode_time:
            return Coord._to_datetime_list(self.vals)
        return super().convert(profile)


class TimeCoord(Coord):
    pass
    # def convert(self, profile):
    #     if profile.decode_time:
    #         from earthkit.data.utils.dates import to_time_list

    #         return to_time_list(self.vals)
    #     return super().convert(profile)


class StepCoord(Coord):
    def convert(self, profile):
        if profile.decode_time:
            from earthkit.data.utils.dates import step_to_delta

            return [step_to_delta(x) for x in self.vals]
        return super().convert(profile)

    def encoding(self, profile):
        if profile.decode_time:
            return ({"dtype": "timedelta64[s]"},)
        return {}


class LevelCoord(Coord):
    def __init__(self, name, vals, dims=None, ds=None):
        self.levtype = {}
        if ds is not None:
            for k in ["levtype", "typeOfLevel"]:
                if k in ds.indices():
                    self.levtype[k] = ds.index(k)[0]
                else:
                    v = ds[0].metadata(k, default=None)
                    if v is not None:
                        self.levtype[k] = v

        super().__init__(name, vals, dims)

    def attrs(self, name, profile):
        return profile.add_level_coord_attrs(name, self.levtype)
