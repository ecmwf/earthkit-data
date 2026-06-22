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
from earthkit.data.utils.testing import NO_FDB, earthkit_test_data_file

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
    ds = from_source("sample", "pl.grib").to_fieldlist()
    config = make_fdb_config(path)
    ds.to_target("fdb", config=config)
    return ds, config


def compare_coord(ds, coord_name, ref_values):
    assert coord_name in ds.coords
    for v, v_ref in zip(ds.coords[coord_name].values, ref_values):
        assert v == v_ref, f"Coordinate '{coord_name}' value {v} != {v_ref}"


def compare_fields(fl_in, fl, ds, ref):
    for r in ref:
        xr_var, xr_isel, xr_meta = r["xr"]
        grib_in_idx, grib_in_meta = r["grib_in"]
        grib_idx, grib_meta = r["grib"]

        xr_f = ds[xr_var].isel(
            forecast_reference_time=xr_isel["xr_forecast_reference_time"],
            step=xr_isel["xr_step"],
            level=xr_isel["level"],
        )
        for k, v in xr_meta.items():
            assert xr_f[k].values == v, f"{k} {xr_f[k].values} != {v}"

        g = fl_in[grib_in_idx]
        for k, v in grib_in_meta.items():
            assert g.get(k) == v, f"{k} {g.get(k)} != {v}"
        np.testing.assert_allclose(
            xr_f.values, g.to_numpy(), err_msg=f"Field values for {xr_var} do not match for grib_in index {grib_in_idx}"
        )

        g = fl[grib_idx]
        for k, v in grib_meta.items():
            assert g.get(k) == v, f"{k} {g.get(k)} != {v}"
        np.testing.assert_allclose(
            xr_f.values, g.to_numpy(), err_msg=f"Field values for {xr_var} do not match for grib index {grib_idx}"
        )


