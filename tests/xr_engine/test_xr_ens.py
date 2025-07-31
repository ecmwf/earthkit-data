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
from earthkit.data.testing import earthkit_remote_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from xr_engine_fixtures import compare_dims  # noqa: E402


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs,dims",
    [
        (
            {},
            {
                "number": [0, 1, 2],
            },
        ),
        (
            {
                "dim_roles": {"number": "perturbationNumber"},
                "dim_name_from_role_name": True,
            },
            {
                "number": [0, 1, 2],
            },
        ),
        (
            {
                "dim_roles": {"ens": "perturbationNumber"},
                "dim_name_from_role_name": True,
            },
            {
                "number": [0, 1, 2],
            },
        ),
        (
            {
                "dim_roles": {"number": "perturbationNumber"},
                "dim_name_from_role_name": False,
            },
            {
                "perturbationNumber": [0, 1, 2],
            },
        ),
    ],
)
def test_xr_number_dim(kwargs, dims):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/ens/ens_cf_pf.grib"))

    ds = ds_ek.to_xarray(**kwargs)
    compare_dims(ds, dims, order_ref_var="t")


@pytest.mark.cache
def test_xr_number_dim_missing():
    ds_ek = from_source(
        "url", earthkit_remote_test_data_file("test-data", "xr_engine", "date", "t2_td2_1_year.grib")
    )

    ds = ds_ek[10].to_xarray(time_dim_mode="valid_time", ensure_dims="number", fill_metadata={"number": 10})
    assert ds is not None

    dims = {"number": [10]}
    compare_dims(ds, dims, order_ref_var="2t")
