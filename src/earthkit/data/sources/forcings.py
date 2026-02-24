# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import itertools
import logging

import numpy as np

from earthkit.data.decorators import cached_method
from earthkit.data.decorators import normalise
from earthkit.data.field.handler.data import DataFieldComponentHandler
from earthkit.data.indexing.simple import SimpleFieldList
from earthkit.data.utils.dates import to_datetime

LOG = logging.getLogger(__name__)


class ForcingMaker:
    def __init__(self, field):
        self.field = field
        self.shape = self.field.shape

    @cached_method
    def grid_points(self):
        return self.field.geography.latlons(flatten=True)

    @cached_method
    def ecef_xyz(self):
        # https://en.wikipedia.org/wiki/Geographic_coordinate_conversion#From_geodetic_to_ECEF_coordinates
        # We assume that the Earth is a sphere of radius 1 so N(phi) = 1
        # We assume h = 0

        lat, lon = self.grid_points()

        phi = np.deg2rad(lat)
        lda = np.deg2rad(lon)

        cos_phi = np.cos(phi)
        cos_lda = np.cos(lda)
        sin_phi = np.sin(phi)
        sin_lda = np.sin(lda)

        x = cos_phi * cos_lda
        y = cos_phi * sin_lda
        z = sin_phi

        return x, y, z

    @cached_method
    def latitude_(self):
        return self.grid_points()[0]

    def latitude(self, date):
        return self.latitude_()

    @cached_method
    def cos_latitude_(self):
        return np.cos(np.deg2rad(self.grid_points()[0]))

    def cos_latitude(self, date):
        return self.cos_latitude_()

    @cached_method
    def sin_latitude_(self):
        return np.sin(np.deg2rad(self.grid_points()[0]))

    def sin_latitude(self, date):
        return self.sin_latitude_()

    @cached_method
    def longitude_(self):
        return self.grid_points()[1]

    def longitude(self, date):
        return self.longitude_()

    @cached_method
    def cos_longitude_(self):
        return np.cos(np.deg2rad(self.grid_points()[1]))

    def cos_longitude(self, date):
        return self.cos_longitude_()

    @cached_method
    def sin_longitude_(self):
        return np.sin(np.deg2rad(self.grid_points()[1]))

    def sin_longitude(self, date):
        return self.sin_longitude_()

    def ecef_x(self, date):
        return self.ecef_xyz()[0]

    def ecef_y(self, date):
        return self.ecef_xyz()[1]

    def ecef_z(self, date):
        return self.ecef_xyz()[2]

    def julian_day(self, date):
        date = to_datetime(date)
        if date.tzinfo is not None and date.tzinfo.utcoffset(date) is not None:
            year_start = datetime.datetime(date.year, 1, 1, tzinfo=date.tzinfo)
        else:
            year_start = datetime.datetime(date.year, 1, 1)
        delta = date - year_start
        julian_day = delta.days + delta.seconds / 86400.0
        return np.full((np.prod(self.field.shape),), julian_day)

    def cos_julian_day(self, date):
        radians = self.julian_day(date) / 365.25 * np.pi * 2
        return np.cos(radians)

    def sin_julian_day(self, date):
        radians = self.julian_day(date) / 365.25 * np.pi * 2
        return np.sin(radians)

    def local_time(self, date):
        lon = self.longitude(date)
        date = to_datetime(date)
        if date.tzinfo is not None and date.tzinfo.utcoffset(date) is not None:
            day_start = datetime.datetime(date.year, date.month, date.day, tzinfo=date.tzinfo)
        else:
            day_start = datetime.datetime(date.year, date.month, date.day)
        delta = date - day_start
        hours_since_midnight = (delta.days + delta.seconds / 86400.0) * 24
        return (lon / 360.0 * 24.0 + hours_since_midnight) % 24

    def cos_local_time(self, date):
        radians = self.local_time(date) / 24 * np.pi * 2
        return np.cos(radians)

    def sin_local_time(self, date):
        radians = self.local_time(date) / 24 * np.pi * 2
        return np.sin(radians)

    def insolation(self, date):
        return self.cos_solar_zenith_angle(date)

    def toa_incident_solar_radiation(self, date):
        from earthkit.data.utils.meteo import toa_incident_solar_radiation

        date = to_datetime(date)
        result = toa_incident_solar_radiation(
            date - datetime.timedelta(minutes=30),
            date + datetime.timedelta(minutes=30),
            self.latitude_(),
            self.longitude_(),
            intervals_per_hour=2,
        )
        return result.flatten()

    def cos_solar_zenith_angle(self, date):
        from earthkit.data.utils.meteo import cos_solar_zenith_angle

        date = to_datetime(date)
        result = cos_solar_zenith_angle(
            date,
            self.latitude_(),
            self.longitude_(),
        )
        return result.flatten()

    def __getattr__(self, name):
        if "+" not in name and "-" not in name:
            # If we are here, we are looking for a method that does not exist,
            # it has to be a method with a time delta.
            raise AttributeError(name)
        if "+" in name:
            fname, delta = name.split("+")
            sign = 1
        if "-" in name:
            fname, delta = name.split("-")
            sign = -1
        method = getattr(self, fname)

        if delta.endswith("h"):
            factor = 60
        elif delta.endswith("d"):
            factor = 24 * 60
        else:
            raise ValueError(f"Invalid time delta {delta} in {name}")

        delta = delta[:-1]
        delta = int(delta)
        delta = datetime.timedelta(minutes=delta) * factor * sign

        def wrapper(date):
            date = date + delta
            value = method(date)
            return value

        return wrapper


