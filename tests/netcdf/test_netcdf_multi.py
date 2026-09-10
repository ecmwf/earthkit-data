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

from earthkit.data import create_fieldlist, from_source
from earthkit.data.core.fieldlist import FieldList
from earthkit.data.utils.testing import earthkit_test_data_file

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


def _make_netcdf_data():
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

    return d1, d2


def merger_func(paths_or_sources):
    return xr.open_mfdataset(paths_or_sources)


class Merger_obj:
    def __init__(self):
        self._called_to_xarray = False
        self._called_to_fieldlist = False

    def to_xarray(self, paths_or_sources, **kwargs):
        self._called_to_xarray = True
        print("to_xarray called with:", paths_or_sources)
        return xr.open_mfdataset(paths_or_sources)

    def to_fieldlist(self, paths_or_sources, **kwargs):
        self._called_to_fieldlist = True
        res_fl = []
        for s in paths_or_sources:
            if isinstance(s, FieldList):
                fl = s
            elif isinstance(s, str):
                fl = from_source("file", s).to_fieldlist(**kwargs)
            else:
                fl = s.to_fieldlist(**kwargs)

            if fl:
                res_fl.extend([f for f in fl])

        return create_fieldlist(res_fl)


def test_netcdf_multi_data():
    d = from_source(
        "file",
        [
            earthkit_test_data_file("era5_2t_1.nc"),
            earthkit_test_data_file("era5_2t_2.nc"),
        ],
    )
    fl = d.to_fieldlist()

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


def test_netcdf_multi_fieldlist_merge_object():
    d1, d2 = _make_netcdf_data()
    merger = Merger_obj()

    fl1 = d1.to_fieldlist()
    ds1 = d1.to_xarray()
    fl2 = d2.to_fieldlist()
    ds2 = d2.to_xarray()

    target = xr.merge([ds1, ds2])

    d_merged = from_source("multi", [fl1, fl2], merger=merger)

    assert merger._called_to_xarray is False
    assert merger._called_to_fieldlist is False

    fl_merged = d_merged.to_fieldlist()
    assert len(fl_merged) == len(fl1) + len(fl2)
    assert merger._called_to_fieldlist is True

    ds_merged = d_merged.to_xarray()
    assert merger._called_to_xarray is True
    assert target.identical(ds_merged)

    target2 = xr.open_mfdataset([d1.path, d2.path])
    assert target2.identical(ds_merged)


@pytest.mark.parametrize("_kwargs", [{}, {"merger": None}])
def test_netcdf_multi_fieldlist_merge_default(_kwargs):
    d1, d2 = _make_netcdf_data()

    fl1 = d1.to_fieldlist()
    ds1 = d1.to_xarray()
    fl2 = d2.to_fieldlist()
    ds2 = d2.to_xarray()

    target = xr.merge([ds1, ds2])

    d_merged = from_source("multi", [fl1, fl2], **_kwargs)

    fl_merged = d_merged.to_fieldlist()
    assert len(fl_merged) == len(fl1) + len(fl2)

    ds_merged = d_merged.to_xarray()
    # ds.graph()
    # merged = ds.to_xarray()

    assert target.identical(ds_merged)

    target2 = xr.open_mfdataset([d1.path, d2.path])
    assert target2.identical(ds_merged)


def test_netcdf_multi_data_merge_object():
    d1, d2 = _make_netcdf_data()
    merger = Merger_obj()

    fl1 = d1.to_fieldlist()
    ds1 = d1.to_xarray()
    fl2 = d2.to_fieldlist()
    ds2 = d2.to_xarray()

    target = xr.merge([ds1, ds2])

    d_merged = from_source("multi", [d1, d2], merger=merger)

    assert merger._called_to_xarray is False
    assert merger._called_to_fieldlist is False

    fl_merged = d_merged.to_fieldlist()
    assert len(fl_merged) == len(fl1) + len(fl2)
    assert merger._called_to_fieldlist is True

    ds_merged = d_merged.to_xarray()
    assert merger._called_to_xarray is True
    assert target.identical(ds_merged)

    target2 = xr.open_mfdataset([d1.path, d2.path])
    assert target2.identical(ds_merged)


@pytest.mark.parametrize("_kwargs", [{}, {"merger": None}])
def test_netcdf_multi_data_merge_default(_kwargs):
    d1, d2 = _make_netcdf_data()

    fl1 = d1.to_fieldlist()
    ds1 = d1.to_xarray()
    fl2 = d2.to_fieldlist()
    ds2 = d2.to_xarray()

    target = xr.merge([ds1, ds2])

    d_merged = from_source("multi", [d1, d2], **_kwargs)

    fl_merged = d_merged.to_fieldlist()
    assert len(fl_merged) == len(fl1) + len(fl2)

    ds_merged = d_merged.to_xarray()
    # ds.graph()
    # merged = ds.to_xarray()

    assert target.identical(ds_merged)

    target2 = xr.open_mfdataset([d1.path, d2.path])
    assert target2.identical(ds_merged)


def test_netcdf_multi_data_merge_callable():
    d1, d2 = _make_netcdf_data()
    merger = merger_func

    ds1 = d1.to_xarray()
    ds2 = d2.to_xarray()

    target = xr.merge([ds1, ds2])

    d_merged = from_source("multi", [d1, d2], merger=merger)

    ds_merged = d_merged.to_xarray()
    assert target.identical(ds_merged)

    target2 = xr.open_mfdataset([d1.path, d2.path])
    assert target2.identical(ds_merged)


def _multi_fieldlist_merge_var_different_coords(kind1, kind2):
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
def test_netcdf_multi_fieldlist_merge_var_different_coords():
    _multi_fieldlist_merge_var_different_coords("netcdf", "netcdf")


