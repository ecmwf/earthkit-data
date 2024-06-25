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

import numpy as np
import pytest
import xarray as xr

from earthkit.data import from_source
from earthkit.data.testing import earthkit_test_data_file
from earthkit.data.testing import load_nc_or_xr_source

# These functionalities are variations around
# http://xarray.pydata.org/en/stable/user-guide/combining.html#combining-multi


def assert_same_xarray(x, y):
    assert x.broadcast_equals(y)
    assert x.equals(y)
    assert x.identical(y)
    assert len(x) == len(y)
    assert set(x.keys()) == set(y.keys())
    assert len(x.dims) == len(y.dims)
    assert len(x.coords) == len(y.coords)
    for k in x.keys():
        xda, yda = x[k], y[k]
        assert xda.values.shape == yda.values.shape
        assert np.all(xda.values == yda.values)


def merger_func(paths_or_sources):
    return xr.open_mfdataset(paths_or_sources)


class Merger_obj:
    def to_xarray(self, paths_or_sources, **kwargs):
        return xr.open_mfdataset(paths_or_sources)


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_concat(mode):
    ds1 = load_nc_or_xr_source(earthkit_test_data_file("era5_2t_1.nc"), mode)
    ds2 = load_nc_or_xr_source(earthkit_test_data_file("era5_2t_2.nc"), mode)
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

    import xarray as xr

    target = xr.merge([ds1.to_xarray(), ds2.to_xarray()])
    merged = ds.to_xarray()
    assert target.identical(merged)


def test_netcdf_read_multiple_files():
    ds = from_source(
        "file",
        [
            earthkit_test_data_file("era5_2t_1.nc"),
            earthkit_test_data_file("era5_2t_2.nc"),
        ],
    )

    assert len(ds) == 2
    assert ds.metadata("variable") == ["t2m", "t2m"]

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

    import xarray as xr

    target = xr.merge(
        [
            xr.open_dataset(earthkit_test_data_file("era5_2t_1.nc")),
            xr.open_dataset(earthkit_test_data_file("era5_2t_2.nc")),
        ]
    )
    merged = ds.to_xarray()
    assert target.identical(merged)


@pytest.mark.parametrize("custom_merger", (merger_func, Merger_obj()))
def test_netdcf_merge_custom(custom_merger):
    s1 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "time"],
        variables=["a", "b"],
    )
    ds1 = s1.to_xarray()

    s2 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "time"],
        variables=["c", "d"],
    )
    ds2 = s2.to_xarray()

    target = xr.merge([ds1, ds2])

    ds = from_source("multi", [s1, s2], merger=custom_merger)
    ds.graph()
    merged = ds.to_xarray()

    assert target.identical(merged)

    target2 = xr.open_mfdataset([s1.path, s2.path])
    assert target2.identical(merged)


def test_netcdf_merge_var():
    s1 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "time"],
        variables=["a", "b"],
    )
    ds1 = s1.to_xarray()

    s2 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "time"],
        variables=["c", "d"],
    )
    ds2 = s2.to_xarray()

    target = xr.merge([ds1, ds2])
    ds = from_source("multi", [s1, s2])
    ds.graph()
    merged = ds.to_xarray()

    assert target.identical(merged)

    target2 = xr.open_mfdataset([s1.path, s2.path])
    assert target2.identical(merged)


def _merge_var_different_coords(kind1, kind2):
    s1 = from_source(
        "dummy-source",
        kind=kind1,
        dims=["lat", "lon"],
        variables=["a", "b"],
    )
    ds1 = s1.to_xarray()

    s2 = from_source(
        "dummy-source",
        kind=kind2,
        dims=["lat", "time"],
        variables=["c", "d"],
    )
    ds2 = s2.to_xarray()

    target = xr.merge([ds1, ds2])
    ds = from_source("multi", [s1, s2])
    ds.graph()
    merged = ds.to_xarray()

    assert target.identical(merged)


def test_netcdf_merge_var_different_coords():
    _merge_var_different_coords("netcdf", "netcdf")


@pytest.mark.skipif(True, reason="Test not yet implemented")
def test_grib_merge_var_different_coords():
    _merge_var_different_coords("grib", "grib")


