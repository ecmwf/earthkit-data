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
import tempfile

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.readers.netcdf import NetCDFField
from earthkit.data.testing import (
    earthkit_examples_file,
    earthkit_file,
    earthkit_remote_test_data_file,
    earthkit_test_data_file,
)
from earthkit.data.utils import projections


def check_array(v, shape=None, first=None, last=None, meanv=None, eps=1e-3):
    assert v.shape == shape
    assert np.isclose(v[0], first, eps)
    assert np.isclose(v[-1], last, eps)
    assert np.isclose(v.mean(), meanv, eps)


def test_netcdf():
    for s in from_source("file", earthkit_file("docs/examples/test.nc")):
        s is not None


def test_dummy_netcdf_reader_1():
    s = from_source("file", earthkit_file("docs/examples/test.nc"))
    r = s._reader
    assert str(r).startswith("NetCDFReader"), r
    assert len(r) == 2
    assert isinstance(r[1], NetCDFField), r


@pytest.mark.parametrize("attribute", ["coordinates", "bounds", "grid_mapping"])
def test_dummy_netcdf_reader_2(attribute):
    s = from_source(
        "dummy-source",
        kind="netcdf",
        attributes={"a": {attribute: f"{attribute}_of_a"}},
        variables=["a", f"{attribute}_of_a"],
    )
    ds = s.to_xarray()
    assert "lat" in ds.dims
    assert len(s) == 1
    # s.to_datetime_list()
    s.bounding_box()


def test_dummy_netcdf():
    s = from_source("dummy-source", kind="netcdf")
    ds = s.to_xarray()
    assert "lat" in ds.dims


def test_dummy_netcdf_2():
    s = from_source(
        "dummy-source", kind="netcdf", dims=["lat", "lon", "time"], variables=["a", "b"]
    )
    ds = s.to_xarray()
    assert "lat" in ds.dims


def test_dummy_netcdf_3():
    s = from_source(
        "dummy-source",
        kind="netcdf",
        dims={"lat": dict(size=3), "lon": dict(size=2), "time": dict(size=2)},
        variables=["a", "b"],
    )
    ds = s.to_xarray()
    assert "lat" in ds.dims


def test_dummy_netcdf_4():
    s = from_source(
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
    s1 = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        product_type="reanalysis",
        param="2t",
        date="2021-03-01",
        format="netcdf",
    )
    s1.to_xarray()
    s2 = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        product_type="reanalysis",
        param="2t",
        date="2021-03-02",
        format="netcdf",
    )
    s2.to_xarray()

    source = from_source("multi", s1, s2)
    for s in source:
        print(s)

    source.to_xarray()


def test_datetime():
    s = from_source("file", earthkit_file("docs/examples/test.nc"))

    ref = {
        "base_time": [datetime.datetime(2020, 5, 13, 12)],
        "valid_time": [datetime.datetime(2020, 5, 13, 12)],
    }
    assert s.datetime() == ref

    s = from_source(
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

    # print(s.to_xarray())
    # print(s.to_xarray().time)
    ref = {
        "base_time": [
            datetime.datetime(1990, 1, 1, 12, 0),
            datetime.datetime(1990, 1, 2, 12, 0),
        ],
        "valid_time": [
            datetime.datetime(1990, 1, 1, 12, 0),
            datetime.datetime(1990, 1, 2, 12, 0),
        ],
    }
    assert s.datetime() == ref


def test_netcdf_to_points_1():
    f = from_source("file", earthkit_test_data_file("test_single.nc"))

    eps = 1e-5
    v = f[0].to_points(flatten=True)
    assert isinstance(v, dict)
    assert isinstance(v["x"], np.ndarray)
    assert isinstance(v["y"], np.ndarray)
    check_array(
        v["x"],
        (84,),
        first=0.0,
        last=330.0,
        meanv=165.0,
        eps=eps,
    )
    check_array(
        v["y"],
        (84,),
        first=90,
        last=-90,
        meanv=0,
        eps=eps,
    )


def test_bbox():
    ds = from_source("file", earthkit_file("docs/examples/test.nc"))
    bb = ds.bounding_box()
    assert len(bb) == 2
    for b in bb:
        assert b.as_tuple() == (73, -27, 33, 45)


def test_netcdf_proj_string_non_cf():
    f = from_source("file", earthkit_examples_file("test.nc"))
    with pytest.raises(AttributeError):
        f[0].to_proj()


def test_netcdf_proj_string_laea():
    f = from_source("url", earthkit_remote_test_data_file("examples", "efas.nc"))
    r = f[0].to_proj()
    assert len(r) == 2
    assert (
        r[0]
        == "+proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +ellps=GRS80 +units=m +no_defs"
    )
    assert r[1] == "+proj=eqc +datum=WGS84 +units=m +no_defs"


def test_netcdf_projection_laea():
    f = from_source("url", earthkit_remote_test_data_file("examples", "efas.nc"))
    projection = f[0].projection()
    assert isinstance(projection, projections.LambertAzimuthalEqualArea)
    assert projection.parameters == {
        "central_latitude": 52.0,
        "central_longitude": 10.0,
        "false_northing": 3210000.0,
        "false_easting": 4321000.0,
    }
    assert projection.globe == {
        "ellipse": "GRS80",
    }


def test_get_fields_missing_standard_name_attr_in_coord_array():
    """test _get_fields() can handle a missing 'standard_name' attr in coordinate data arrays"""

    # example dataset
    fs = from_source("file", earthkit_examples_file("test.nc"))
    ds = fs.to_xarray()

    # delete 'standard_name' attribute (if exists) in any coordinate data arrays
    for coord_name in ds.coords:
        try:
            del ds.coords[coord_name].attrs["standard_name"]
        except Exception as e:
            print(e)

    # save updates to disk and try read that file source
    with tempfile.TemporaryDirectory() as tmp_dir:
        fpath = os.path.join(tmp_dir, "tmp.nc")
        ds.to_netcdf(fpath)
        fs = from_source("file", earthkit_test_data_file(fpath))
        assert len(fs) == 2


if __name__ == "__main__":
    from earthkit.data.testing import main

    # test_datetime()
    main(__file__)
