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

import pytest

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_directory
from earthkit.data.testing import NO_FDB
from earthkit.data.testing import NO_PROD_FDB
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_test_data_file


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_FDB, reason="No access to FDB")
@pytest.mark.skipif(NO_PROD_FDB, reason="No access to operational FDB")
def test_fdb_grib_stream():
    d = datetime.datetime.now() - datetime.timedelta(days=2)
    request = {
        "class": "od",
        "expver": "0001",
        "stream": "oper",
        "date": d.strftime("%Y%m%d"),
        "time": [0, 12],
        "domain": "g",
        "type": "an",
        "levtype": "sfc",
        "step": 0,
        "param": [151, 167],
    }

    ds = from_source("fdb", request)
    cnt = sum([1 for f in ds])
    assert cnt == 4


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_FDB, reason="No access to FDB")
@pytest.mark.skipif(NO_PROD_FDB, reason="No access to operational FDB")
def test_fdb_grib_file():
    d = datetime.datetime.now() - datetime.timedelta(days=2)
    request = {
        "class": "od",
        "expver": "0001",
        "stream": "oper",
        "date": d.strftime("%Y%m%d"),
        "time": [0, 12],
        "domain": "g",
        "type": "an",
        "levtype": "sfc",
        "step": 0,
        "param": [151, 167],
    }

    ds = from_source("fdb", request, stream=False)
    assert len(ds) == 4


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


@pytest.mark.skipif(NO_FDB, reason="No access to FDB")
@pytest.mark.parametrize("use_kwargs", [True, False])
def test_fdb_grib_write(monkeypatch, use_kwargs):
    with temp_directory() as tmpdir:
        config = make_fdb_config(os.path.join(tmpdir, "_fdb"))

        ds = from_source("file", earthkit_examples_file("test.grib"))

        import pyfdb

        fdb = pyfdb.FDB(config=config)
        for f in ds:
            fdb.archive(f.message())
        fdb.flush()

        request = {
            "class": "od",
            "expver": "0001",
            "stream": "oper",
            "date": "20200513",
            "time": 1200,
            "domain": "g",
            "type": "an",
            "levtype": "sfc",
            "step": 0,
            "param": [167, 151],
        }

        if use_kwargs:
            ds1 = from_source("fdb", request, config=config, stream=False)
        else:
            monkeypatch.setenv("FDB5_CONFIG", str(config))
            ds1 = from_source("fdb", request, stream=False)

        assert len(ds1) == 2
        assert ds1.metadata("param") == ["2t", "msl"]


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
