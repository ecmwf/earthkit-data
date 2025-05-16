#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

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


@pytest.mark.skipif(NO_FDB, reason="No access to FDB")
@pytest.mark.cache
def test_lazy_fdb():
    with temp_directory() as tmpdir:
        ds, config = make_fdb(os.path.join(tmpdir, "_fdb"))

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

        assert not hasattr(ds, "path")
        assert not hasattr(ds[0], "path")

        a = ds.to_xarray(time_dim_mode="forecast")
        assert a["t"].values.shape == (4, 2, 2, 19, 36)
        assert a["r"].values.shape == (4, 2, 2, 19, 36)

        m = a.mean("step").load()
        assert m["t"].values.shape == (4, 2, 19, 36)
        assert m["r"].values.shape == (4, 2, 19, 36)
        assert np.allclose(m["r"].values.flatten()[85:87], [47.66908598, 53.43959379])
        assert np.allclose(m["t"].values.flatten()[85:87], [253.22625732, 252.78778076])
