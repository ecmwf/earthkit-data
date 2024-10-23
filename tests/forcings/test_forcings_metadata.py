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
def test_forcings_datetime(input_data):
    ds, _ = load_forcings_fs(last_step=12, input_data=input_data)

    ref = {
        "base_time": [None],
        "valid_time": [
            datetime.datetime(2020, 5, 13, 18),
            datetime.datetime(2020, 5, 14, 0),
        ],
    }

    assert ds.datetime() == ref


@pytest.mark.parametrize("input_data", ["grib", "latlon"])
def test_forcings_valid_datetime(input_data):
    ds, _ = load_forcings_fs(last_step=12, input_data=input_data)
    f = ds[4]

    assert f.metadata("valid_datetime") == "2020-05-13T18:00:00"


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
