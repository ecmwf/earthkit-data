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

from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_test_data_file
from earthkit.data.testing import load_nc_or_xr_source


@pytest.mark.parametrize("mode", ["nc", "xr"])
@pytest.mark.parametrize("key", ["parameter.variable"])
def test_netcdf_sel_single_message(mode, key):
    ds = load_nc_or_xr_source(earthkit_test_data_file("test_single.nc"), mode)

    r = ds.sel(**{key: "t2m"})
    assert len(r) == 1
    assert r[0].get(key) == "t2m"


@pytest.mark.parametrize("mode", ["nc", "xr"])
@pytest.mark.parametrize(
    "params,expected_meta,metadata_keys",
    [
        ({"parameter.variable": "u", "vertical.level": 700}, [["u", 700]], []),
        (
            {"parameter.variable": ["t", "u"], "vertical.level": [700, 500]},
            [
                ["t", 700],
                ["t", 500],
                ["u", 700],
                ["u", 500],
            ],
            ["parameter.variable", "vertical.level"],
        ),
        ({"parameter.variable": "w"}, [], []),
        ({"INVALIDKEY": "w"}, [], []),
        (
            {
                "parameter.variable": ["t"],
                "vertical.level": [500, 700],
                "time.valid_datetime": datetime.datetime.fromisoformat("2018-08-01T12:00:00"),
            },
            [
                ["t", 700, datetime.datetime.fromisoformat("2018-08-01T12:00:00")],
                ["t", 500, datetime.datetime.fromisoformat("2018-08-01T12:00:00")],
            ],
            ["parameter.variable", "vertical.level", "time.valid_datetime"],
        ),
        (
            {
                "parameter.variable": ["t"],
                "vertical.level": [500, 700],
                "time.valid_datetime": "2018-08-01T12:00:00",
            },
            [
                ["t", 700, datetime.datetime(2018, 8, 1, 12, 0)],
                ["t", 500, datetime.datetime(2018, 8, 1, 12, 0)],
            ],
            ["parameter.variable", "vertical.level", "time.valid_datetime"],
        ),
    ],
)
def test_netcdf_sel_single_file_1(mode, params, expected_meta, metadata_keys):
    ds = load_nc_or_xr_source(earthkit_examples_file("tuv_pl.nc"), mode)

    g = ds.sel(**params)
    assert len(g) == len(expected_meta)
    if len(expected_meta) > 0:
        keys = list(params.keys())
        if metadata_keys:
            keys = metadata_keys

        assert g.get(keys) == expected_meta
    return


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_sel_single_file_as_dict(mode):
    ds = load_nc_or_xr_source(earthkit_examples_file("tuv_pl.nc"), mode)

    g = ds.sel({"parameter.variable": "t", "vertical.level": [500, 700]})
    assert len(g) == 2
    assert g.get(["parameter.variable", "vertical.level"]) == [
        ["t", 700],
        ["t", 500],
    ]


# TODO: allow using slice in sel for netcdf/xarray
@pytest.mark.migrate
@pytest.mark.parametrize("mode", ["nc", "xr"])
@pytest.mark.parametrize(
    "variable,level,expected_meta",
    [
        ("t", (slice(600, 700)), [["t", 700]]),
        ("t", (slice(650, 750)), [["t", 700]]),
        ("t", (slice(1000, None)), [["t", 1000]]),
        ("t", (slice(None, 300)), [["t", 300]]),
        ("t", (slice(500, 700)), [["t", 700], ["t", 500]]),
        ("t", (slice(510, 520)), []),
    ],
)
def test_netcdf_sel_slice_single_file(mode, variable, level, expected_meta):
    ds = load_nc_or_xr_source(earthkit_examples_file("tuv_pl.nc"), mode)

    g = ds.sel({"paremeter.variable": variable, "vertical.level": level})
    assert len(g) == len(expected_meta)
    if expected_meta:
        assert g.get(["parameter.variable", "vertical.level"]) == expected_meta


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