def make_datetime(date, time):
    if time is None:
        return date
    if date.hour or date.minute:
        raise ValueError(
            (
                f"Duplicate information about time time={time},"
                f"and time={date.hour}:{date.minute} from date={date}"
            )
        )
    assert date.hour == 0, (date, time)
    assert date.minute == 0, (date, time)
    assert str(time).isdigit(), (type(time), time)
    time = int(time)
    if time > 24:
        time = time // 100
    return datetime.datetime(date.year, date.month, date.day, time)


def index_to_coords(index: int, shape):
    assert isinstance(index, int), (index, type(index))

    result = [None] * len(shape)
    i = len(shape) - 1

    while i >= 0:
        result[i] = index % shape[i]
        index = index // shape[i]
        i -= 1

    result = tuple(result)

    assert len(result) == len(shape)
    return result


class ForcingsData:
    def __init__(self, source_or_dataset=None, request={}, **kwargs):
        # self.source_or_dataset = source_or_dataset
        request = dict(**request)
        request.update(kwargs)
        request = self.normalise_request(**request)

        if source_or_dataset is None:
            lats, lons = self.find_latlons(request)
            if lats is None:
                raise ValueError("latitudes must be specified when no source or dataset provided")

            if lons is None:
                raise ValueError("longitudes must be specified when no source or dataset provided")

            from earthkit.data import from_source

            vals = np.ones(lats.shape)
            d = {"values": vals, "geography": {"latitudes": lats, "longitudes": lons}}
            # d.update(self.request)
            source_or_dataset = from_source("list-of-dicts", [d])

        self.field = source_or_dataset[0]

        self.dates = self.find_dates(source_or_dataset, request)

        self.params = request["param"]
        if not isinstance(self.params, (tuple, list)):
            self.params = [self.params]

        self.numbers = self.find_numbers(source_or_dataset, request)
        if not isinstance(self.numbers, (tuple, list)):
            self.numbers = [self.numbers]

        # self.maker = ForcingMaker(field=field)
        # self.procs = {param: getattr(self.maker, param) for param in self.params}

    @staticmethod
    def find_latlons(request):
        lats = None
        for k in ["latitudes", "latitude"]:
            if k in request:
                lats = np.asarray(request.pop(k))
                break

        lons = None
        for k in ["longitudes", "longitude"]:
            if k in request:
                lons = np.asarray(request.pop(k))
                break

        return lats, lons

    @staticmethod
    def find_numbers(source_or_dataset, request):
        if "number" in request:
            return request["number"]

        assert hasattr(source_or_dataset, "unique"), (
            f"{source_or_dataset} (type '{type(source_or_dataset).__name__}')",
            " must have the unique method",
        )

        r = source_or_dataset.unique(
            "ensemble.member", squeeze=False, drop_none=True, patches={"ensemble.member": {None: 0}}
        )

        r = r.get("member", (0,))
        if not r:
            r = (0,)

        return r

    @staticmethod
    def find_dates(source_or_dataset, request):
        if "date" not in request and "time" in request:
            raise ValueError("Cannot specify time without date")

        if "date" in request and "time" not in request:
            return request["date"]

        if "date" in request and "time" in request:
            dates = [
                make_datetime(date, time)
                for date, time in itertools.product(request["date"], request["time"])
            ]
            assert len(set(dates)) == len(dates), "Duplicates dates in forcings."
            return dates

        assert "date" not in request and "time" not in request
        assert hasattr(source_or_dataset, "unique"), (
            f"{source_or_dataset} (type '{type(source_or_dataset).__name__}')",
            " must have the unique method",
        )

        r = source_or_dataset.unique("time.valid_datetime", squeeze=False)["valid_datetime"]
        return r

    @staticmethod
    @normalise("date", "date-list")
    @normalise("time", "int-list")
    @normalise("number", "int-list")
    def normalise_request(**request):
        return request


class ForcingsFieldData(DataFieldComponentHandler):
    def __init__(self, proc, date):
        self.proc = proc
        self.date = date

    def get_values(self, dtype=None, copy=True):
        """Get the values stored in the field as an array."""
        values = self.proc(self.date)
        if dtype is not None:
            values = values.astype(dtype)
        if copy:
            values = values.copy()
        return values

    def __getstate__(self):
        pass

    def __setstate__(self, state):
        pass


class ForcingsFieldList(SimpleFieldList):
    def __init__(self, source_or_dataset=None, *, request={}, **kwargs):
        self._data = ForcingsData(source_or_dataset, request, **kwargs)

        self.maker = ForcingMaker(field=self._data.field)
        self.procs = {param: getattr(self.maker, param) for param in self._data.params}
        self._len = len(self._data.dates) * len(self._data.params) * len(self._data.numbers)
        fields = []
        for n in range(self._len):
            field = self._make_one(n)
            fields.append(field)

        super().__init__(fields=fields)

    def _make_one(self, n):
        if n < 0:
            n = self._len + n

        if n >= self._len or n < 0:
            raise IndexError(n)

        date, param, number = index_to_coords(
            n, (len(self._data.dates), len(self._data.params), len(self._data.numbers))
        )

        date = self._data.dates[date]
        # assert isinstance(date, datetime.datetime), (date, type(date))
        param = self._data.params[param]
        number = self._data.numbers[number]

        return self._make_field(param, date, number)

    def _make_field(self, param, date, number):
        from earthkit.data.core.field import Field

        data = ForcingsFieldData(self.procs[param], date)

        # this will reuse geography from the maker.field
        field = Field.from_field(
            self.maker.field,
            data=data,
            parameter=dict(variable=param),
            time=dict(base_datetime=date),
            ensemble={"member": number},
        )

        return field


source = ForcingsFieldList
