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
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import load_nc_or_xr_source


@pytest.mark.parametrize("mode", ["nc", "xr"])
@pytest.mark.parametrize(
    "key,expected_value",
    [
        ("variable", "t"),
        ("level", 1000),
        (["variable"], ["t"]),
        (["variable", "level"], ["t", 1000]),
        (("variable"), "t"),
        (("variable", "level"), ("t", 1000)),
        (("param", "levelist"), ("t", 1000)),
    ],
)
def test_netcdf_metadata_single_field(mode, key, expected_value):
    f = load_nc_or_xr_source(earthkit_examples_file("tuv_pl.nc"), mode)

    # sn = f.metadata(key)
    # assert sn == [expected_value]
    sn = f[0].metadata(key)
    assert sn == expected_value


def test_netcdf_datetime():
    ds = from_source("file", earthkit_examples_file("test.nc"))

    ref = {
        "base_time": [datetime.datetime(2020, 5, 13, 12)],
        "valid_time": [datetime.datetime(2020, 5, 13, 12)],
    }
    assert ds.datetime() == ref

    ds = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "time"],
        variables=["a", "b"],
        coord_values=dict(
            time=[
                datetime.datetime(1990, 1, 1, 12, 0),
                datetime.datetime(1990, 1, 2, 12, 0),
            ]
        ),
    )

    ref = {
        "base_time": [
            datetime.datetime(1990, 1, 1, 12, 0),
            datetime.datetime(1990, 1, 2, 12, 0),
        ],
        "valid_time": [
            datetime.datetime(1990, 1, 1, 12, 0),
            datetime.datetime(1990, 1, 2, 12, 0),
        ],
    }
    assert ds.datetime() == ref


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_valid_datetime(mode):
    ds = load_nc_or_xr_source(earthkit_examples_file("test.nc"), mode)
    assert ds[0].metadata("valid_datetime") == "2020-05-13T12:00:00"


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
