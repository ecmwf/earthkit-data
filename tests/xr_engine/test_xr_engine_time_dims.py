#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Tests for the ``time_dims`` kwarg that replaced ``time_dim_mode``.

All tests use synthetic list-of-dicts data so no network access is needed.
"""

import numpy as np
import pytest
from xr_engine_fixtures import compare_dims

from earthkit.data import from_source

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def forecast_fl():
    """FieldList with forecast_reference_time + step metadata (2 params, 2 steps)."""
    proto = {
        "geography": {"latitudes": [10.0, 0.0, -10.0], "longitudes": [20.0, 40.0]},
        "values": [1, 2, 3, 4, 5, 6],
    }
    d = [
        {
            "parameter": {"variable": "t"},
            "vertical": {"level": 500},
            "time": {"base_datetime": "2024-06-03T00:00:00", "step": 0},
            **proto,
        },
        {
            "parameter": {"variable": "t"},
            "vertical": {"level": 500},
            "time": {"base_datetime": "2024-06-03T00:00:00", "step": 6},
            **proto,
        },
        {
            "parameter": {"variable": "u"},
            "vertical": {"level": 500},
            "time": {"base_datetime": "2024-06-03T00:00:00", "step": 0},
            **proto,
        },
        {
            "parameter": {"variable": "u"},
            "vertical": {"level": 500},
            "time": {"base_datetime": "2024-06-03T00:00:00", "step": 6},
            **proto,
        },
    ]
    return from_source("list-of-dicts", d).to_fieldlist()


@pytest.fixture
def multi_date_fl():
    """FieldList with 2 dates × 2 steps × 1 param – suitable for all time_dims configs."""
    proto = {
        "geography": {"latitudes": [10.0, 0.0], "longitudes": [20.0, 40.0]},
        "values": [1, 2, 3, 4],
    }
    d = [
        {
            "parameter": {"variable": "t"},
            "vertical": {"level": 500},
            "time": {"base_datetime": "2024-06-03T00:00:00", "step": 0},
            **proto,
        },
        {
            "parameter": {"variable": "t"},
            "vertical": {"level": 500},
            "time": {"base_datetime": "2024-06-03T00:00:00", "step": 6},
            **proto,
        },
        {
            "parameter": {"variable": "t"},
            "vertical": {"level": 500},
            "time": {"base_datetime": "2024-06-04T00:00:00", "step": 0},
            **proto,
        },
        {
            "parameter": {"variable": "t"},
            "vertical": {"level": 500},
            "time": {"base_datetime": "2024-06-04T00:00:00", "step": 6},
            **proto,
        },
    ]
    return from_source("list-of-dicts", d).to_fieldlist()


@pytest.fixture
def valid_time_fl():
    """FieldList with valid_datetime only (no base_datetime / step)."""
    proto = {
        "geography": {"latitudes": [10.0, 0.0, -10.0], "longitudes": [20.0, 40.0]},
        "values": [1, 2, 3, 4, 5, 6],
    }
    d = [
        {"parameter": {"variable": "t"}, "time": {"valid_datetime": "2024-06-03T00:00:00"}, **proto},
        {"parameter": {"variable": "t"}, "time": {"valid_datetime": "2024-06-03T06:00:00"}, **proto},
        {"parameter": {"variable": "u"}, "time": {"valid_datetime": "2024-06-03T00:00:00"}, **proto},
        {"parameter": {"variable": "u"}, "time": {"valid_datetime": "2024-06-03T06:00:00"}, **proto},
    ]
    return from_source("list-of-dicts", d).to_fieldlist()


# ---------------------------------------------------------------------------
# Tests: default time_dims (forecast_reference_time + step)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("lazy_load", [True, False])
def test_default_time_dims(forecast_fl, lazy_load):
    """Default time_dims produces forecast_reference_time and step dimensions."""
    ds = forecast_fl.to_xarray(profile="earthkit", lazy_load=lazy_load)

    dims = {
        "step": [np.timedelta64(0, "h"), np.timedelta64(6, "h")],
    }
    compare_dims(ds, dims, order_ref_var="t")
    assert "forecast_reference_time" not in ds.dims or ds.sizes.get("forecast_reference_time", 0) <= 1
    assert "date" not in ds.dims
    assert "time" not in ds.dims
    assert "valid_time" not in ds.dims


# ---------------------------------------------------------------------------
# Tests: time_dims=["valid_time"]
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("lazy_load", [True, False])
def test_time_dims_valid_time(valid_time_fl, lazy_load):
    """time_dims=["valid_time"] produces a single valid_time dimension."""
    ds = valid_time_fl.to_xarray(
        profile="earthkit",
        time_dims=["valid_time"],
        lazy_load=lazy_load,
    )

    dims = {
        "valid_time": [
            np.datetime64("2024-06-03T00:00:00", "ns"),
            np.datetime64("2024-06-03T06:00:00", "ns"),
        ],
    }
    compare_dims(ds, dims, order_ref_var="t")
    assert "forecast_reference_time" not in ds.dims
    assert "step" not in ds.dims
    assert "date" not in ds.dims


# ---------------------------------------------------------------------------
# Tests: time_dims=["date", "time", "step"]
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("lazy_load", [True, False])
def test_time_dims_date_time_step(forecast_fl, lazy_load):
    """time_dims=["date", "time", "step"] produces three separate dimensions."""
    ds = forecast_fl.to_xarray(
        profile="earthkit",
        time_dims=["date", "time", "step"],
        lazy_load=lazy_load,
        squeeze=False,
    )

    assert "date" in ds.dims
    assert "time" in ds.dims
    assert "step" in ds.dims
    assert "forecast_reference_time" not in ds.dims
    assert "valid_time" not in ds.dims


# ---------------------------------------------------------------------------
# Tests: time_dims=["forecast_reference_time", "step"] (explicit)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("lazy_load", [True, False])
def test_time_dims_explicit_forecast(multi_date_fl, lazy_load):
    """Explicitly requesting ["forecast_reference_time", "step"] works the same as default."""
    ds = multi_date_fl.to_xarray(
        profile="earthkit",
        time_dims=["forecast_reference_time", "step"],
        lazy_load=lazy_load,
    )

    assert "forecast_reference_time" in ds.dims
    assert "step" in ds.dims
    assert "date" not in ds.dims
    assert "time" not in ds.dims
    assert "valid_time" not in ds.dims

    dims = {
        "forecast_reference_time": [
            np.datetime64("2024-06-03T00:00:00", "ns"),
            np.datetime64("2024-06-04T00:00:00", "ns"),
        ],
        "step": [np.timedelta64(0, "h"), np.timedelta64(6, "h")],
    }
    compare_dims(ds, dims, order_ref_var="t")


# ---------------------------------------------------------------------------
# Tests: dimension ordering follows time_dims order
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("lazy_load", [True, False])
def test_time_dims_order_step_before_forecast(multi_date_fl, lazy_load):
    """The order of roles in time_dims controls the dimension order in the dataset."""
    ds = multi_date_fl.to_xarray(
        profile="earthkit",
        time_dims=["step", "forecast_reference_time"],
        lazy_load=lazy_load,
    )

    # Both dims must be present
    assert "step" in ds.dims
    assert "forecast_reference_time" in ds.dims

    # Verify the order: step should come before forecast_reference_time
    var_dims = list(ds["t"].dims)
    step_idx = var_dims.index("step")
    frt_idx = var_dims.index("forecast_reference_time")
    assert step_idx < frt_idx, (
        f"Expected step (idx={step_idx}) before forecast_reference_time (idx={frt_idx}), got dims={var_dims}"
    )


# ---------------------------------------------------------------------------
# Tests: single-element time_dims
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("lazy_load", [True, False])
def test_time_dims_step_only(forecast_fl, lazy_load):
    """time_dims=["step"] produces only a step dimension, no forecast_reference_time."""
    ds = forecast_fl.to_xarray(
        profile="earthkit",
        time_dims=["step"],
        lazy_load=lazy_load,
    )

    assert "step" in ds.dims
    assert "forecast_reference_time" not in ds.dims
    assert "valid_time" not in ds.dims
    assert "date" not in ds.dims

    dims = {
        "step": [np.timedelta64(0, "h"), np.timedelta64(6, "h")],
    }
    compare_dims(ds, dims, order_ref_var="t")


@pytest.mark.parametrize("lazy_load", [True, False])
def test_time_dims_forecast_reference_time_only(lazy_load):
    """time_dims=["forecast_reference_time"] produces only a forecast_reference_time dimension."""
    proto = {
        "geography": {"latitudes": [10.0, 0.0], "longitudes": [20.0, 40.0]},
        "values": [1, 2, 3, 4],
    }
    # Use single step so the data forms a valid hypercube without a step dimension
    d = [
        {
            "parameter": {"variable": "t"},
            "vertical": {"level": 500},
            "time": {"base_datetime": "2024-06-03T00:00:00", "step": 0},
            **proto,
        },
        {
            "parameter": {"variable": "t"},
            "vertical": {"level": 500},
            "time": {"base_datetime": "2024-06-04T00:00:00", "step": 0},
            **proto,
        },
    ]
    fl = from_source("list-of-dicts", d).to_fieldlist()
    ds = fl.to_xarray(
        profile="earthkit",
        time_dims=["forecast_reference_time"],
        lazy_load=lazy_load,
    )

    assert "forecast_reference_time" in ds.dims
    assert "step" not in ds.dims
    assert "valid_time" not in ds.dims

    dims = {
        "forecast_reference_time": [
            np.datetime64("2024-06-03T00:00:00", "ns"),
            np.datetime64("2024-06-04T00:00:00", "ns"),
        ],
    }
    compare_dims(ds, dims, order_ref_var="t")


# ---------------------------------------------------------------------------
# Tests: interaction with dim_name_from_role_name
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("lazy_load", [True, False])
def test_time_dims_valid_time_dim_name_from_key(valid_time_fl, lazy_load):
    """With dim_name_from_role_name=False, the dim name comes from the metadata key."""
    ds = valid_time_fl.to_xarray(
        profile="earthkit",
        time_dims=["valid_time"],
        dim_name_from_role_name=False,
        lazy_load=lazy_load,
    )

    # The metadata key for valid_time is "time.valid_datetime", stripped to "valid_datetime"
    assert "valid_datetime" in ds.dims
    assert "valid_time" not in ds.dims


@pytest.mark.parametrize("lazy_load", [True, False])
def test_time_dims_forecast_dim_name_from_key(multi_date_fl, lazy_load):
    """With dim_name_from_role_name=False, forecast dims get names from metadata keys."""
    ds = multi_date_fl.to_xarray(
        profile="earthkit",
        time_dims=["forecast_reference_time", "step"],
        dim_name_from_role_name=False,
        lazy_load=lazy_load,
    )

    # The metadata key for forecast_reference_time is "time.forecast_reference_time"
    # stripped to "forecast_reference_time" — same as role name in this case
    assert "forecast_reference_time" in ds.dims
    # The metadata key for step is "time.step", stripped to "step"
    assert "step" in ds.dims


# ---------------------------------------------------------------------------
# Tests: invalid role name
# ---------------------------------------------------------------------------


def test_time_dims_invalid_role_raises():
    """An unrecognised role name in time_dims raises ValueError."""
    proto = {
        "geography": {"latitudes": [10.0], "longitudes": [20.0]},
        "values": [1],
        "time": {"valid_datetime": "2024-06-03T00:00:00"},
    }
    d = [{"parameter": {"variable": "t"}, **proto}]
    fl = from_source("list-of-dicts", d).to_fieldlist()

    with pytest.raises(ValueError, match="Unknown time dimension role"):
        fl.to_xarray(profile="earthkit", time_dims=["not_a_role"])


# ---------------------------------------------------------------------------
# Tests: time_dims as a single string (convenience)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("lazy_load", [True, False])
def test_time_dims_single_string(valid_time_fl, lazy_load):
    """A single string value for time_dims is coerced to a list."""
    ds = valid_time_fl.to_xarray(
        profile="earthkit",
        time_dims="valid_time",
        lazy_load=lazy_load,
    )

    dims = {
        "valid_time": [
            np.datetime64("2024-06-03T00:00:00", "ns"),
            np.datetime64("2024-06-03T06:00:00", "ns"),
        ],
    }
    compare_dims(ds, dims, order_ref_var="t")


# ---------------------------------------------------------------------------
# Tests: extra_dims colliding with ignored (inactive) predefined time dims
# ---------------------------------------------------------------------------
# When a user specifies extra_dims that overlap with a known time role that
# is *not* in time_dims, the ignored-dim blocklist should suppress the extra
# dim so it does not appear twice or conflict with the active configuration.


@pytest.fixture
def collision_fl():
    """FieldList carrying forecast metadata from which date, time, step, and
    valid_datetime can all be derived.

    Using base_datetime + step lets the LOD time component derive all the
    other keys (base_date, base_time, valid_datetime) automatically.
    """
    proto = {
        "geography": {"latitudes": [10.0, 0.0], "longitudes": [20.0, 40.0]},
        "values": [1, 2, 3, 4],
    }
    d = [
        {
            "parameter": {"variable": "t"},
            "vertical": {"level": 500},
            "time": {"base_datetime": "2024-06-03T00:00:00", "step": 0},
            **proto,
        },
        {
            "parameter": {"variable": "t"},
            "vertical": {"level": 500},
            "time": {"base_datetime": "2024-06-03T00:00:00", "step": 6},
            **proto,
        },
        {
            "parameter": {"variable": "u"},
            "vertical": {"level": 500},
            "time": {"base_datetime": "2024-06-03T00:00:00", "step": 0},
            **proto,
        },
        {
            "parameter": {"variable": "u"},
            "vertical": {"level": 500},
            "time": {"base_datetime": "2024-06-03T00:00:00", "step": 6},
            **proto,
        },
    ]
    return from_source("list-of-dicts", d).to_fieldlist()


@pytest.mark.parametrize("lazy_load", [True, False])
def test_extra_dims_date_ignored_when_using_valid_time(collision_fl, lazy_load):
    """extra_dims='time.base_date' should be blocked when time_dims=["valid_time"].

    'time.base_date' is an alias of the date dim role NOT in time_dims, so it ends up
    ignored and must not appear as a dimension.
    """
    ds = collision_fl.to_xarray(
        profile="earthkit",
        time_dims=["valid_time"],
        extra_dims=["time.base_date"],
        lazy_load=lazy_load,
        squeeze=False,
    )

    assert "valid_time" in ds.dims
    # 'time.base_date' collides with an ignored predefined dim → should NOT appear
    assert "date" not in ds.dims
    assert "time.base_date" not in ds.dims


@pytest.mark.parametrize("lazy_load", [True, False])
def test_extra_dims_step_ignored_when_using_valid_time(collision_fl, lazy_load):
    """extra_dims='time.step' should be blocked when time_dims=["valid_time"].

    'time.step' is an alias of the step dim role NOT in time_dims, so it lands in ignored.
    """
    ds = collision_fl.to_xarray(
        profile="earthkit",
        time_dims=["valid_time"],
        extra_dims=["time.step"],
        lazy_load=lazy_load,
        squeeze=False,
    )

    assert "valid_time" in ds.dims
    assert "step" not in ds.dims
    assert "time.step" not in ds.dims


@pytest.mark.parametrize("lazy_load", [True, False])
def test_extra_dims_valid_time_ignored_when_using_forecast(collision_fl, lazy_load):
    """extra_dims='time.valid_datetime' should be blocked when time_dims=["date","time","step"].

    'time.valid_datetime' is an alias of the valid_time dim role NOT in time_dims → ignored.
    """
    ds = collision_fl.to_xarray(
        profile="earthkit",
        time_dims=["date", "time", "step"],
        extra_dims=["time.valid_datetime"],
        lazy_load=lazy_load,
        squeeze=False,
    )

    assert "date" in ds.dims
    assert "time" in ds.dims
    assert "step" in ds.dims
    assert "valid_time" not in ds.dims
    assert "time.valid_datetime" not in ds.dims


@pytest.mark.parametrize("lazy_load", [True, False])
def test_extra_dims_forecast_ref_time_ignored_when_using_valid_time(collision_fl, lazy_load):
    """extra_dims='time.forecast_reference_time' should be blocked when time_dims=["valid_time"].

    'time.forecast_reference_time' is an alias of the forecast_reference_time dim role NOT in time_dims → ignored.
    """
    ds = collision_fl.to_xarray(
        profile="earthkit",
        time_dims=["valid_time"],
        extra_dims=["time.forecast_reference_time"],
        lazy_load=lazy_load,
        squeeze=False,
    )

    assert "valid_time" in ds.dims
    assert "forecast_reference_time" not in ds.dims
    assert "time.forecast_reference_time" not in ds.dims
