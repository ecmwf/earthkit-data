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

from emohawk import load_from
from emohawk.readers.netcdf import NetCDFField
from emohawk.testing import emohawk_examples_file, emohawk_file


def test_netcdf():
    for s in load_from("file", emohawk_file("docs/examples/test.nc")):
        s is not None


def test_dummy_netcdf_reader_1():
    s = load_from("file", emohawk_file("docs/examples/test.nc"))
    r = s._reader
    assert str(r).startswith("NetCDFReader"), r
    assert len(r) == 2
    assert isinstance(r[1], NetCDFField), r


@pytest.mark.parametrize("attribute", ["coordinates", "bounds", "grid_mapping"])
def test_dummy_netcdf_reader_2(attribute):
    s = load_from(
        "dummy-source",
        kind="netcdf",
        attributes={"a": {attribute: f"{attribute}_of_a"}},
        variables=["a", f"{attribute}_of_a"],
    )
    ds = s.to_xarray()
    assert "lat" in ds.dims
    assert len(s) == 1
    # s.to_datetime_list()
    s.to_bounding_box()


def test_dummy_netcdf():
    s = load_from("dummy-source", kind="netcdf")
    ds = s.to_xarray()
    assert "lat" in ds.dims


def test_dummy_netcdf_2():
    s = load_from(
        "dummy-source", kind="netcdf", dims=["lat", "lon", "time"], variables=["a", "b"]
    )
    ds = s.to_xarray()
    assert "lat" in ds.dims


def test_dummy_netcdf_3():
    s = load_from(
        "dummy-source",
        kind="netcdf",
        dims={"lat": dict(size=3), "lon": dict(size=2), "time": dict(size=2)},
        variables=["a", "b"],
    )
    ds = s.to_xarray()
    assert "lat" in ds.dims


def test_dummy_netcdf_4():
    s = load_from(
        "dummy-source",
        kind="netcdf",
        dims={"lat": dict(size=3), "lon": dict(size=2), "time": dict(size=2)},
        variables={
            "a": dict(dims=["lat", "lon"]),
            "b": dict(dims=["lat", "time"]),
        },
    )
    ds = s.to_xarray()
    assert "lat" in ds.dims


@pytest.mark.skip
@pytest.mark.long_test
def test_multi():
    if not os.path.exists(os.path.expanduser("~/.cdsapirc")):
        pytest.skip("No ~/.cdsapirc")
    s1 = load_from(
        "cds",
        "reanalysis-era5-single-levels",
        product_type="reanalysis",
        param="2t",
        date="2021-03-01",
        format="netcdf",
    )
    s1.to_xarray()
    s2 = load_from(
        "cds",
        "reanalysis-era5-single-levels",
        product_type="reanalysis",
        param="2t",
        date="2021-03-02",
        format="netcdf",
    )
    s2.to_xarray()

    source = load_from("multi", s1, s2)
    for s in source:
        print(s)

    source.to_xarray()


def test_datetime():

    s = load_from("file", emohawk_file("docs/examples/test.nc"))

    assert s.to_datetime() == datetime.datetime(2020, 5, 13, 12), s.to_datetime()

    assert s.to_datetime_list() == [
        datetime.datetime(2020, 5, 13, 12)
    ], s.to_datetime_list()

    s = load_from(
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

    print(s.to_xarray())
    print(s.to_xarray().time)
    assert s.to_datetime_list() == [
        datetime.datetime(1990, 1, 1, 12, 0),
        datetime.datetime(1990, 1, 2, 12, 0),
    ], s.to_datetime_list()


def test_bbox():
    s = load_from("file", emohawk_file("docs/examples/test.nc"))
    assert s.to_bounding_box().as_tuple() == (73, -27, 33, 45), s.to_bounding_box()


def test_netcdf_proj_string_non_cf():
    f = load_from("file", emohawk_examples_file("test.nc"))
    with pytest.raises(AttributeError):
        f[0].to_proj()


def test_netcdf_proj_string_laea():
    f = load_from("file", emohawk_examples_file("efas.nc"))
    r = f[0].to_proj()
    assert len(r) == 2
    assert (
        r[0]
        == "+proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +ellps=GRS80 +units=m +no_defs"
    )
    assert r[1] == "+proj=eqc +datum=WGS84 +units=m +no_defs"


if __name__ == "__main__":
    from emohawk.testing import main

    # test_datetime()
    main(__file__)
