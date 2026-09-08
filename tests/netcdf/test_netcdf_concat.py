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

from earthkit.data import concat, create_fieldlist, from_source
from earthkit.data.core.fieldlist import FieldList
from earthkit.data.utils.testing import earthkit_test_data_file, load_nc_or_xr_source

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

    def to_fieldlist(self, paths_or_sources, **kwargs):
        fl = []
        for s in paths_or_sources:
            if isinstance(s, FieldList):
                fl.extend(s)
            elif isinstance(s, str):
                fl.append(from_source("file", s).to_fieldlist(**kwargs))
            else:
                fl.append(s.to_fieldlist(**kwargs))

        return create_fieldlist(fl)


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_concat_core(mode):
    fl1 = load_nc_or_xr_source(earthkit_test_data_file("era5_2t_1.nc"), mode)
    fl2 = load_nc_or_xr_source(earthkit_test_data_file("era5_2t_2.nc"), mode)
    fl = concat(fl1, fl2)

    assert len(fl) == 2
    md = fl1.get("parameter.variable") + fl2.get("parameter.variable")
    assert fl.get("parameter.variable") == md

    assert fl[0].get("time.base_datetime") == datetime.datetime(2021, 3, 1, 12, 0)
    assert fl[0].get("time.valid_datetime") == datetime.datetime(2021, 3, 1, 12, 0)
    assert fl[0].get("time.step") == datetime.timedelta(0)
    assert fl[1].get("time.base_datetime") == datetime.datetime(2021, 3, 2, 12, 0)
    assert fl[1].get("time.valid_datetime") == datetime.datetime(2021, 3, 2, 12, 0)
    assert fl[1].get("time.step") == datetime.timedelta(0)


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_concat_to_xarray(mode):
    fl1 = load_nc_or_xr_source(earthkit_test_data_file("era5_2t_1.nc"), mode)
    fl2 = load_nc_or_xr_source(earthkit_test_data_file("era5_2t_2.nc"), mode)
    fl = concat(fl1, fl2)

    assert len(fl) == 2

    import xarray as xr

    target = xr.merge([fl1.to_xarray(), fl2.to_xarray()])
    merged = fl.to_xarray()
    assert target.identical(merged)


def test_netcdf_read_multiple_files():
    ds = from_source(
        "file",
        [
            earthkit_test_data_file("era5_2t_1.nc"),
            earthkit_test_data_file("era5_2t_2.nc"),
        ],
    )
    fl = ds.to_fieldlist()

    assert len(fl) == 2
    assert fl.get("parameter.variable") == ["t2m", "t2m"]

    assert fl[0].get("time.base_datetime") == datetime.datetime(2021, 3, 1, 12, 0)
    assert fl[0].get("time.valid_datetime") == datetime.datetime(2021, 3, 1, 12, 0)
    assert fl[0].get("time.step") == datetime.timedelta(0)

    assert fl[1].get("time.base_datetime") == datetime.datetime(2021, 3, 2, 12, 0)
    assert fl[1].get("time.valid_datetime") == datetime.datetime(2021, 3, 2, 12, 0)
    assert fl[1].get("time.step") == datetime.timedelta(0)

    import xarray as xr

    target = xr.merge([
        xr.open_dataset(earthkit_test_data_file("era5_2t_1.nc")),
        xr.open_dataset(earthkit_test_data_file("era5_2t_2.nc")),
    ])
    merged = fl.to_xarray()
    assert target.identical(merged)


# # @pytest.mark.parametrize("custom_merger", (merger_func, Merger_obj()))
# @pytest.mark.parametrize("custom_merger", [Merger_obj()])
# def test_netcdf_merge_custom_1(custom_merger):
#     s1 = from_source(
#         "dummy-source",
#         kind="netcdf",
#         dims=["lat", "lon", "time"],
#         variables=["a", "b"],
#     ).to_fieldlist()
#     ds1 = s1.to_xarray()

#     s2 = from_source(
#         "dummy-source",
#         kind="netcdf",
#         dims=["lat", "lon", "time"],
#         variables=["c", "d"],
#     ).to_fieldlist()
#     ds2 = s2.to_xarray()

#     target = xr.merge([ds1, ds2])

#     ds = from_source("multi", [s1, s2], merger=custom_merger).to_fieldlist()
#     # ds.graph()
#     merged = ds.to_xarray()

#     assert target.identical(merged)

#     target2 = xr.open_mfdataset([s1.path, s2.path])
#     assert target2.identical(merged)


def test_netcdf_fieldlist_merge_object():
    d1 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "time"],
        variables=["a", "b"],
        coord_values={
            "lat": [0, 1],
            "lon": [0, 1],
            "time": [datetime.datetime(2021, 3, 1, 12, 0), datetime.datetime(2021, 3, 2, 12, 0)],
        },
    )
    fl1 = d1.to_fieldlist()
    ds1 = d1.to_xarray()

    d2 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "time"],
        variables=["c", "d"],
        coord_values={
            "lat": [0, 1],
            "lon": [0, 1],
            "time": [datetime.datetime(2021, 3, 1, 12, 0), datetime.datetime(2021, 3, 2, 12, 0)],
        },
    )
    fl2 = d2.to_fieldlist()
    ds2 = d2.to_xarray()

    target = xr.merge([ds1, ds2])

    d_merged = from_source("multi", [fl1, fl2], merger=Merger_obj())

    fl_merged = d_merged.to_fieldlist()
    assert len(fl_merged) == len(fl1) + len(fl2)

    ds_merged = d_merged.to_xarray()
    # ds.graph()
    # merged = ds.to_xarray()

    assert target.identical(ds_merged)

    target2 = xr.open_mfdataset([d1.path, d2.path])
    assert target2.identical(ds_merged)


