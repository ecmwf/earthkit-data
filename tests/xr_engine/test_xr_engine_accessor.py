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
import xarray as xr

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.utils.testing import IN_GITHUB, earthkit_remote_test_data_file, earthkit_test_data_file
from earthkit.data.xr_engine.accessor import decode_earthkit_attrs


@pytest.mark.skipif(IN_GITHUB, reason="Skipping test on GitHub CI")
@pytest.mark.cache
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_accessor_grib(lazy_load):
    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl.grib")).to_fieldlist()
    ds = ds_ek.to_xarray(lazy_load=lazy_load)
    da = ds["t"]

    ref_grid_spec_dict = {"grid": [10, 10]}
    ref_grid_spec_1_dict = {"grid": "O32"}

    # _earthkit is stored as a JSON string; decode it for inspection
    md = decode_earthkit_attrs(da.attrs["_earthkit"])
    assert "message" in md
    assert isinstance(md["message"], bytes)
    assert md["grid_spec"] == ref_grid_spec_dict
    assert da.earthkit.grid_spec == ref_grid_spec_dict

    field = da.earthkit.reference_field
    assert field is not None
    assert field._get_grib().message(deflate=True) == md["message"]
    assert field.geography.grid_spec() == ref_grid_spec_dict

    # modify via set() (updates reference field)
    da_1 = da.earthkit.set({"geography.grid_spec": {"grid": "O32"}})

    md_1 = decode_earthkit_attrs(da_1.attrs["_earthkit"])
    assert "message" in md_1
    assert isinstance(md_1["message"], bytes)
    assert md_1["grid_spec"] == ref_grid_spec_1_dict
    assert da_1.earthkit.grid_spec == ref_grid_spec_1_dict

    field_1 = da_1.earthkit.reference_field
    assert field_1 is not None
    assert field_1.geography.grid_spec() == ref_grid_spec_1_dict

    with temp_file() as path:
        da.to_netcdf(path)
        _da = xr.open_dataset(path)["t"]
        assert _da.earthkit.grid_spec == ref_grid_spec_dict
        assert _da.earthkit.reference_field.geography.grid_spec() == ref_grid_spec_dict
        assert _da.earthkit.reference_field.get("parameter.variable") == "t"

    with temp_file() as path:
        ds.to_netcdf(path)
        _ds = xr.open_dataset(path)
        assert _ds.earthkit.grid_spec == ref_grid_spec_dict
        for v in _ds.data_vars:
            _da = _ds[v]
            assert _da.earthkit.reference_field.geography.grid_spec() == ref_grid_spec_dict
            assert _da.earthkit.reference_field.get("parameter.variable") == v


def test_xr_engine_accessor_netcdf():
    ds_ek = from_source("file", earthkit_test_data_file("test4.nc"))
    ds = ds_ek.to_xarray()
    da = ds["t"]

    ref_grid_spec_1_dict = {"grid": "O32"}

    assert da.earthkit.grid_spec is None

    # modify via set() (special-case: geography.grid_spec without reference field)
    da_1 = da.earthkit.set({"geography.grid_spec": {"grid": "O32"}})
    assert da_1.earthkit.grid_spec == ref_grid_spec_1_dict
