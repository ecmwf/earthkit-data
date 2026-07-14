#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pytest

from earthkit.data import from_source
from earthkit.data.field.component.time import DailyClimatologyTime, create_time
from earthkit.data.utils.testing import earthkit_test_data_file


def test_daily_climatology_time_from_grib():
    """Test that daily climatology GRIB data produces DailyClimatologyTime."""
    ds = from_source("file", earthkit_test_data_file("t-130-pl-em.grib")).to_fieldlist()

    f = ds[0]
    # dataDate=101 means January 1 -> DOY=1
    assert isinstance(f.time, DailyClimatologyTime)
    assert f.time.day_of_year() == 1
    assert f.time.month == 1
    assert f.time.day == 1

    # Other time fields should be None for daily climatology
    assert f.time.base_datetime() is None
    assert f.time.base_date() is None
    assert f.time.base_time() is None
    assert f.time.valid_datetime() is None
    assert f.time.step() is None
    assert f.time.forecast_month() is None
    assert f.time.indexing_datetime() is None


def test_daily_climatology_time_get_key():
    """Test that the day_of_year key is accessible via .get()."""
    ds = from_source("file", earthkit_test_data_file("t-130-pl-em.grib")).to_fieldlist()

    f = ds[0]
    assert f.time.get("day_of_year") == 1


def test_daily_climatology_time_all_fields():
    """Test that all fields in the dataset have consistent daily climatology time."""
    ds = from_source("file", earthkit_test_data_file("t-130-pl-em.grib")).to_fieldlist()

    for f in ds:
        assert isinstance(f.time, DailyClimatologyTime)
        assert f.time.day_of_year() == 1
        assert f.time.month == 1
        assert f.time.day == 1


class TestDailyClimatologyTimeComponent:
    """Unit tests for DailyClimatologyTime class."""

    def test_from_day_of_year(self):
        t = DailyClimatologyTime.from_day_of_year(day_of_year=1)
        assert t.day_of_year() == 1
        assert t.month == 1
        assert t.day == 1

    def test_from_day_of_year_feb29(self):
        # DOY 60 = Feb 29 in a leap year (reference year 2000)
        t = DailyClimatologyTime.from_day_of_year(day_of_year=60)
        assert t.day_of_year() == 60
        assert t.month == 2
        assert t.day == 29

    def test_from_day_of_year_dec31(self):
        # DOY 366 = Dec 31 in a leap year
        t = DailyClimatologyTime.from_day_of_year(day_of_year=366)
        assert t.day_of_year() == 366
        assert t.month == 12
        assert t.day == 31

    def test_from_month_day_jan1(self):
        t = DailyClimatologyTime.from_month_day(month=1, day=1)
        assert t.day_of_year() == 1
        assert t.month == 1
        assert t.day == 1

    def test_from_month_day_jul15(self):
        t = DailyClimatologyTime.from_month_day(month=7, day=15)
        assert t.month == 7
        assert t.day == 15
        # July 15 in a leap year: 31(Jan) + 29(Feb) + 31(Mar) + 30(Apr) + 31(May) + 30(Jun) + 15 = 197
        assert t.day_of_year() == 197

    def test_from_month_day_dec31(self):
        t = DailyClimatologyTime.from_month_day(month=12, day=31)
        assert t.day_of_year() == 366
        assert t.month == 12
        assert t.day == 31

    def test_from_dict(self):
        t = create_time({"day_of_year": 1})
        assert isinstance(t, DailyClimatologyTime)
        assert t.day_of_year() == 1

    def test_from_dict_mid_year(self):
        t = create_time({"day_of_year": 182})
        assert isinstance(t, DailyClimatologyTime)
        assert t.day_of_year() == 182

    def test_to_dict(self):
        t = DailyClimatologyTime.from_day_of_year(day_of_year=42)
        d = t.to_dict()
        assert d == {"day_of_year": 42}

    def test_set(self):
        t = DailyClimatologyTime.from_day_of_year(day_of_year=1)
        t2 = t.set(day_of_year=100)
        assert t2.day_of_year() == 100
        # Original unchanged
        assert t.day_of_year() == 1

    def test_set_no_change(self):
        t = DailyClimatologyTime.from_day_of_year(day_of_year=1)
        t2 = t.set()
        assert t2 is t

    def test_invalid_day_of_year_zero(self):
        with pytest.raises(ValueError):
            DailyClimatologyTime(day_of_year=0)

    def test_invalid_day_of_year_367(self):
        with pytest.raises(ValueError):
            DailyClimatologyTime(day_of_year=367)

    def test_invalid_day_of_year_negative(self):
        with pytest.raises(ValueError):
            DailyClimatologyTime(day_of_year=-1)

    def test_pickle(self):
        import pickle

        t = DailyClimatologyTime.from_day_of_year(day_of_year=42)
        data = pickle.dumps(t)
        t2 = pickle.loads(data)
        assert t2.day_of_year() == 42
        assert t2.month == t.month
        assert t2.day == t.day


class TestDailyClimatologyGribRoundtrip:
    """Test GRIB encoding/decoding roundtrip for daily climatology."""

    def test_doy_to_grib_jan1(self):
        """DOY 1 (Jan 1) should encode as dataDate=101."""
        from earthkit.data.field.grib.time import _month_day_from_day_of_year

        month, day = _month_day_from_day_of_year(1)
        assert month == 1
        assert day == 1
        # GRIB encoding: 100*month + day
        assert month * 100 + day == 101

    def test_doy_to_grib_dec31(self):
        """DOY 366 (Dec 31) should encode as dataDate=1231."""
        from earthkit.data.field.grib.time import _month_day_from_day_of_year

        month, day = _month_day_from_day_of_year(366)
        assert month == 12
        assert day == 31
        assert month * 100 + day == 1231

    def test_grib_to_doy_jan1(self):
        """dataDate=101 (Jan 1) should produce DOY=1."""
        from earthkit.data.field.grib.time import _day_of_year_from_month_day

        # dataDate=101 -> month=1, day=1
        data_date = 101
        month = data_date // 100
        day = data_date % 100
        doy = _day_of_year_from_month_day(month, day)
        assert doy == 1

    def test_grib_to_doy_dec31(self):
        """dataDate=1231 (Dec 31) should produce DOY=366."""
        from earthkit.data.field.grib.time import _day_of_year_from_month_day

        data_date = 1231
        month = data_date // 100
        day = data_date % 100
        doy = _day_of_year_from_month_day(month, day)
        assert doy == 366

    def test_roundtrip_all_days(self):
        """Test that all DOY values roundtrip correctly through GRIB encoding."""
        from earthkit.data.field.grib.time import _day_of_year_from_month_day, _month_day_from_day_of_year

        for doy in range(1, 367):
            month, day = _month_day_from_day_of_year(doy)
            data_date = month * 100 + day
            # Reverse: parse dataDate back
            m2 = data_date // 100
            d2 = data_date % 100
            doy2 = _day_of_year_from_month_day(m2, d2)
            assert doy2 == doy, f"Roundtrip failed for DOY {doy}: got {doy2}"
