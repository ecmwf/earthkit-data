#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import sys

import pytest

from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_remote_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from xr_engine_fixtures import compare_dims  # noqa: E402


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "kwargs,dims",
    [
        (
            {"profile": "earthkit"},
            {
                "member": ["0", "1", "2"],
            },
        ),
        (
            {
                "profile": "earthkit",
                "dim_roles": {"member": "metadata.perturbationNumber"},
                "dim_name_from_role_name": True,
            },
            {
                "member": [0, 1, 2],
            },
        ),
        (
            {
                "profile": "earthkit",
                "dim_roles": {"member": "metadata.perturbationNumber"},
                "dim_name_from_role_name": False,
            },
            {
                "perturbationNumber": [0, 1, 2],
            },
        ),
        (
            {"profile": "mars"},
            {
                "member": [0, 1, 2],
            },
        ),
        (
            {
                "profile": "mars",
                "dim_roles": {"member": "metadata.perturbationNumber"},
                "dim_name_from_role_name": True,
            },
            {
                "member": [0, 1, 2],
            },
        ),
        (
            {
                "profile": "mars",
                "dim_roles": {"member": "metadata.perturbationNumber"},
                "dim_name_from_role_name": False,
            },
            {
                "perturbationNumber": [0, 1, 2],
            },
        ),
    ],
)
def test_xr_engine_member_dim_1(allow_holes, lazy_load, kwargs, dims):
    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine/ens/ens_cf_pf.grib"))

    ds = ds_ek.to_xarray(allow_holes=allow_holes, lazy_load=lazy_load, **kwargs)
    compare_dims(ds, dims, order_ref_var="t")


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "kwargs,dims",
    [
        (
            {
                "profile": "mars",
                "dim_roles": {"ens": "metadata.perturbationNumber"},
                "dim_name_from_role_name": True,
            },
            {
                "member": [0, 1, 2],
            },
        ),
        (
            {
                "profile": "mars",
                "dim_roles": {"number": "metadata.perturbationNumber"},
                "dim_name_from_role_name": True,
            },
            {
                "member": [0, 1, 2],
            },
        ),
    ],
)
def test_xr_engine_member_dim_2(allow_holes, lazy_load, kwargs, dims):
    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine/ens/ens_cf_pf.grib"))

    with pytest.raises(ValueError):
        ds_ek.to_xarray(allow_holes=allow_holes, lazy_load=lazy_load, **kwargs)


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_member_dim_missing_1(allow_holes, lazy_load):
    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine", "date", "t2_td2_1_year.grib"))

    ds = ds_ek[10].to_xarray(
        profile="mars",
        time_dim_mode="valid_time",
        ensure_dims="member",
        fill_metadata={"metadata.number": 10},
        allow_holes=allow_holes,
        lazy_load=lazy_load,
    )
    assert ds is not None

    dims = {"member": [10]}
    compare_dims(ds, dims, order_ref_var="2t")


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_member_dim_missing_2(allow_holes, lazy_load):
    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine", "date", "t2_td2_1_year.grib"))

    ds = ds_ek[10].to_xarray(
        profile="mars",
        time_dim_mode="valid_time",
        dim_roles={"member": "metadata.number"},
        ensure_dims="number",
        fill_metadata={"metadata.number": 10},
        dim_name_from_role_name=False,
        allow_holes=allow_holes,
        lazy_load=lazy_load,
    )
    assert ds is not None

    dims = {"number": [10]}
    compare_dims(ds, dims, order_ref_var="2t")