def test_netcdf_data_merge_object():
    d1 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "time"],
        variables=["a", "b"],
    )
    ds1 = d1.to_xarray()

    d2 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "time"],
        variables=["c", "d"],
    )
    ds2 = d2.to_xarray()

    target = xr.merge([ds1, ds2])

    merged = from_source("multi", [d1, d2], merger=Merger_obj()).to_xarray()
    # ds.graph()
    # merged = ds.to_xarray()

    assert target.identical(merged)

    target2 = xr.open_mfdataset([d1.path, d2.path])
    assert target2.identical(merged)


def test_netcdf_data_merge_callable():
    d1 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "time"],
        variables=["a", "b"],
    )
    ds1 = d1.to_xarray()

    d2 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "time"],
        variables=["c", "d"],
    )
    ds2 = d2.to_xarray()

    target = xr.merge([ds1, ds2])

    merged = from_source("multi", [d1, d2], merger=merger_func).to_xarray()

    assert target.identical(merged)

    target2 = xr.open_mfdataset([d1.path, d2.path])
    assert target2.identical(merged)


def test_netcdf_merge_var_1():
    s1 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "time"],
        variables=["a", "b"],
    ).to_fieldlist()
    ds1 = s1.to_xarray()

    s2 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "time"],
        variables=["c", "d"],
    ).to_fieldlist()
    ds2 = s2.to_xarray()

    target = xr.merge([ds1, ds2])
    ds = from_source("multi", [s1, s2]).to_fieldlist()

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
    ).to_fieldlist()
    ds1 = s1.to_xarray()

    s2 = from_source(
        "dummy-source",
        kind=kind2,
        dims=["lat", "time"],
        variables=["c", "d"],
    ).to_fieldlist()
    ds2 = s2.to_xarray()

    target = xr.merge([ds1, ds2])
    ds = from_source("multi", [s1, s2]).to_fieldlist()
    ds.graph()
    merged = ds.to_xarray()

    assert target.identical(merged)


@pytest.mark.migrate
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

    # ds.graph()
    merged = ds.to_xarray()

    assert target.identical(merged)


# def test_netcdf_wrong_concat_var_ori():
#     s1 = from_source(
#         "dummy-source",
#         kind="netcdf",
#         dims=["lat", "lon", "time"],
#         variables=["a", "b"],
#         coord_values=dict(time=[1, 2]),
#     ).to_fieldlist()
#     ds1 = s1.to_xarray()

#     s2 = from_source(
#         "dummy-source",
#         kind="netcdf",
#         dims=["lat", "time"],
#         variables=["a", "b"],
#         coord_values=dict(time=[8, 9]),
#     ).to_fieldlist()
#     ds2 = s2.to_xarray()

#     print(f"s1={s1}")
#     print(f"s2={s2}")
#     target = xr.concat([ds1, ds2], dim="time")
#     ds = from_source("multi", [s1, s2], merger="concat(concat_dim=time)").to_fieldlist()

#     ds.graph()
#     merged = ds.to_xarray()

#     assert target.identical(merged)


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

    # print(f"s1={s1}")
    # print(f"s2={s2}")
    target = xr.concat([ds1, ds2], dim="time")
    merged = from_source("multi", [s1, s2], merger="concat(concat_dim=time)").to_xarray()

    # ds.graph()
    # merged = ds.to_xarray()

    assert target.identical(merged)


def get_hierarchy():
    a1 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "forecast_time"],
        variables=["a"],
        coord_values=dict(forecast_time=[1, 3]),
    ).to_fieldlist()
    a2 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "forecast_time"],
        variables=["a"],
        coord_values=dict(forecast_time=[2, 4]),
    ).to_fieldlist()
    b1 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "forecast_time"],
        variables=["b"],
        coord_values=dict(forecast_time=[1, 3]),
    ).to_fieldlist()
    b2 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "forecast_time"],
        variables=["b"],
        coord_values=dict(forecast_time=[2, 4]),
    ).to_fieldlist()

    target = xr.merge([
        xr.merge([a1.to_xarray(), a2.to_xarray()]),
        xr.merge([b1.to_xarray(), b2.to_xarray()]),
    ])
    return target, a1, a2, b1, b2


@pytest.mark.skipif(True, reason="Test not yet implemented")
def test_nc_concat_merge_var():
    target, a1, a2, b1, b2 = get_hierarchy()

    s = from_source(
        "multi",
        [
            from_source("multi", [a1, a2], merger="concat(dim=forecast_time)").to_fieldlist(),
            from_source("multi", [b1, b2], merger="concat(dim=forecast_time)").to_fieldlist(),
        ],
        merger="merge",
    ).to_fieldlist()

    merged = s.to_xarray()
    assert target.identical(merged), merged


@pytest.mark.skipif(True, reason="Test not yet implemented")
def test_netcdf_merge_concat_var():
    target, a1, a2, b1, b2 = get_hierarchy()
    s = from_source(
        "multi",
        [
            from_source("multi", [a1, b1], merger="merge()").to_fieldlist(),
            from_source("multi", [a2, b2], merger="merge()").to_fieldlist(),
        ],
        merger="concat(dim=forecast_time)",
    ).to_fieldlist()
    merged = s.to_xarray()
    assert target.identical(merged)


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main()
