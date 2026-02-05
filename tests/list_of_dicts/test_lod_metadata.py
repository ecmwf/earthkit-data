#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import os
import sys

import pytest

here = os.path.dirname(__file__)
sys.path.insert(0, here)

from lod_fixtures import build_lod_fieldlist  # noqa: E402


@pytest.mark.parametrize("mode", ["list-of-dicts", "loop"])
def test_lod_metadata_core(lod_ll_flat, mode):
    ds = build_lod_fieldlist(lod_ll_flat, mode)

    ref = [500, 850, 500, 850, 850, 600]
    assert ds.get("vertical.level") == ref

    assert ds[0].get("vertical.level") == 500
    assert ds[0].vertical.level() == 500

    assert ds[0].get("parameter.variable") == "t"
    assert ds[0].parameter.variable() == "t"
    # assert ds[0].get("shortName") == "t"

    dt_ref = datetime.datetime.fromisoformat("2018-08-01T09:00:00")
    assert ds[0].get("time.valid_datetime") == dt_ref
    # assert ds[0].metadata().valid_datetime() == dt_ref
    # assert ds[0].datetime() == {"base_time": None, "valid_time": dt_ref}
    assert ds[0].datetime() == {"base_time": dt_ref, "valid_time": dt_ref}


@pytest.mark.parametrize("data", ["lod_ll_forecast_1", "lod_ll_forecast_2"])
@pytest.mark.parametrize("mode", ["list-of-dicts", "loop"])
def test_lod_metadata_forecast_a(request, data, mode):
    ds = build_lod_fieldlist(request.getfixturevalue(data), mode)

    valid_ref = datetime.datetime.fromisoformat("2018-08-01T09:00:00")
    base_ref = datetime.datetime.fromisoformat("2018-08-01T03:00:00")
    assert ds[0].get("time.valid_datetime") == valid_ref
    assert ds[0].time.valid_datetime() == valid_ref
    # assert ds[0].metadata().valid_datetime() == valid_ref
    assert ds[0].get("time.base_datetime") == base_ref
    # assert ds[0].metadata().base_datetime() == base_ref
    assert ds[0].datetime() == {"base_time": base_ref, "valid_time": valid_ref}
    assert ds[0].get("time.step") == datetime.timedelta(hours=6)
    # assert ds[0].metadata().step_timedelta() == datetime.timedelta(hours=6)
    assert ds[0].time.step() == datetime.timedelta(hours=6)
    assert ds[0].get("time.forecast_reference_time") == base_ref
    assert ds[1].get("time.forecast_reference_time") == base_ref


@pytest.mark.parametrize("data", ["lod_ll_forecast_3", "lod_ll_forecast_4"])
@pytest.mark.parametrize("mode", ["list-of-dicts", "loop"])
def test_lod_metadata_forecast_b(request, data, mode):
    ds = build_lod_fieldlist(request.getfixturevalue(data), mode)

    valid_ref = datetime.datetime.fromisoformat("2018-08-01T09:00:00")
    base_ref = datetime.datetime.fromisoformat("2018-08-01T03:00:00")
    assert ds[0].get("time.valid_datetime") == valid_ref
    assert ds[0].time.valid_datetime() == valid_ref
    # assert ds[0].metadata().valid_datetime() == valid_ref
    assert ds[0].get("time.base_datetime") == base_ref
    assert ds[0].time.base_datetime() == base_ref
    # assert ds[0].metadata().base_datetime() == base_ref
    assert ds[0].datetime() == {"base_time": base_ref, "valid_time": valid_ref}
    assert ds[0].get("time.step") == datetime.timedelta(hours=6)
    # assert ds[0].metadata().step_timedelta() == datetime.timedelta(hours=6)
    assert ds[0].time.step() == datetime.timedelta(hours=6)
    assert ds[0].get("time.forecast_reference_time") == base_ref
    assert ds[1].get("time.forecast_reference_time") == base_ref
