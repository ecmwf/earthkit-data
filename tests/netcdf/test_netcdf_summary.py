#!/usr/bin/env python3

# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import pytest

from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import load_nc_or_xr_source


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_ls(mode):
    f = load_nc_or_xr_source(earthkit_examples_file("tuv_pl.nc"), mode)

    # default keys
    f1 = f[:4]
    df = f1.ls()

    ref = {
        "variable": {0: "t", 1: "t", 2: "t", 3: "t"},
        "level": {0: 1000, 1: 850, 2: 700, 3: 500},
        "valid_datetime": {
            0: "2018-08-01T12:00:00",
            1: "2018-08-01T12:00:00",
            2: "2018-08-01T12:00:00",
            3: "2018-08-01T12:00:00",
        },
        "units": {0: "K", 1: "K", 2: "K", 3: "K"},
    }

    assert ref == df.to_dict()

    # extra keys
    f1 = f[:2]
    df = f1.ls(extra_keys=["long_name"])

    ref = {
        "variable": {0: "t", 1: "t"},
        "level": {0: 1000, 1: 850},
        "valid_datetime": {
            0: "2018-08-01T12:00:00",
            1: "2018-08-01T12:00:00",
        },
        "units": {0: "K", 1: "K"},
        "long_name": {0: "Temperature", 1: "Temperature"},
    }
    assert ref == df.to_dict()


if __name__ == "__main__":
    from earthkit.data.testing import main

    # test_datetime()
    main(__file__)
