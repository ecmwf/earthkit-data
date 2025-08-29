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
from earthkit.data.testing import NO_COVJSONKIT
from earthkit.data.testing import earthkit_test_data_file


def test_covjson():
    ds = from_source("file", earthkit_test_data_file("time_series.covjson"))
    assert ds


@pytest.mark.skipif(NO_COVJSONKIT, reason="no covjsonkit available")
def test_covjson_to_xarray():
    ds = from_source("file", earthkit_test_data_file("time_series.covjson"))
    assert ds
    a = ds.to_xarray()
    assert len(a.data_vars) == 1

@pytest.mark.skipif(NO_COVJSONKIT, reason="no covjsonkit available")
def test_covjson_to_geojson():
    ds = from_source("file", earthkit_test_data_file("time_series.covjson"))
    assert ds
    a = ds.to_geojson()
    assert len(len(a['features'])) == 9


@pytest.mark.skipif(NO_COVJSONKIT, reason="no covjsonkit available")
def test_covjson_memory():
    with open(earthkit_test_data_file("time_series.covjson"), "r") as f:
        d = f.read().encode()

    ds = from_source("memory", d)
    assert ds
    a = ds.to_xarray()
    assert len(a.data_vars) == 1


@pytest.mark.skipif(NO_COVJSONKIT, reason="no covjsonkit available")
def test_covjson_stream():
    stream = open(earthkit_test_data_file("time_series.covjson"), "rb")

    ds = from_source("stream", stream)
    assert ds
    it = iter(ds)
    c = next(it)
    a = c.to_xarray()
    assert len(a.data_vars) == 1

    with pytest.raises(StopIteration):
        next(it)


@pytest.mark.skipif(NO_COVJSONKIT, reason="no covjsonkit available")
def test_covjson_stream_memory():
    stream = open(earthkit_test_data_file("time_series.covjson"), "rb")

    ds = from_source("stream", stream, read_all=True)
    assert ds
    a = ds.to_xarray()
    assert len(a.data_vars) == 1


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