@pytest.mark.skipif(True, reason="Test not yet implemented")
def test_grib_nc_merge_var_different_coords():
    _merge_var_different_coords("netcdf", "grib")


def _concat_var_different_coords_1(kind1, kind2):
    s1 = from_source(
        "dummy-source",
        kind=kind1,
        variables=["a"],
        dims=["lat", "lon", "time"],
        coord_values=dict(time=[1, 3]),
    )
    ds1 = s1.to_xarray()

    s2 = from_source(
        "dummy-source",
        kind=kind2,
        variables=["a"],
        dims=["lat", "lon", "time"],
        coord_values=dict(time=[2, 4]),
    )
    ds2 = s2.to_xarray()

    target = xr.concat([ds1, ds2], dim="time")

    ds = from_source("multi", [s1, s2], merger="concat(concat_dim=time)")
    ds.graph()
    merged = ds.to_xarray()

    assert target.identical(merged), f"Concat failed for {kind1}, {kind2}"


def test_netcdf_concat_var_different_coords_1():
    for kind1 in ["netcdf"]:  # ["netcdf", "grib"]:
        for kind2 in ["netcdf"]:  # ["netcdf", "grib"]:
            _concat_var_different_coords_1(kind1, kind2)


def test_netcdf_concat_var_different_coords_2():
    s1 = from_source(
        "dummy-source",
        kind="netcdf",
        variables=["a"],
        dims=["lat", "lon", "time"],
        coord_values=dict(time=[2, 1]),
    )
    ds1 = s1.to_xarray()

    s2 = from_source(
        "dummy-source",
        kind="netcdf",
        variables=["a"],
        dims=["lat", "lon", "time"],
        coord_values=dict(time=[3, 4]),
    )
    ds2 = s2.to_xarray()

    target = xr.concat([ds1, ds2], dim="time")

    ds = from_source("multi", [s1, s2], merger="concat(concat_dim=time)")

    ds.graph()
    merged = ds.to_xarray()

    assert target.identical(merged)


def test_netcdf_wrong_concat_var():
    s1 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "time"],
        variables=["a", "b"],
        coord_values=dict(time=[1, 2]),
    )
    ds1 = s1.to_xarray()

    s2 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "time"],
        variables=["a", "b"],
        coord_values=dict(time=[8, 9]),
    )
    ds2 = s2.to_xarray()

    print(f"s1={s1}")
    print(f"s2={s2}")
    target = xr.concat([ds1, ds2], dim="time")
    ds = from_source("multi", [s1, s2], merger="concat(concat_dim=time)")

    ds.graph()
    merged = ds.to_xarray()

    assert target.identical(merged)


def get_hierarchy():
    a1 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "forecast_time"],
        variables=["a"],
        coord_values=dict(forecast_time=[1, 3]),
    )
    a2 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "forecast_time"],
        variables=["a"],
        coord_values=dict(forecast_time=[2, 4]),
    )
    b1 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "forecast_time"],
        variables=["b"],
        coord_values=dict(forecast_time=[1, 3]),
    )
    b2 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "forecast_time"],
        variables=["b"],
        coord_values=dict(forecast_time=[2, 4]),
    )

    target = xr.merge(
        [
            xr.merge([a1.to_xarray(), a2.to_xarray()]),
            xr.merge([b1.to_xarray(), b2.to_xarray()]),
        ]
    )
    return target, a1, a2, b1, b2


@pytest.mark.skipif(True, reason="Test not yet implemented")
def test_nc_concat_merge_var():
    target, a1, a2, b1, b2 = get_hierarchy()

    s = from_source(
        "multi",
        [
            from_source("multi", [a1, a2], merger="concat(dim=forecast_time)"),
            from_source("multi", [b1, b2], merger="concat(dim=forecast_time)"),
        ],
        merger="merge",
    )

    merged = s.to_xarray()
    assert target.identical(merged), merged


@pytest.mark.skipif(True, reason="Test not yet implemented")
def test_netcdf_merge_concat_var():
    target, a1, a2, b1, b2 = get_hierarchy()
    s = from_source(
        "multi",
        [
            from_source("multi", [a1, b1], merger="merge()"),
            from_source("multi", [a2, b2], merger="merge()"),
        ],
        merger="concat(dim=forecast_time)",
    )
    merged = s.to_xarray()
    assert target.identical(merged)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
