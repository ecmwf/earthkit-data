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

from earthkit.data import from_source
from earthkit.data.testing import earthkit_test_data_file


def test_netcdf_concat():
    ds1 = from_source("file", earthkit_test_data_file("era5_2t_1.nc"))
    ds2 = from_source("file", earthkit_test_data_file("era5_2t_2.nc"))
    ds = ds1 + ds2

    assert len(ds) == 2
    md = ds1.metadata("variable") + ds2.metadata("variable")
    assert ds.metadata("variable") == md

    assert ds[0].datetime() == {
        "base_time": datetime.datetime(2021, 3, 1, 12, 0),
        "valid_time": datetime.datetime(2021, 3, 1, 12, 0),
    }
    assert ds[1].datetime() == {
        "base_time": datetime.datetime(2021, 3, 2, 12, 0),
        "valid_time": datetime.datetime(2021, 3, 2, 12, 0),
    }
    assert ds.datetime() == {
        "base_time": [
            datetime.datetime(2021, 3, 1, 12, 0),
            datetime.datetime(2021, 3, 2, 12, 0),
        ],
        "valid_time": [
            datetime.datetime(2021, 3, 1, 12, 0),
            datetime.datetime(2021, 3, 2, 12, 0),
        ],
    }


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
