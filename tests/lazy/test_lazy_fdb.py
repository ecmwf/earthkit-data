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

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_directory
from earthkit.data.testing import NO_FDB
from earthkit.data.testing import earthkit_test_data_file

TEST_GRIB_REQUEST = {
    "class": "od",
    "expver": "0001",
    "stream": "oper",
    "date": [20240603, 20240604],
    "time": [0, 1200],
    "domain": "g",
    "type": "fc",
    "levtype": "pl",
    "levelist": [500, 700],
    "step": [0, 6],
    "param": [130, 157],
}


def make_fdb_config(path):
    fdb_schema = earthkit_test_data_file("fdb_schema.txt")
    fdb_dir = path
    os.makedirs(fdb_dir, exist_ok=True)
    config = {
        "type": "local",
        "engine": "toc",
        "schema": fdb_schema,
        "spaces": [{"handler": "Default", "roots": [{"path": fdb_dir}]}],
    }
    return config


def make_fdb(path):
    ds = from_source("sample", "pl.grib")
    config = make_fdb_config(path)
    ds.to_target("fdb", config=config)
    return ds, config


def compare_coord(ds, coord_name, ref_values):
    assert coord_name in ds.coords
    for v, v_ref in zip(ds.coords[coord_name].values, ref_values):
        assert v == v_ref, f"Coordinate '{coord_name}' value {v} != {v_ref}"


@pytest.mark.skipif(NO_FDB, reason="No access to FDB")
@pytest.mark.cache
def test_lazy_fdb():
    with temp_directory() as tmpdir:
        ds_in, config = make_fdb(os.path.join(tmpdir, "_fdb"))

        ds = from_source("fdb", TEST_GRIB_REQUEST, config=config, stream=False, lazy=True)
        assert len(ds) == 32

        assert ds[0].shape == (19, 36)
        assert ds[1].shape == (19, 36)
        assert ds[0].metadata(["shortName", "param", "units", "cfName"]) == ["t", "t", "K", "air_temperature"]
        assert ds[1].metadata(["shortName", "param", "units", "cfName"]) == [
            "r",
            "r",
            "%",
            "relative_humidity",
        ]

        assert ds[0].metadata(["date", "time", "step", "levelist", "level"]) == [20240603, 0, 0, 500, 500]
        assert ds[1].metadata(["date", "time", "step", "levelist", "level"]) == [20240603, 0, 0, 500, 500]

        assert ds[0].metadata("step_timedelta") == datetime.timedelta(hours=0)
        assert ds[4].metadata("step_timedelta") == datetime.timedelta(hours=6)

        # compare all the fields
        ds_in_sorted = ds_in.order_by(["shortName", "date", "time", "step", "levelist"])
        ds_sorted = ds.order_by(["shortName", "date", "time", "step", "levelist"])
        t = ds_in_sorted.sel(shortName="t")
        r = ds_in_sorted.sel(shortName="r")
        t_fdb = ds_sorted.sel(shortName="t")
        r_fdb = ds_sorted.sel(shortName="r")

        assert len(t) == 16
        assert len(r) == 16
        assert len(t_fdb) == 16
        assert len(r_fdb) == 16

        assert t.metadata(["shortName", "date", "time", "step", "levelist"]) == t_fdb.metadata(
            ["shortName", "date", "time", "step", "levelist"]
        )
        assert r.metadata(["shortName", "date", "time", "step", "levelist"]) == r_fdb.metadata(
            ["shortName", "date", "time", "step", "levelist"]
        )

        assert np.allclose(t.to_numpy(), t_fdb.to_numpy().reshape(16, 19, 36))
        assert np.allclose(r.to_numpy(), r_fdb.to_numpy().reshape(16, 19, 36))

        assert not hasattr(ds, "path")
        assert not hasattr(ds[0], "path")

        # --------------------
        #  Xarray tests
        # --------------------

        a = ds.to_xarray(time_dim_mode="forecast")

        # TODO: use methods from xr_engine tests for comparison
        compare_coord(
            a,
            "forecast_reference_time",
            [
                np.datetime64("2024-06-03T00:00:00.000000000"),
                np.datetime64("2024-06-03T12:00:00.000000000"),
                np.datetime64("2024-06-04T00:00:00.000000000"),
                np.datetime64("2024-06-04T12:00:00.000000000"),
            ],
        )
        compare_coord(a, "step", [np.timedelta64(0, "h"), np.timedelta64(6, "h")])
        compare_coord(a, "level", [500, 700])

        assert a["t"].values.shape == (4, 2, 2, 19, 36)
        assert a["r"].values.shape == (4, 2, 2, 19, 36)

        # Compare a few fields manually
        ref = [
            {
                "xr": (
                    "r",
                    {
                        "xr_forecast_reference_time": 0,
                        "xr_step": 0,
                        "level": 0,
                    },
                    {
                        "forecast_reference_time": np.datetime64("2024-06-03T00:00:00.000000000"),
                        "step": np.timedelta64(0, "h"),
                        "level": 500,
                    },
                ),
                "grib": (3, {"date": 20240603, "time": 0, "step": 0, "level": 500, "shortName": "r"}),
            },
            {
                "xr": (
                    "r",
                    {
                        "xr_forecast_reference_time": 1,
                        "xr_step": 0,
                        "level": 1,
                    },
                    {
                        "forecast_reference_time": np.datetime64("2024-06-03T12:00:00.000000000"),
                        "step": np.timedelta64(0, "h"),
                        "level": 700,
                    },
                ),
                "grib": (9, {"date": 20240603, "time": 1200, "step": 0, "level": 700, "shortName": "r"}),
            },
        ]

        for r in ref:
            xr_var, xr_sel, xr_meta = r["xr"]
            grib_idx, grib_meta = r["grib"]

            f = a[xr_var].isel(
                forecast_reference_time=xr_sel["xr_forecast_reference_time"],
                step=xr_sel["xr_step"],
                level=xr_sel["level"],
            )
            for k, v in xr_meta.items():
                assert f[k].values == v, f"{k} {f[k].values} != {v}"

            g = ds_in[grib_idx]
            for k, v in grib_meta.items():
                assert g.metadata(k) == v, f"{k} {g.metadata(k)} != {v}"

            assert np.allclose(f.values, g.to_numpy())

        # compare all the field values
        ds_in_sorted = ds_in.order_by(["shortName", "date", "time", "step", "levelist"])
        t = ds_in_sorted.sel(shortName="t")
        r = ds_in_sorted.sel(shortName="r")

        assert len(t) == 16
        assert len(r) == 16

        assert np.allclose(t.to_numpy(), a["t"].values.reshape(16, 19, 36))
        assert np.allclose(r.to_numpy(), a["r"].values.reshape(16, 19, 36))

        # test aggregation
        m = a.mean("step").load()
        assert m["t"].values.shape == (4, 2, 19, 36)
        assert m["r"].values.shape == (4, 2, 19, 36)
        assert np.allclose(m["r"].values.flatten()[85:87], [47.66908598, 53.43959379])
        assert np.allclose(m["t"].values.flatten()[85:87], [253.22625732, 252.78778076])