@pytest.mark.skipif(True, reason="Test not yet implemented")
def test_grib_multi_fieldlist_merge_var_different_coords():
    _multi_fieldlist_merge_var_different_coords("grib", "grib")


@pytest.mark.skipif(True, reason="Test not yet implemented")
def test_grib_nc_multi_fieldlist_merge_var_different_coords():
    _multi_fieldlist_merge_var_different_coords("netcdf", "grib")


# def _multi_data_merge_var_different_coords_1(kind1, kind2):
#     d1 = from_source(
#         "dummy-source",
#         kind=kind1,
#         variables=["a"],
#         dims=["lat", "lon", "time"],
#         coord_values=dict(time=[1, 3]),
#     )
#     ds1 = d1.to_xarray()

#     d2 = from_source(
#         "dummy-source",
#         kind=kind2,
#         variables=["a"],
#         dims=["lat", "lon", "time"],
#         coord_values=dict(time=[2, 4]),
#     )
#     ds2 = d2.to_xarray()

#     target = xr.concat([ds1, ds2], dim="time")

#     ds = from_source("multi", [d1, d2], merger="concat(concat_dim=time)")
#     merged = ds.to_xarray()

#     assert target.identical(merged), f"Concat failed for {kind1}, {kind2}"


@pytest.mark.parametrize("time", [[[1, 3], [2, 4]], [[2, 1], [3, 4]]])
def test_netcdf_multi_data_merge_time_dim(time):
    d1 = from_source(
        "dummy-source",
        kind="netcdf",
        variables=["a"],
        dims=["lat", "lon", "time"],
        coord_values=dict(time=time[0]),
    )
    ds1 = d1.to_xarray()

    d2 = from_source(
        "dummy-source",
        kind="netcdf",
        variables=["a"],
        dims=["lat", "lon", "time"],
        coord_values=dict(time=time[1]),
    )
    ds2 = d2.to_xarray()

    target = xr.concat([ds1, ds2], dim="time")

    ds = from_source("multi", [d1, d2], merger="concat(concat_dim=time)")
    merged = ds.to_xarray()

    assert target.identical(merged)


# def test_netcdf_multi_data_merge_var_different_coords_2():
#     d1 = from_source(
#         "dummy-source",
#         kind="netcdf",
#         variables=["a"],
#         dims=["lat", "lon", "time"],
#         coord_values=dict(time=[2, 1]),
#     )
#     ds1 = d1.to_xarray()

#     d2 = from_source(
#         "dummy-source",
#         kind="netcdf",
#         variables=["a"],
#         dims=["lat", "lon", "time"],
#         coord_values=dict(time=[3, 4]),
#     )
#     ds2 = d2.to_xarray()

#     target = xr.concat([ds1, ds2], dim="time")

#     ds = from_source("multi", [d1, d2], merger="concat(concat_dim=time)")

#     # ds.graph()
#     merged = ds.to_xarray()

#     assert target.identical(merged)


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


def test_netcdf_multi_merge_different_coords():
    d1 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "time"],
        variables=["a", "b"],
        coord_values=dict(time=[1, 2]),
    )
    ds1 = d1.to_xarray()

    d2 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "time"],
        variables=["a", "b"],
        coord_values=dict(time=[8, 9]),
    )
    ds2 = d2.to_xarray()

    # print(f"d1={d1}")
    # print(f"d2={d2}")
    target = xr.concat([ds1, ds2], dim="time")
    merged = from_source("multi", [d1, d2], merger="concat(concat_dim=time)").to_xarray()

    # ds.graph()
    # merged = ds.to_xarray()

    assert target.identical(merged)


def _get_hierarchy():
    d_a1 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "forecast_time"],
        variables=["a"],
        coord_values=dict(forecast_time=[1, 3]),
    )
    d_a2 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "forecast_time"],
        variables=["a"],
        coord_values=dict(forecast_time=[2, 4]),
    )
    d_b1 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "forecast_time"],
        variables=["b"],
        coord_values=dict(forecast_time=[1, 3]),
    )
    d_b2 = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "forecast_time"],
        variables=["b"],
        coord_values=dict(forecast_time=[2, 4]),
    )

    # target = xr.merge([
    #     xr.merge([a1.to_xarray(), a2.to_xarray()], join='outer', compat='no_conflicts', concat_dim='forecast_time'),
    #     xr.merge([b1.to_xarray(), b2.to_xarray()], join='outer', compat='no_conflicts', concat_dim='forecast_time'),
    # ])

    target = xr.merge([
        xr.concat([d_a1.to_xarray(), d_a2.to_xarray()], dim="forecast_time"),
        xr.concat([d_b1.to_xarray(), d_b2.to_xarray()], dim="forecast_time"),
    ])

    return target, d_a1, d_a2, d_b1, d_b2


# @pytest.mark.skipif(True, reason="Test not yet implemented")
def test_netcdf_multi_fieldlist_merge_complex_11():
    target, d_a1, d_a2, d_b1, d_b2 = _get_hierarchy()

    d = from_source(
        "multi",
        [
            from_source("multi", [d_a1, d_a2], merger="concat(dim=forecast_time)"),
            from_source("multi", [d_b1, d_b2], merger="concat(dim=forecast_time)"),
        ],
        merger="merge",
    )

    merged = d.to_xarray()
    assert target.identical(merged), merged


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
def test_netcdf_multi_fieldlist_merge_complex_1a():
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

    print(f"target={target}")
    print(f"merged={merged}")
    assert target.identical(merged), merged


@pytest.mark.skipif(True, reason="Test not yet implemented")
def test_netcdf_merge_concat_var_11():
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