@pytest.mark.skipif(NO_FDB, reason="No access to FDB")
@pytest.mark.cache
def test_lazy_fdb():
    with temp_directory() as tmpdir:
        # fl_in is the original fieldlist from the sample grib file, fl is the fieldlist retrieved from FDB
        fl_in, config = make_fdb(os.path.join(tmpdir, "_fdb"))

        # import pyfdb
        # fdb = pyfdb.FDB(config=config)
        # stream = fdb.retrieve(TEST_GRIB_REQUEST)

        # from eccodes.highlevel.reader import codes_new_from_stream
        # h = codes_new_from_stream(stream)

        # print(h)
        # return

        # fl is the virtual fieldlist retrieved from FDB
        fl = from_source("fdb", TEST_GRIB_REQUEST, config=config, stream=False, lazy=True).to_fieldlist()
        assert len(fl) == 32

        # print(fl_in.ls())
        # print(fl.ls())

        assert fl[0].shape == (19, 36)
        assert fl[1].shape == (19, 36)
        assert fl[0].get(["parameter.variable", "metadata.param", "parameter.units", "metadata.cfName"]) == [
            "t",
            "t",
            "K",
            "air_temperature",
        ]
        assert fl[1].get(["parameter.variable", "metadata.param", "parameter.units", "metadata.cfName"]) == [
            "r",
            "r",
            "%",
            "relative_humidity",
        ]

        ref_keys = ["parameter.variable", "time.base_datetime", "time.step", "vertical.level", "ensemble.member"]
        ref_vals = {
            "parameter.variable": [
                "t",
                "r",
                "t",
                "r",
                "t",
                "r",
                "t",
                "r",
                "t",
                "r",
                "t",
                "r",
                "t",
                "r",
                "t",
                "r",
                "t",
                "r",
                "t",
                "r",
                "t",
                "r",
                "t",
                "r",
                "t",
                "r",
                "t",
                "r",
                "t",
                "r",
                "t",
                "r",
            ],
            "time.base_datetime": [
                datetime.datetime(2024, 6, 3, 0, 0),
                datetime.datetime(2024, 6, 3, 0, 0),
                datetime.datetime(2024, 6, 3, 0, 0),
                datetime.datetime(2024, 6, 3, 0, 0),
                datetime.datetime(2024, 6, 3, 0, 0),
                datetime.datetime(2024, 6, 3, 0, 0),
                datetime.datetime(2024, 6, 3, 0, 0),
                datetime.datetime(2024, 6, 3, 0, 0),
                datetime.datetime(2024, 6, 3, 12, 0),
                datetime.datetime(2024, 6, 3, 12, 0),
                datetime.datetime(2024, 6, 3, 12, 0),
                datetime.datetime(2024, 6, 3, 12, 0),
                datetime.datetime(2024, 6, 3, 12, 0),
                datetime.datetime(2024, 6, 3, 12, 0),
                datetime.datetime(2024, 6, 3, 12, 0),
                datetime.datetime(2024, 6, 3, 12, 0),
                datetime.datetime(2024, 6, 4, 0, 0),
                datetime.datetime(2024, 6, 4, 0, 0),
                datetime.datetime(2024, 6, 4, 0, 0),
                datetime.datetime(2024, 6, 4, 0, 0),
                datetime.datetime(2024, 6, 4, 0, 0),
                datetime.datetime(2024, 6, 4, 0, 0),
                datetime.datetime(2024, 6, 4, 0, 0),
                datetime.datetime(2024, 6, 4, 0, 0),
                datetime.datetime(2024, 6, 4, 12, 0),
                datetime.datetime(2024, 6, 4, 12, 0),
                datetime.datetime(2024, 6, 4, 12, 0),
                datetime.datetime(2024, 6, 4, 12, 0),
                datetime.datetime(2024, 6, 4, 12, 0),
                datetime.datetime(2024, 6, 4, 12, 0),
                datetime.datetime(2024, 6, 4, 12, 0),
                datetime.datetime(2024, 6, 4, 12, 0),
            ],
            "time.step": [
                datetime.timedelta(0),
                datetime.timedelta(0),
                datetime.timedelta(0),
                datetime.timedelta(0),
                datetime.timedelta(seconds=21600),
                datetime.timedelta(seconds=21600),
                datetime.timedelta(seconds=21600),
                datetime.timedelta(seconds=21600),
                datetime.timedelta(0),
                datetime.timedelta(0),
                datetime.timedelta(0),
                datetime.timedelta(0),
                datetime.timedelta(seconds=21600),
                datetime.timedelta(seconds=21600),
                datetime.timedelta(seconds=21600),
                datetime.timedelta(seconds=21600),
                datetime.timedelta(0),
                datetime.timedelta(0),
                datetime.timedelta(0),
                datetime.timedelta(0),
                datetime.timedelta(seconds=21600),
                datetime.timedelta(seconds=21600),
                datetime.timedelta(seconds=21600),
                datetime.timedelta(seconds=21600),
                datetime.timedelta(0),
                datetime.timedelta(0),
                datetime.timedelta(0),
                datetime.timedelta(0),
                datetime.timedelta(seconds=21600),
                datetime.timedelta(seconds=21600),
                datetime.timedelta(seconds=21600),
                datetime.timedelta(seconds=21600),
            ],
            "vertical.level": [
                500,
                500,
                700,
                700,
                500,
                500,
                700,
                700,
                500,
                500,
                700,
                700,
                500,
                500,
                700,
                700,
                500,
                500,
                700,
                700,
                500,
                500,
                700,
                700,
                500,
                500,
                700,
                700,
                500,
                500,
                700,
                700,
            ],
            "ensemble.member": [
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
            ],
        }

        assert fl.get(ref_keys, output=dict, group_by_key=True) == ref_vals

        # compare all the fields between fl_in and fl
        fl_in_sorted = fl_in.order_by(["parameter.variable", "time.base_datetime", "time.step", "vertical.level"])
        fl_sorted = fl.order_by(["parameter.variable", "time.base_datetime", "time.step", "vertical.level"])

        t = fl_in_sorted.sel({"parameter.variable": "t"})
        r = fl_in_sorted.sel({"parameter.variable": "r"})
        t_fdb = fl_sorted.sel({"parameter.variable": "t"})
        r_fdb = fl_sorted.sel({"parameter.variable": "r"})

        assert len(t) == 16
        assert len(r) == 16
        assert len(t_fdb) == 16
        assert len(r_fdb) == 16

        assert t.get(["parameter.variable", "time.base_datetime", "time.step", "vertical.level"]) == t_fdb.get([
            "parameter.variable",
            "time.base_datetime",
            "time.step",
            "vertical.level",
        ])
        assert r.get(["parameter.variable", "time.base_datetime", "time.step", "vertical.level"]) == r_fdb.get([
            "parameter.variable",
            "time.base_datetime",
            "time.step",
            "vertical.level",
        ])

        np.testing.assert_allclose(t.to_numpy(), t_fdb.to_numpy().reshape(16, 19, 36))
        np.testing.assert_allclose(r.to_numpy(), r_fdb.to_numpy().reshape(16, 19, 36))

        # the virtual fieldlist should not have a path attribute and the fields should not have a path attribute
        assert not hasattr(fl, "path")
        assert not hasattr(fl[0], "path")

        # --------------------
        #  Xarray tests
        # --------------------

        ds = fl.to_xarray(time_dims=["forecast_reference_time", "step"])

        # TODO: use methods from xr_engine tests for comparison
        compare_coord(
            ds,
            "forecast_reference_time",
            [
                np.datetime64("2024-06-03T00:00:00.000000000"),
                np.datetime64("2024-06-03T12:00:00.000000000"),
                np.datetime64("2024-06-04T00:00:00.000000000"),
                np.datetime64("2024-06-04T12:00:00.000000000"),
            ],
        )
        compare_coord(ds, "step", [np.timedelta64(0, "h"), np.timedelta64(6, "h")])
        compare_coord(ds, "level", [500, 700])

        # assert ds["t"].values.shape == (4, 2, 2, 19, 36)
        # assert ds["r"].values.shape == (4, 2, 2, 19, 36)

        # Compare a few fields manually
        ref = [
            {
                "xr": (
                    "t",
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
                "grib_in": (
                    2,
                    {
                        "time.base_datetime": datetime.datetime(2024, 6, 3, 0, 0),
                        "time.step": datetime.timedelta(0),
                        "vertical.level": 500,
                        "parameter.variable": "t",
                    },
                ),
                "grib": (
                    0,
                    {
                        "time.base_datetime": datetime.datetime(2024, 6, 3, 0, 0),
                        "time.step": datetime.timedelta(0),
                        "vertical.level": 500,
                        "parameter.variable": "t",
                    },
                ),
            },
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
                "grib_in": (
                    3,
                    {
                        "time.base_datetime": datetime.datetime(2024, 6, 3, 0, 0),
                        "time.step": datetime.timedelta(0),
                        "vertical.level": 500,
                        "parameter.variable": "r",
                    },
                ),
                "grib": (
                    1,
                    {
                        "time.base_datetime": datetime.datetime(2024, 6, 3, 0, 0),
                        "time.step": datetime.timedelta(0),
                        "vertical.level": 500,
                        "parameter.variable": "r",
                    },
                ),
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
                "grib_in": (
                    9,
                    {
                        "time.base_datetime": datetime.datetime(2024, 6, 3, 12, 0),
                        "time.step": datetime.timedelta(0),
                        "vertical.level": 700,
                        "parameter.variable": "r",
                    },
                ),
                "grib": (
                    11,
                    {
                        "time.base_datetime": datetime.datetime(2024, 6, 3, 12, 0),
                        "time.step": datetime.timedelta(0),
                        "vertical.level": 700,
                        "parameter.variable": "r",
                    },
                ),
            },
        ]

        compare_fields(fl_in, fl, ds, ref)

        # sort the input fieldlist according to the "fields" in the xarray dataset and compare the values
        fl_in_sorted = fl_in.order_by(["parameter.variable", "time.base_datetime", "time.step", "vertical.level"])
        t = fl_in_sorted.sel({"parameter.variable": "t"})
        r = fl_in_sorted.sel({"parameter.variable": "r"})

        assert len(t) == 16
        assert len(r) == 16

        np.testing.assert_allclose(t.to_numpy(), ds["t"].values.reshape(16, 19, 36))
        np.testing.assert_allclose(r.to_numpy(), ds["r"].values.reshape(16, 19, 36))

        # test aggregation
        m = ds.mean("step").load()
        assert m["t"].values.shape == (4, 2, 19, 36)
        assert m["r"].values.shape == (4, 2, 19, 36)
        assert np.allclose(m["r"].values.flatten()[85:87], [47.66908598, 53.43959379])
        assert np.allclose(m["t"].values.flatten()[85:87], [253.22625732, 252.78778076])
