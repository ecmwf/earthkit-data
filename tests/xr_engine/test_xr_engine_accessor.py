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
from earthkit.utils.array import array_namespace as eku_array_namespace

from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_remote_test_data_file

_NUMPY = eku_array_namespace("numpy")


@pytest.mark.cache
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_accessor_1(lazy_load):
    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl.grib")).to_fieldlist()

    ds = ds_ek.to_xarray(lazy_load=lazy_load)

    print(ds)
    da = ds["t"]
    print(da)

    ref_grid_spec_dict = {"grid": [10, 10]}
    ref_grid_spec_str = '{"grid": [10, 10]}'
    ref_grid_spec_1_dict = {"grid": "O32"}
    ref_grid_spec_1_str = '{"grid": "O32"}'

    md = da.attrs["_earthkit"]
    assert "message" in md
    assert isinstance(md["message"], bytes)
    assert md["grid_spec"] == ref_grid_spec_str
    assert da.attrs["earthkit_grid_spec"] == ref_grid_spec_str
    assert da.earthkit.grid_spec == ref_grid_spec_dict

    field = da.earthkit._reference_field
    assert field is not None
    assert field._get_grib().message(deflate=True) == md["message"]
    assert field.geography.grid_spec() == ref_grid_spec_dict

    # modify
    da_1 = da.earthkit.set({"geography.grid_spec": {"grid": "O32"}})

    md_1 = da_1.attrs["_earthkit"]
    assert "message" in md_1
    assert isinstance(md_1["message"], bytes)
    assert md_1["grid_spec"] == ref_grid_spec_1_str
    assert da_1.attrs["earthkit_grid_spec"] == ref_grid_spec_1_str
    assert da_1.earthkit.grid_spec == ref_grid_spec_1_dict

    field_1 = da_1.earthkit._reference_field
    assert field_1 is not None
    assert field_1.geography.grid_spec() == ref_grid_spec_1_dict
    assert da_1.attrs["_earthkit"]["grid_spec"] == ref_grid_spec_1_str
    assert da_1.attrs["earthkit_grid_spec"] == ref_grid_spec_1_str
