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
import glob
import os

import pytest

from earthkit.data import from_source
from earthkit.data.field.component.processing import Duration, Processing, ProcessingStep
from earthkit.data.utils.testing import earthkit_examples_file, earthkit_remote_test_data_file

# local ERA6 statistics sample data (deterministic and ensemble)
_ERA6 = "/Users/ecm8620/data/era6/GRIBs"
_STTD = os.path.join(_ERA6, "sttd", "fc")  # deterministic statistics
_STTE = os.path.join(_ERA6, "stte", "fc")  # ensemble members (GRIB2 PDT 11)
_STTE_EM = os.path.join(_ERA6, "stte", "em")  # ensemble mean (GRIB2 PDT 12)
_STTE_ES = os.path.join(_ERA6, "stte", "es")  # ensemble spread (GRIB2 PDT 12)


def _requires(dirpath):
    return pytest.mark.skipif(not os.path.isdir(dirpath), reason=f"ERA6 sample data not available: {dirpath}")


requires_sttd = _requires(_STTD)
requires_stte = _requires(_STTE)
requires_stte_em = _requires(_STTE_EM)
requires_stte_es = _requires(_STTE_ES)


def _find(dirpath, pattern):
    matches = sorted(glob.glob(os.path.join(dirpath, pattern)))
    assert matches, f"no file matching {pattern} in {dirpath}"
    return matches[0]


def _summary(processing):
    """(kind, axis, method, window_length, window_anchor) per step, ignoring sampling frequency."""
    return [(s.kind(), s.axis(), s.method(), s.window_length(), s.window_anchor()) for s in processing]


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
        s = p[0]
        assert s.kind() == "time_aggregation"
        assert s.axis() == "forecast_period"
        assert s.method() == "sum"
        assert s.window_length() == "PT1H"
        assert s.window_length(type=datetime.timedelta) == datetime.timedelta(hours=1)
        assert s.window_anchor() == "right"
        assert s.sampling_frequency() == "PT200S"  # timeIncrement = 200 s


def test_grib2_processing_mapping_helpers():
    from earthkit.data.field.grib.processing import (
        _coded_duration,
        _methods_windows_from_high_level,
        _parse_timespan,
        _split_stattype,
    )

    assert _parse_timespan("1h") == Duration("PT1H")
    assert _parse_timespan("6h") == Duration("PT6H")
    assert _parse_timespan("1d") == Duration("P1D")
    assert _parse_timespan("900s") == Duration("PT900S")

    assert _coded_duration(24, 1) == Duration("P1D")  # 24 hours
    assert _coded_duration(1, 3) == Duration("P1M")  # 1 month (calendar)
    assert _coded_duration(1, 4) == Duration("P1Y")  # 1 year
    assert _coded_duration(900, 13) == Duration("PT900S")  # 900 seconds

    assert _split_stattype("daav") == [("da", "av")]
    assert _split_stattype("momx_daav") == [("mo", "mx"), ("da", "av")]

    def mw(meta, n):
        return _methods_windows_from_high_level(lambda k, d=None: meta.get(k, d), n)

    # "daily maximum of 1h average" (ERA6 damx-1h): outer from stattype, inner from stepType + timespan
    assert mw({"stattype": "damx", "stepType": "avg", "timespan": "1h"}, 2) == [
        ("maximum", Duration("P1D")),
        ("mean", Duration("PT1H")),
    ]

    # "daily average" with no timespan (ERA6 daav-none): stepType echoes the outer stat -> no inner step
    assert mw({"stattype": "daav", "stepType": "avg", "timespan": "none"}, 1) == [("mean", Duration("P1D"))]

    # "monthly average of daily values" (ERA6 moav-24h)
    assert mw({"stattype": "moav", "stepType": "avg", "timespan": "24h"}, 2) == [
        ("mean", Duration("P1M")),
        ("mean", Duration("P1D")),
    ]

    # multi-segment stattype "a_b": segment a is the outer step, b the inner (no separate stepType step)
    assert mw({"stattype": "momx_daav", "stepType": "avg", "timespan": "none"}, 2) == [
        ("maximum", Duration("P1M")),
        ("mean", Duration("P1D")),
    ]

    # a plain forecast accumulation (no stattype): inner comes from stepType + step range
    assert mw({"stepType": "accum", "startStep": 0, "endStep": 6}, 1) == [("sum", Duration("PT6H"))]


