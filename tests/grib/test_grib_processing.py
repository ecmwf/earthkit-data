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

import pytest

from earthkit.data import from_source
from earthkit.data.field.component.processing import Duration, Processing, ProcessingStep
from earthkit.data.utils.testing import earthkit_examples_file, earthkit_remote_test_data_file


@pytest.mark.cache
def test_grib_processing_analysis():
    ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/msl_analysis.grib")).to_fieldlist()

    f = ds[0]
    assert f.time.base_datetime() == datetime.datetime(2016, 9, 25)
    assert f.time.step() == datetime.timedelta(0)

    # an analysis field has no processing steps
    assert isinstance(f.processing, Processing)
    assert len(f.processing) == 0
    assert f.processing.kind() == ()
    assert f.get("processing.method") == ()
    assert f.get("processing.method[0]") is None


@pytest.mark.cache
def test_grib_processing_step_range_1():
    ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/wgust_step_range.grib1")).to_fieldlist()

    f = ds[2]
    assert f.time.step() == datetime.timedelta(hours=24)

    p = f.processing
    assert len(p) == 1
    step = p[0]
    assert step.kind() == ProcessingStep.TIME_AGGREGATION
    assert step.axis() == "forecast_period"
    assert step.method() == "maximum"
    assert step.window_length() == "PT6H"
    assert step.window_length(type=datetime.timedelta) == datetime.timedelta(hours=6)
    assert step.window_length(type=Duration) == Duration("PT6H")
    assert step.window_anchor() == "right"

    assert f.get("processing.method[0]") == "maximum"
    assert f.get("processing[0].window_length") == "PT6H"
    assert f.get("processing.window_length") == ("PT6H",)


@pytest.mark.cache
def test_grib_processing_step_range_2():
    ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/lsp_step_range.grib2")).to_fieldlist()

    for i in (0, 1):
        p = ds[i].processing
        assert len(p) == 1
        assert p[0].kind() == "time_aggregation"
        assert p[0].method() == "sum"
        assert p[0].window_length() == "PT1H"
        assert p[0].window_length(type=datetime.timedelta) == datetime.timedelta(hours=1)


def test_grib_processing_instant_collector():
    f = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()[0]

    ctx = {}
    handler = f._components["processing"]
    handler.COLLECTOR.collect_keys(handler, ctx)

    assert ctx == {"stepType": "instant"}


def test_grib_processing_set_and_collect():
    f = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()[0]

    f2 = f.set({
        "processing": [
            {
                "kind": "time_aggregation",
                "axis": "forecast_period",
                "method": "sum",
                "window_length": "PT6H",
                "window_anchor": "right",
                "sampling_frequency": "PT0S",
            }
        ]
    })
    assert len(f2.processing) == 1
    assert f2.get("processing.method[0]") == "sum"
    assert f2.get("processing[0].method") == "sum"

    from earthkit.data.field.grib.processing import COLLECTOR

    ctx = {}
    handler = f2._components["processing"]
    COLLECTOR.collect_keys(handler, ctx)
    assert ctx["stepType"] == "accum"


def test_grib_processing_selection():
    base = from_source("file", earthkit_examples_file("test.grib")).to_fieldlist()[0]

    def mk(steps):
        return base.set({"processing": steps})

    f_max6_mean = mk([
        {
            "kind": "time_aggregation",
            "axis": "forecast_period",
            "method": "maximum",
            "window_length": "PT6H",
            "window_anchor": "right",
            "sampling_frequency": "PT0S",
        },
        {"kind": "reduction", "axis": "ensemble", "method": "mean", "sample_size": 50},
    ])
    f_sum1 = mk([
        {
            "kind": "time_aggregation",
            "axis": "forecast_period",
            "method": "sum",
            "window_length": "PT1H",
            "window_anchor": "right",
            "sampling_frequency": "PT0S",
        }
    ])
    f_monthly = mk([
        {
            "kind": "time_aggregation",
            "axis": "forecast_reference_time",
            "method": "mean",
            "window_length": "P1M",
            "window_anchor": "left",
            "sampling_frequency": "P1D",
        }
    ])
    f_plain = base

    from earthkit.data.indexing.simple import SimpleFieldList

    fl = SimpleFieldList.from_fields([f_max6_mean, f_sum1, f_monthly, f_plain])
    assert len(fl) == 4

    # indexed key pins a position in the chain
    assert len(fl.sel({"processing.axis[0]": "ensemble"})) == 0
    r = fl.sel({"processing[0].method": "maximum", "processing[0].window_length": "PT6H"})
    assert len(r) == 1

    # plain (chain-valued) key matches if any item matches
    assert len(fl.sel({"processing.window_length": "PT6H"})) == 1
    assert len(fl.sel({"processing.window_length": ["PT6H", "PT1H"]})) == 2

    # slices select a closed interval
    assert len(fl.sel({"processing.window_length": slice("PT6H", "P1D")})) == 1
    assert len(fl.sel({"processing.window_length": slice("PT6H", None)})) == 2

    # fuzzy calendar duration matching
    assert len(fl.sel({"processing.window_length": "P30D"})) == 1

    # enum value matching across the chain
    assert len(fl.sel({"processing.method": "mean"})) == 2


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
