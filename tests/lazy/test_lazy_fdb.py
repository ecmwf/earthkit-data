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

        assert ds[0].metadata("step_timedelta") == datetime.timedelta(hours=0)
        assert ds[4].metadata("step_timedelta") == datetime.timedelta(hours=6)

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


@pytest.mark.skipif(NO_FDB, reason="No access to FDB")
@pytest.mark.cache
def test_lazy_fdb_group_1():
    with temp_directory() as tmpdir:
        ds, config = make_fdb(os.path.join(tmpdir, "_fdb"))

        ds_ref = from_source("fdb", TEST_GRIB_REQUEST, config=config, stream=True, read_all=True)

        ds = from_source(
            "fdb", TEST_GRIB_REQUEST, config=config, stream=False, lazy=True, lazy_request_grouping=True
        )
        assert ds._group_cache is None
        assert len(ds) == 32
        assert ds[0].shape == (19, 36)
        assert ds[1].shape == (19, 36)
        assert ds._group_cache is None

        v = ds.to_numpy(context=ds)
        assert v.shape == (32, 19, 36)
        assert np.allclose(v, ds_ref.to_numpy())
        assert len(ds._group_cache.fields) == 32
        assert list(ds._group_cache.fields.keys()) == list(range(32))


@pytest.mark.skipif(NO_FDB, reason="No access to FDB")
@pytest.mark.cache
def test_lazy_fdb_group_2():
    with temp_directory() as tmpdir:
        ds, config = make_fdb(os.path.join(tmpdir, "_fdb"))

        ds_ref = from_source("fdb", TEST_GRIB_REQUEST, config=config, stream=True, read_all=True).sel(
            param="t"
        )

        ds = from_source(
            "fdb", TEST_GRIB_REQUEST, config=config, stream=False, lazy=True, lazy_request_grouping=True
        )
        assert ds._group_cache is None
        assert len(ds) == 32
        assert ds[0].shape == (19, 36)
        assert ds[1].shape == (19, 36)
        assert ds._group_cache is None

        # case 1
        ds1 = ds.sel(param="t")
        assert len(ds1) == 16
        assert ds1[0].shape == (19, 36)
        assert ds1[1].shape == (19, 36)
        assert ds._group_cache is None

        v = ds1.to_numpy(context=ds1)
        assert v.shape == (16, 19, 36)
        assert np.allclose(v, ds_ref.to_numpy())
        assert np.allclose(v, ds.to_numpy()[np.array([i for i in range(0, 32, 2)])])
        assert len(ds._group_cache.fields) == 16
        assert list(ds._group_cache.fields.keys()) == [i for i in range(0, 32, 2)]

        # case 2
        ds2 = ds[0:4]
        assert len(ds2) == 4
        assert ds2[0].shape == (19, 36)
        assert ds2[1].shape == (19, 36)
        assert ds._group_cache is not None

        v = ds2.to_numpy(context=ds2)
        assert v.shape == (4, 19, 36)
        assert np.allclose(v, ds.to_numpy()[np.array([0, 1, 2, 3])])
        assert len(ds._group_cache.fields) == 4
        assert list(ds._group_cache.fields.keys()) == [0, 1, 2, 3]

        # case 3 - still using the same group as case 2
        ds3 = ds[0:2]
        assert len(ds3) == 2
        assert ds3[0].shape == (19, 36)
        assert ds3[1].shape == (19, 36)
        assert ds._group_cache is not None

        v = ds3.to_numpy(context=ds3)
        assert v.shape == (2, 19, 36)
        assert np.allclose(v, ds.to_numpy()[np.array([0, 1])])
        assert len(ds._group_cache.fields) == 4
        assert list(ds._group_cache.fields.keys()) == [0, 1, 2, 3]