def test_grib2_processing_multi_range_statistics():
    eccodes = pytest.importorskip("eccodes")

    # start from a real GRIB2 accumulation and turn it into a 2 time-range product:
    # a daily average (typeOfTimeIncrement=1) of a 1h maximum (typeOfTimeIncrement=2)
    src = from_source("url", earthkit_remote_test_data_file("xr_engine/date/lsp_step_range.grib2")).to_fieldlist()
    h = eccodes.codes_new_from_message(bytes(src[0].message()))
    try:
        eccodes.codes_set(h, "numberOfTimeRanges", 2)
        eccodes.codes_set_array(h, "typeOfStatisticalProcessing", [0, 2])  # average, maximum
        eccodes.codes_set_array(h, "typeOfTimeIncrement", [1, 2])
        eccodes.codes_set_array(h, "indicatorOfUnitForTimeRange", [1, 1])  # hours
        eccodes.codes_set_array(h, "lengthOfTimeRange", [24, 1])
        eccodes.codes_set_array(h, "indicatorOfUnitForTimeIncrement", [1, 13])  # hour, second
        eccodes.codes_set_array(h, "timeIncrement", [1, 900])
        buf = eccodes.codes_get_message(h)
    finally:
        eccodes.codes_release(h)

    f = from_source("memory", bytes(buf)).to_fieldlist()[0]
    assert f.processing.to_dict() == {
        "items": [
            {
                "kind": "time_aggregation",
                "axis": "forecast_reference_time",
                "method": "mean",
                "window_length": "P1D",
                "window_anchor": "left",
                "sampling_frequency": "PT1H",
            },
            {
                "kind": "time_aggregation",
                "axis": "forecast_period",
                "method": "maximum",
                "window_length": "PT1H",
                "window_anchor": "right",
                "sampling_frequency": "PT900S",
            },
        ]
    }

    # propagated accessors across the chain
    assert f.get("processing.method") == ("mean", "maximum")
    assert f.get("processing.axis") == ("forecast_reference_time", "forecast_period")
    assert f.get("processing.method[1]") == "maximum"


@requires_sttd
def test_era6_sttd_daily_max_of_hourly_mean():
    # damx-1h: daily maximum of 1-hourly averages (deterministic -> no ensemble step)
    f = from_source("file", _find(_STTD, "*-base-damx-1h-fc.grib")).to_fieldlist()[0]
    assert _summary(f.processing) == [
        ("time_aggregation", "forecast_reference_time", "maximum", "P1D", "left"),
        ("time_aggregation", "forecast_period", "mean", "PT1H", "right"),
    ]
    # sampling frequencies come from the coded timeIncrement arrays
    assert f.processing[0].sampling_frequency() == "PT1H"
    assert f.processing[1].sampling_frequency() is not None


@requires_sttd
def test_era6_sttd_monthly_max_of_daily_total():
    # momx-24h: monthly maximum of daily totals
    f = from_source("file", _find(_STTD, "*-base-momx-24h-fc.grib")).to_fieldlist()[0]
    assert _summary(f.processing) == [
        ("time_aggregation", "forecast_reference_time", "maximum", "P1M", "left"),
        ("time_aggregation", "forecast_reference_time", "sum", "P1D", "left"),
    ]


