#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file


def test_lod_to_grib_1():
    data = np.random.random((181, 360))

    d = ({"param": "t", "levelist": 500, "date": 20010101, "time": 1200, "step": 6, "values": data},)
    ds = from_source("list-of-dicts", d)

    print(ds[0].shape)

    with temp_file() as path:
        ds.to_target("file", path, encoder="grib")

        from_source("file", path)


def test_lod_to_grib_2():
    data = np.random.random((181, 360))

    d = (
        {
            "param": "t",
            "levelist": 500,
            "date": 20010101,
            "time": 1200,
            "step": 6,
            "values": data,
            "veryBadKey": 1,
        },
    )
    ds = from_source("list-of-dicts", d)

    with temp_file() as path:
        # This should fail because of the veryBadKey
        with pytest.raises(Exception):
            ds.to_target("file", path, encoder="grib")

    with temp_file() as path:
        md = {"param": "t", "levelist": 500, "date": 20010101, "time": 1200, "step": 6}
        ds.to_target("file", path, encoder="grib", metadata=md, use_metadata_from_data=False)

        from_source("file", path)
