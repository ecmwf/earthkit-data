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
from forcings_fixtures import load_forcings_fs  # noqa: E402


@pytest.mark.parametrize("input_data", ["grib", "latlon"])
@pytest.mark.parametrize(
    "params,expected_meta",
    [
        (
            dict(param="sin_longitude", valid_datetime="2020-05-13T18:00:00"),
            [["sin_longitude", datetime.datetime.fromisoformat("2020-05-13T18:00:00")]],
        ),
        (
            dict(
                param=["sin_longitude", "local_time"],
                valid_datetime=[
                    datetime.datetime.fromisoformat("2020-05-14T06:00:00"),
                    datetime.datetime.fromisoformat("2020-05-13T18:00:00"),
                ],
            ),
            [
                ["sin_longitude", datetime.datetime.fromisoformat("2020-05-13T18:00:00")],
                ["local_time", datetime.datetime.fromisoformat("2020-05-13T18:00:00")],
                ["sin_longitude", datetime.datetime.fromisoformat("2020-05-14T06:00:00")],
                ["local_time", datetime.datetime.fromisoformat("2020-05-14T06:00:00")],
            ],
        ),
        (dict(param="invalidval"), []),
        (dict(INVALIDKEY="sin_logitude"), []),
    ],
)
def test_forcings_sel_single_file_1(input_data, params, expected_meta):
    ds, _ = load_forcings_fs(input_data=input_data)

    g = ds.sel(**params)
    assert len(g) == len(expected_meta)
    if len(expected_meta) > 0:
        keys = list(params.keys())
        assert g.get(keys) == expected_meta
    return


@pytest.mark.parametrize("input_data", ["grib", "latlon"])
def test_forcings_sel_single_file_as_dict(input_data):
    ds, _ = load_forcings_fs(input_data=input_data)

    g = ds.sel(
        {
            "param": "sin_longitude",
            "valid_datetime": ["2020-05-14T06:00:00", "2020-05-13T18:00:00"],
        }
    )

    assert len(g) == 2
    assert g.get(["param", "valid_datetime"]) == [
        ["sin_longitude", datetime.datetime.fromisoformat("2020-05-13T18:00:00")],
        ["sin_longitude", datetime.datetime.fromisoformat("2020-05-14T06:00:00")],
    ]


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