@requires_sttd
def test_era6_sttd_daily_average_no_inner():
    # daav-none: a single daily-average step (timespan "none" -> no inner step)
    f = from_source("file", _find(_STTD, "*-base-daav-none-fc.grib")).to_fieldlist()[0]
    assert _summary(f.processing) == [
        ("time_aggregation", "forecast_reference_time", "mean", "P1D", "left"),
    ]


@requires_stte
def test_era6_stte_members_have_no_ensemble_reduction():
    # these ensemble products are individual members (GRIB2 PDT 11, not derived forecasts),
    # so they carry no ensemble reduction step - only the time aggregation chain
    f = from_source("file", _find(_STTE, "*-base-damx-1h-fc.grib")).to_fieldlist()[0]
    assert f.get("metadata.productDefinitionTemplateNumber") == 11
    assert _summary(f.processing) == [
        ("time_aggregation", "forecast_reference_time", "maximum", "P1D", "left"),
        ("time_aggregation", "forecast_period", "mean", "PT1H", "right"),
    ]


@requires_stte_em
def test_era6_stte_ensemble_mean():
    # em: ensemble mean (GRIB2 PDT 12, derivedForecast=0) -> outermost ensemble mean reduction
    f = from_source("file", _find(_STTE_EM, "*-base-daav-none-em.grib")).to_fieldlist()[0]
    assert f.get("metadata.productDefinitionTemplateNumber") == 12

    steps = f.processing
    assert steps[0].kind() == "reduction"
    assert steps[0].axis() == "ensemble"
    assert steps[0].method() == "mean"
    assert steps[0].sample_size() == f.get("metadata.numberOfForecastsInEnsemble")
    assert _summary(steps) == [
        ("reduction", "ensemble", "mean", None, None),
        ("time_aggregation", "forecast_reference_time", "mean", "P1D", "left"),
    ]


@requires_stte_es
def test_era6_stte_ensemble_spread():
    # es: ensemble spread (GRIB2 PDT 12, derivedForecast=4) -> ensemble standard deviation reduction
    f = from_source("file", _find(_STTE_ES, "*-base-daav-none-es.grib")).to_fieldlist()[0]
    assert f.get("metadata.productDefinitionTemplateNumber") == 12
    assert f.get("metadata.derivedForecast") == 4

    steps = f.processing
    assert steps[0].kind() == "reduction"
    assert steps[0].axis() == "ensemble"
    assert steps[0].method() == "standard_deviation"
    assert steps[0].sample_size() == f.get("metadata.numberOfForecastsInEnsemble")


def test_grib2_derived_forecast_ensemble_reduction():
    # a derived forecast (GRIB2 PDT 12) adds an outermost ensemble reduction step whose
    # method comes from derivedForecast and size from numberOfForecastsInEnsemble
    eccodes = pytest.importorskip("eccodes")

    src = from_source("url", earthkit_remote_test_data_file("xr_engine/date/lsp_step_range.grib2")).to_fieldlist()
    h = eccodes.codes_new_from_message(bytes(src[0].message()))
    try:
        eccodes.codes_set(h, "productDefinitionTemplateNumber", 12)
        eccodes.codes_set(h, "derivedForecast", 0)  # unweighted mean of all members
        eccodes.codes_set(h, "numberOfForecastsInEnsemble", 51)
        buf = eccodes.codes_get_message(h)
    finally:
        eccodes.codes_release(h)

    f = from_source("memory", bytes(buf)).to_fieldlist()[0]
    assert f.processing.to_dict() == {
        "items": [
            {"kind": "reduction", "axis": "ensemble", "method": "mean", "sample_size": 51},
            {
                "kind": "time_aggregation",
                "axis": "forecast_period",
                "method": "sum",
                "window_length": "PT1H",
                "window_anchor": "right",
                "sampling_frequency": "PT200S",
            },
        ]
    }

    fl = f.to_fieldlist()
    assert len(fl.sel({"processing.axis[0]": "ensemble"})) == 1
    assert len(fl.sel({"processing.method[0]": "mean", "processing.sample_size[0]": 51})) == 1


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
