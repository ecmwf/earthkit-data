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
from earthkit.data.testing import earthkit_remote_test_data_file


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "file,variables,sel_dicts,shapes",
    [
        (
            "regular_ll.grib2",
            ["t", "r"],
            [
                {"step": slice("1h", "5h")},
                {"step": "0h", "latitude": slice(31, 39)},
                {"step": "0h", "latitude": [30, 40], "longitude": slice(11, 19)},
                {"step": "0h", "latitude": 30, "longitude": 20},
                {"step": slice("1h", "5h"), "latitude": 30, "longitude": 20},
                {"step": slice("1h", "5h"), "latitude": 30, "longitude": slice(11, 19)},
                {"step": slice("1h", "5h"), "latitude": [30], "longitude": slice(11, 19)},
                {"step": slice("1h", "5h"), "latitude": slice(30, 20), "longitude": [0, 10, 20]},
                {"step": slice("1h", "5h"), "latitude": slice(30, 20), "longitude": slice(11, 19)},
                {"step": slice("1h", "5h"), "latitude": slice(29, 21), "longitude": slice(11, 19)},
            ],
            [(0, 19, 36), (0, 36), (2, 0), (), (0,), (0, 0), (0, 1, 0), (0, 2, 3), (0, 2, 0), (0, 0, 0)],
        ),
        (
            "reduced_gg_O32.grib2",
            ["t", "q"],
            [
                {"step": "0h"},
                {"step": slice("1h", "5h")},
                {"step": slice("1h", "5h"), "values": slice(1000)},
                {"step": slice("1h", "5h"), "values": slice(0)},
                {"values": slice(0)},
                {"step": "0h", "values": slice(0)},
                {"step": ["0h"], "values": slice(0)},
            ],
            [(5248,), (0, 5248), (0, 1000), (0, 0), (2, 0), (0,), (1, 0)],
        ),
        (
            "reduced_rotated_gg_subarea_O32.grib1",
            ["t", "r"],
            [
                {"step": ["0h"]},
                {"step": "0h", "values": 224},
                {"step": slice("1h", "5h"), "values": 224},
                {"step": slice("1h", "5h")},
                {"step": ["0h"], "values": slice(0)},
                {"values": slice(0)},
            ],
            [(1, 225), (), (0,), (0, 225), (1, 0), (2, 0)],
        ),
        (
            "healpix_H8_nested.grib2",
            ["t", "r"],
            [
                {"step": "0h"},
                {"step": slice("1h", "5h")},
                {"step": ["0h"], "values": slice(500, 400, -2)},
                {"step": slice("1h", "5h"), "values": slice(500, 400, -2)},
            ],
            [(768,), (0, 768), (1, 50), (0, 50)],
        ),
        (
            "sh_t32.grib1",
            ["t", "r"],
            [
                {"step": ["0h"]},
                {"step": ["0h"], "values": slice(0)},
                {"step": "0h", "values": slice(0)},
                {"step": slice("1h", "5h"), "values": slice(0)},
                {"step": "0h", "values": [1, 2, 10]},
                {"step": slice("1h", "5h"), "values": [1, 2, 10]},
            ],
            [(1, 1122), (1, 0), (0,), (0, 0), (3,), (0, 3)],
        ),
    ],
)
def test_xr_empty_slices(allow_holes, lazy_load, file, variables, sel_dicts, shapes):
    kwargs = dict(squeeze=False, allow_holes=allow_holes, lazy_load=lazy_load)

    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine", "grid", file))

    ds = ds_ek.to_xarray(**kwargs).squeeze()
    assert set(ds) == set(variables)

    for sel_dict, shape in zip(sel_dicts, shapes):
        _ds = ds.sel(**sel_dict)
        for v in _ds:
            assert _ds[v].shape == shape
        _ds.load()
